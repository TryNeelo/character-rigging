"""Build a self-contained preview page for one dialogue line.

Usage: python3 tools/build_preview.py onboarding_nova_dialogue1
Reads  dialogue/<line>/<line>.mp3 (or any .mp3 in that folder) and dialogue/<line>/cues.json
Writes preview/<line>.html  (audio, art and cues all embedded; opens in any browser)
"""
import base64, glob, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
line = sys.argv[1] if len(sys.argv) > 1 else 'onboarding_nova_dialogue1'
d = os.path.join(ROOT, 'dialogue', line)
mp3 = os.path.join(d, line + '.mp3')
if not os.path.exists(mp3):
    mp3 = sorted(glob.glob(os.path.join(d, '*.mp3')))[0]
cues = json.load(open(os.path.join(d, 'cues.json')))['mouthCues']
svg = open(os.path.join(ROOT, 'art', 'Character-rigged.svg')).read().replace(
    'width="1194" height="834" viewBox="0 0 1194 834"',
    'viewBox="20 225 430 609" role="img" aria-label="Bear character in a teal hoodie and cap"', 1)
audio = 'data:audio/mpeg;base64,' + base64.b64encode(open(mp3, 'rb').read()).decode()
page = open(os.path.join(ROOT, 'tools', 'preview_template.html')).read()
page = (page.replace('%%SVG%%', svg)
            .replace('%%CUES%%', json.dumps([{k: c[k] for k in ('start', 'end', 'value')} for c in cues]))
            .replace('%%AUDIO%%', audio)
            .replace('%%NCUES%%', str(len(cues)))
            .replace('%%DUR%%', f"{cues[-1]['end']:.1f}"))
os.makedirs(os.path.join(ROOT, 'preview'), exist_ok=True)
out = os.path.join(ROOT, 'preview', line + '.html')
open(out, 'w').write(page)
print('wrote', out)
