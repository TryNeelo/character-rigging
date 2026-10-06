"""Time each sentence of a line's script for on-screen captions.

The exact words come from dialogue/<line>/script.txt; Whisper (faster-whisper) only
supplies when each word is heard. Script words are matched to Whisper's words in order,
so a misheard word (e.g. "Nilo" for "Neelo") still gets the right time. Writes
dialogue/<line>/captions.json as [{"start", "end", "text"}], one entry per sentence.
Run it again whenever a line's audio or script changes.

Needs faster-whisper:  python3 -m venv ~/whisper-venv && ~/whisper-venv/bin/pip install faster-whisper
Usage: ~/whisper-venv/bin/python tools/build_captions.py [line_name ...]   (all lines with a script if none given)
"""
import difflib, glob, json, os, re, sys
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAD, HOLD = 0.1, 0.4   # show a caption just before its first word; keep it up a moment after the last

norm = lambda w: re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))
model = WhisperModel('small.en', compute_type='int8')

lines = sys.argv[1:] or [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'dialogue', '*', 'script.txt'))]
for line in sorted(lines):
    d = os.path.join(ROOT, 'dialogue', line)
    script = ' '.join(open(os.path.join(d, 'script.txt')).read().split())
    audio = sorted(glob.glob(os.path.join(d, '*.mp3')))[0]
    duration = json.load(open(os.path.join(d, 'cues.json')))['mouthCues'][-1]['end']
    segments, _ = model.transcribe(audio, word_timestamps=True, beam_size=5)
    heard = [(norm(w.word), w.start, w.end) for s in segments for w in s.words]

    sentences = re.findall(r'[^.!?]+[.!?]*', script)
    words = [(i, w) for i, s in enumerate(sentences) for w in s.split()]
    # Line up script words with heard words; unmatched words take their neighbours' times
    times = [None] * len(words)
    sm = difflib.SequenceMatcher(a=[norm(w) for _, w in words], b=[h[0] for h in heard], autojunk=False)
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag in ('equal', 'replace') and b1 > b0:
            for k in range(a1 - a0):
                h = heard[b0 + min(k * (b1 - b0) // (a1 - a0), b1 - b0 - 1)]
                times[a0 + k] = (h[1], h[2])
    for k in range(len(times)):          # fill any gaps from the nearest timed word
        if times[k] is None:
            near = next((times[j] for j in list(range(k - 1, -1, -1)) + list(range(k + 1, len(times))) if times[j]), (0, 0))
            times[k] = near

    captions = []
    for i, text in enumerate(sentences):
        ts = [times[k] for k, (si, _) in enumerate(words) if si == i]
        captions.append({'start': round(float(max(0, ts[0][0] - LEAD)), 2), 'end': round(float(ts[-1][1] + HOLD), 2), 'text': text.strip()})
    for a, b in zip(captions, captions[1:]):    # never overlap the next sentence
        a['end'] = round(float(min(a['end'], b['start'])), 2)
    captions[-1]['end'] = round(float(min(captions[-1]['end'], duration)), 2)
    json.dump(captions, open(os.path.join(d, 'captions.json'), 'w'), indent=1)
    print(line, [(c['start'], c['end'], c['text']) for c in captions])
