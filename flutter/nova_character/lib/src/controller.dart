import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';

import 'line.dart';

/// An app event from a line's markers, such as "show_logo" when Nova says "Neelo".
/// When a line finishes, an event named [NovaEvent.lineEnd] is sent.
class NovaEvent {
  const NovaEvent(this.name, this.lineId, this.time);
  final String name, lineId;

  /// Seconds into the line.
  final double time;

  static const lineEnd = 'line_end';

  @override
  String toString() => 'NovaEvent($name at ${time.toStringAsFixed(2)}s in $lineId)';
}

/// Where Nova looks when no line is telling him. Directions are on screen: [x] -1 left to
/// 1 right, [y] -1 up to 1 down. [name] matches the "direction" of look markers.
enum NovaLook {
  ahead(0, 0, 'ahead'),
  left(-1, 0, 'left'),
  right(1, 0, 'right'),
  up(0, -1, 'up'),
  down(0, 1, 'down'),
  upLeft(-1, -1, 'up-left'),
  upRight(1, -1, 'up-right'),
  downLeft(-1, 1, 'down-left'),
  downRight(1, 1, 'down-right');

  const NovaLook(this.x, this.y, this.name);
  final double x, y;
  final String name;

  /// The direction named in a look marker, or [ahead].
  static NovaLook byName(String? name) => values.firstWhere((v) => v.name == name, orElse: () => ahead);
}

/// Plays Nova's lines and reports their events. Give it to a [NovaCharacter] widget.
///
/// ```dart
/// final nova = NovaController();
/// nova.events.listen((e) { if (e.name == 'show_shops') highlightShops(); });
/// await nova.play('scene_1');
/// ```
class NovaController extends ChangeNotifier {
  NovaController() {
    _player.processingStateStream.listen((s) {
      if (s == ProcessingState.completed && _line != null) _finish();
    });
  }

  final AudioPlayer _player = AudioPlayer();
  final StreamController<NovaEvent> _events = StreamController<NovaEvent>.broadcast();
  Timer? _ticker;
  NovaLine? _line;
  double _lastTime = -1;
  NovaLook _look = NovaLook.ahead;
  String? _expression;

  /// Events from the playing line's markers, as they happen.
  Stream<NovaEvent> get events => _events.stream;

  /// The line being spoken, or null when Nova is idle.
  NovaLine? get line => _line;
  bool get isSpeaking => _line != null;

  /// Seconds into the current line (0 when idle). The audio is the clock, so slow
  /// devices and changed speeds stay in sync.
  double get time => _line == null ? 0 : _player.position.inMicroseconds / 1e6;

  /// Where Nova looks when the line isn't directing his gaze.
  NovaLook get look => _look;
  set look(NovaLook v) {
    _look = v;
    notifyListeners();
  }

  /// A brow expression to hold ("happy", "surprised", "concerned"), or null to follow the line.
  String? get expression => _expression;
  set expression(String? v) {
    _expression = v;
    notifyListeners();
  }

  /// Speaks a line bundled with the package, by its folder name. [speed] 0.5 plays at
  /// half speed, which is handy for checking timing. Completes when playback starts.
  Future<void> play(String lineId, {double speed = 1}) async {
    await stop();
    final line = await NovaLine.load(lineId);
    await _player.setAudioSource(AudioSource.asset(line.audioAsset));
    await _player.setSpeed(speed);
    _line = line;
    _lastTime = -1;
    _ticker = Timer.periodic(const Duration(milliseconds: 16), (_) => _checkMarkers());
    notifyListeners();
    unawaited(_player.play());
  }

  /// Stops speaking. No [NovaEvent.lineEnd] is sent.
  Future<void> stop() async {
    _ticker?.cancel();
    _ticker = null;
    if (_line == null) return;
    _line = null;
    await _player.stop();
    notifyListeners();
  }

  Future<void> pause() => _player.pause();
  Future<void> resume() => _player.play();

  void _checkMarkers() {
    final line = _line;
    if (line == null) return;
    final t = time;
    for (final m in line.markers) {
      if (m.type == 'event' && m.name != null && _lastTime < m.time && t >= m.time) {
        _events.add(NovaEvent(m.name!, line.id, m.time));
      }
    }
    _lastTime = t;
  }

  void _finish() {
    final line = _line!;
    _checkMarkers();
    _ticker?.cancel();
    _ticker = null;
    _line = null;
    _events.add(NovaEvent(NovaEvent.lineEnd, line.id, line.duration));
    notifyListeners();
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _player.dispose();
    _events.close();
    super.dispose();
  }
}
