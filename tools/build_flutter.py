"""Package Nova for the Flutter component in flutter/nova_character/.

Copies the part files from art/parts/ (run tools/build_rig.py first), writes
assets/rig.json (canvas, pivots, framing, idle, look, blink and outline settings)
and one folder per dialogue line with its audio and timing.json, then lists the
asset folders in the package's pubspec.yaml.

Usage: python3 tools/build_flutter.py
"""
import glob, json, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, 'flutter', 'nova_character')
ASSETS = os.path.join(PKG, 'assets')

shutil.rmtree(ASSETS, ignore_errors=True)
os.makedirs(os.path.join(ASSETS, 'parts'))
for f in glob.glob(os.path.join(ROOT, 'art', 'parts', '*.svg')):
    shutil.copy(f, os.path.join(ASSETS, 'parts'))

rigged = open(os.path.join(ROOT, 'art', 'Nova-rigged.svg')).read()
def pivot(id_):
    return [float(v) for v in re.search(rf'<g id="{id_}"[^>]*data-pivot="([^"]+)"', rigged).group(1).split()]
eyes = re.search(r'<clipPath id="clip-eyes">(.*?)</clipPath>', rigged).group(1)
legs_line = re.search(r'<g id="legs">.*', rigged).group(0)  # one group per outfit
settings = json.load(open(os.path.join(ROOT, 'tools', 'rig_settings.json')))
rig = {
    'canvas': {'width': 556, 'height': 837},
    'anchor': {'x': 278, 'y': 837},
    'pivots': {'head': pivot('head')},
    # Parts that change with the outfit: legs_<id>, arm_left_<id>, arm_right_<id>, body_<id>, hat_<id>
    'outfits': {
        o: {'label': label,
            'hatBack': os.path.exists(os.path.join(ROOT, 'art', 'parts', f'hat_back_{o}.svg')),
            'pivots': {side: [float(v) for v in re.search(
                rf'<g id="arm-{css}".*?data-outfit="{o}"[^>]*data-pivot="([^"]+)"', rigged, re.S).group(1).split()]
                for side, css in (('armLeft', 'left'), ('armRight', 'right'))}}
        for o, label in re.findall(r'<g class="outfit" data-outfit="([^"]+)" data-label="([^"]+)"', legs_line)
    },
    'defaultOutfit': re.search(r'<g id="legs"><g class="outfit" data-outfit="([^"]+)"', rigged).group(1),
    'eyes': {'centers': [[float(x), float(y)] for x, y in re.findall(r'cx="([\d.]+)" cy="([\d.]+)"', eyes)],
             'radius': 24.654,
             'pupilRest': [float(v) for v in re.findall(r'id="pupil-(?:left|right)" data-rest="([-\d.]+)"', rigged)]},
    **settings,
}
json.dump(rig, open(os.path.join(ASSETS, 'rig.json'), 'w'), indent=1)

lines = []
for d in sorted(glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json'))):
    line = os.path.basename(os.path.dirname(d))
    src = json.load(open(d))
    mp3s = sorted(glob.glob(os.path.join(os.path.dirname(d), '*.mp3')))
    out = os.path.join(ASSETS, 'lines', line)
    os.makedirs(out)
    shutil.copy(mp3s[0], os.path.join(out, 'audio.mp3'))
    cues = [{'start': c['start'], 'end': c['end'], 'shape': c['value']} for c in src['mouthCues']]
    json.dump({'id': line, 'audio': 'audio.mp3', 'duration': cues[-1]['end'], 'cues': cues,
               'markers': src.get('markers', [])}, open(os.path.join(out, 'timing.json'), 'w'), indent=1)
    lines.append(line)

pub = os.path.join(PKG, 'pubspec.yaml')
block = '    - assets/\n    - assets/parts/\n' + ''.join(f'    - assets/lines/{l}/\n' for l in lines)
s = open(pub).read()
s = re.sub(r'(    # BEGIN GENERATED ASSETS\n).*?(    # END GENERATED ASSETS)', lambda m: m.group(1) + block + m.group(2), s, flags=re.S)
open(pub, 'w').write(s)
print('packaged', len(os.listdir(os.path.join(ASSETS, 'parts'))), 'parts and lines', lines)
