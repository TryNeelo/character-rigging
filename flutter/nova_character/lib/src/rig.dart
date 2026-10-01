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

/// Nova's rig: canvas, pivots and motion settings, loaded from assets/rig.json.
/// Generated from the character repo by tools/build_flutter.py.
class NovaRig {
  NovaRig._(this._j)
      : width = _num(_j['canvas']['width']),
        height = _num(_j['canvas']['height']),
        anchorX = _num(_j['anchor']['x']),
        headPivot = _offset(_j['pivots']['head']),
        armLeftPivot = _offset(_j['pivots']['armLeft']),
        armRightPivot = _offset(_j['pivots']['armRight']),
        eyeCenters = [for (final c in _j['eyes']['centers'] as List) _offset(c)],
        eyeRadius = _num(_j['eyes']['radius']),
        framing = {
          for (final e in (_j['framing'] as Map<String, dynamic>).entries)
            e.key: NovaFramingSpec.fromJson(e.value as Map<String, dynamic>)
        },
        mouthOpenness = {
          for (final e in (_j['mouthOpenness'] as Map<String, dynamic>).entries) e.key: _num(e.value)
        };

  final Map<String, dynamic> _j;
  final double width, height, anchorX, eyeRadius;
  final Offset headPivot, armLeftPivot, armRightPivot;
  final List<Offset> eyeCenters;
  final Map<String, NovaFramingSpec> framing;
  final Map<String, double> mouthOpenness;

  double idle(String key) => _num(_j['idle'][key]);
  double look(String key) => _num(_j['look'][key]);
  double blink(String key) => _num(_j['blink'][key]);
  double outline(String key) => _num(_j['outline'][key]);

  static Future<NovaRig>? _loading;

  /// Loads the rig once and shares it between all Nova widgets.
  static Future<NovaRig> load() => _loading ??= rootBundle
      .loadString(novaAsset('rig.json'))
      .then((s) => NovaRig._(jsonDecode(s) as Map<String, dynamic>));

  static double _num(dynamic v) => (v as num).toDouble();
  static Offset _offset(dynamic v) => Offset(_num((v as List)[0]), _num(v[1]));
}
