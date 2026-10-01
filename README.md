# Neelo | Character Rig

This folder is the single source for Nova's character rig: the artwork, the lip-sync rig, the dialogue audio and the timing for each line. Prototyping lives in a separate project and reads files from here without changing them.

## Folder layout

```
art/
  Nova-outfit_1.svg             Full-body Figma export, outfit 1. Never edited. The two magenta dots mark the shoulder pivots.
  Nova-rigged.svg               Current rig, built from Nova-outfit_1.svg: grouped parts, hat, eyelids and mouth shapes.
  Character.svg                 First flat Figma export (waist up, with hat). Never edited. Source of the hat and smile.
  Character-rigged.svg          First rig, kept for the prototyping project. Built by an earlier build_rig.py (see git history).
  parts/                        Each part on its own full canvas, for the Flutter component. Built by build_rig.py.
  mouth-shapes-reference.png    Sheet of all mouth shapes, in order X A B C D E F G H, smile.
dialogue/
  <line_name>/
    <line_name>.mp3             Voice audio for the line.
    cues.json                   Approved mouth timing and markers (what the app and previews use).
    cues-rhubarb-raw.json       Untouched output from the lip-sync tool, kept for reference.
    script.txt                  Exact words spoken (add when available).
preview/
  <line_name>.html              Self-contained player for one line. Open in any browser.
flutter/nova_character/         Nova as a ready-made Flutter widget, with a demo app. Its assets/ folder is generated.
dist/                           Zips for the developers (not in git). Built by make_handoff.py.
tools/
  build_rig.py                  Rebuilds art/Nova-rigged.svg from art/Nova-outfit_1.svg and art/Character.svg.
  build_preview.py              Builds preview/<line_name>.html for one line.
  preview_template.html         Page template the preview builder fills in.
  rig_settings.json             Framing, idle, look, blink and outline numbers, shared by the preview and the Flutter widget.
  build_flutter.py              Packages parts, settings and lines into flutter/nova_character/assets/.
  make_handoff.py               Runs every build step and writes dist/nova_character-<version>.zip.
```

## How the rig works

`art/Nova-rigged.svg` is the outfit 1 artwork regrouped into parts. Nothing in the drawing was moved or redrawn. The artboard is 556 × 837; Nova stands centred at x = 278 with his feet on the bottom edge (y = 837), which is the anchor scenes place him by.

**Parts.** Back to front. Each movable part has `class="part"` and its pivot in `data-pivot`.

| Id | Holds | Pivot |
|---|---|---|
| `legs` | Legs and shoes | Not posed yet |
| `upper` | Everything below; moves for breathing | None (moves up and down) |
| `arm-left`, `arm-right` | Fur arm, sleeve and a round sleeve cap | Shoulder: (194.4, 432.8) and (359.7, 433.5) |
| `pants`, `torso` | Shorts; hood, neck, shirt and jacket | Move with `upper` |
| `head` | Ears, face, `pupils`, `brows`, eyelids, mouth and `hat` | Base of the neck, (278.7, 392) |

The arms always stay behind the outfit. The shoulder pivots come from the magenta dots in the source art, moved onto each sleeve's centre line. Each sleeve gets a round cap there (a circle as wide as the sleeve, in the sleeve colour), so the arm can rotate up to 180° without its flat top showing. If the art is redrawn with this cap, the generated one can go.

**Hat, eyes and mouth.** The head in the outfit 1 art is the original head moved by (+54, −168.13) at the same scale, so the original hat, eyelids and mouth shapes are reused in their original coordinates inside a `translate(54 -168.129)` group.

**Outline.** `#character` carries `filter="url(#outline)"`: a white edge about 8 px wide grown from the silhouette, plus the original soft shadow. Because it is generated, it follows any pose. Remove the attribute to turn it off.

**Mouth.** All mouth shapes sit in one group, `#mouth`. Each shape is a child group with the id `mouth-<letter>`, and exactly one is visible at a time. The letters follow Rhubarb Lip Sync's naming, so its output plugs in directly.

| Id | Name | Used for |
|---|---|---|
| `mouth-smile` | Smile | Original idle face, shown when Nova isn't speaking |
| `mouth-X` | Rest | Pauses and silence within a line |
| `mouth-A` | Closed | M, B, P |
| `mouth-B` | Narrow | S, T, K, EE and most consonants |
| `mouth-C` | Open | EH, AE |
| `mouth-D` | Wide | AA as in "father" |
| `mouth-E` | Round | AO, ER |
| `mouth-F` | Pucker | OO, OW, W |
| `mouth-G` | Bite | F, V |
| `mouth-H` | Tongue up | L |

**Teeth.** Removed in this version. Shapes B, D, G and H have no teeth and still read clearly.

**Eyes.** Each eye has a lid group clipped to the eye white. A blink runs through three frames:

1. Half lid: `.lid` moved to `translate(0 -15)`.
2. Closed: `.eye-closed` shown (fur fill with a curved lash line).
3. Half lid again, then open: `.lid` at `translate(0 -51.3)` and `.eye-closed` hidden.

Timing is 40 ms half, 80 ms closed, 50 ms half. Blinks happen at random every 2.5 to 5.5 seconds, with a 15% chance of a quick double blink.

**Playback.** The player reads the audio's current time on every frame, finds the cue covering that moment and shows its mouth. Because the audio is the clock, half-speed playback and slow devices stay in sync. When the line ends, the mouth returns to the smile.

**Idle motion.** Subtle and always on unless switched off: one breath every 4.2 s (`upper` rises up to 1.6 px), a ±0.8° head sway every 7.3 s, and the arms swing ±1.2° with the breath. While a line plays, the head lifts and tips slightly with how open the mouth is.

**Scenes.** The preview places Nova in a frame by setting the SVG's `viewBox`. Framing presets are vertical ranges in artboard units (full body, knees up, waist up, close-up); the crop is aligned to the bottom of the frame, and Nova can stand left, centre or right.

**Markers.** `cues.json` can carry a `markers` list next to the mouth cues. `{"time", "type": "event", "name"}` sends an event to the app at that moment, for example to highlight the shops. `{"time", "end", "type": "look", "direction": "left" | "right"}` turns Nova's eyes and head toward that side of the screen; the pupils slide up to 8 px, the head turns 2.5°. The preview shows markers under the timeline and pops up each event as it fires.

**Not rigged yet.** Legs, elbows, separate paws, ears, gaze (`pupils`) and brow expressions.

## Adding a new dialogue line

1. Make a folder `dialogue/<line_name>/` and add the audio as `<line_name>.mp3`, plus `script.txt` with the exact words.
2. Convert the audio to WAV: `ffmpeg -i <line_name>.mp3 -ar 16000 -ac 1 <line_name>.wav`
3. Run Rhubarb Lip Sync (free, from github.com/DanielSWolf/rhubarb-lip-sync/releases; use the macOS build on a Mac):
   `rhubarb -f json --extendedShapes GHX --dialogFile script.txt -o cues-rhubarb-raw.json <line_name>.wav`
4. Copy `cues-rhubarb-raw.json` to `cues.json`.
5. Build the preview: `python3 tools/build_preview.py <line_name>` and open `preview/<line_name>.html`.
6. Review at half speed. Fix any mouth holds that look wrong by editing `cues.json` (each cue is `{"start", "end", "value"}` in seconds), then rebuild the preview.

Giving Rhubarb the script text (step 3) usually improves accuracy a lot. The first line was timed from audio alone because no script was available.

## Handing Nova to the developers

The developers get Nova as a Flutter package (`flutter/nova_character/`): a widget they place on a screen, a controller that plays lines, and a stream of events. Art, audio and timing are bundled inside, so there is nothing to assemble. Its README is the developer guide, and `example/` is a demo screen.

To send a new version: bump `version` in `flutter/nova_character/pubspec.yaml`, run `python3 tools/make_handoff.py`, and send `dist/nova_character-<version>.zip`.

## Line log

**onboarding_nova_dialogue1** (3.8 s, 36 cues). Words (from an automatic transcript, to confirm): "Welcome to Neelo. I'm Nova. Let's get this journey started." Timed by Rhubarb from audio only, then hand-fixed against the audio (energy, frication and vowel formants per 10 ms). Shapes lead the sound by about 30 ms, as Rhubarb does. Sample markers for the developer handoff: event `show_logo` on "Neelo" (0.56 s), look right through "Let's get this journey started" (2.28 to 3.70 s), event `show_path` on "journey" (2.88 s). Hand fixes: (1) "welcome": short B and C for "kuh" before A for M (0.30 to 0.45 s). (2) "to Neelo": B for T, F for OO, then B for N and EE, H for L, E closing to F for O (0.45 to 1.09 s). (3) Both pauses are true silence and now rest on X instead of holding B (1.09 to 1.33 s and 2.00 to 2.28 s). (4) "Nova": B for N, and G for V moved about 50 ms earlier (1.54 to 2.00 s). (5) "Let's": C opens on the E before B for TS (2.28 to 2.50 s). The earlier split of a long B over "get this" into B, C, B, C, B is kept. (6) "started": B for T, C for the "-te-" vowel, B for D, then X (3.44 to 3.76 s).

## Decisions so far

- Full-body art from outfit 1 replaces the first waist-up rig. The original hat, eyes and mouth shapes are kept.
- The white outline is generated in code and can be turned off.
- Teeth are removed.
- Arms stay behind the outfit. Idle motion stays subtle.
- Nova will be drawn live in the app from these layers (audio plus cue file per line), not played as pre-rendered video. New lines only need new audio and cues; the character never has to be re-animated.

## Planned: outfits

To let Nova change outfits without breaking the rig, the artwork will need to be split into a base (body, head, face rig) and outfit slots (hat, top, bottoms, accessories). The face rig never belongs to an outfit, so every outfit keeps lip-sync and blinks. It also needs:

- A complete base body under the clothes (currently the hoodie is the torso).
- Every part drawn on the same artboard size and position, with a fixed layer order per slot.
- The white outline and drop shadow generated in code around whatever outfit is worn (done in outfit 1).
- Figma exports with "Include 'id' attribute" ticked, so parts arrive grouped and named instead of being found by their order.
