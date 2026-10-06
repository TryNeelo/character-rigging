import 'package:flutter_test/flutter_test.dart';
import 'package:nova_character/src/line.dart';

NovaLine sampleLine() => NovaLine.fromJson({
      'id': 'test',
      'audio': 'audio.mp3',
      'duration': 4.0,
      'cues': [],
      'markers': [
        {'time': 0.56, 'type': 'event', 'name': 'show_logo'},
        {'time': 2.28, 'end': 3.7, 'type': 'look', 'direction': 'right'},
        {'time': 2.88, 'type': 'event', 'name': 'show_path'},
      ],
    });

void main() {
  test('each event fires once, in order, as time passes it', () {
    final gate = NovaEventGate(sampleLine());
    expect(gate.due(0.3), isEmpty);
    expect(gate.due(0.6).map((m) => m.name), ['show_logo']);
    expect(gate.due(1.5), isEmpty);
    expect(gate.due(3.0).map((m) => m.name), ['show_path']);
    expect(gate.due(3.9), isEmpty);
  });

  test('a position that wobbles backwards does not fire an event again', () {
    final gate = NovaEventGate(sampleLine());
    expect(gate.due(0.57).map((m) => m.name), ['show_logo']);
    expect(gate.due(0.55), isEmpty); // the player reports a slightly earlier position
    expect(gate.due(0.58), isEmpty); // and moves on again
  });

  test('a big jump forward fires everything it skipped, once', () {
    final gate = NovaEventGate(sampleLine());
    expect(gate.due(3.5).map((m) => m.name), ['show_logo', 'show_path']);
    expect(gate.due(3.6), isEmpty);
  });

  test('only event markers fire', () {
    final gate = NovaEventGate(sampleLine());
    expect(gate.due(4.0).every((m) => m.type == 'event'), isTrue);
  });
}
