import 'dart:convert';

import 'package:flutter/services.dart';

import 'controller.dart';
import 'rig.dart';

/// One mouth shape held from [start] to [end] seconds. Shapes follow Rhubarb Lip Sync
/// naming: A to H, X (rest), plus "smile" when Nova isn't speaking.
class NovaCue {
  const NovaCue(this.start, this.end, this.shape);
  final double start, end;
  final String shape;
}

/// A moment in a line. Either an app event (`type: "event"`, with a [name]) or something
/// Nova does from [time] to [end]: `type: "look"` toward [direction] on screen ("left",
/// "right", "up", "down", "up-left", "up-right", "down-left", "down-right"), `type: "arm"` raising the arm on the screen's [side] by [degrees], or
/// `type: "expression"` setting his brows to [name] ("happy", "surprised", "concerned").
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

/// Decides which of a line's events are due as playback moves on. Each event fires once
/// per playthrough, even if the reported audio position wobbles backwards for a moment.
class NovaEventGate {
  NovaEventGate(this.line);
  final NovaLine line;
  final Set<int> _fired = {};

  /// Events whose time has been reached by [t] seconds and that haven't fired yet.
  List<NovaMarker> due(double t) {
    final out = <NovaMarker>[];
    for (final (i, m) in line.markers.indexed) {
      if (m.type == 'event' && m.name != null && t >= m.time && _fired.add(i)) out.add(m);
    }
    return out;
  }
}

/// One sentence of a line, to show as a subtitle from [start] to [end] seconds.
/// The app draws the subtitle in its own style.
class NovaCaption {
  const NovaCaption(this.start, this.end, this.text);
  final double start, end;
  final String text;

  @override
  String toString() => 'NovaCaption("$text", $start–$end s)';
}

/// A dialogue line (or a whole scene): its audio, mouth timing and markers.
class NovaLine {
  NovaLine._(this.id, this.audio, this.duration, this.cues, this.markers, this.emphasis, this.captions);
  final String id, audio;
  final double duration;
  final List<NovaCue> cues;
  final List<NovaMarker> markers;

  /// Stressed moments found in the audio, as (time in seconds, strength 0 to 1).
  /// Nova's brows lift briefly on each.
  final List<(double, double)> emphasis;

  /// The line's words, one entry per sentence, timed to the audio.
  final List<NovaCaption> captions;

  /// Asset key of this line's audio file.
  String get audioAsset => novaAsset('lines/$id/$audio');

  static Future<NovaLine> load(String id) async =>
      NovaLine.fromJson(jsonDecode(await rootBundle.loadString(novaAsset('lines/$id/timing.json'))) as Map<String, dynamic>);

  /// A line from its timing.json contents.
  factory NovaLine.fromJson(Map<String, dynamic> j) {
    return NovaLine._(
        j['id'] as String,
        j['audio'] as String,
        (j['duration'] as num).toDouble(),
        [
          for (final c in j['cues'] as List)
            NovaCue((c['start'] as num).toDouble(), (c['end'] as num).toDouble(), c['shape'] as String)
        ],
        [for (final m in j['markers'] as List) NovaMarker.fromJson(m as Map<String, dynamic>)],
        [
          for (final e in (j['emphasis'] as List?) ?? [])
            ((e['time'] as num).toDouble(), (e['strength'] as num).toDouble())
        ],
        [
          for (final c in (j['captions'] as List?) ?? [])
            NovaCaption((c['start'] as num).toDouble(), (c['end'] as num).toDouble(), c['text'] as String)
        ]);
  }

  /// The caption to show at [t] seconds, or null between sentences.
  NovaCaption? captionAt(double t) {
    for (final c in captions) {
      if (t >= c.start && t < c.end) return c;
    }
    return null;
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

  /// Brow expression at [t] seconds ("happy", "surprised", "concerned"), or null.
  String? expressionAt(double t) {
    for (final m in markers) {
      if (m.type == 'expression' && t >= m.time && t < (m.end ?? m.time)) return m.name;
    }
    return null;
  }

  /// Look direction at [t] seconds, or null when the line isn't directing his gaze.
  NovaLook? lookAt(double t) {
    for (final m in markers) {
      if (m.type == 'look' && t >= m.time && t < (m.end ?? m.time)) return NovaLook.byName(m.direction);
    }
    return null;
  }
}
