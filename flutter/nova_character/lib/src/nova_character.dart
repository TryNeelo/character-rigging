import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/widgets.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'controller.dart';
import 'rig.dart';

/// How much of Nova to show. The crop line sits at the bottom of the widget.
enum NovaFraming {
  full('full'),
  kneesUp('knees'),
  waistUp('waist'),
  closeUp('close');

  const NovaFraming(this.key);
  final String key;
}

/// Where Nova stands in the widget when it's wider than he needs.
enum NovaAlign { left, center, right }

/// Nova, drawn live: lip-sync, blinks, subtle idle motion and looks.
///
/// Fills the space it's given. If the height is unbounded, it sizes itself to the framing.
class NovaCharacter extends StatefulWidget {
  const NovaCharacter({
    super.key,
    required this.controller,
    this.framing = NovaFraming.full,
    this.align = NovaAlign.center,
    this.outline = true,
    this.idle = true,
    this.blink = true,
    this.outfit,
  });

  final NovaController controller;
  final NovaFraming framing;
  final NovaAlign align;

  /// White sticker outline and soft shadow around Nova.
  final bool outline;

  /// Movement switch: breathing and slight sway between lines, nods and brow lifts
  /// while talking. When off, Nova only blinks and lip-syncs, and he doesn't redraw
  /// at all between blinks.
  final bool idle;

  /// Random blinks every few seconds.
  final bool blink;

  /// Outfit id, such as "hoodie" or "aviator". Null uses the default outfit.
  /// Unknown ids fall back to the default.
  final String? outfit;

  @override
  State<NovaCharacter> createState() => _NovaCharacterState();
}

enum _Eye { open, half, closed }

class _NovaCharacterState extends State<NovaCharacter> {
  NovaRig? _rig;
  // Nova's own frame clock: wakes only at his frame rate (not every screen refresh),
  // and stops entirely when he's still.
  Timer? _frameTimer;
  final Stopwatch _clock = Stopwatch()..start();
  // Arms ease in and out: each follows a midpoint that follows the target, so moves start softly
  double _midLeft = 0, _midRight = 0;
  double _t = 0, _lastFrame = -1, _look = 0, _raiseLeft = 0, _raiseRight = 0, _browLift = 0, _browTilt = 0;
  _Eye _eye = _Eye.open;
  Timer? _blinkTimer;
  final _random = math.Random();

  static const _mouths = ['smile', 'X', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_wake);
    NovaRig.load().then((rig) {
      if (!mounted) return;
      setState(() => _rig = rig);
      _scheduleBlink();
      _wake();
    });
  }

  @override
  void didUpdateWidget(NovaCharacter old) {
    super.didUpdateWidget(old);
    if (old.blink != widget.blink) _scheduleBlink();
    if (old.controller != widget.controller) {
      old.controller.removeListener(_wake);
      widget.controller.addListener(_wake);
    }
    _wake();
  }

  /// Starts redrawing again after Nova has been still (a line starts, a look is set...).
  void _wake() {
    if (_frameTimer == null && mounted) _nextFrame();
  }

  // True while an arm or the head is on its way somewhere: those moves get full smoothness
  bool _moving = false;

  void _nextFrame() {
    final rig = _rig;
    if (rig == null) return;
    final fps = _moving
        ? rig.frameRate('moving')
        : widget.controller.isSpeaking
            ? rig.frameRate('talking')
            : rig.frameRate('idle');
    _frameTimer = Timer(Duration(microseconds: (1e6 / fps).round()), _frame);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_wake);
    _frameTimer?.cancel();
    _blinkTimer?.cancel();
    super.dispose();
  }

  String get _shape => widget.controller.line?.shapeAt(widget.controller.time) ?? 'smile';

  /// One frame of Nova: 30 fps while talking, 15 fps for slow idle motion, and none
  /// at all once he's still with movement off.
  void _frame() {
    _frameTimer = null;
    final rig = _rig;
    if (rig == null || !mounted) return;
    final c = widget.controller;
    final now = _clock.elapsedMicroseconds / 1e6;
    final fps = _moving ? rig.frameRate('moving') : c.isSpeaking ? rig.frameRate('talking') : rig.frameRate('idle');
    final dt = _lastFrame < 0 ? 1 / fps : math.min(now - _lastFrame, 0.25);
    _lastFrame = now;
    final lineLook = c.line?.lookAt(c.time) ?? 0;
    final lookTarget = lineLook != 0 ? lineLook : c.look.value;
    final (armLeft, armRight) = c.line?.armsAt(c.time) ?? (0.0, 0.0);
    final (lift, tilt) = rig.browExpressions[c.expression ?? c.line?.expressionAt(c.time)] ?? (0.0, 0.0);
    // Smoothing amounts are tuned per 60 fps frame; scale them to the real frame time
    double ease(double perFrame) => 1 - math.pow(1 - perFrame, dt * 60).toDouble();
    setState(() {
      _t = now;
      _look += (lookTarget - _look) * ease(rig.look('smoothing'));
      final arm = ease(rig.gesture('smoothing') * 1.6);
      _midLeft += (armLeft - _midLeft) * arm;
      _midRight += (armRight - _midRight) * arm;
      _raiseLeft += (_midLeft - _raiseLeft) * arm;
      _raiseRight += (_midRight - _raiseRight) * arm;
      _browLift += (lift - _browLift) * ease(rig.brows('smoothing'));
      _browTilt += (tilt - _browTilt) * ease(rig.brows('smoothing'));
    });
    // With movement off and nothing left to settle, stop redrawing until something changes.
    // Blinks redraw on their own.
    _moving = (lookTarget - _look).abs() > 0.01 || (armLeft - _raiseLeft).abs() > 0.3 || (armRight - _raiseRight).abs() > 0.3;
    final settled = (lookTarget - _look).abs() < 0.002 && (armLeft - _raiseLeft).abs() < 0.05 &&
        (armRight - _raiseRight).abs() < 0.05 && (lift - _browLift).abs() < 0.02 && (tilt - _browTilt).abs() < 0.02;
    if (!widget.idle && !c.isSpeaking && settled) {
      _lastFrame = -1;
    } else {
      _nextFrame();
    }
  }

  /// A smooth bump around a stressed moment, [d] seconds after it: quick rise, short hold, slower fall.
  static double _bump(double d, double rise, double hold, double fall) {
    var k = 0.0;
    if (d >= -rise && d < 0) {
      k = 1 + d / rise;
    } else if (d >= 0 && d < hold) {
      k = 1;
    } else if (d >= hold && d < hold + fall) {
      k = 1 - (d - hold) / fall;
    }
    return k * k * (3 - 2 * k);
  }

  /// Brow lift from stressed moments in the line.
  double _autoBrowLift(NovaRig rig) {
    final c = widget.controller;
    final line = c.line;
    if (line == null || !widget.idle) return 0;
    var v = 0.0;
    for (final (time, strength) in line.emphasis) {
      v = math.max(v, _bump(c.time - time, rig.brows('autoRiseSeconds'), rig.brows('autoHoldSeconds'),
              rig.brows('autoFallSeconds')) * strength);
    }
    return v * rig.brows('autoLiftPx');
  }

  /// Talking head: a small nod on each stressed word, with a slight tilt that alternates
  /// side to side. Returns (dip down in canvas units, tilt in degrees).
  (double, double) _talkHead(NovaRig rig) {
    final c = widget.controller;
    final line = c.line;
    if (line == null || !widget.idle) return (0, 0);
    var dip = 0.0, tilt = 0.0;
    for (final (i, (time, strength)) in line.emphasis.indexed) {
      final k = _bump(c.time - time, rig.talk('riseSeconds'), rig.talk('holdSeconds'), rig.talk('fallSeconds')) * strength;
      dip = math.max(dip, k);
      tilt += (i.isOdd ? -1 : 1) * k;
    }
    return (dip * rig.talk('nodPx'), tilt * rig.talk('tiltDegrees'));
  }

  // ---- Blinks: half lid, closed, half lid, open ----
  void _scheduleBlink() {
    _blinkTimer?.cancel();
    final rig = _rig;
    if (rig == null || !widget.blink) return;
    final gap = rig.blink('minGapMs') + _random.nextDouble() * (rig.blink('maxGapMs') - rig.blink('minGapMs'));
    _blinkTimer = Timer(Duration(milliseconds: gap.round()), () async {
      await _blink();
      if (_random.nextDouble() < rig.blink('doubleChance')) {
        await _wait(rig.blink('doubleGapMs'));
        await _blink();
      }
      _scheduleBlink();
    });
  }

  Future<void> _wait(double ms) => Future.delayed(Duration(milliseconds: ms.round()));

  Future<void> _blink() async {
    final rig = _rig!;
    for (final (eye, ms) in [
      (_Eye.half, rig.blink('halfMs')),
      (_Eye.closed, rig.blink('closedMs')),
      (_Eye.half, rig.blink('halfAgainMs')),
    ]) {
      if (!mounted) return;
      setState(() => _eye = eye);
      await _wait(ms);
    }
    if (mounted) setState(() => _eye = _Eye.open);
  }

  // ---- Drawing ----
  @override
  Widget build(BuildContext context) {
    final rig = _rig;
    final f = rig?.framing[widget.framing.key];
    return LayoutBuilder(builder: (context, box) {
      final aspect = f == null ? 556 / 837 : f.width / (f.bottom - f.top);
      final fw = box.hasBoundedWidth ? box.maxWidth : 300.0;
      final fh = box.hasBoundedHeight ? box.maxHeight : fw / aspect;
      if (rig == null || f == null) return SizedBox(width: fw, height: fh);

      // Fit the framing's height (or width) into the widget, crop line at the bottom.
      final s = math.min(fh / (f.bottom - f.top), fw / f.width);
      final vw = fw / s, vh = fh / s;
      var vx = rig.anchorX - vw / 2;
      if (widget.align == NovaAlign.left) vx = math.max(vx, rig.anchorX - f.width / 2);
      if (widget.align == NovaAlign.right) vx = math.min(vx, rig.anchorX + f.width / 2 - vw);
      final vy = f.bottom - vh;

      return ClipRect(
        child: SizedBox(
          width: fw,
          height: fh,
          child: Stack(clipBehavior: Clip.none, children: [
            Positioned(
              left: -vx * s,
              top: -vy * s,
              width: rig.width * s,
              height: rig.height * s,
              child: _character(rig, s),
            ),
          ]),
        ),
      );
    });
  }

  /// The white outline is drawn into the art: white copies of the outer parts, a little
  /// bigger, drawn first with the same moves, then the coloured parts on top. No blur.
  Widget _character(NovaRig rig, double s) {
    if (!widget.outline) return _layers(rig, s);
    return Stack(clipBehavior: Clip.none, children: [_layers(rig, s, outline: true), _layers(rig, s)]);
  }

  /// Nova's parts, back to front, posed for this frame. With [outline], only the white
  /// outline copies of the outer parts (legs, arms, body, head, hat).
  Widget _layers(NovaRig rig, double s, {bool outline = false}) {
    final w = rig.width * s, h = rig.height * s;
    // Each part is drawn once and kept (RepaintBoundary); moving it only shifts the finished
    // picture, so breathing and sway don't redraw the art.
    Widget part(String name) => RepaintBoundary(
        child: SvgPicture.asset('assets/parts/$name.svg',
            package: novaPackage, width: w, height: h, fit: BoxFit.fill, allowDrawingOutsideViewBox: true));
    Widget shown(bool visible, Widget child) =>
        Visibility(visible: visible, maintainState: true, maintainAnimation: true, maintainSize: true, child: child);
    Matrix4 rotateAbout(Offset p, double degrees) => Matrix4.translationValues(p.dx * s, p.dy * s, 0)
      ..multiply(Matrix4.rotationZ(degrees * math.pi / 180))
      ..multiply(Matrix4.translationValues(-p.dx * s, -p.dy * s, 0));

    final idle = widget.idle ? 1.0 : 0.0;
    final breathSec = rig.idle('breathSeconds');
    final breath = idle * math.sin(_t * 2 * math.pi / breathSec);
    final sway = idle * math.sin(_t * 2 * math.pi / rig.idle('swaySeconds')) * rig.idle('swayDegrees');
    final swing = idle * math.sin(_t * 2 * math.pi / breathSec + 0.6) * rig.idle('armSwingDegrees');
    final upperY = idle * -rig.idle('breathPx') * (1 + breath);
    final shape = _shape;
    final browLift = _browLift + _autoBrowLift(rig);
    final (dip, talkTilt) = _talkHead(rig);
    final outfitId = rig.outfits.containsKey(widget.outfit) ? widget.outfit! : rig.defaultOutfit;
    final outfit = rig.outfits[outfitId]!;

    final ol = outline ? '_outline' : '';
    final head = Transform(
      transform: Matrix4.translationValues(rig.look('headPx') * _look * s, dip * s, 0)
        ..multiply(rotateAbout(rig.headPivot, sway + talkTilt + rig.look('headDegrees') * _look)),
      child: Stack(children: outline
          ? [
              if (outfit.hatBack) part('hat_back_${outfitId}_outline'),
              part('head_outline'),
              part('hat_${outfitId}_outline'),
            ]
          : [
        if (outfit.hatBack) part('hat_back_$outfitId'),
        part('head_back'),
        ClipPath(
          clipper: _EyesClipper(rig, s),
          child: Stack(children: [
            // Each pupil moves from its resting spot to the same spot in its own eye
            for (final (i, side) in [(0, 'left'), (1, 'right')])
              Transform.translate(
                offset: Offset((rig.look('pupilReach') * _look - rig.pupilRest[i] * _look.abs()) * s, 0),
                child: part('pupil_$side'),
              ),
          ]),
        ),
        shown(_eye == _Eye.half, part('lids_half')),
        shown(_eye == _Eye.closed, part('lids_closed')),
        part('ears'),
        // Positive tilt raises the inner ends: the screen-left brow turns anticlockwise, the right one clockwise
        for (final (side, pivot, sign) in [('left', rig.browLeftPivot, -1.0), ('right', rig.browRightPivot, 1.0)])
          Transform(
            transform: Matrix4.translationValues(0, -browLift * s, 0)..multiply(rotateAbout(pivot, sign * _browTilt)),
            child: part('brow_$side'),
          ),
        part('muzzle'),
        for (final m in _mouths) shown(m == shape, part('mouth_$m')),
        part('nose'),
        part('hat_$outfitId'),
      ]),
    );

    return SizedBox(
      width: w,
      height: h,
      child: Stack(children: [
        part('legs_$outfitId$ol'),
        Transform.translate(
          offset: Offset(0, upperY * s),
          child: Stack(children: [
            // Positive raises lift each arm outward, away from the body
            Transform(transform: rotateAbout(outfit.armLeftPivot, _raiseLeft + swing), child: part('arm_left_$outfitId$ol')),
            Transform(transform: rotateAbout(outfit.armRightPivot, -_raiseRight - swing), child: part('arm_right_$outfitId$ol')),
            part('body_$outfitId$ol'),
            head,
          ]),
        ),
      ]),
    );
  }
}

/// Keeps the pupils inside the eye whites when they move.
class _EyesClipper extends CustomClipper<Path> {
  _EyesClipper(this.rig, this.s);
  final NovaRig rig;
  final double s;

  @override
  Path getClip(Size size) {
    final path = Path();
    for (final c in rig.eyeCenters) {
      path.addOval(Rect.fromCircle(center: c * s, radius: rig.eyeRadius * s));
    }
    return path;
  }

  @override
  bool shouldReclip(_EyesClipper old) => old.s != s;
}
