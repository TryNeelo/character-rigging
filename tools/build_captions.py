"""Time a line's captions and script cues from its script and audio.

Script format (dialogue/<line>/script.txt), plain text:
  - Each line of the file is one caption, broken wherever the writer wants it to change.
  - [Bracketed cues] mark where something happens, right before the word it happens on:
        There's lots to explore. [Highlight the shops] See those shops?
    Cues are removed from the caption text and become event markers at that word. A cue
    must match an event in dialogue/events.json (its name, or one of its "cues"), or the
    build stops so nothing slips through.
  - Any caption longer than captions.maxChars (tools/rig_settings.json) is split at a
    sentence end, then a comma, then a space, and is flagged to check.

Whisper (faster-whisper) only supplies when each word is heard; the words always come from
the script, so a misheard word (e.g. "Nilo" for "Neelo") still gets the right time.
Writes dialogue/<line>/captions.json as [{"start", "end", "text", "words", "split"}] (words: each
word's time, for the preview's script view; split: true if the caption was split for length) and puts the cue events
into cues.json markers (marked "source": "script", replaced on every run).

Needs faster-whisper:  python3 -m venv ~/whisper-venv && ~/whisper-venv/bin/pip install faster-whisper
Usage: ~/whisper-venv/bin/python tools/build_captions.py [line_name ...]   (all lines with a script if none given)
"""
import difflib, glob, json, os, re, sys
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAD, HOLD = 0.1, 0.4      # show a caption just before its first word; keep it up a moment after the last
CUE_LEAD = 0.03            # cues land just ahead of their word, like the mouth shapes
MAX = json.load(open(os.path.join(ROOT, 'tools', 'rig_settings.json')))['captions']['maxChars']
EVENTS = {k: v for k, v in json.load(open(os.path.join(ROOT, 'dialogue', 'events.json'))).items() if not k.startswith('_')}

norm = lambda w: re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))
plain = lambda s: ' '.join(re.sub(r"[^a-z0-9 ]", ' ', s.lower().replace('’', "'")).split())

def event_for(cue):
    """The event a bracketed cue means: an event's listed cue wording (whole or as the start
    of a longer note), or its name written out ("Highlight the shops" -> highlight_shops)."""
    text = plain(cue)
    for name, ev in EVENTS.items():
        for alias in ev.get('cues', []):
            if text == plain(alias) or text.startswith(plain(alias) + ' '):
                return name
    slug = '_'.join(w for w in text.split() if w not in ('the', 'a', 'an'))
    return slug if slug in EVENTS else None

def split_long(caption):
    """Split a caption over MAX characters: at sentence ends, then commas, then spaces."""
    if len(caption) <= MAX:
        return [caption]
    for pattern in (r'(?<=[.!?])\s+', r'(?<=,)\s+', r'\s+'):
        cuts = [m.end() for m in re.finditer(pattern, caption) if m.end() <= MAX + 1]
        if cuts:
            cut = cuts[-1]
            return [caption[:cut].strip()] + split_long(caption[cut:].strip())
    return [caption]

model = WhisperModel('small.en', compute_type='int8')
problems = []
lines = sys.argv[1:] or [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'dialogue', '*', 'script.txt'))]
for line in sorted(lines):
    d = os.path.join(ROOT, 'dialogue', line)
    raw = [l.strip() for l in open(os.path.join(d, 'script.txt')).read().splitlines() if l.strip()]
    # A script written as one paragraph is split by sentence; otherwise each line is a caption
    if len(raw) == 1:
        raw = [s.strip() for s in re.findall(r'[^.!?]+[.!?]*', raw[0]) if s.strip()]

    # Words of every caption, with any cues that sit right before a word
    words, captions_text, cues = [], [], []
    for row in raw:
        pending = []
        for part in re.split(r'(\[[^\]]*\])', row):
            if part.startswith('['):
                pending.append(part[1:-1].strip())
                continue
            for w in part.split():
                cues += [(c, len(words)) for c in pending]   # cue happens on this word
                pending = []
                words.append((len(captions_text), w))
        cues += [(c, len(words) - 1, 'after') for c in pending]  # a cue at the end of a row
        text = ' '.join(re.sub(r'\[[^\]]*\]', ' ', row).split())
        pieces = split_long(text)
        if len(pieces) > 1:
            problems.append(f'{line}: split a long caption ({len(text)} > {MAX} characters), please check: {pieces}')
        captions_text.append(pieces)

    audio = sorted(glob.glob(os.path.join(d, '*.mp3')))[0]
    timing = json.load(open(os.path.join(d, 'cues.json')))
    duration = timing['mouthCues'][-1]['end']
    segments, _ = model.transcribe(audio, word_timestamps=True, beam_size=5)
    heard = [(norm(w.word), w.start, w.end) for s in segments for w in s.words]

    # Line up script words with heard words; unmatched words take their neighbours' times
    times = [None] * len(words)
    sm = difflib.SequenceMatcher(a=[norm(w) for _, w in words], b=[h[0] for h in heard], autojunk=False)
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag in ('equal', 'replace') and b1 > b0:
            for k in range(a1 - a0):
                h = heard[b0 + min(k * (b1 - b0) // (a1 - a0), b1 - b0 - 1)]
                times[a0 + k] = (float(h[1]), float(h[2]))
    for k in range(len(times)):
        if times[k] is None:
            times[k] = next((times[j] for j in list(range(k - 1, -1, -1)) + list(range(k + 1, len(times))) if times[j]), (0.0, 0.0))

    # Captions: each piece of a row gets the time of its own words
    captions, k = [], 0
    for row_pieces in captions_text:
        for piece in row_pieces:
            n = len(piece.split())
            ts = times[k:k + n]; k += n
            captions.append({'start': round(max(0.0, ts[0][0] - LEAD), 2), 'end': round(ts[-1][1] + HOLD, 2), 'text': piece,
                             'words': [{'w': w, 's': round(s, 2), 'e': round(e, 2)} for w, (s, e) in zip(piece.split(), ts)],
                             'split': len(row_pieces) > 1})
    for a, b in zip(captions, captions[1:]):
        a['end'] = min(a['end'], b['start'])
    captions[-1]['end'] = round(min(captions[-1]['end'], duration), 2)
    json.dump(captions, open(os.path.join(d, 'captions.json'), 'w'), indent=1)

    # Cues become event markers at their word
    markers = [m for m in timing.get('markers', []) if m.get('source') != 'script']
    for cue in cues:
        text, at = cue[0], cue[1]
        name = event_for(text)
        if not name:
            problems.append(f'{line}: cue [{text}] matches no event in dialogue/events.json')
            continue
        t = times[at][1] if len(cue) > 2 else max(0.0, times[at][0] - CUE_LEAD)
        markers.append({'time': round(t, 2), 'type': 'event', 'name': name, 'source': 'script', 'note': f'Script cue: [{text}]'})
    timing['markers'] = sorted(markers, key=lambda m: m['time'])
    json.dump(timing, open(os.path.join(d, 'cues.json'), 'w'), indent=1)
    print(line, [(c['start'], c['end'], c['text']) for c in captions], 'cues:', [(c[0], round(times[c[1]][0], 2)) for c in cues])

if problems:
    print('\nTo check:\n  ' + '\n  '.join(problems))
    if any('matches no event' in p for p in problems):
        sys.exit(1)
