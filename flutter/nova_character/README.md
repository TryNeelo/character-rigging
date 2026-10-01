# nova_character

Nova, Neelo's talking character, as a ready-made Flutter widget. He lip-syncs to his
audio, blinks, breathes, looks where the script tells him, and sends your app events at
set moments in a line ("when Nova says *see those shops*, highlight the shops").

Everything Nova needs (art, audio, timing) is bundled in the package. You don't
assemble anything: add the widget, play a line, and listen for events.

## Try it

```bash
cd example
flutter run -d chrome     # or any device
```

The demo screen has a Play button, framing and position controls, and a log of the
events Nova sends.

## Add it to your app

```yaml
# pubspec.yaml
dependencies:
  nova_character:
    path: ../nova_character   # wherever you put this folder
```

```dart
import 'package:nova_character/nova_character.dart';

final nova = NovaController();

// In your screen. Nova fills the space you give him.
NovaCharacter(
  controller: nova,
  framing: NovaFraming.waistUp,   // full, kneesUp, waistUp, closeUp
  align: NovaAlign.right,         // where he stands if the space is wide
  outline: true,                  // white sticker outline and soft shadow
)

// React to what he says.
nova.events.listen((event) {
  switch (event.name) {
    case 'show_logo': showLogo();
    case 'line_end': goToNextStep();
  }
});

// Make him talk.
await nova.play('onboarding_nova_dialogue1');
```

Dispose the controller with your screen (`nova.dispose()`).

## The controller

| Member | What it does |
|---|---|
| `play(lineId, {speed})` | Speaks a bundled line. `speed: 0.5` is handy for checking timing. |
| `stop()`, `pause()`, `resume()` | Playback control. |
| `events` | Stream of `NovaEvent(name, lineId, time)` from the line's markers. `line_end` arrives when a line finishes. |
| `isSpeaking`, `line`, `time` | Current state. |
| `look` | Where Nova looks when no line is directing him: `NovaLook.left`, `ahead`, `right`. |

## The widget

| Parameter | Default | Notes |
|---|---|---|
| `framing` | `full` | How much of Nova to show. The crop line sits at the bottom of the widget. |
| `align` | `center` | Only matters when the widget is wider than the framing needs. |
| `outline` | `true` | White outline and shadow, generated around any pose. |
| `idle` | `true` | Breathing, slight sway, small nod while talking. Kept subtle. |
| `blink` | `true` | Random blinks every 2.5 to 5.5 s. |

If the widget's height is unbounded, it sizes itself to the framing's proportions.

## What's in a line

Each line is a folder in `assets/lines/<line_id>/` with `audio.mp3` and `timing.json`.
The timing file holds the mouth shapes and the markers:

```json
"markers": [
  { "time": 0.56, "type": "event", "name": "show_logo" },
  { "time": 2.28, "end": 3.70, "type": "look", "direction": "right" },
  { "time": 2.28, "end": 3.70, "type": "arm", "side": "right", "degrees": 32 }
]
```

- `event` markers become `NovaEvent`s in your app. The names are agreed per scene.
- `look` markers turn Nova's eyes and head toward the screen's left or right between
  `time` and `end`. `arm` markers raise the arm on that side of the screen, then lower it
  at `end`. You don't need to do anything with these; the widget handles them.

The audio is the clock, so slow devices and speed changes stay in sync.

## Where this comes from

This package is generated from the Nova character repo, which is the single source for
his art, lines and timing. New lines, timing fixes and art changes arrive as a new
version of this folder; please don't edit `assets/` by hand.

Built and checked with Flutter 3.47 (Dart 3.13). Uses `flutter_svg` and `just_audio`.
