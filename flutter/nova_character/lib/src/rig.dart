import 'dart:convert';

import 'package:flutter/services.dart';

/// The package name, used to resolve bundled assets.
const novaPackage = 'nova_character';

/// Asset key of a file bundled with this package.
String novaAsset(String path) => 'packages/$novaPackage/assets/$path';

/// A framing preset: a vertical range of Nova's canvas to show, and the width to keep.
class NovaFramingSpec {
  const NovaFramingSpec({required this.label, required this.top, required this.bottom, required this.width});
  final String label;
  final double top, bottom, width;

  factory NovaFramingSpec.fromJson(Map<String, dynamic> j) => NovaFramingSpec(
      label: j['label'] as String,
      top: (j['top'] as num).toDouble(),
      bottom: (j['bottom'] as num).toDouble(),
      width: (j['width'] as num).toDouble());
}

/// An outfit: its name and the shoulder pivots its sleeves give.
class NovaOutfitSpec {
  const NovaOutfitSpec(
      {required this.label,
      required this.armLeftPivot,
      required this.armRightPivot,
      this.hat = true,
      this.hatBack = false,
      this.bodyBack = false,
      this.headOutline = true,
      this.elbowLeftPivot,
      this.elbowRightPivot,
      this.armRestLeft,
      this.armRestRight,
      this.armDownLeft = 0,
      this.armDownRight = 0,
      this.forearmBehind = false});
  final String label;

  /// Whether there is a hat (hat.svg). Obselda has none.
  final bool hat;

  /// Whether the hat has a piece behind the head (hat_back_<id>.svg), like a hard hat's brim.
  final bool hatBack;

  /// Whether the body has a piece behind the arms (body_back.svg), like a cape.
  final bool bodyBack;

  /// Whether the head gets its white outline. Off for Nova's diver outfit: his head is inside a
  /// glass helmet, which has the outline instead.
  final bool headOutline;

  /// Elbows, for arms that bend (forearm_<side>.svg turns about them). Null for arms without elbows.
  final Offset? elbowLeftPivot, elbowRightPivot;

  /// For arms with elbows, the resting pose as drawn: (shoulder out from straight down,
  /// elbow bend), in degrees. Skyrian rests with his hands behind his back.
  final (double, double)? armRestLeft, armRestRight;

  /// For arms with elbows, the shoulder's angle out from vertical when the arm hangs straight
  /// down as drawn. Arm markers count their degrees up from this pose (0 is arms down).
  final double armDownLeft, armDownRight;

  bool get hasElbows => elbowLeftPivot != null;

  /// Whether the forearms are drawn behind the upper arms and sleeves (Tydras).
  final bool forearmBehind;
  final Offset armLeftPivot, armRightPivot;
}

/// A character's rig: canvas, pivots and motion settings, loaded from assets/rig.json (Nova)
/// or assets/characters/<id>/rig.json (every other character).
/// Generated from the character repo by tools/build_flutter.py.
class NovaRig {
  NovaRig._(this._j, this.character)
      : label = _j['label'] as String? ?? 'Nova',
        partsDir = _j['partsDir'] as String? ?? 'parts',
        headLayers = [for (final l in (_j['headLayers'] as List?) ?? _novaHead) l as String],
        headBehindLayers = [for (final l in (_j['headBehindLayers'] as List?) ?? const []) l as String],
        width = _num(_j['canvas']['width']),
        height = _num(_j['canvas']['height']),
        anchorX = _num(_j['anchor']['x']),
        headPivot = _offset(_j['pivots']['head']),
        defaultOutfit = _j['defaultOutfit'] as String,
        outfits = {
          for (final e in (_j['outfits'] as Map<String, dynamic>).entries)
            e.key: NovaOutfitSpec(
                label: e.value['label'] as String,
                armLeftPivot: _offset(e.value['pivots']['armLeft']),
                armRightPivot: _offset(e.value['pivots']['armRight']),
                hat: e.value['hat'] as bool? ?? true,
                hatBack: e.value['hatBack'] as bool? ?? false,
                bodyBack: e.value['bodyBack'] as bool? ?? false,
                headOutline: e.value['headOutline'] as bool? ?? true,
                elbowLeftPivot: e.value['pivots']['elbowLeft'] == null ? null : _offset(e.value['pivots']['elbowLeft']),
                elbowRightPivot: e.value['pivots']['elbowRight'] == null ? null : _offset(e.value['pivots']['elbowRight']),
                armRestLeft: _pair(e.value['armRest']?['left']),
                armRestRight: _pair(e.value['armRest']?['right']),
                armDownLeft: (e.value['armDown']?['left'] as num?)?.toDouble() ?? 0,
                armDownRight: (e.value['armDown']?['right'] as num?)?.toDouble() ?? 0,
                forearmBehind: e.value['forearmBehind'] as bool? ?? false)
        },
        eyeCenters = [for (final c in _j['eyes']['centers'] as List) _offset(c)],
        eyeClipPolygons = [
          for (final p in (_j['eyes']['clipPolygons'] as List?) ?? const []) [for (final c in p as List) _offset(c)]
        ],
        eyeRadius = _num(_j['eyes']['radius']),
        pupilRest = [for (final v in _j['eyes']['pupilRest'] as List) _num(v)],
        pupilRestY = _num(_j['eyes']['pupilRestY']),
        framing = {
          for (final e in (_j['framing'] as Map<String, dynamic>).entries)
            e.key: NovaFramingSpec.fromJson(e.value as Map<String, dynamic>)
        };

  final Map<String, dynamic> _j;

  /// The character's id ("nova", "skyrian") and name.
  final String character, label;

  /// Where this character's part files are, under assets/.
  final String partsDir;

  /// The head's layers, back to front: part files in base/, or the face rig's moving pieces
  /// ("pupils", "lids", "brows", "mouth", "hat", "hat_back").
  final List<String> headLayers;

  /// Head parts drawn behind the body and arms that still turn with the head, like Tydras's hair
  /// (part files in base/).
  final List<String> headBehindLayers;
  static const _novaHead = ['hat_back', 'head_back', 'pupils', 'lids', 'ears', 'brows', 'muzzle', 'mouth', 'nose', 'hat'];
  final double width, height, anchorX, eyeRadius;
  final Offset headPivot;

  /// Outfits by id (for example "hoodie", "aviator"). Each has its own legs, arms, body and hat.
  final Map<String, NovaOutfitSpec> outfits;
  final String defaultOutfit;
  final List<Offset> eyeCenters;

  /// When a character's eye whites aren't round (Voltis), their outlines: the pupils stay inside
  /// these instead of circles.
  final List<List<Offset>> eyeClipPolygons;

  /// How far each pupil (left, right) sits from its eye's centre at rest, in canvas units.
  final List<double> pupilRest;

  /// How far both pupils sit below their eye's centre at rest.
  final double pupilRestY;
  final Map<String, NovaFramingSpec> framing;


  double idle(String key) => _num(_j['idle'][key]);
  double talk(String key) => _num(_j['talk'][key]);
  double look(String key) => _num(_j['look'][key]);
  double blink(String key) => _num(_j['blink'][key]);
  double gesture(String key) => _num(_j['gesture'][key]);
  double outline(String key) => _num(_j['outline'][key]);
  double brows(String key) => _num(_j['brows'][key]);
  double frameRate(String key) => _num(_j['frameRate'][key]);

  /// Brow expressions by name: (lift in canvas units, tilt in degrees; positive raises the inner ends).
  late final Map<String, (double, double)> browExpressions = {
    for (final e in (_j['brows']['expressions'] as Map<String, dynamic>).entries)
      e.key: (_num(e.value['liftPx']), _num(e.value['tiltDegrees']))
  };

  /// Where each brow (by screen side) tilts from.
  late final Offset browLeftPivot = _offset(_j['brows']['pivots']['left']);
  late final Offset browRightPivot = _offset(_j['brows']['pivots']['right']);

  static final Map<String, Future<NovaRig>> _loading = {};

  /// Loads a character's rig once and shares it between all widgets showing him.
  /// Nova by default; an unknown character falls back to Nova.
  static Future<NovaRig> load([String character = 'nova']) => _loading[character] ??= rootBundle
      .loadString(novaAsset(character == 'nova' ? 'rig.json' : 'characters/$character/rig.json'))
      .then((s) => NovaRig._(jsonDecode(s) as Map<String, dynamic>, character))
      .catchError((Object e) => character == 'nova' ? Future<NovaRig>.error(e) : load());

  static double _num(dynamic v) => (v as num).toDouble();
  static Offset _offset(dynamic v) => Offset(_num((v as List)[0]), _num(v[1]));
  static (double, double)? _pair(dynamic v) => v == null ? null : (_num((v as List)[0]), _num(v[1]));
}
