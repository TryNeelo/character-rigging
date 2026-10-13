"""The shared face rig and drawing helpers, used for every character.

The mouth shapes and eyelids were first drawn for Nova. Every character reuses them:
the mouth shapes keep Nova's coordinates and are placed on a character's face with a
transform (see mouth_shapes), and the eyelids are drawn around each character's own
eyes in his skin colours (see lid).
"""
import json, math, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPE = r'<(?:path|rect|ellipse|circle)[^>]*?/>'
D = '#3D200A'   # mouth inside and lash line
T = '#D64327'   # tongue
CX = 224.7      # centre line of Nova's original mouth shapes
LID_R = 24.654  # the eye radius the lid sizes were drawn for (Nova's)
OUTLINE_PX = json.load(open(os.path.join(ROOT, 'tools', 'rig_settings.json')))['outline']['widthPx']

def shapes_of(path, count):
    """Every shape in a flat Figma export, in drawing order. The count guards against a re-export."""
    els = re.findall(SHAPE, open(path).read())
    assert len(els) == count, (path, len(els), count)
    return els

def centre(shape):
    """Centre of a path's bounding box, rounded: where a brow tilts from."""
    n = [float(v) for v in re.findall(r'-?\d+\.?\d*', re.search(r'd="([^"]*)"', shape).group(1))]
    return round((min(n[0::2]) + max(n[0::2])) / 2, 1), round((min(n[1::2]) + max(n[1::2])) / 2, 1)

def lid(cx, cy, r, fur, side, extra=''):
    """An eye's lid group, clipped to the eye: the lid (moved up out of sight while open,
    translateY animates it) and the closed eye. Sizes scale with the eye's radius."""
    k = r / LID_R
    a = lambda v: v * k                       # a length drawn for Nova's eye, at this eye's size
    sw = lambda v: f'{round(v * k, 2):g}'     # a stroke width, likewise
    return f'''<g id="eye-{side}-lid-wrap" clip-path="url(#clip-eye-{side})"{extra}>
<g id="eye-{side}-lid" class="lid" transform="translate(0 -{2*r+a(2):.1f})">
<path d="M{cx-r-a(3):.1f} {cy-2*r-a(6):.1f} H{cx+r+a(3):.1f} V{cy+a(2):.1f} Q{cx:.1f} {cy+a(14):.1f} {cx-r-a(3):.1f} {cy+a(2):.1f} Z" fill="{fur}"/>
<path d="M{cx-r-a(3):.1f} {cy+a(2):.1f} Q{cx:.1f} {cy+a(14):.1f} {cx+r+a(3):.1f} {cy+a(2):.1f}" stroke="{D}" stroke-width="{sw(3.2)}" fill="none" stroke-linecap="round"/>
</g>
<g id="eye-{side}-closed" class="eye-closed" style="display:none">
<rect x="{cx-r-a(3):.1f}" y="{cy-r-a(3):.1f}" width="{2*r+a(6):.1f}" height="{2*r+a(6):.1f}" fill="{fur}"/>
<path d="M{cx-r+a(3):.1f} {cy+a(3):.1f} Q{cx:.1f} {cy+a(17):.1f} {cx+r-a(3):.1f} {cy+a(3):.1f}" stroke="{D}" stroke-width="{sw(3.4)}" fill="none" stroke-linecap="round"/>
</g></g>'''

def lid_parts(eyes, state, half_y):
    """The half-closed or closed lids of both eyes, for the app's part files.
    eyes: [(side, cx, cy, r, fur)]. half_y: how far the lid sits up when half closed."""
    out = ''
    for side, cx, cy, r, fur in eyes:
        g = lid(cx, cy, r, fur, side)
        lid_g = re.search(r'<g id="eye-%s-lid".*?</g>' % side, g, re.S).group(0)
        closed_g = re.search(r'<g id="eye-%s-closed".*?</g>' % side, g, re.S).group(0)
        if state == 'half':
            out += f'<g clip-path="url(#clip-eye-{side})">' + re.sub(r'translate\(0 -[\d.]+\)', f'translate(0 -{half_y:g})', lid_g, 1) + '</g>'
        else:
            out += f'<g clip-path="url(#clip-eye-{side})">' + closed_g.replace(' style="display:none"', '') + '</g>'
    return out

def mouth_shapes(smile, lip='#C8985A'):
    """The mouth shapes, Rhubarb Lip Sync naming (A-H, X) plus the idle smile, in Nova's
    original coordinates. Returns ([(letter, svg)], clip paths). No teeth in this version."""
    clips = []
    def dshape(x0, x1, top, bot):
        w = x1 - x0
        return f'M{x0} {top} H{x1} C{x1} {top+(bot-top)*0.62:.1f} {CX+w*0.27:.1f} {bot} {CX} {bot} C{CX-w*0.27:.1f} {bot} {x0} {top+(bot-top)*0.62:.1f} {x0} {top}Z'
    def clipped(cid, d, inner):
        clips.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
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
     ('F', f'<ellipse cx="{CX}" cy="516" rx="10.5" ry="11" fill="{D}" stroke="{lip}" stroke-width="3"/>'),
     ('G', f'<path d="{dG}" fill="{D}"/>'),
     ('H', clipped('mc-H', dH, f'<ellipse cx="{CX}" cy="515" rx="13" ry="5.5" fill="{T}"/>')),
     ('smile', smile),
    ]
    return shapes, clips

def mouth_group(m_id, body, vis=False):
    hid = '' if vis else ' style="display:none"'
    return f'<g id="mouth-{m_id}" class="mouth"{hid}>{body}</g>'

def whiten(fragment):
    """White outline, drawn into the art: every shape again in white, its edge grown by
    OUTLINE_PX with a round stroke. The app draws these first, then the coloured parts on top."""
    def white(m):
        tag = m.group(0)
        attr = lambda name: (re.search(rf'\s{name}="([^"]*)"', tag) or [None, None])[1]
        fill, stroke_w = attr('fill'), float(attr('stroke-width') or 0) if attr('stroke') not in (None, 'none') else 0
        tag = re.sub(r'\s(?:fill|fill-opacity|fill-rule|clip-rule|stroke|stroke-width|stroke-linecap|stroke-linejoin|class|style)="[^"]*"', '', tag)
        return (tag[:-2] + f' fill="{"none" if fill == "none" else "#FFFFFF"}" stroke="#FFFFFF"'
                f' stroke-width="{2 * OUTLINE_PX + stroke_w:g}" stroke-linejoin="round" stroke-linecap="round"/>')
    return re.sub(SHAPE, white, fragment)

def part_writer(parts_dir, width, height):
    """A function that writes one part file: the part alone on the character's full canvas."""
    def part(name, body, defs=''):
        path = os.path.join(parts_dir, name + '.svg')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').write(
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">'
            + (f'<defs>{defs}</defs>' if defs else '') + body + '</svg>\n')
    return part

def clips_used(clips, body):
    """The clip paths a fragment refers to."""
    return ''.join(c for c in clips if f'url(#{c.split(chr(34))[1]})' in body)

# ---- Geometry for shapes found in a character's export ----
def matrix(tag):
    """A shape's transform as (a, b, c, d, e, f); identity if it has none."""
    t = (re.search(r'transform="([^"]*)"', tag) or [None, ''])[1]
    m = (1, 0, 0, 1, 0, 0)
    for kind, args in re.findall(r'(\w+)\(([^)]*)\)', t):
        v = [float(x) for x in re.split(r'[\s,]+', args.strip())]
        if kind == 'matrix': n = tuple(v)
        elif kind == 'translate': n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif kind == 'rotate':
            a = math.radians(v[0]); c, s = math.cos(a), math.sin(a)
            x, y = (v[1], v[2]) if len(v) > 2 else (0, 0)
            n = (c, s, -s, c, x - c * x + s * y, y - s * x - c * y)
        else: raise ValueError(kind)
        a1, b1, c1, d1, e1, f1 = m; a2, b2, c2, d2, e2, f2 = n
        m = (a1*a2 + c1*b2, b1*a2 + d1*b2, a1*c2 + c1*d2, b1*c2 + d1*d2, a1*e2 + c1*f2 + e1, b1*e2 + d1*f2 + f1)
    return m

def num(tag, name):
    return float(re.search(rf'\s{name}="([-\d.]+)"', tag).group(1))

def round_rect_centre(tag):
    """Centre and half size of an (untransformed) rounded rect or ellipse, such as an eye white."""
    if tag.startswith('<ellipse') or tag.startswith('<circle'):
        r = num(tag, 'r') if tag.startswith('<circle') else None
        return num(tag, 'cx'), num(tag, 'cy'), r or num(tag, 'rx'), r or num(tag, 'ry')
    x, y, w, h = num(tag, 'x'), num(tag, 'y'), num(tag, 'width'), num(tag, 'height')
    return x + w / 2, y + h / 2, w / 2, h / 2

def rect_centre(tag):
    """Centre of a rect after its transform, such as a brow."""
    a, b, c, d, e, f = matrix(tag)
    x = (re.search(r'\sx="([-\d.]+)"', tag) or [0, 0])[1]; y = (re.search(r'\sy="([-\d.]+)"', tag) or [0, 0])[1]
    px, py = float(x) + num(tag, 'width') / 2, float(y) + num(tag, 'height') / 2
    return round(a * px + c * py + e, 1), round(b * px + d * py + f, 1)

def capsule_top(tag):
    """For a capsule (a rect with fully rounded ends, like an upper arm): the centre of its
    upper round end. A shoulder turning about this point keeps the end in place."""
    a, b, c, d, e, f = matrix(tag)
    x = float((re.search(r'\sx="([-\d.]+)"', tag) or [0, 0])[1]); y = float((re.search(r'\sy="([-\d.]+)"', tag) or [0, 0])[1])
    w, h = num(tag, 'width'), num(tag, 'height')
    r = w / 2
    ends = [(x + r, y + r), (x + r, y + h - r)]
    pts = [(a * px + c * py + e, b * px + d * py + f) for px, py in ends]
    top = min(pts, key=lambda p: p[1])
    return round(top[0], 1), round(top[1], 1)

def path_box(tag):
    """Bounding box of a path with absolute commands (from its points and control points,
    which is close enough for the simple shapes in a face)."""
    xs, ys = [], []
    for cmd, args in re.findall(r'([MLHVCSQTZ])([^MLHVCSQTZ]*)', re.search(r'd="([^"]*)"', tag).group(1)):
        n = [float(v) for v in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', args)]
        if cmd == 'H': xs += n
        elif cmd == 'V': ys += n
        else: xs += n[0::2]; ys += n[1::2]
    return min(xs), min(ys), max(xs), max(ys)
