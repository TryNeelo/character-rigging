"""Build the preview page with every dialogue line on it.

Usage: python3 tools/build_preview.py
Reads  art/Nova-rigged.svg and, for each folder in dialogue/: its .mp3, cues.json,
       emphasis.json (from build_emphasis.py) and script.txt (optional, the exact words)
Writes preview/index.html  (art, audio and timing all embedded; opens in any browser)
       preview/<line>.html (a short page that opens index.html on that line, so older links keep working)

Each line is listed in the Audio files panel by its audio file's name, length and number of markers.
"""
import base64, glob, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'preview')

def load(line):
    d = os.path.join(ROOT, 'dialogue', line)
    mp3 = os.path.join(d, line + '.mp3')
    if not os.path.exists(mp3):
        mp3 = sorted(glob.glob(os.path.join(d, '*.mp3')))[0]
    timing = json.load(open(os.path.join(d, 'cues.json')))
    read = lambda name, default: (json.load(open(os.path.join(d, name))) if name.endswith('.json')
                                  else open(os.path.join(d, name)).read().strip()) if os.path.exists(os.path.join(d, name)) else default
    return {
        'id': line,
        'title': os.path.basename(mp3),
        'words': ' '.join(read('script.txt', '').split()),
        'audio': 'data:audio/mpeg;base64,' + base64.b64encode(open(mp3, 'rb').read()).decode(),
        'cues': [{k: c[k] for k in ('start', 'end', 'value')} for c in timing['mouthCues']],
        'markers': timing.get('markers', []),
        'emphasis': read('emphasis.json', []),
    }

lines = [load(os.path.basename(os.path.dirname(p))) for p in sorted(glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json')))]
svg = open(os.path.join(ROOT, 'art', 'Nova-rigged.svg')).read().replace(
    '<svg id="nova" ', '<svg id="nova" role="img" aria-label="Nova, a bear, in his chosen outfit" ', 1)
page = (open(os.path.join(ROOT, 'tools', 'preview_template.html')).read()
        .replace('%%SVG%%', svg)
        .replace('%%SETTINGS%%', json.dumps(json.load(open(os.path.join(ROOT, 'tools', 'rig_settings.json')))))
        .replace('%%LINES%%', json.dumps(lines)))
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w').write(page)
for l in lines:
    open(os.path.join(OUT, l['id'] + '.html'), 'w').write(
        f'<!doctype html><meta charset="utf-8"><title>{l["title"]}</title>'
        f'<meta http-equiv="refresh" content="0; url=index.html#{l["id"]}">'
        f'<a href="index.html#{l["id"]}">Open the Nova preview</a>\n')
print('wrote', os.path.join(OUT, 'index.html'), 'with', len(lines), 'lines')
