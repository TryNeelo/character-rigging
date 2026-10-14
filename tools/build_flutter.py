"""Package the characters for the Flutter component in flutter/nova_character/.

Copies Nova's part files from art/parts/ (run tools/build_rig.py first), writes
assets/rig.json (canvas, pivots, framing, idle, look, blink and outline settings),
packages every other character into assets/characters/<name>/ (his parts and rig.json),
writes one folder per dialogue line with its audio and timing.json (with "character"
when someone other than Nova speaks it), then lists the asset folders in the package's
pubspec.yaml.

Usage: python3 tools/build_flutter.py
"""
import copy, glob, json, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, 'flutter', 'nova_character')
ASSETS = os.path.join(PKG, 'assets')

shutil.rmtree(ASSETS, ignore_errors=True)
os.makedirs(ASSETS)
shutil.copytree(os.path.join(ROOT, 'art', 'parts'), os.path.join(ASSETS, 'parts'))   # base/ and outfits/<outfit>/

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
            'hatBack': os.path.exists(os.path.join(ROOT, 'art', 'parts', 'outfits', o, 'hat_back.svg')),
            'pivots': {side: [float(v) for v in re.search(
                rf'<g id="arm-{css}".*?data-outfit="{o}"[^>]*data-pivot="([^"]+)"', rigged, re.S).group(1).split()]
                for side, css in (('armLeft', 'left'), ('armRight', 'right'))}}
        for o, label in re.findall(r'<g class="outfit" data-outfit="([^"]+)" data-label="([^"]+)"', legs_line)
    },
    'defaultOutfit': re.search(r'<g id="legs"><g class="outfit" data-outfit="([^"]+)"', rigged).group(1),
    'eyes': {'centers': [[float(x), float(y)] for x, y in re.findall(r'cx="([\d.]+)" cy="([\d.]+)"', eyes)],
             'radius': 24.654,
             'pupilRest': [float(v) for v in re.findall(r'id="pupil-(?:left|right)" data-rest="([-\d.]+)"', rigged)],
             'pupilRestY': float(re.search(r'data-rest-y="([-\d.]+)"', rigged).group(1))},
    **settings,
}
rig['brows']['pivots'] = {side: pivot(f'brow-{side}') for side in ('left', 'right')}
# Nova's head can be drawn smaller than the art (headScale in nova.json): his part files have it baked in,
# so the head numbers the app uses (eye centres and size, pupil and brow moves, brow pivots) shrink to match
hs = json.load(open(os.path.join(ROOT, 'tools', 'characters', 'nova.json'))).get('headScale')
if hs:
    k, (ax, ay) = hs['scale'], hs['anchor']
    rig = copy.deepcopy(rig)   # (the settings are shared with the other characters)
    at = lambda p: [round(ax + k * (p[0] - ax), 3), round(ay + k * (p[1] - ay), 3)]
    sz = lambda v: round(v * k, 3)
    e = rig['eyes']
    e['centers'] = [at(c) for c in e['centers']]
    e['radius'], e['pupilRest'], e['pupilRestY'] = sz(e['radius']), [sz(v) for v in e['pupilRest']], sz(e['pupilRestY'])
    rig['brows']['pivots'] = {side: at(p) for side, p in rig['brows']['pivots'].items()}
    for key in ('pupilReach', 'pupilReachY', 'browLiftUp'): rig['look'][key] = sz(rig['look'][key])
    rig['brows']['autoLiftPx'] = sz(rig['brows']['autoLiftPx'])
    for x in rig['brows']['expressions'].values(): x['liftPx'] = sz(x['liftPx'])
json.dump(rig, open(os.path.join(ASSETS, 'rig.json'), 'w'), indent=1)

def merged(base, change):
    """Settings with a character's own changes laid over them (framing is replaced whole)."""
    out = dict(base)
    for k, v in change.items():
        out[k] = merged(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) and k != 'framing' else v
    return out
# Every other character: assets/characters/<name>/rig.json and parts/ (base/ and outfits/<outfit>/)
characters = []
for path in sorted(glob.glob(os.path.join(ROOT, 'tools', 'characters', '*.json'))):
    name = os.path.splitext(os.path.basename(path))[0]
    if name == 'nova': continue
    src = json.load(open(os.path.join(ROOT, 'art', name, 'rig.json')))
    out = os.path.join(ASSETS, 'characters', name)
    shutil.copytree(os.path.join(ROOT, 'art', name, 'parts'), os.path.join(out, 'parts'))
    crig = {'label': src['label'], 'partsDir': f'characters/{name}/parts', 'headLayers': src['headLayers'],
            **{k: src[k] for k in ('canvas', 'anchor', 'pivots', 'outfits', 'defaultOutfit', 'eyes')},
            **merged(settings, src['settings'])}
    crig['brows'] = dict(crig['brows'], pivots=src['browPivots'])
    if src.get('headBehindLayers'): crig['headBehindLayers'] = src['headBehindLayers']
    json.dump(crig, open(os.path.join(out, 'rig.json'), 'w'), indent=1)
    characters.append(name)

lines = []
for d in sorted(glob.glob(os.path.join(ROOT, 'dialogue', '*', 'cues.json'))):
    line = os.path.basename(os.path.dirname(d))
    src = json.load(open(d))
    mp3s = sorted(glob.glob(os.path.join(os.path.dirname(d), '*.mp3')))
    out = os.path.join(ASSETS, 'lines', line)
    os.makedirs(out)
    shutil.copy(mp3s[0], os.path.join(out, 'audio.mp3'))
    cues = [{'start': c['start'], 'end': c['end'], 'shape': c['value']} for c in src['mouthCues']]
    emph = os.path.join(os.path.dirname(d), 'emphasis.json')
    caps = os.path.join(os.path.dirname(d), 'captions.json')    # from build_captions.py
    who = src.get('character', 'nova')
    assert who == 'nova' or who in characters, (line, who)
    json.dump({'id': line, **({'character': who} if who != 'nova' else {}), 'audio': 'audio.mp3', 'duration': cues[-1]['end'], 'cues': cues,
               'markers': src.get('markers', []),
               'emphasis': json.load(open(emph)) if os.path.exists(emph) else [],
               # the app only needs each caption's text and timing
               'captions': [{k: c[k] for k in ('start', 'end', 'text')} for c in json.load(open(caps))] if os.path.exists(caps) else []},
              open(os.path.join(out, 'timing.json'), 'w'), indent=1)
    lines.append(line)

pub = os.path.join(PKG, 'pubspec.yaml')
# Flutter needs every asset folder listed: base parts, one folder per outfit, one per line
outfit_dirs = sorted(os.listdir(os.path.join(ASSETS, 'parts', 'outfits')))
block = ('    - assets/\n    - assets/parts/base/\n' + ''.join(f'    - assets/parts/outfits/{o}/\n' for o in outfit_dirs)
         + ''.join(f'    - assets/characters/{c}/\n    - assets/characters/{c}/parts/base/\n'
                   + ''.join(f'    - assets/characters/{c}/parts/outfits/{o}/\n'
                             for o in sorted(os.listdir(os.path.join(ASSETS, 'characters', c, 'parts', 'outfits'))))
                   for c in characters)
         + ''.join(f'    - assets/lines/{l}/\n' for l in lines))
s = open(pub).read()
s = re.sub(r'(    # BEGIN GENERATED ASSETS\n).*?(    # END GENERATED ASSETS)', lambda m: m.group(1) + block + m.group(2), s, flags=re.S)
open(pub, 'w').write(s)
print('packaged', len(os.listdir(os.path.join(ASSETS, 'parts', 'base'))), 'base parts, outfits', outfit_dirs, 'characters', characters, 'and lines', lines)
