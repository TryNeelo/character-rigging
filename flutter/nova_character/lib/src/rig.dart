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
      {required this.label, required this.armLeftPivot, required this.armRightPivot, this.hatBack = false});
  final String label;

  /// Whether the hat has a piece behind the head (hat_back_<id>.svg), like a hard hat's brim.
  final bool hatBack;
  final Offset armLeftPivot, armRightPivot;
}

/// Nova's rig: canvas, pivots and motion settings, loaded from assets/rig.json.
/// Generated from the character repo by tools/build_flutter.py.
class NovaRig {
  NovaRig._(this._j)
      : width = _num(_j['canvas']['width']),
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
                hatBack: e.value['hatBack'] as bool? ?? false)
        },
        eyeCenters = [for (final c in _j['eyes']['centers'] as List) _offset(c)],
        eyeRadius = _num(_j['eyes']['radius']),
        pupilRest = [for (final v in _j['eyes']['pupilRest'] as List) _num(v)],
        framing = {
          for (final e in (_j['framing'] as Map<String, dynamic>).entries)
            e.key: NovaFramingSpec.fromJson(e.value as Map<String, dynamic>)
        };

  final Map<String, dynamic> _j;
  final double width, height, anchorX, eyeRadius;
  final Offset headPivot;

  /// Outfits by id (for example "hoodie", "aviator"). Each has its own legs, arms, body and hat.
  final Map<String, NovaOutfitSpec> outfits;
  final String defaultOutfit;
  final List<Offset> eyeCenters;

  /// How far each pupil (left, right) sits from its eye's centre at rest, in canvas units.
  final List<double> pupilRest;
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

  static Future<NovaRig>? _loading;

  /// Loads the rig once and shares it between all Nova widgets.
  static Future<NovaRig> load() => _loading ??= rootBundle
      .loadString(novaAsset('rig.json'))
      .then((s) => NovaRig._(jsonDecode(s) as Map<String, dynamic>));

  static double _num(dynamic v) => (v as num).toDouble();
  static Offset _offset(dynamic v) => Offset(_num((v as List)[0]), _num(v[1]));
}
