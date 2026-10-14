"""Print a line's sound map, for timing its mouth shapes by hand.

1. Letter order: a forced alignment of the script's letters to the audio (wav2vec2, torchaudio).
   The letter times can lag vowels by up to 0.1 s, so use them for the order of sounds only.
2. Segments: stretches of silence (.), quiet sound (q), hiss (s: s, sh, f, t bursts) and voice (V),
   with their loudness and brightness (spectral centroid: low = rounded oo, w, m; high = ee, eh).
3. Frames: every 10 ms of speech as time:loudness/brightness, with [letters] and ~ for hiss.

Place each shape about 30 ms ahead of its sound, keep every shape at least 40 ms long (the app
runs at 30 fps), rest on X in true silences, and close the lips (A) on real closures (m, b, p).

Needs torch, torchaudio and numpy (all in ~/whisper-venv). Make a 16 kHz mono WAV first:
    afconvert -f WAVE -d LEI16@16000 -c 1 dialogue/<line>/<line>.mp3 line.wav
Usage: ~/whisper-venv/bin/python tools/sound_map.py line.wav dialogue/<line>/script.txt
"""
import re, sys, wave
import numpy as np, torch, torchaudio
from torchaudio.functional import forced_align

wav, script = sys.argv[1:3]
w = wave.open(wav)
x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
sr = w.getframerate()
assert sr == 16000, 'the WAV must be 16 kHz mono'
hop, win = 160, 400
frames = []
for i in range(0, len(x) - win, hop):
    seg = x[i:i + win] * np.hanning(win)
    sp = np.abs(np.fft.rfft(seg)) ** 2; f = np.fft.rfftfreq(win, 1 / sr); e = sp.sum() + 1e-12
    frames.append((20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9), sp[f > 3500].sum() / e, (sp * f).sum() / e))
feat = np.array(frames)

bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
model, labels = bundle.get_model(), bundle.get_labels()
with torch.inference_mode():
    em, _ = model(torch.tensor(x, dtype=torch.float32)[None])
em = torch.log_softmax(em, -1)
text = re.sub(r'\[[^\]]*\]', ' ', open(script).read()).replace('’', "'")
words = [t for t in (re.sub(r"[^A-Z']", '', t.upper()) for t in text.split()) if t]
index = {c: i for i, c in enumerate(labels)}
ali, _ = forced_align(em, torch.tensor([[index[c] for c in '|'.join(words)]]), blank=0)
ali = ali[0].tolist()
ratio = len(x) / em.shape[1] / sr
spans, i = [], 0
while i < len(ali):
    if ali[i] != 0:
        j = i
        while j + 1 < len(ali) and ali[j + 1] == ali[i]: j += 1
        spans.append((labels[ali[i]], i * ratio)); i = j + 1
    else:
        i += 1
k, letters = 0, {}
for wd in words:
    chars = spans[k:k + len(wd)]; k += len(wd)
    if k < len(spans) and spans[k][0] == '|': k += 1
    print(wd, ' '.join(f'{c}{t:.2f}' for c, t in chars))
    for c, t in chars: letters.setdefault(int(round((t - 0.0125) * 100)), []).append(c)

db, hiss, bright = feat[:, 0], feat[:, 1], feat[:, 2]
top = db.max()
kind = ['.' if db[i] < top - 38 else 's' if hiss[i] > 0.4 else 'q' if db[i] < top - 24 else 'V' for i in range(len(feat))]
print('\nSEGMENTS')
runs, i = [], 0
while i < len(kind):
    j = i
    while j < len(kind) and kind[j] == kind[i]: j += 1
    said = ''.join(''.join(letters.get(t, [])) for t in range(i, j))
    print(f'{i / 100 + 0.0125:5.2f}-{j / 100 + 0.0125:5.2f} {kind[i]} {np.mean(db[i:j]):5.1f}dB c{np.mean(bright[i:j]):4.0f} {said}')
    if kind[i] != '.': runs.append([i, j])
    i = j
print('\nFRAMES (time:dB/brightness[letters])')
speech = []
for a, b in runs:
    if speech and a - speech[-1][1] <= 3: speech[-1][1] = b
    else: speech.append([a, b])
for a, b in speech:
    print(f'== {a / 100:.2f}-{b / 100:.2f}')
    row = [f"{i / 100 + 0.0125:.2f}:{db[i]:.0f}/{bright[i] / 100:.0f}{'[' + ''.join(letters[i]) + ']' if i in letters else ''}{'~' if hiss[i] > 0.4 else ''}"
           for i in range(a, b)]
    for n in range(0, len(row), 10): print('  ' + '  '.join(row[n:n + 10]))
