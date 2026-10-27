# nova_character

Nova, Neelo's talking character, as a ready-made Flutter widget. He lip-syncs to his
audio, blinks, breathes, looks where the script tells him, and sends your app events at
set moments in a line ("when Nova says *see those shops*, highlight the shops").

Everything Nova needs (art, audio, timing) is bundled in the package. You don't
assemble anything: add the widget, play a line, and listen for events.

The other characters come in the same package and work the same way. Today that's
**Skyrian** (world 1), **Obselda** (world 2), **Tydras** (world 3), **Voltis** (world 4) and **Tremu** (world 5):
pass `character: 'skyrian'`, `'obselda'`, `'tydras'`, `'voltis'` or `'tremu'` (see "Other characters").
Nothing changes for code that only shows Nova.

## What's new in 0.4.2

- Two new Nova outfits: `'futurist'` (the World 4 look) and `'woodlander'` (the World 5 look).
- World rotation now happens once: a new event, `show_next_world`, slides the world selection screen to the next world once, right after "Tap the arrow to see the next world!" in `ftux_world_select` and `ftux_world_select_deep_link`. `start_world_rotation` and `stop_world_rotation` are retired: no line sends them any more, so replace them with `show_next_world` (see EVENTS.md).
- `ftux_home`: `highlight_home` now fires on "let's head inside your home", a little earlier than before.

## What's new in 0.4.1

Nothing to change in code written for 0.4.0.

- A new Nova outfit, `'diver'`: a glass helmet (Nova's head turns inside it), air hoses, and a glare on the glass that stays still in front of his face.
- The construction outfit now has a neck scarf.
- A new Nova line, `ftux_world_select_deep_link`: the world selection line for players arriving by a deep link, with the same events as `ftux_world_select` (see EVENTS.md).

## What's new in 0.4.0

Nothing to change in code written for 0.3.0.

- Five world characters: Skyrian, Obselda, Tydras, Voltis and Tremu, each with a welcome line (`ftux_w1` to `ftux_w5`).
  Pick one with `NovaCharacter(character: ...)`; a line's `character` tells you who speaks it.
- Elbows: Skyrian's, Obselda's, Tydras's and Tremu's arms bend, and their lines can hold arms down, raised or bent.
- Nova's head (and hat) is 10% smaller. Only his art and `assets/rig.json` changed.
- Tremu's mouth is a stand-in for now; his drawn mouth will come in a later version, as an art update only.

## Try it

```bash
cd example
flutter run -d chrome     # or any device
```

The demo screen has a Play button, a character picker (Nova, Skyrian, Obselda, Tydras, Voltis or Tremu, each with a
sample line), framing and position controls, and a log of the events he sends.

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
  outfit: 'aviator',              // 'hoodie' (default), 'aviator', 'construction', 'diver', 'futurist' or 'woodlander'
)

// React to what he says. EVENTS.md lists every event and what it should do.
nova.events.listen((event) {
  switch (event.name) {
    case 'highlight_shops': highlightShops();
    case 'line_end': goToNextStep();
  }
});

// Make him talk.
await nova.play('ftux_home');
```

Dispose the controller with your screen (`nova.dispose()`).

### Other characters

Add `character:` to the widget. Leave it out (or pass `'nova'`) and you get Nova, so
existing code doesn't change. The controller is the same for every character.

```dart
NovaCharacter(
  controller: nova,
  character: 'skyrian',           // 'nova' (default), 'skyrian', 'obselda', 'tydras', 'voltis' or 'tremu'
  framing: NovaFraming.full,
)

await nova.play('ftux_w1');       // a Skyrian line ('ftux_w2' Obselda's, 'ftux_w3' Tydras's, 'ftux_w4' Voltis's, 'ftux_w5' Tremu's)
```

Each line knows who speaks it: `NovaLine.character` (`nova.line?.character` while it
plays) is the speaker's id (`'nova'`, `'skyrian'`, `'obselda'`, `'tydras'`, `'voltis'` or `'tremu'`), so you can pass it straight to the widget. Every
character lip-syncs, blinks, looks, raises his arms, sets his brows and sends events
the same way. The world characters have one look each, so `outfit` doesn't apply to them.

Skyrian's, Obselda's, Tydras's and Tremu's arms bend at the elbow. Skyrian, Obselda and Tremu rest with
their hands behind their back; Tydras rests with her arms down. Voltis's arms are one piece,
like Nova's. Tremu has no drawn mouth: his mouth shows under his mustache only while it's open. Their lines can hold the
arms straight down, raise them straight, and bend either elbow.
The widget handles all of it from the line's markers (below). All characters
are drawn at the same scale as Nova; Skyrian is a little taller with his hat, so his
full-body framing is a little taller too.

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
| `outfit` | `'hoodie'` | Which outfit Nova wears: `'hoodie'`, `'aviator'`, `'construction'`, `'diver'`, `'futurist'` or `'woodlander'`. Change it any time; his face, lip-sync and motion carry over. |
| `character` | `'nova'` | Which character to draw: `'nova'`, `'skyrian'`, `'obselda'`, `'tydras'`, `'voltis'` or `'tremu'`. Unknown ids fall back to Nova. Change it any time. |

If the widget's height is unbounded, it sizes itself to the framing's proportions.

## What's in a line

This version has the four Nova FTUX lines and Skyrian's world 1 line, all with the final audio:

| Line id | Speaker | Scene |
|---|---|---|
| `ftux_home` | Nova | Home map: shops, then the home |
| `ftux_room` | Nova | Nova's room: sticker book, then the closet |
| `ftux_home_return` | Nova | Back on the home map: the back arrow |
| `ftux_world_select` | Nova | World selection: rotating worlds, next-world arrow, Enter |
| `ftux_world_select_deep_link` | Nova | World selection for players arriving by a deep link: the same events as `ftux_world_select` |
| `ftux_w1` | Skyrian | World 1: Skyrian's welcome (no events yet) |
| `ftux_w2` | Obselda | World 2: Obselda's welcome (no events yet) |
| `ftux_w3` | Tydras | World 3: Tydras's welcome (no events yet) |
| `ftux_w4` | Voltis | World 4: Voltis's welcome to Lumina (no events yet) |
| `ftux_w5` | Tremu | World 5: Tremu's welcome to Everglen (no events yet) |

Each line is a folder in `assets/lines/<line_id>/` with `audio.mp3` and `timing.json`.
The timing file holds the mouth shapes and the markers, plus `"character"` when someone
other than Nova speaks it:

```json
"markers": [
  { "time": 5.65, "type": "event", "name": "highlight_shops" },
  { "time": 5.65, "end": 11.32, "type": "look", "direction": "right" },
  { "time": 5.65, "end": 11.32, "type": "arm", "side": "right", "degrees": 32 },
  { "time": 0.0, "end": 1.85, "type": "expression", "name": "surprised" }
]
```

- `event` markers become `NovaEvent`s in your app. **`EVENTS.md`** lists every event name,
  which line sends it and when, and what the app should do on screen. It starts with how
  highlights work: each highlight is a spotlight plus an arrow, and it stays until
  `clear_highlight` (both fade) or `clear_spotlight` (the arrow stays and blinks until the
  child taps), or until the next highlight replaces it.
- `look` markers turn Nova's eyes and head toward one of eight directions on screen between
  `time` and `end`: `left`, `right`, `up`, `down`, `up-left`, `up-right`, `down-left`,
  `down-right`. `arm` markers raise the arm on that side of the screen, then lower it
  at `end`. For characters with elbows (Skyrian), an `arm` marker holds a straight arm
  raised `degrees` from hanging down (0 is arms down) and `elbow` markers bend the elbow
  (`{ "type": "elbow", "side": "right", "degrees": 90 }`: positive bends it in toward the
  body, negative bends it out); with neither, his arms rest behind his back. `expression` markers set his brows: `happy`, `surprised` or `concerned`. You
  don't need to do anything with these; the widget handles them.
- His brows also lift briefly on the stressed words of each line (the `emphasis` list,
  found from the audio when the line is packaged).

- `captions` holds the line's words, one entry per sentence with its start and end time.
  You don't read these yourself: `NovaController.caption` tells you which sentence to show
  as Nova speaks, and goes back to null between sentences and when he's quiet.

The audio is the clock, so slow devices and speed changes stay in sync.

## Where this comes from

This package is generated from the character repo, which is the single source for
the characters' art, lines and timing. New lines, timing fixes and art changes arrive as a new
version of this folder; please don't edit `assets/` by hand.

Built and checked with Flutter 3.47 (Dart 3.13). Uses `flutter_svg` and `just_audio`.
