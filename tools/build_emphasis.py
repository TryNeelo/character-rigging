"""Find the stressed moments in a line's audio, for Nova's automatic brow lifts.

Decodes the line's audio (afconvert on a Mac, or ffmpeg), measures loudness every
10 ms and keeps the clear peaks: the loudest syllables, at most one every 0.35 s.
Writes dialogue/<line>/emphasis.json as [{"time", "strength"}], with times shifted
30 ms early like the mouth cues. Run it again whenever a line's audio changes.

Usage: python3 tools/build_emphasis.py [line_name ...]   (all lines if none given)
"""
import array, glob, json, math, os, shutil, subprocess, sys, tempfile, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATE, HOP = 16000, 160   # 10 ms frames
LEAD = 0.03              # shapes lead the sound, as Rhubarb's cues do

def decode(audio):
    out = os.path.join(tempfile.mkdtemp(), 'line.wav')
    if shutil.which('afconvert'):
        subprocess.run(['afconvert', '-f', 'WAVE', '-d', f'LEI16@{RATE}', '-c', '1', audio, out], check=True)
    else:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', audio, '-ar', str(RATE), '-ac', '1', out], check=True)
    with wave.open(out) as w:
        return array.array('h', w.readframes(w.getnframes()))

def emphasis(samples):
    db = []
    for i in range(0, len(samples) - HOP, HOP):
        frame = samples[i:i + 2 * HOP]
        db.append(10 * math.log10(sum(x * x for x in frame) / len(frame) / 32768 ** 2 + 1e-10))
    smooth = [sum(db[max(0, i - 2):i + 3]) / len(db[max(0, i - 2):i + 3]) for i in range(len(db))]
    loudest = max(smooth)
    speech = sorted(v for v in smooth if v > loudest - 35)
    median = speech[len(speech) // 2]
    peaks = []
    for i, v in enumerate(smooth):
        window = smooth[max(0, i - 15):i + 16]
        dip = min(smooth[max(0, i - 20):i + 1])
        if v == max(window) and v >= median + 2 and v - dip >= 6:
            peaks.append((i, v))
    kept = []
    for i, v in sorted(peaks, key=lambda p: -p[1]):          # strongest first, then keep spacing
        if all(abs(i - j) >= 35 for j, _ in kept):
            kept.append((i, v))
    return [{'time': round(max(0, (i + 1) * HOP / RATE - LEAD), 2),
             'strength': round(min(1, max(0.3, (v - median) / (loudest - median))), 2)}
            for i, v in sorted(kept)]

lines = sys.argv[1:] or [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json'))]
for line in sorted(lines):
    d = os.path.join(ROOT, 'dialogue', line)
    audio = sorted(glob.glob(os.path.join(d, '*.mp3')))[0]
    result = emphasis(decode(audio))
    json.dump(result, open(os.path.join(d, 'emphasis.json'), 'w'), indent=1)
    print(line, [(e['time'], e['strength']) for e in result])
