"""Bring a new recording to the same loudness as the other lines.

Measures the speech level (the louder 30 dB of 20 ms frames), applies the gain that brings it to
the target, keeps peaks at -1 dBFS with a gentle 5 ms look-ahead limiter, and writes a 192 kbps
mp3. The FTUX lines sit at about -16.5 dB.

Needs numpy and lameenc (both in ~/whisper-venv). Decode the source to WAV first with afconvert:
    afconvert -f WAVE -d LEI16 source.mp3 source.wav
Usage: ~/whisper-venv/bin/python tools/raise_audio.py source.wav dialogue/<line>/<line>.mp3 [-16.5]
       ~/whisper-venv/bin/python tools/raise_audio.py --measure file.wav ...   (just print the levels)
"""
import sys, wave
import numpy as np

def load(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768, w.getframerate()

def speech_db(x, sr):
    n = int(sr * 0.02)
    frames = x[:len(x) // n * n].reshape(-1, n)
    r = 20 * np.log10(np.sqrt((frames ** 2).mean(1)) + 1e-9)
    loud = r[r > r.max() - 30]
    return 20 * np.log10(np.sqrt(np.mean(10 ** (loud / 10))))

if sys.argv[1] == '--measure':
    for p in sys.argv[2:]:
        x, sr = load(p)
        print(f'{p}: speech {speech_db(x, sr):.1f} dB, peak {20 * np.log10(np.abs(x).max()):.1f} dBFS, {len(x) / sr:.2f} s')
    sys.exit()

import lameenc
src, out = sys.argv[1], sys.argv[2]
target = float(sys.argv[3]) if len(sys.argv) > 3 else -16.5
x, sr = load(src)
speech = speech_db(x, sr)
y = x * 10 ** ((target - speech) / 20)
# Limiter: the gain each sample needs to stay under -1 dBFS, held over +-5 ms and smoothed, so it never jumps
thr = 10 ** (-1 / 20)
need = np.minimum(1, thr / (np.abs(y) + 1e-12))
k = int(sr * 0.005)
win = np.lib.stride_tricks.sliding_window_view(np.pad(need, k, constant_values=1), 2 * k + 1).min(1)
c = np.cumsum(np.pad(win, (k, k), constant_values=1))
g = np.minimum(((c[2 * k:] - np.concatenate([[0], c[:-2 * k - 1]])) / (2 * k + 1))[:len(y)], win)
y = y * g
print(f'speech {speech:.1f} -> {target:.1f} dB, gain {target - speech:+.1f} dB, '
      f'peak {20 * np.log10(np.abs(y).max()):.2f} dBFS, limited samples {np.mean(g < 0.999) * 100:.2f}%')
enc = lameenc.Encoder(); enc.set_bit_rate(192); enc.set_in_sample_rate(sr); enc.set_channels(1); enc.set_quality(2)
open(out, 'wb').write(enc.encode((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()) + enc.flush())
