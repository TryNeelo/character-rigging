import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/scheduler.dart';
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
  });

  final NovaController controller;
  final NovaFraming framing;
  final NovaAlign align;

  /// White sticker outline and soft shadow around Nova.
  final bool outline;

  /// Breathing, slight sway and a small nod while talking.
  final bool idle;

  /// Random blinks every few seconds.
  final bool blink;

  @override
  State<NovaCharacter> createState() => _NovaCharacterState();
}

enum _Eye { open, half, closed }

class _NovaCharacterState extends State<NovaCharacter> with SingleTickerProviderStateMixin {
  NovaRig? _rig;
  late final Ticker _ticker;
  double _t = 0, _nod = 0, _look = 0, _raiseLeft = 0, _raiseRight = 0;
  _Eye _eye = _Eye.open;
  Timer? _blinkTimer;
  final _random = math.Random();

  static const _mouths = ['smile', 'X', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_tick)..start();
    NovaRig.load().then((rig) {
      if (!mounted) return;
      setState(() => _rig = rig);
      _scheduleBlink();
    });
  }

  @override
  void didUpdateWidget(NovaCharacter old) {
    super.didUpdateWidget(old);
    if (old.blink != widget.blink) _scheduleBlink();
  }

  @override
  void dispose() {
    _ticker.dispose();
    _blinkTimer?.cancel();
    super.dispose();
  }

  String get _shape => widget.controller.line?.shapeAt(widget.controller.time) ?? 'smile';

  void _tick(Duration elapsed) {
    final rig = _rig;
    if (rig == null) return;
    final c = widget.controller;
    final lineLook = c.line?.lookAt(c.time) ?? 0;
    final lookTarget = lineLook != 0 ? lineLook : c.look.value;
    final (armLeft, armRight) = c.line?.armsAt(c.time) ?? (0.0, 0.0);
    final open = (c.isSpeaking && widget.idle) ? (rig.mouthOpenness[_shape] ?? 0) : 0.0;
    setState(() {
      _t = elapsed.inMicroseconds / 1e6;
      _nod += (open - _nod) * rig.idle('talkNodSmoothing');
      _look += (lookTarget - _look) * rig.look('smoothing');
      _raiseLeft += (armLeft - _raiseLeft) * rig.gesture('smoothing');
      _raiseRight += (armRight - _raiseRight) * rig.gesture('smoothing');
    });
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
      if (widget.align == NovaAlign.left) vx = math.min(vx, rig.anchorX - f.width / 2);
      if (widget.align == NovaAlign.right) vx = math.max(vx, rig.anchorX + f.width / 2 - vw);
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

  Widget _character(NovaRig rig, double s) {
    final body = _layers(rig, s);
    if (!widget.outline) return body;
    // Outline: blur the silhouette, then keep everything above a low alpha as solid white.
    // The shadow is that white edge, blurred again at 25% black.
    const white = ColorFilter.matrix([0, 0, 0, 0, 255, 0, 0, 0, 0, 255, 0, 0, 0, 0, 255, 0, 0, 0, 40, -408]);
    final shadowA = rig.outline('shadowOpacity');
    final black = ColorFilter.matrix([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, shadowA, 0]);
    ui.ImageFilter blur(double sigma) => ui.ImageFilter.blur(sigmaX: sigma * s, sigmaY: sigma * s, tileMode: TileMode.decal);
    final edge = ColorFiltered(colorFilter: white, child: ImageFiltered(imageFilter: blur(rig.outline('blur')), child: body));
    return Stack(clipBehavior: Clip.none, children: [
      ImageFiltered(imageFilter: blur(rig.outline('shadowBlur')), child: ColorFiltered(colorFilter: black, child: edge)),
      edge,
      body,
    ]);
  }

  Widget _layers(NovaRig rig, double s) {
    final w = rig.width * s, h = rig.height * s;
    Widget part(String name) => SvgPicture.asset('assets/parts/$name.svg',
        package: novaPackage, width: w, height: h, fit: BoxFit.fill, allowDrawingOutsideViewBox: true);
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

    final head = Transform(
      transform: Matrix4.translationValues(rig.look('headPx') * _look * s, -rig.idle('talkNodPx') * _nod * s, 0)
        ..multiply(rotateAbout(rig.headPivot,
            sway - rig.idle('talkNodDegrees') * _nod + rig.look('headDegrees') * _look)),
      child: Stack(children: [
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
        part('head_front'),
        for (final m in _mouths) shown(m == shape, part('mouth_$m')),
        part('head_top'),
      ]),
    );

    return SizedBox(
      width: w,
      height: h,
      child: Stack(children: [
        part('legs'),
        Transform.translate(
          offset: Offset(0, upperY * s),
          child: Stack(children: [
            // Positive raises lift each arm outward, away from the body
            Transform(transform: rotateAbout(rig.armLeftPivot, _raiseLeft + swing), child: part('arm_left')),
            Transform(transform: rotateAbout(rig.armRightPivot, -_raiseRight - swing), child: part('arm_right')),
            part('body'),
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
