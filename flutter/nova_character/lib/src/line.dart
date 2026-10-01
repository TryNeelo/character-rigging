import 'dart:convert';

import 'package:flutter/services.dart';

import 'rig.dart';

/// One mouth shape held from [start] to [end] seconds. Shapes follow Rhubarb Lip Sync
/// naming: A to H, X (rest), plus "smile" when Nova isn't speaking.
class NovaCue {
  const NovaCue(this.start, this.end, this.shape);
  final double start, end;
  final String shape;
}

/// A moment in a line. Either an app event (`type: "event"`, with a [name]) or something
/// Nova does from [time] to [end]: `type: "look"` toward [direction] "left" or "right" of
/// the screen, or `type: "arm"` raising the arm on the screen's [side] by [degrees].
class NovaMarker {
  const NovaMarker(
      {required this.time, required this.type, this.end, this.name, this.direction, this.side, this.degrees});
  final double time;
  final double? end;
  final String type;
  final String? name;
  final String? direction;
  final String? side;
  final double? degrees;

  factory NovaMarker.fromJson(Map<String, dynamic> j) => NovaMarker(
      time: (j['time'] as num).toDouble(),
      end: (j['end'] as num?)?.toDouble(),
      type: j['type'] as String,
      name: j['name'] as String?,
      direction: j['direction'] as String?,
      side: j['side'] as String?,
      degrees: (j['degrees'] as num?)?.toDouble());
}

/// A dialogue line (or a whole scene): its audio, mouth timing and markers.
class NovaLine {
  NovaLine._(this.id, this.audio, this.duration, this.cues, this.markers);
  final String id, audio;
  final double duration;
  final List<NovaCue> cues;
  final List<NovaMarker> markers;

  /// Asset key of this line's audio file.
  String get audioAsset => novaAsset('lines/$id/$audio');

  static Future<NovaLine> load(String id) async {
    final j = jsonDecode(await rootBundle.loadString(novaAsset('lines/$id/timing.json'))) as Map<String, dynamic>;
    return NovaLine._(
        id,
        j['audio'] as String,
        (j['duration'] as num).toDouble(),
        [
          for (final c in j['cues'] as List)
            NovaCue((c['start'] as num).toDouble(), (c['end'] as num).toDouble(), c['shape'] as String)
        ],
        [for (final m in j['markers'] as List) NovaMarker.fromJson(m as Map<String, dynamic>)]);
  }

  /// Mouth shape at [t] seconds, or null outside the line.
  String? shapeAt(double t) {
    for (final c in cues) {
      if (t >= c.start && t < c.end) return c.shape;
    }
    return null;
  }

  /// How far each arm is raised at [t] seconds, in degrees: (left, right) by screen side.
  (double, double) armsAt(double t) {
    var left = 0.0, right = 0.0;
    for (final m in markers) {
      if (m.type == 'arm' && t >= m.time && t < (m.end ?? m.time)) {
        if (m.side == 'left') left = m.degrees ?? 0;
        if (m.side == 'right') right = m.degrees ?? 0;
      }
    }
    return (left, right);
  }

  /// Look direction at [t] seconds: -1 screen left, 1 screen right, 0 straight ahead.
  double lookAt(double t) {
    for (final m in markers) {
      if (m.type == 'look' && t >= m.time && t < (m.end ?? m.time)) return m.direction == 'left' ? -1 : 1;
    }
    return 0;
  }
}
