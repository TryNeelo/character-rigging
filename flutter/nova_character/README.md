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
  outline: true,                  // white sticker outline
  outfit: 'aviator',              // 'hoodie' (default), 'aviator' or 'construction'
)

// React to what he says. EVENTS.md lists every event and what it should do.
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
| `look` | Where Nova looks when no line is directing him: `NovaLook.ahead`, `left`, `right`, `up`, `down`, `upLeft`, `upRight`, `downLeft`, `downRight`. |
| `caption` | The sentence Nova is saying now (`NovaCaption`: `text`, `start`, `end`), or null. Listen to it to show subtitles in the app's own style. |
| `expression` | Brows to hold (`'happy'`, `'surprised'`, `'concerned'`), or null to follow the line. |

## The widget

| Parameter | Default | Notes |
|---|---|---|
| `framing` | `full` | How much of Nova to show. The crop line sits at the bottom of the widget. |
| `align` | `center` | Only matters when the widget is wider than the framing needs. |
| `outline` | `true` | White sticker outline. It's drawn into the art (white copies of the outer parts), so it follows any pose and costs no blur. |
| `idle` | `true` | Movement switch. Nova draws at 15 fps for idle motion, 30 while talking and 60 during arm and look moves (they last a moment). On: breathing and slight sway between lines, nods and brow lifts while talking. Off: he only blinks and lip-syncs, and doesn't redraw between blinks. |
| `blink` | `true` | Random blinks every 2.5 to 5.5 s. |
| `outfit` | `'hoodie'` | Which outfit Nova wears: `'hoodie'`, `'aviator'` or `'construction'`. Change it any time; his face, lip-sync and motion carry over. |

If the widget's height is unbounded, it sizes itself to the framing's proportions.

## What's in a line

Each line is a folder in `assets/lines/<line_id>/` with `audio.mp3` and `timing.json`.
The timing file holds the mouth shapes and the markers:

```json
"markers": [
  { "time": 0.56, "type": "event", "name": "show_logo" },
  { "time": 2.28, "end": 3.70, "type": "look", "direction": "right" },
  { "time": 2.28, "end": 3.70, "type": "arm", "side": "right", "degrees": 32 },
  { "time": 0.04, "end": 1.09, "type": "expression", "name": "happy" }
]
```

- `event` markers become `NovaEvent`s in your app. **`EVENTS.md`** lists every event name,
  which line sends it and when, and what the app should do on screen.
- `look` markers turn Nova's eyes and head toward one of eight directions on screen between
  `time` and `end`: `left`, `right`, `up`, `down`, `up-left`, `up-right`, `down-left`,
  `down-right`. `arm` markers raise the arm on that side of the screen, then lower it
  at `end`. `expression` markers set his brows: `happy`, `surprised` or `concerned`. You
  don't need to do anything with these; the widget handles them.
- His brows also lift briefly on the stressed words of each line (the `emphasis` list,
  found from the audio when the line is packaged).

- `captions` holds the line's words, one entry per sentence with its start and end time.
  You don't read these yourself: `NovaController.caption` tells you which sentence to show
  as Nova speaks, and goes back to null between sentences and when he's quiet.

The audio is the clock, so slow devices and speed changes stay in sync.

## Where this comes from

This package is generated from the Nova character repo, which is the single source for
his art, lines and timing. New lines, timing fixes and art changes arrive as a new
version of this folder; please don't edit `assets/` by hand.

Built and checked with Flutter 3.47 (Dart 3.13). Uses `flutter_svg` and `just_audio`.
