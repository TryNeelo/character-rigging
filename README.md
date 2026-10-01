# Neelo | Character Rig

This folder is the single source for Nova's character rig: the artwork, the lip-sync rig, the dialogue audio and the timing for each line. Prototyping lives in a separate project and reads files from here without changing them.

## Folder layout

```
art/
  Character.svg                 Original flat Figma export. Never edited.
  Character-rigged.svg          Rigged version: eyelids and mouth shapes added.
  mouth-shapes-reference.png    Sheet of all mouth shapes, in order X A B C D E F G H, smile.
dialogue/
  <line_name>/
    <line_name>.mp3             Voice audio for the line.
    cues.json                   Approved mouth timing (what the app and previews use).
    cues-rhubarb-raw.json       Untouched output from the lip-sync tool, kept for reference.
    script.txt                  Exact words spoken (add when available).
preview/
  <line_name>.html              Self-contained player for one line. Open in any browser.
tools/
  build_rig.py                  Rebuilds art/Character-rigged.svg from art/Character.svg.
  build_preview.py              Builds preview/<line_name>.html for one line.
  preview_template.html         Page template the preview builder fills in.
```

## How the rig works

The rigged SVG is the original artwork with extra layers. Nothing in the original drawing was moved or redrawn, and the white sticker outline is unchanged.

**Mouth.** All mouth shapes sit in one group, `#mouth`. Each shape is a child group with the id `mouth-<letter>`, and exactly one is visible at a time. The letters follow Rhubarb Lip Sync's naming, so its output plugs in directly.

| Id | Name | Used for |
|---|---|---|
| `mouth-smile` | Smile | Original idle face, shown when Nova isn't speaking |
| `mouth-X` | Rest | Pauses and silence within a line |
| `mouth-A` | Closed | M, B, P |
| `mouth-B` | Teeth | S, T, K, EE and most consonants |
| `mouth-C` | Open | EH, AE |
| `mouth-D` | Wide | AA as in "father" |
| `mouth-E` | Round | AO, ER |
| `mouth-F` | Pucker | OO, OW, W |
| `mouth-G` | Bite | F, V |
| `mouth-H` | Tongue up | L |

**Teeth.** Shapes B, D, G and H include cream teeth, each tagged `class="teeth"`. Current decision: teeth are hidden during dialogue (the preview adds `no-teeth` to the SVG, which hides every `.teeth` element) and shown only when inspecting a single shape. The toothless versions still read clearly.

**Eyes.** Each eye has a lid group clipped to the eye white. A blink runs through three frames:

1. Half lid: `.lid` moved to `translate(0 -15)`.
2. Closed: `.eye-closed` shown (fur fill with a curved lash line).
3. Half lid again, then open: `.lid` at `translate(0 -51.3)` and `.eye-closed` hidden.

Timing is 40 ms half, 80 ms closed, 50 ms half. Blinks happen at random every 2.5 to 5.5 seconds, with a 15% chance of a quick double blink.

**Playback.** The player reads the audio's current time on every frame, finds the cue covering that moment and shows its mouth. Because the audio is the clock, half-speed playback and slow devices stay in sync. When the line ends, the mouth returns to the smile.

**Not rigged yet.** Head and body movement, the outline (it's one merged shape, so head motion would expose it) and outfit swaps.

## Adding a new dialogue line

1. Make a folder `dialogue/<line_name>/` and add the audio as `<line_name>.mp3`, plus `script.txt` with the exact words.
2. Convert the audio to WAV: `ffmpeg -i <line_name>.mp3 -ar 16000 -ac 1 <line_name>.wav`
3. Run Rhubarb Lip Sync (free, from github.com/DanielSWolf/rhubarb-lip-sync/releases; use the macOS build on a Mac):
   `rhubarb -f json --extendedShapes GHX --dialogFile script.txt -o cues-rhubarb-raw.json <line_name>.wav`
4. Copy `cues-rhubarb-raw.json` to `cues.json`.
5. Build the preview: `python3 tools/build_preview.py <line_name>` and open `preview/<line_name>.html`.
6. Review at half speed. Fix any mouth holds that look wrong by editing `cues.json` (each cue is `{"start", "end", "value"}` in seconds), then rebuild the preview.

Giving Rhubarb the script text (step 3) usually improves accuracy a lot. The first line was timed from audio alone because no script was available.

## Line log

**onboarding_nova_dialogue1** (3.8 s, 36 cues). Words (from an automatic transcript, to confirm): "Welcome to Neelo. I'm Nova. Let's get this journey started." Timed by Rhubarb from audio only, then hand-fixed against the audio (energy, frication and vowel formants per 10 ms). Shapes lead the sound by about 30 ms, as Rhubarb does. Hand fixes: (1) "welcome": short B and C for "kuh" before A for M (0.30 to 0.45 s). (2) "to Neelo": B for T, F for OO, then B for N and EE, H for L, E closing to F for O (0.45 to 1.09 s). (3) Both pauses are true silence and now rest on X instead of holding B (1.09 to 1.33 s and 2.00 to 2.28 s). (4) "Nova": B for N, and G for V moved about 50 ms earlier (1.54 to 2.00 s). (5) "Let's": C opens on the E before B for TS (2.28 to 2.50 s). The earlier split of a long B over "get this" into B, C, B, C, B is kept. (6) "started": B for T, C for the "-te-" vowel, B for D, then X (3.44 to 3.76 s).

## Decisions so far

- The white outline stays as is. Motion is limited to blinks and mouth for now.
- Teeth are hidden in dialogue but kept as an option.
- Nova will be drawn live in the app from these layers (audio plus cue file per line), not played as pre-rendered video. New lines only need new audio and cues; the character never has to be re-animated.

## Planned: outfits

To let Nova change outfits without breaking the rig, the artwork will need to be split into a base (body, head, face rig) and outfit slots (hat, top, bottoms, accessories). The face rig never belongs to an outfit, so every outfit keeps lip-sync and blinks. It also needs:

- A complete base body under the clothes (currently the hoodie is the torso).
- Every part drawn on the same artboard size and position, with a fixed layer order per slot.
- The white outline and drop shadow generated in code around whatever outfit is worn, instead of drawn as one fixed shape.
