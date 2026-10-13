"""Build every character's rig: Nova here, the others with tools/build_character.py.

Nova: builds art/Nova-rigged.svg and art/parts/ from the outfit exports, with the numbers
in tools/characters/nova.json. His head and face are shared; each outfit brings its own
legs, arms, body and hat from its flat Figma export. Adds the shared face rig (eyelids and
mouth shapes, tools/face_rig.py) and the original cap from art/Character.svg, and gives
each sleeve a round cap so the arm can rotate without its flat top showing.

Then builds each other character in tools/characters/ (art/<name>/).

Usage: python3 tools/build_rig.py
"""
import glob, json, math, os, re, shutil
from face_rig import (ROOT, centre, clips_used, lid, lid_parts, mouth_group, mouth_shapes, part_writer,
                      shapes_of, whiten)
import build_character

C = json.load(open(os.path.join(ROOT, 'tools', 'characters', 'nova.json')))
SRC = os.path.join(ROOT, 'art', C['source'])
OUT = os.path.join(ROOT, 'art', 'Nova-rigged.svg')
W, H = C['canvas']

els = shapes_of(SRC, C['shapeCount'])
old = shapes_of(os.path.join(ROOT, 'art', C['original']), C['originalShapeCount'])
src = open(SRC).read()
R = lambda spans: [i for a, b in spans for i in range(a, b)]   # [[a, b), ...] -> positions

# The head in the new art is the original head moved by this offset (same scale),
# so the hat and face rig are reused in the original coordinates inside a translate.
OFF = f'translate({C["faceOffset"][0]} {C["faceOffset"][1]})'

# Pivot dots (magenta circles) mark the shoulders; they are read here, not drawn.
dots = sorted((float(m[0]), float(m[1])) for m in
              re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="4" fill="#F006D8"/>', src))
assert len(dots) == 2, dots
HEAD_PIVOT = tuple(C['headPivot'])  # base of the neck, where the chin meets the collar
E = C['eyes']
PUPIL_REST = tuple(E['pupilRest'])
PUPIL_REST_Y = E['pupilRestY']  # both pupils also sit a little below their eye's centre
HD = C['head']
# Brows by screen side
BROWS = {side: els[HD['brows'][side]] for side in ('left', 'right')}

def sleeve_cap(sleeve, dot):
    """Round cap for a sleeve: a circle on the sleeve's centre line, as wide as the
    sleeve, centred where the pivot dot projects onto that line."""
    pts = [float(n) for n in re.findall(r'-?\d+\.?\d*', re.search(r'd="([^"]*)"', sleeve).group(1))[:4]]
    (x1, y1), (x2, y2) = pts[:2], pts[2:4]  # the flat top edge
    ex, ey = x2 - x1, y2 - y1
    half = math.hypot(ex, ey) / 2
    ax, ay = -ey / (2 * half), ex / (2 * half)  # perpendicular to the top edge...
    if ay < 0: ax, ay = -ax, -ay                 # ...pointing down the arm
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    t = (dot[0] - mx) * ax + (dot[1] - my) * ay
    return round(mx + t * ax, 1), round(my + t * ay, 1), round(half, 1)

def arm(fur, sleeve, extras, dot):
    """An arm's shapes plus its round sleeve cap, and the shoulder pivot (the cap's centre)."""
    cx, cy, r = sleeve_cap(sleeve, dot)
    fill = re.search(r'fill="([^"]*)"', sleeve).group(1)
    return (fur + sleeve + f'<circle class="sleeve-cap" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            + ''.join(extras)), (cx, cy)

# ---- face rig (tools/face_rig.py), in the original coordinates ----
shapes, CLIPS = mouth_shapes(''.join(old[i] for i in C['originalSmile']))
mouth = f'<g id="mouth" transform="{OFF}">' + ''.join(mouth_group(k, b, vis=(k == 'smile')) for k, b in shapes) + '</g>'
LIDS = [(side, *E['lids'][side]) for side in ('left', 'right')]   # (side, cx, cy, fur)
R_EYE = E['radius']
eyelids = (f'<g id="eyelids" transform="{OFF}">' + ''.join(lid(cx, cy, R_EYE, fur, side) for side, cx, cy, fur in LIDS)
           + '</g>')
# ---- Outfits (tools/characters/nova.json). The head comes from outfit 1's file and is the same in every outfit.
OUTFITS = C['outfits']
DEFAULT_OUTFIT = C['defaultOutfit']
CAP = f'<g transform="{OFF}">' + ''.join(old[C['originalCap'][0]:C['originalCap'][1]]) + '</g>'  # the original cap, in its own coordinates
OUTFIT_DEFS = ''   # gradients etc. that outfit shapes refer to
for name, o in OUTFITS.items():
    osrc = open(os.path.join(ROOT, 'art', o['file'])).read()
    oels = shapes_of(os.path.join(ROOT, 'art', o['file']), o['count'])
    odots = sorted((float(m[0]), float(m[1])) for m in
                   re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="4" fill="#F006D8"/>', osrc))
    pick = lambda ids: ''.join(oels[i] for i in ids)
    o['legs_svg'] = pick(R(o['legs']))
    o['body_svg'] = pick(R(o['body']))
    o['hat_svg'] = CAP if o['hat'] == 'cap' else pick(R(o['hat']))
    o['hat_back_svg'] = pick(R(o.get('hat_back', [])))
    for side, dot in (('left', odots[0]), ('right', odots[1])):
        fur, sleeve, extras = o[f'arm_{side}']
        o[f'arm_{side}_svg'], o[f'pivot_{side}'] = arm(oels[fur], oels[sleeve], [oels[i] for i in R(extras)], dot)
    for g in re.findall(r'<linearGradient.*?</linearGradient>|<radialGradient.*?</radialGradient>', osrc, re.S):
        OUTFIT_DEFS += g
        o['defs'] = o.get('defs', '') + g

def per_outfit(key, pivot=None):
    """One group per outfit; only the default outfit is shown."""
    out = ''
    for name, o in OUTFITS.items():
        attrs = f' data-pivot="{o[pivot][0]} {o[pivot][1]}"' if pivot else ''
        hide = '' if name == DEFAULT_OUTFIT else ' style="display:none"'
        out += f'<g class="outfit" data-outfit="{name}" data-label="{o["label"]}"{attrs}{hide}>{o[key]}</g>'
    return out
# White outline, drawn into the art (face_rig.whiten): every outer part again in white, a little bigger.
for o in OUTFITS.values():
    for k in ('legs', 'arm_left', 'arm_right', 'body', 'hat', 'hat_back'):
        o[f'{k}_ol_svg'] = whiten(o[f'{k}_svg'])

hat = '<g id="hat">' + per_outfit('hat_svg') + '</g>'
hat_back = '<g id="hat-back">' + per_outfit('hat_back_svg') + '</g>'

# ---- parts, back to front. Index = position in the flat export (0-based). ----
J = lambda a, b: ''.join(els[a:b])
legs = '<g id="legs">' + per_outfit('legs_svg') + '</g>'                    # legs and shoes
d = OUTFITS[DEFAULT_OUTFIT]
arms = ''.join(f'<g id="arm-{side}" class="part" data-pivot="{d["pivot_" + side][0]} {d["pivot_" + side][1]}">'
               + per_outfit(f'arm_{side}_svg', f'pivot_{side}') + '</g>' for side in ('left', 'right'))
body = '<g id="body">' + per_outfit('body_svg') + '</g>'                    # shorts, neck, shirt, jacket
EAR_ROOTS = ''.join(els[i] for i in HD['earRoots'])                       # behind the head
FUR = ''.join(els[i] for i in HD['fur'])                                  # head fur
EYES = J(*HD['eyes'])                                                     # eye patches, eye whites
EARS = J(*HD['ears'])
head = (f'<g id="head" class="part" data-pivot="{HEAD_PIVOT[0]} {HEAD_PIVOT[1]}">'
        + hat_back                                              # any part of the hat behind the head
        + els[HD['earRoots'][0]] + els[HD['earRoots'][1]]       # ear roots, behind the head
        + FUR
        + EYES
        + '<g id="pupils" clip-path="url(#clip-eyes)">'                 # pupils stay inside the eyes when they move
        + f'<g id="pupil-left" data-rest="{PUPIL_REST[0]}" data-rest-y="{PUPIL_REST_Y}">' + els[HD['pupils']['left']] + '</g>'
        + f'<g id="pupil-right" data-rest="{PUPIL_REST[1]}" data-rest-y="{PUPIL_REST_Y}">' + els[HD['pupils']['right']] + '</g></g>'
        + eyelids
        + EARS
        + '<g id="brows">' + ''.join(f'<g id="brow-{side}" data-pivot="{centre(b)[0]} {centre(b)[1]}">{b}</g>'
                                     for side, b in BROWS.items()) + '</g>'
        + els[HD['muzzle']]                                     # muzzle
        + mouth                                                 # replaces the drawn smile
        + ''.join(els[i] for i in HD['nose'])                   # nose
        + hat + '</g>')

# The outline layer mirrors the moving groups (-ol ids); the preview copies their transforms.
HEAD_OL = whiten(EAR_ROOTS + FUR + EARS)   # ear roots, head fur, ears
outline = ('<g id="outline">'
           + '<g id="legs-ol">' + per_outfit('legs_ol_svg') + '</g><g id="upper-ol">'
           + ''.join(f'<g id="arm-{side}-ol">' + per_outfit(f'arm_{side}_ol_svg') + '</g>' for side in ('left', 'right'))
           + '<g id="body-ol">' + per_outfit('body_ol_svg') + '</g>'
           + '<g id="head-ol"><g id="hat-back-ol">' + per_outfit('hat_back_ol_svg') + '</g>' + HEAD_OL
           + '<g id="hat-ol">' + per_outfit('hat_ol_svg') + '</g></g></g></g>')
LID_CLIPS = ''.join(f'<clipPath id="clip-eye-{side}"><ellipse cx="{cx}" cy="{cy}" rx="{round(R_EYE + 0.75, 1)}" ry="{round(R_EYE + 0.75, 1)}"/></clipPath>'
                    for side, cx, cy, fur in LIDS)
clips = ('<clipPath id="clip-eyes">' + ''.join(f'<ellipse cx="{x}" cy="{y}" rx="{R_EYE}" ry="{E["radiusY"]}"/>' for x, y in E['whites']) + '</clipPath>'
         + LID_CLIPS + ''.join(CLIPS))

svg = (f'<svg id="nova" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
       f'<defs>{clips}{OUTFIT_DEFS}</defs>\n'
       '<g id="character">\n'
       f'{outline}\n{legs}\n<g id="upper">\n{arms}\n{body}\n{head}\n</g>\n'
       '</g>\n</svg>\n')
open(OUT, 'w').write(svg)
print('wrote', OUT, len(svg), 'bytes; arm pivots', {n: (o['pivot_left'], o['pivot_right']) for n, o in OUTFITS.items()})

# ---- Separate part files for the app (art/parts/). Every part is drawn on the full
# 556 x 837 canvas, so the app stacks them in this order and moves them by their pivots.
#   base/              the same in every outfit: head, eyes, brows, mouths, nose
#   outfits/<outfit>/  that outfit's legs, arms, body and hat (and their white outlines)
# A new outfit only adds a folder; base/ never changes.
PARTS_DIR = os.path.join(ROOT, 'art', 'parts')
shutil.rmtree(PARTS_DIR, ignore_errors=True)
part = part_writer(PARTS_DIR, W, H)
lids = lambda state: f'<g transform="{OFF}">' + lid_parts([(side, cx, cy, R_EYE, fur) for side, cx, cy, fur in LIDS], state, 15) + '</g>'
for name, o in OUTFITS.items():
    for k in ('legs', 'arm_left', 'arm_right', 'body', 'hat', 'hat_back'):
        if o[f'{k}_svg']:
            part(f'outfits/{name}/{k}', o[f'{k}_svg'], o.get('defs', '') if k.startswith('hat') else '')
            part(f'outfits/{name}/{k}_outline', o[f'{k}_ol_svg'])
part('base/head_outline', HEAD_OL)
part('base/head_back', EAR_ROOTS + FUR + EYES)
part('base/pupil_left', els[HD['pupils']['left']])
part('base/pupil_right', els[HD['pupils']['right']])
part('base/lids_half', lids('half'), LID_CLIPS)
part('base/lids_closed', lids('closed'), LID_CLIPS)
part('base/ears', EARS)
part('base/brow_left', BROWS['left'])
part('base/brow_right', BROWS['right'])
part('base/muzzle', els[HD['muzzle']])
for k, b in shapes:
    part(f'base/mouth_{k}', f'<g transform="{OFF}">{b}</g>', clips_used(CLIPS, b))
part('base/nose', ''.join(els[i] for i in HD['nose']))
print('wrote', sum(len(f) for _, _, f in os.walk(PARTS_DIR)), 'part files to', PARTS_DIR, '(base/ and outfits/)')

# ---- Every other character (tools/characters/<name>.json, art/<name>/) ----
for path in sorted(glob.glob(os.path.join(ROOT, 'tools', 'characters', '*.json'))):
    if os.path.basename(path) != 'nova.json':
        build_character.build(path)
