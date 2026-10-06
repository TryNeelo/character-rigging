"""Build art/Nova-rigged.svg and art/parts/ from the outfit exports.

Nova's head and face are shared; each outfit (see OUTFITS) brings its own legs,
arms, body and hat from its flat Figma export. Adds the face rig (eyelids and mouth
shapes) and the original cap from art/Character.svg, and gives each sleeve a round
cap so the arm can rotate without its flat top showing.

Element indexes refer to the flat Figma exports, so re-check them if either
source file is re-exported.

Usage: python3 tools/build_rig.py
"""
import json, math, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'art', 'Nova-outfit_1.svg')
OLD = os.path.join(ROOT, 'art', 'Character.svg')
OUT = os.path.join(ROOT, 'art', 'Nova-rigged.svg')

SHAPE = r'<(?:path|rect|ellipse|circle)[^>]*?/>'
src = open(SRC).read()
els = re.findall(SHAPE, src)
assert len(els) == 64, len(els)
old = re.findall(SHAPE, open(OLD).read())
assert len(old) == 60, len(old)

# The head in the new art is the original head moved by this offset (same scale),
# so the hat and face rig are reused in the original coordinates inside a translate.
OFF = 'translate(54 -168.129)'

# Pivot dots (magenta circles) mark the shoulders; they are read here, not drawn.
dots = sorted((float(m[0]), float(m[1])) for m in
              re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="4" fill="#F006D8"/>', src))
assert len(dots) == 2, dots
HEAD_PIVOT = (278.7, 392)  # base of the neck, where the chin meets the collar
# How far each pupil sits from its eye's centre at rest (x). The art has them turned slightly
# inward, so looking sideways moves each pupil a different amount to the same spot.
PUPIL_REST = (8.2, -7.8)

def centre(shape):
    """Centre of a path's bounding box, rounded: where a brow tilts from."""
    n = [float(v) for v in re.findall(r'-?\d+\.?\d*', re.search(r'd="([^"]*)"', shape).group(1))]
    return round((min(n[0::2]) + max(n[0::2])) / 2, 1), round((min(n[1::2]) + max(n[1::2])) / 2, 1)
# Brows by screen side: in the export, the screen-right brow comes first (55), then the left (56).
BROWS = {'left': els[56], 'right': els[55]}

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

# ---- face rig, in the original coordinates (copied from the first rig) ----
CLIPS = []
D = '#3D200A'; T = '#D64327'; CX = 224.7

def lid(cx, cy, r, fur, side):
    # lid sits in local coords centred on the eye; translateY animates it
    return f'''<g id="eye-{side}-lid-wrap" clip-path="url(#clip-eye-{side})">
<g id="eye-{side}-lid" class="lid" transform="translate(0 -{2*r+2:.1f})">
<path d="M{cx-r-3:.1f} {cy-2*r-6:.1f} H{cx+r+3:.1f} V{cy+2:.1f} Q{cx:.1f} {cy+14:.1f} {cx-r-3:.1f} {cy+2:.1f} Z" fill="{fur}"/>
<path d="M{cx-r-3:.1f} {cy+2:.1f} Q{cx:.1f} {cy+14:.1f} {cx+r+3:.1f} {cy+2:.1f}" stroke="{D}" stroke-width="3.2" fill="none" stroke-linecap="round"/>
</g>
<g id="eye-{side}-closed" class="eye-closed" style="display:none">
<rect x="{cx-r-3:.1f}" y="{cy-r-3:.1f}" width="{2*r+6:.1f}" height="{2*r+6:.1f}" fill="{fur}"/>
<path d="M{cx-r+3:.1f} {cy+3:.1f} Q{cx:.1f} {cy+17:.1f} {cx+r-3:.1f} {cy+3:.1f}" stroke="{D}" stroke-width="3.4" fill="none" stroke-linecap="round"/>
</g></g>'''

# mouth shapes, Rhubarb Lip Sync naming (A-H, X) + original smile. No teeth in this version.
def m(id_, body, vis=False):
    hid = '' if vis else ' style="display:none"'
    return f'<g id="mouth-{id_}" class="mouth"{hid}>{body}</g>'
def dshape(x0, x1, top, bot):
    w = x1 - x0
    return f'M{x0} {top} H{x1} C{x1} {top+(bot-top)*0.62:.1f} {CX+w*0.27:.1f} {bot} {CX} {bot} C{CX-w*0.27:.1f} {bot} {x0} {top+(bot-top)*0.62:.1f} {x0} {top}Z'
def clipped(cid, d, inner):
    CLIPS.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
    return f'<path d="{d}" fill="{D}"/><g clip-path="url(#{cid})">{inner}</g>'

dB = dshape(204.5, 244.9, 508, 519.5)
dC = dshape(200.2, 249.2, 508, 528)
dD = dshape(196.8, 252.6, 507.8, 541)
dE = f'M207.2 510.5 C207.2 506.2 216 505.2 {CX} 505.2 C233.4 505.2 242.2 506.2 242.2 510.5 C242.2 523 234.5 532 {CX} 532 C214.9 532 207.2 523 207.2 510.5Z'
dG = dshape(205.5, 243.9, 508, 517)
dH = dshape(200.2, 249.2, 508, 528)
shapes = [
 ('X', f'<path d="M204 510.5 Q{CX} 523 245.4 510.5" stroke="{D}" stroke-width="4.2" fill="none" stroke-linecap="round"/>'),
 ('A', f'<path d="M206 513 Q{CX} 518.5 243.4 513" stroke="{D}" stroke-width="5.6" fill="none" stroke-linecap="round"/>'),
 ('B', f'<path d="{dB}" fill="{D}"/>'),
 ('C', clipped('mc-C', dC, f'<ellipse cx="{CX}" cy="530" rx="17" ry="8.5" fill="{T}"/>')),
 ('D', clipped('mc-D', dD, f'<ellipse cx="{CX}" cy="543" rx="20" ry="10.5" fill="{T}"/>')),
 ('E', clipped('mc-E', dE, f'<ellipse cx="{CX}" cy="533" rx="13" ry="7.5" fill="{T}"/>')),
 ('F', f'<ellipse cx="{CX}" cy="516" rx="10.5" ry="11" fill="{D}" stroke="#C8985A" stroke-width="3"/>'),
 ('G', f'<path d="{dG}" fill="{D}"/>'),
 ('H', clipped('mc-H', dH, f'<ellipse cx="{CX}" cy="515" rx="13" ry="5.5" fill="{T}"/>')),
 ('smile', old[47] + old[48]),
]
mouth = f'<g id="mouth" transform="{OFF}">' + ''.join(m(k, b, vis=(k == 'smile')) for k, b in shapes) + '</g>'
eyelids = (f'<g id="eyelids" transform="{OFF}">' + lid(178.875, 437.312, 24.654, '#983820', 'left')
           + lid(270.259, 437.312, 24.654, '#84270F', 'right') + '</g>')
# ---- Outfits. Each lists, by position in its flat export (0-based), the shapes that
# make its legs, arms (fur, sleeve, then shapes drawn over the sleeve) and body, plus
# its hat. The head comes from outfit 1's file and is the same in every outfit.
R = lambda a, b: list(range(a, b))
OUTFITS = {
    'hoodie': dict(label='Hoodie', file='Nova-outfit_1.svg', count=64, legs=R(1, 13),
                   arm_left=(13, 14, []), arm_right=(15, 16, []), body=[17] + R(18, 42), hat='cap'),
    'aviator': dict(label='Aviator', file='Nova-outfit_2.svg', count=97, legs=R(0, 16),
                    arm_left=(16, 17, R(18, 21)), arm_right=(21, 22, R(23, 26)),
                    body=R(26, 33) + R(35, 59), hat=R(80, 97)),
    # The hard hat's brim has a back piece that sits behind the head (hat_back).
    'construction': dict(label='Construction', file='Nova-outfit_3.svg', count=62, legs=R(1, 15),
                         arm_left=(15, 16, []), arm_right=(17, 18, []), body=R(19, 25) + R(52, 62),
                         hat=R(48, 52), hat_back=[0]),
}
DEFAULT_OUTFIT = 'hoodie'
CAP = f'<g transform="{OFF}">' + ''.join(old[54:59]) + '</g>'  # the original cap, in its own coordinates
OUTFIT_DEFS = ''   # gradients etc. that outfit shapes refer to
for name, o in OUTFITS.items():
    osrc = open(os.path.join(ROOT, 'art', o['file'])).read()
    oels = re.findall(SHAPE, osrc)
    assert len(oels) == o['count'], (name, len(oels))
    odots = sorted((float(m[0]), float(m[1])) for m in
                   re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="4" fill="#F006D8"/>', osrc))
    pick = lambda ids: ''.join(oels[i] for i in ids)
    o['legs_svg'] = pick(o['legs'])
    o['body_svg'] = pick(o['body'])
    o['hat_svg'] = CAP if o['hat'] == 'cap' else pick(o['hat'])
    o['hat_back_svg'] = pick(o.get('hat_back', []))
    for side, dot in (('left', odots[0]), ('right', odots[1])):
        fur, sleeve, extras = o[f'arm_{side}']
        o[f'arm_{side}_svg'], o[f'pivot_{side}'] = arm(oels[fur], oels[sleeve], [oels[i] for i in extras], dot)
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
# White outline, drawn into the art: every outer part again in white, its edge grown by
# OUTLINE_PX with a round stroke. The app draws these first, then the coloured parts on top.
OUTLINE_PX = json.load(open(os.path.join(ROOT, 'tools', 'rig_settings.json')))['outline']['widthPx']
def whiten(fragment):
    def white(m):
        tag = m.group(0)
        attr = lambda name: (re.search(rf'\s{name}="([^"]*)"', tag) or [None, None])[1]
        fill, stroke_w = attr('fill'), float(attr('stroke-width') or 0) if attr('stroke') not in (None, 'none') else 0
        tag = re.sub(r'\s(?:fill|fill-opacity|fill-rule|clip-rule|stroke|stroke-width|stroke-linecap|stroke-linejoin|class|style)="[^"]*"', '', tag)
        return (tag[:-2] + f' fill="{"none" if fill == "none" else "#FFFFFF"}" stroke="#FFFFFF"'
                f' stroke-width="{2 * OUTLINE_PX + stroke_w:g}" stroke-linejoin="round" stroke-linecap="round"/>')
    return re.sub(SHAPE, white, fragment)
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
head = (f'<g id="head" class="part" data-pivot="{HEAD_PIVOT[0]} {HEAD_PIVOT[1]}">'
        + hat_back                                              # any part of the hat behind the head
        + els[0] + els[42]                                      # ear roots, behind the head
        + els[43] + els[44]                                     # head fur
        + J(45, 49)                                             # eye patches, eye whites
        + '<g id="pupils" clip-path="url(#clip-eyes)">'                 # pupils stay inside the eyes when they move
        + f'<g id="pupil-left" data-rest="{PUPIL_REST[0]}">' + els[49] + '</g>'
        + f'<g id="pupil-right" data-rest="{PUPIL_REST[1]}">' + els[50] + '</g></g>'
        + eyelids
        + J(51, 55)                                             # ears
        + '<g id="brows">' + ''.join(f'<g id="brow-{side}" data-pivot="{centre(b)[0]} {centre(b)[1]}">{b}</g>'
                                     for side, b in BROWS.items()) + '</g>'
        + els[57]                                               # muzzle
        + mouth                                                 # replaces the drawn smile (58, 59)
        + els[60] + els[61]                                     # nose
        + hat + '</g>')

# The outline layer mirrors the moving groups (-ol ids); the preview copies their transforms.
HEAD_OL = whiten(els[0] + els[42] + els[43] + els[44] + J(51, 55))   # ear roots, head fur, ears
outline = ('<g id="outline">'
           + '<g id="legs-ol">' + per_outfit('legs_ol_svg') + '</g><g id="upper-ol">'
           + ''.join(f'<g id="arm-{side}-ol">' + per_outfit(f'arm_{side}_ol_svg') + '</g>' for side in ('left', 'right'))
           + '<g id="body-ol">' + per_outfit('body_ol_svg') + '</g>'
           + '<g id="head-ol"><g id="hat-back-ol">' + per_outfit('hat_back_ol_svg') + '</g>' + HEAD_OL
           + '<g id="hat-ol">' + per_outfit('hat_ol_svg') + '</g></g></g></g>')
EYE_WHITES = [(232.875, 269.183), (324.259, 269.183)]  # new-art coordinates, radius 24.654
clips = ('<clipPath id="clip-eyes">' + ''.join(f'<ellipse cx="{x}" cy="{y}" rx="24.654" ry="24.6125"/>' for x, y in EYE_WHITES) + '</clipPath>'
         '<clipPath id="clip-eye-left"><ellipse cx="178.875" cy="437.312" rx="25.4" ry="25.4"/></clipPath>'
         '<clipPath id="clip-eye-right"><ellipse cx="270.259" cy="437.312" rx="25.4" ry="25.4"/></clipPath>' + ''.join(CLIPS))

svg = (f'<svg id="nova" width="556" height="837" viewBox="0 0 556 837" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
       f'<defs>{clips}{OUTFIT_DEFS}</defs>\n'
       '<g id="character">\n'
       f'{outline}\n{legs}\n<g id="upper">\n{arms}\n{body}\n{head}\n</g>\n'
       '</g>\n</svg>\n')
open(OUT, 'w').write(svg)
print('wrote', OUT, len(svg), 'bytes; arm pivots', {n: (o['pivot_left'], o['pivot_right']) for n, o in OUTFITS.items()})

# ---- Separate part files for the app (art/parts/). Every part is drawn on the full
# 556 x 837 canvas, so the app stacks them in this order and moves them by their pivots.
PARTS_DIR = os.path.join(ROOT, 'art', 'parts')
os.makedirs(PARTS_DIR, exist_ok=True)
for f in os.listdir(PARTS_DIR):
    if f.endswith('.svg'): os.remove(os.path.join(PARTS_DIR, f))
def part(name, body, defs=''):
    open(os.path.join(PARTS_DIR, name + '.svg'), 'w').write(
        f'<svg width="556" height="837" viewBox="0 0 556 837" fill="none" xmlns="http://www.w3.org/2000/svg">'
        + (f'<defs>{defs}</defs>' if defs else '') + body + '</svg>\n')
eye_clips = ('<clipPath id="clip-eye-left"><ellipse cx="178.875" cy="437.312" rx="25.4" ry="25.4"/></clipPath>'
             '<clipPath id="clip-eye-right"><ellipse cx="270.259" cy="437.312" rx="25.4" ry="25.4"/></clipPath>')
def lids(state):
    out = ''
    for side, (cx, fur) in {'left': (178.875, '#983820'), 'right': (270.259, '#84270F')}.items():
        g = lid(cx, 437.312, 24.654, fur, side)
        lid_g = re.search(r'<g id="eye-%s-lid".*?</g>' % side, g, re.S).group(0)
        closed_g = re.search(r'<g id="eye-%s-closed".*?</g>' % side, g, re.S).group(0)
        if state == 'half':
            out += f'<g clip-path="url(#clip-eye-{side})">' + lid_g.replace(f'translate(0 -{2*24.654+2:.1f})', 'translate(0 -15)') + '</g>'
        else:
            out += f'<g clip-path="url(#clip-eye-{side})">' + closed_g.replace(' style="display:none"', '') + '</g>'
    return f'<g transform="{OFF}">{out}</g>'
for name, o in OUTFITS.items():
    for k in ('legs', 'arm_left', 'arm_right', 'body', 'hat', 'hat_back'):
        if o[f'{k}_svg']:
            part(f'{k}_{name}', o[f'{k}_svg'], o.get('defs', '') if k.startswith('hat') else '')
            part(f'{k}_{name}_outline', o[f'{k}_ol_svg'])
part('head_outline', HEAD_OL)
part('head_back', els[0] + els[42] + els[43] + els[44] + J(45, 49))
part('pupil_left', els[49])
part('pupil_right', els[50])
part('lids_half', lids('half'), eye_clips)
part('lids_closed', lids('closed'), eye_clips)
part('ears', J(51, 55))
part('brow_left', BROWS['left'])
part('brow_right', BROWS['right'])
part('muzzle', els[57])
for k, b in shapes:
    used = ''.join(c for c in CLIPS if f'url(#{c.split(chr(34))[1]})' in b)
    part(f'mouth_{k}', f'<g transform="{OFF}">{b}</g>', used)
part('nose', els[60] + els[61])
print('wrote', len([f for f in os.listdir(PARTS_DIR) if f.endswith('.svg')]), 'part files to', PARTS_DIR)
