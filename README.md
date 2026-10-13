# Neelo | Character Rig

This folder is the single source for Neelo's character rigs (Nova, Skyrian the world 1 wizard and Obselda the world 2 explorer): the artwork, the lip-sync rig, the dialogue audio and the timing for each line. Prototyping lives in a separate project and reads files from here without changing them.

## Folder layout

```
art/
  Nova-outfit_1.svg             Full-body Figma export, outfit 1 (Hoodie). Never edited. The two magenta dots mark the shoulder pivots.
  Nova-outfit_2.svg             Full-body Figma export, outfit 2 (Aviator). Never edited. Same head, pivot dots and canvas.
  Nova-outfit_3.svg             Full-body Figma export, outfit 3 (Construction). Never edited. Its hard hat has a back piece behind the head.
  Nova-rigged.svg               Current rig, built from Nova-outfit_1.svg: grouped parts, hat, eyelids and mouth shapes.
  Character.svg                 First flat Figma export (waist up, with hat). Never edited. Source of the hat and smile.
  Character-rigged.svg          First rig, kept for the prototyping project. Built by an earlier build_rig.py (see git history).
  parts/                        Each part on its own full canvas, for the Flutter component. Built by build_rig.py.
    base/                       The same in every outfit: head, eyes, brows, mouth shapes, nose.
    outfits/<outfit>/           That outfit's legs, arms, body and hat, each with a white *_outline copy. A new outfit only adds a folder.
  mouth-shapes-reference.png    Sheet of all mouth shapes, in order X A B C D E F G H, smile.
  skyrian/                      Skyrian, the wizard. Every character other than Nova gets a folder like this.
    Skyrian.svg                 Full-body Figma export (the assembled wizard). Never edited.
    poses/                      The same Figma frame with his arms moved: rest.svg (hands behind back), arms-down.svg,
                                right-arm-up.svg, left-arm-up.svg (45°). Never edited. They set his shoulder and elbow pivots.
    Skyrian-rigged.svg          His rig for the preview, with the same ids as Nova's. Built by build_rig.py.
    parts/                      His part files for the Flutter component: base/ and outfits/wizard/.
    rig.json                    Canvas, pivots, eyes, head layers and setting changes, for the Flutter packaging.
  obselda/                      Obselda, the explorer: Obselda.svg (Figma export, never edited), Obselda-rigged.svg, parts/, rig.json.
dialogue/
  events.json                   Every app event name and what the app should do. Lines may only use events listed here.
  <line_name>/
    <line_name>.mp3             Voice audio for the line.
    cues.json                   Approved mouth timing and markers (what the app and previews use). "character" says who speaks it (Nova if not set).
    cues-rhubarb-raw.json       Untouched output from the lip-sync tool, kept for reference.
    script.txt                  Exact words spoken, one caption per line, with optional [cues]. See "Script format" below.
    emphasis.json               Stressed moments in the audio, from build_emphasis.py.
    captions.json               Each sentence of script.txt with its start and end time, from build_captions.py. The app shows these as subtitles.
preview/
  index.html                    The rig preview with every line, switched from its Audio files panel. Open in any browser.
  <line_name>.html              Short link that opens index.html on that line.
flutter/nova_character/         The characters as a ready-made Flutter widget, with a demo app. Its assets/ folder is generated
                                (Nova at its top level, every other character in assets/characters/<name>/).
dist/                           Zips for the developers (not in git). Built by make_handoff.py.
tools/
  characters/<name>.json        One settings file per character: his export, parts, pivots, face placement and colours,
                                and his changes to rig_settings.json. nova.json holds the numbers that used to be in build_rig.py.
  face_rig.py                   The shared face rig (mouth shapes, eyelids) and the white outline, used for every character.
  build_rig.py                  Rebuilds art/Nova-rigged.svg and art/parts/ from Nova's exports, then every other character.
  build_character.py            Builds one character other than Nova into art/<name>/ (build_rig.py runs it for each).
  build_preview.py              Builds preview/index.html with every line in dialogue/.
  build_emphasis.py             Finds each line's stressed moments for the brow lifts and head nods.
  build_captions.py             Times each sentence of a line's script for captions (needs faster-whisper; see the file).
  build_events.py               Checks every event in the lines against dialogue/events.json and writes the developers' EVENTS.md.
  preview_template.html         Page template the preview builder fills in.
  rig_settings.json             Framing, idle, look, blink and outline numbers, shared by the preview and the Flutter widget.
  build_flutter.py              Packages every character's parts and settings, and every line, into flutter/nova_character/assets/.
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

**Outfits.** Nova's head, face, blinks and mouths are shared. Each outfit supplies its own legs, arms, body and hat (plus, optionally, a hat piece that sits behind the head, like the hard hat's brim), listed by shape position in `OUTFITS` in `tools/build_rig.py`. In the rig, each of those parts holds one `.outfit` group per outfit (`data-outfit="hoodie"`, `"aviator"`), and only the chosen one is shown. Each outfit's sleeves get their own round caps and shoulder pivots. To add an outfit: export it on the same 556 × 837 canvas with the same head and pivot dots, add it to `OUTFITS`, and rebuild.

**Hat, eyes and mouth.** The head in the outfit 1 art is the original head moved by (+54, −168.13) at the same scale, so the original hat, eyelids and mouth shapes are reused in their original coordinates inside a `translate(54 -168.129)` group.

**Outline.** Drawn into the art, not made with a blur: `#outline` holds white copies of the outer parts (legs, arms, body, head with ears, hat), each edge grown by 8 px with a round stroke. They move with their parts and sit behind the coloured layers. The app draws the `*_outline.svg` parts the same way. No drop shadow (decided 2026-10-06). Hide `#outline` to turn it off.

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

**Idle motion.** Subtle and always on unless switched off: one breath every 4.2 s (`upper` rises up to 1.6 px), a ±0.8° head sway every 7.3 s, and the arms swing ±1.2° with the breath. While a line plays, the head gives a small nod (1.3 px) on each stressed word, with a slight tilt (about 0.8°) that alternates side to side, and stays still in pauses. Stressed words come from tools/build_emphasis.py; settings are under "talk" in tools/rig_settings.json.

**Frame rate (app).** The Flutter widget draws Nova on his own clock, not every screen refresh: 30 fps while he talks, 15 fps for idle motion (`frameRate` in `tools/rig_settings.json`). Each part is drawn once and reused, so moving it just shifts the finished picture. With movement off (`idle: false`) he doesn't redraw at all between blinks. Measured in Chrome on a Mac (2026-10-06), all Chrome processes: quiet with movement 56% → 30% of one core, talking 60% → 50%, movement off about 17% (Chrome's own baseline). To be confirmed on tablets.

**Scenes.** The preview places the character in a square frame, as big as the screen allows, by setting the SVG's `viewBox`. It offers two framing presets: full body, and a close-up for checking lip-sync. Presets are vertical ranges in artboard units; the crop is aligned to the bottom of the frame and the character stands in the centre. The app has all four presets (full body, knees up, waist up, close-up) and places characters left, centre or right.

**Markers.** `cues.json` can carry a `markers` list next to the mouth cues. `{"time", "type": "event", "name"}` sends an event to the app at that moment, for example to highlight the shops. `{"time", "end", "type": "look", "direction"}` turns Nova's eyes and head toward one of eight directions on screen (left, right, up, down, up-left, up-right, down-left, down-right; diagonals are scaled to 75% so the pupils stay in the eyes; looking up also lifts the brows 2 px), and `{"time", "end", "type": "arm", "side": "left" | "right", "degrees"}` raises the arm on that side of the screen and lowers it at `end`; each pupil moves from its resting spot to the same spot in its own eye (so the far pupil travels further), and the head turns 2.5°. The preview shows markers under the timeline and pops up each event as it fires.

**Not rigged yet.** Legs, elbows, separate paws and ears.

## Characters

Every character does everything Nova does: lip-sync, blinks, looking in 8 directions, brow expressions, idle motion and talk nods, arm raises, the baked white outline and framing presets, plus every script tag (looks, arms, brows, events). The face rig is shared (`tools/face_rig.py`) and placed on each character from his settings file in `tools/characters/`. All characters are drawn at the same scale as Nova (Manaf sizes them relative to Nova in Figma), so their art is never resized.

**Skyrian** (`art/skyrian/`, `tools/characters/skyrian.json`) is the wizard of world 1. One look ("wizard"), on a 362 × 869 canvas, standing at x = 180.4 with his soles on the bottom edge.

- Parts, back to front: shoes, then (moving with the breath) collar points and cape, arms, robe with belt, sash and buttons, and the head.
- Head: beard, ears and face, mouth, mustache, eyes, pupils, lids, brows, hair and hat. The beard and hat move with the head, which turns about (180.4, 345), under the mouth.
- Arms: they bend at the elbow, unlike Nova's. Each arm is an upper arm and a forearm (with the hand). The pivots come from Manaf's pose exports (`art/skyrian/poses/`): the shoulder and elbow are the exact points his arms turn about between the hands-behind-back drawing and the arms-down drawing, (89.2, 430) and (273.82, 429.99) for the shoulders, (42.31, 511.51) and (320.7, 511.51) for the elbows. As drawn, his hands are behind his back (upper arms 30° out from vertical, elbows bent 90°): that's his resting pose. `[arms down]` is the arms-down drawing (5.1° out on the right, 6.4° on the left, not quite vertical), and `[arms up 45]` measures from vertical, so it matches the two raised-arm drawings. The build checks itself against both raised-arm drawings and stops if either is more than 0.1 units off. In the preview, each pose lined up with its Figma export. The preview's Pose section has elbow sliders for him that start straight in the middle (left bends in, right bends out), and three stacked buttons: Hands behind back, Left hand behind back and Right hand behind back, each with its script tag.
- Mouth: Nova's exact shapes, scaled 0.575 and centred on Skyrian's drawn mouth, behind the mustache. His drawn mouth is his idle smile. The talking shapes sit 3 units lower than the smile, so the mustache doesn't hide the closed and narrow ones. The rest and closed lines are at least 3 units thick. The round mouth's ring matches his beard.
- Eyes: lids in his skin colours (light on the screen-left half, darker on the right), sized to his eyes (radius 22.2). Pupil reach is scaled to his eyes (7.5 across, 6.2 up and down).
- Brows: his "surprised" lift is 7 instead of 9, so his brows stay clear of the hat brim.
- Framing: full body is -14 to 887 (hat tip to below his shoes). He's taller than Nova with his hat, so in the same frame he shows a little smaller than Nova. Close-up is 170 to 470, his face from the hat brim to the beard, for checking lip-sync. Knees up and waist up are Nova's sizes, measured from the top of the hat, and aren't tuned yet (waiting on the developers).
- His export has no layer names, so parts are listed by position, like Nova's. `shapeCount` stops the build if the export changes.

**Obselda** (`art/obselda/`, `tools/characters/obselda.json`) is the explorer of world 2. One look ("explorer"), on a 374 × 814 canvas, standing at x = 184.4 with her soles on the bottom edge.

- Parts, back to front: legs, trousers and boots; then (moving with the breath) her long hair down her back, arms, tunic with belt and buckle, and the head.
- Head: hair, ears, face, mouth, scarf and earrings, bangs, brows, eyes, pupils and lids. The scarf, earrings and hair move with the head, which turns about (184.4, 272), under the chin. Her brows sit in front of her bangs (in Figma they're behind), so they stay visible when they lift.
- Arms: the same as Skyrian's, 1.18 times bigger, so they work the same way: hands behind her back at rest, `[arms down]`, `[arms up 45]`, elbows in and out. There are no pose exports for her: her straight pose and pivots carry over from Skyrian's arms-down drawing (`armsLike` in her settings file). Shoulders (93.89, 307.86) and (272.44, 307.86), elbows (38.39, 404.35) and (327.94, 404.35).
- Mouth: Nova's shapes scaled 0.425 onto her drawn mouth, with lines at least 2.5 units thick. Nothing covers it, so it isn't lowered. The round mouth's ring matches her face.
- Eyes: lids in her two face colours, sized to her eyes (radius 25.5). Pupil reach 8.8 across, 6.8 up and down.
- She has no hat; the app skips hat files for her.
- Framing: full body is -14 to 832. Close-up is 40 to 340, her face from the bun to the scarf, for checking lip-sync. Knees up and waist up aren't tuned yet.

## Adding a character

1. Export the assembled character from Figma as one SVG, sized relative to Nova, and save it as `art/<name>/<Name>.svg`. Never edit it. Ticking "Include 'id' attribute" makes the layers easier to read, but isn't required.
2. Copy `tools/characters/skyrian.json` to `tools/characters/<name>.json`. List his parts by position in the export (legs, body behind the arms, arms with their upper-arm capsule or a `pivot`, body, hat, the head's layers), his head pivot and anchor, his drawn mouth, eye whites, pupils, brows and lid colours.
3. Run `python3 tools/build_rig.py`, then `python3 tools/build_preview.py`. He appears in the preview's Character picker.
4. Check his mouth shapes, blinks, looks, brows and arms in the preview, and tune his settings file (mouth drop, minimum stroke, pupil reach, brow lifts, framing).
5. Give his lines `"character": "<name>"` in cues.json, and run `python3 tools/build_flutter.py` to package him.

Nova's output must not change when a character is added: compare `art/Nova-rigged.svg`, `art/parts/` and `flutter/nova_character/assets/` (Nova's parts, rig.json and lines) before and after.

## Adding a new dialogue line

1. Make a folder `dialogue/<line_name>/` and add the audio as `<line_name>.mp3`, plus `script.txt` with the exact words.
2. Convert the audio to WAV: `afconvert -f WAVE -d LEI16@16000 -c 1 <line_name>.mp3 <line_name>.wav` (or `ffmpeg -i <line_name>.mp3 -ar 16000 -ac 1 <line_name>.wav`)
3. Run Rhubarb Lip Sync (free, from github.com/DanielSWolf/rhubarb-lip-sync/releases; use the macOS build on a Mac):
   `rhubarb -f json --extendedShapes GHX --dialogFile script.txt -o cues-rhubarb-raw.json <line_name>.wav`
4. Copy `cues-rhubarb-raw.json` to `cues.json`.
5. Write `script.txt` (see Script format). Add any new event names to `dialogue/events.json`, then time the captions and cues: `~/whisper-venv/bin/python tools/build_captions.py <line_name>`.
6. Find the stressed words: `python3 tools/build_emphasis.py <line_name>`, and add a `"title"` to `cues.json`: the line's name in the Audio files panel.
7. If someone other than Nova speaks the line, add `"character": "<name>"` (for example `"skyrian"`) to `cues.json`. Build the preview: `python3 tools/build_preview.py` and open `preview/index.html`. The new line is in its speaker's Audio files panel: the panel and the Script drawer only show the lines of the character on stage, and switching characters loads his first line.
8. Review at half speed. Fix any mouth holds that look wrong by editing `cues.json` (each cue is `{"start", "end", "value"}` in seconds), then rebuild the preview.

Giving Rhubarb the script text (step 3) usually improves accuracy a lot. The first line was timed from audio alone because no script was available.

## Handing Nova to the developers

The developers get Nova as a Flutter package (`flutter/nova_character/`): a widget they place on a screen, a controller that plays lines, and a stream of events. Art, audio and timing are bundled inside, so there is nothing to assemble. Its README is the developer guide, and `example/` is a demo screen.

To send a new version: bump `version` in `flutter/nova_character/pubspec.yaml`, run `python3 tools/make_handoff.py`, and send `dist/nova_character-<version>.zip`.

## Script format

A line's `script.txt` is plain text:

- **One caption per line**, broken wherever the caption should change. A script written as one paragraph is split by sentence.
- **Exact words** as spoken, with punctuation.
- **[Bracketed cues]** right before the word where something should happen, even mid-line: `There's lots to explore. [Highlight the shops] See those shops?` The cue is removed from the caption and becomes an event at that word. It must match an event in `dialogue/events.json` (its name, or one of its `cues`), or one of Nova's moves below, or `build_captions.py` stops. The preview's **Events** panel lists every event by scene with its tag (click to copy), plus the highlight rules. A highlight stays until the script ends it: `[Stop highlight]` fades the spotlight and the arrow; `[Stop spotlight]` fades only the spotlight and leaves the arrow blinking until the child taps.
- **Moves** are cued the same way and hold until the next cue of the same kind, or the end of the line. "Left" and "right" are the screen's sides.
  - `[look right]`, `[look up-right]` and the other eight directions; `[look ahead]` looks straight again.
  - `[arms up 32]`, `[right arm up 32]`, `[left arm up 32]` (degrees; `up` alone is 32), and `[arms down]`, `[right arm down]`.
  - Characters with elbows (Skyrian): `[arms behind]`, `[left arm behind]` go back to his resting pose (hands behind his back); `[arms down]` holds his arms straight down at his sides; `[arms up 32]` holds a straight arm raised 32° out from straight down. `[left elbow in 45]` bends the elbow in (toward the body) and `[right elbow out 60]` bends it out (for a wave, with the arm raised); `[elbows 0]` straightens them, and a bare number like `[left elbow 45]` means in. Put an elbow cue after the arm cue at the same word, since an arm cue straightens the elbow. For Nova, `[arms behind]` is the same as `[arms down]`, and elbow cues do nothing (`build_captions.py` notes them).
  - `[happy brows]`, `[surprised brows]`, `[concerned brows]` hold that brow expression; `[normal brows]` returns to neutral.
- Captions longer than `captions.maxChars` in `tools/rig_settings.json` (55, the length of "Each world is packed with stories and games to explore.", set by Manaf) are split at a sentence end, then a comma, then a space, and flagged to check.

## Line log

**ftux_home** "FTUX: home" (17.6 s, 137 cues). The final recording, with Manaf's script and cues. It was about 10 dB quieter than the earlier sample lines, so it was raised to match (speech level within 1 dB, peaks kept at -1 dBFS). Rhubarb's timing was too loose (the mouth opened 0.25 s late on "Hi", held shapes through pauses, and drifted against the vowels), so the mouth track was redone by hand: every shape placed against the audio's 10 ms loudness, hiss and brightness, with a letter-level forced alignment (wav2vec2, torchaudio) for the order of sounds. Shapes start about 30 ms ahead of their sound; lip closures (A) sit on the real closures in "welcome", "neighborhood", "explore", "shops", "be able", "buy", "But", "home" and "make"; F and V get G; every pause rests on X. Nothing is shorter than 40 ms, so it holds up at the app's 30 fps. Moves from the script: both arms up 32° through "Welcome to your neighborhood. There's lots to explore."; look right from "See those shops?" until "cool clothes" and the right arm up 32° until the end of "things!"; look up-right from "But first" through "home", then ahead from "I'll show you around". Events: `highlight_shops`, `highlight_home` on "home" (it replaces the shops highlight), and `clear_spotlight` at the end, so the arrow keeps blinking on the home until the child taps it. (highlight_coins was dropped on 2026-10-13: the home screen has no coins to highlight.)

**ftux_room** "FTUX: room" (18.6 s, 141 cues). Final recording, with Manaf's script and cues. Raised 18.2 dB to match ftux_home (peaks at -1.5 dBFS). He says "Wanna choose…", and the caption says so too. Mouth track hand-timed from the start, the same way as ftux_home (letter alignment plus 10 ms loudness, hiss and brightness; closures on "room", "come", "book", "home", "open", "up"; G on "adventures", "for", "avatar"; X in every pause; nothing under 40 ms). "When you get a new sticker, you can come home to see it." is 56 characters, so it splits at the comma. Moves: arms up 24°/25° on "This is your room!"; look left and the left arm up 32° from "See that book?" until "You earn"; look left and the left arm up 32° on "And this is your closet.", both back down at "Wanna choose" Events: `highlight_sticker_book`, `highlight_closet` (replaces it), `clear_spotlight` at the end.

**ftux_home_return** "FTUX: home return" (8.1 s, 55 cues). Final recording, with Manaf's script and cues. Raised 10.6 dB to match ftux_home (peaks at -1 dBFS). Mouth track hand-timed the same way (closures on "explore", "Tap"; G on "of", "find", "adventure"; X in every pause; nothing under 40 ms). Moves: both arms up 32° and surprised brows on "You look great!"; look up on "Tap the arrow", then ahead from "let's find a new adventure". Events: `highlight_back_arrow` on "Tap", and `clear_spotlight` after "adventure!", so the arrow keeps blinking until the child taps it.

**ftux_world_select** "FTUX: world select" (16.3 s, 103 cues). Final recording, with Manaf's script and cues. Raised 18.6 dB to match ftux_home (peaks at -1.9 dBFS). Mouth track hand-timed the same way (closures on "made", "explore", "packed", "games", "Tap", "exploring"; G on "different", "find"; X in every pause; nothing under 40 ms). "When you find a world you like, tap Enter to start exploring!" is 61 characters, so it splits at the comma, right where the Enter highlight starts. Moves: both arms up 32° on "We made it!", down right after it; look right and the right arm up 32° through "Tap the arrow to see the next world!"; look up-right from "tap Enter" to the end. Events: `start_world_rotation` on "Neelo has…" and `stop_world_rotation` after "games!" (the app rotates the worlds on its own timer in between), `highlight_next_world_arrow` on "Tap", `clear_highlight` after "world!", `highlight_enter` on "tap Enter", `clear_highlight` at the end.

**ftux_w1** "FTUX: world 1" (9.7 s, 82 cues). Spoken by **Skyrian**, the world 1 wizard (`"character": "skyrian"` in cues.json). Final recording, with Manaf's script; no tags yet. Raised 10.1 dB to match ftux_home (peaks at -1 dBFS). Mouth track hand-timed the same way (closures on "I'm", "welcome", "Tap"; G on "for", "discover", "flag"; X in every pause; nothing under 40 ms). "Welcome to Aetheris, where we look out for one another." is exactly 55 characters, so it stays one caption. The preview plays it on Skyrian.

**ftux_w2** "FTUX: world 2" (10.8 s, 76 cues). Spoken by **Obselda** (`"character": "obselda"`). Final recording, with Manaf's script; no tags yet. Raised 3.9 dB to match ftux_home (peaks at -1 dBFS). Mouth track hand-timed the same way (closures on "I'm", the B in "Obselda", "welcome", the P in "Cragspire" and "explore", "Tap"; G on "flag"; X in every pause; nothing under 40 ms). "Welcome to Cragspire and our steady, rocky ground." is 50 characters, so it stays one caption.

The two earlier sample lines (onboarding_nova_dialogue1, voice_line_1) and their sample events (show_logo, show_path) were removed on 2026-10-13, when the final FTUX audio arrived. They're in git history.

## Decisions so far

- Full-body art from outfit 1 replaces the first waist-up rig. The original hat, eyes and mouth shapes are kept.
- The white outline is drawn into the art (white copies of the outer parts), not a blur, so it's cheap on budget tablets. No drop shadow. It can be turned off.
- Teeth are removed.
- Arms stay behind the outfit. Idle motion stays subtle.
- Nova will be drawn live in the app from these layers (audio plus cue file per line), not played as pre-rendered video. New lines only need new audio and cues; the character never has to be re-animated.

## Planned: outfits

To let Nova change outfits without breaking the rig, the artwork will need to be split into a base (body, head, face rig) and outfit slots (hat, top, bottoms, accessories). The face rig never belongs to an outfit, so every outfit keeps lip-sync and blinks. It also needs:

- A complete base body under the clothes (currently the hoodie is the torso).
- Every part drawn on the same artboard size and position, with a fixed layer order per slot.
- The white outline and drop shadow generated in code around whatever outfit is worn (done in outfit 1).
- Figma exports with "Include 'id' attribute" ticked, so parts arrive grouped and named instead of being found by their order.
