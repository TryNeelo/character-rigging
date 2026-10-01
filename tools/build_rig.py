"""Build art/Nova-rigged.svg from art/Nova-outfit_1.svg.

Groups the flat Figma export into movable parts, adds the original hat and the
face rig (eyelids and mouth shapes) from art/Character.svg, and gives each sleeve
a round cap so the arm can rotate without its flat top showing.

Element indexes refer to the flat Figma exports, so re-check them if either
source file is re-exported.

Usage: python3 tools/build_rig.py
"""
import math, os, re
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

def arm(side, fur, sleeve, dot):
    cx, cy, r = sleeve_cap(sleeve, dot)
    fill = re.search(r'fill="([^"]*)"', sleeve).group(1)
    return (f'<g id="arm-{side}" class="part" data-pivot="{cx} {cy}">{fur}{sleeve}'
            f'<circle class="sleeve-cap" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/></g>')

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
hat = f'<g id="hat" class="part" transform="{OFF}">' + ''.join(old[54:59]) + '</g>'

# ---- parts, back to front. Index = position in the flat export (0-based). ----
J = lambda a, b: ''.join(els[a:b])
legs = '<g id="legs">' + J(1, 13) + '</g>'                      # legs and shoes
arms = arm('left', els[13], els[14], dots[0]) + arm('right', els[15], els[16], dots[1])
pants = '<g id="pants">' + els[17] + '</g>'
torso = '<g id="torso">' + J(18, 42) + '</g>'                   # hood, neck, shirt, jacket
head = (f'<g id="head" class="part" data-pivot="{HEAD_PIVOT[0]} {HEAD_PIVOT[1]}">'
        + els[0] + els[42]                                      # ear roots, behind the head
        + els[43] + els[44]                                     # head fur
        + J(45, 49)                                             # eye patches, eye whites
        + '<g id="pupils">' + els[49] + els[50] + '</g>'
        + eyelids
        + J(51, 55)                                             # ears
        + '<g id="brows">' + els[55] + els[56] + '</g>'
        + els[57]                                               # muzzle
        + mouth                                                 # replaces the drawn smile (58, 59)
        + els[60] + els[61]                                     # nose
        + hat + '</g>')

# Outline: white edge grown from the character's silhouette, plus the original soft shadow.
OUTLINE = '''<filter id="outline" x="-0.15" y="-0.1" width="1.3" height="1.2" color-interpolation-filters="sRGB">
<feGaussianBlur in="SourceAlpha" stdDeviation="5" result="b"/>
<feComponentTransfer in="b" result="grown"><feFuncA type="linear" slope="40" intercept="-1.6"/></feComponentTransfer>
<feFlood flood-color="#FFFFFF"/><feComposite in2="grown" operator="in" result="edge"/>
<feGaussianBlur in="grown" stdDeviation="8" result="sb"/>
<feColorMatrix in="sb" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0" result="shadow"/>
<feMerge><feMergeNode in="shadow"/><feMergeNode in="edge"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>'''
clips = ('<clipPath id="clip-eye-left"><ellipse cx="178.875" cy="437.312" rx="25.4" ry="25.4"/></clipPath>'
         '<clipPath id="clip-eye-right"><ellipse cx="270.259" cy="437.312" rx="25.4" ry="25.4"/></clipPath>' + ''.join(CLIPS))

svg = (f'<svg id="nova" width="556" height="837" viewBox="0 0 556 837" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
       f'<defs>{OUTLINE}{clips}</defs>\n'
       '<g id="character" filter="url(#outline)">\n'
       f'{legs}\n<g id="upper">\n{arms}\n{pants}\n{torso}\n{head}\n</g>\n'
       '</g>\n</svg>\n')
open(OUT, 'w').write(svg)
print('wrote', OUT, len(svg), 'bytes; arm pivots', [sleeve_cap(els[14], dots[0]), sleeve_cap(els[16], dots[1])])
