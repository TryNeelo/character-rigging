"""Build a character other than Nova from his flat Figma export and settings file.

Reads  tools/characters/<name>.json (parts, pivots, face placement, colours; see skyrian.json)
       and the export it names in art/
Writes art/<name>/<Name>-rigged.svg   the rig for the preview (same ids and structure as Nova's)
       art/<name>/parts/              one SVG per part on the full canvas, for the app:
                                      base/ (head and face) and outfits/<outfit>/
       art/<name>/rig.json            canvas, pivots, eyes, head layers and setting changes, for the app

The face rig is shared (tools/face_rig.py): Nova's mouth shapes, scaled and centred on the
character's own drawn mouth, and eyelids drawn around his eyes in his skin colours.

Usage: python3 tools/build_character.py tools/characters/<name>.json   (build_rig.py runs it for every character)
"""
import json, os, re, shutil, sys
import math
from face_rig import (ROOT, outline_points, path_d, arm_from_three, mirrored, arm_from_placements, arm_from_poses, arm_joints, straight_like, compose, inverse, placement, turn, clips_used, lid, lid_parts, mouth_group, mouth_shapes, part_writer, path_box,
                      rect_centre, round_rect_centre, capsule_top, shapes_of, whiten, LID_R)

NOVA_SMILE = json.load(open(os.path.join(ROOT, 'tools', 'characters', 'nova.json')))

def build(config_path):
    name = os.path.splitext(os.path.basename(config_path))[0]
    C = json.load(open(config_path))
    W, H = C['canvas']
    els = shapes_of(os.path.join(ROOT, 'art', C['source']), C['shapeCount'])
    R = lambda spans: [i for a, b in spans for i in range(a, b)]
    pick = lambda spans: ''.join(els[i] for i in R(spans))
    F = C['face']

    # ---- Eyes: whites (the pupils stay inside them), pupils at rest, lids in his skin colours ----
    # The eye circle: the eye white, or (when the white isn't round, like Voltis's half-covered eyes) the
    # round eye shape around it (eyeCircles), which the lids close over
    eyes = {side: round_rect_centre(els[F.get('eyeCircles', F['whites'])[side]]) for side in ('left', 'right')}
    r = round(sum(e[2] for e in eyes.values()) / 2, 3)
    k = r / LID_R
    open_y, half_y = round(2 * r + 2 * k, 1), round(15 * k, 1)   # how far the lid sits up: open, half closed
    rest = {}
    for side in ('left', 'right'):
        x0, y0, x1, y1 = path_box(els[F['pupils'][side]])
        rest[side] = (round((x0 + x1) / 2 - eyes[side][0], 2), round((y0 + y1) / 2 - eyes[side][1], 2))
    rest_y = round((rest['left'][1] + rest['right'][1]) / 2, 2)
    lid_eyes = [(side, round(eyes[side][0], 3), round(eyes[side][1], 3), r, F['lidColors'][side]) for side in ('left', 'right')]
    eyelids = ('<g id="eyelids">' + ''.join(
        lid(cx, cy, rr, fur, side, f' data-open="{open_y:g}" data-half="{half_y:g}"') for side, cx, cy, rr, fur in lid_eyes) + '</g>')
    lid_clips = ''.join(f'<clipPath id="clip-eye-{side}"><ellipse cx="{cx}" cy="{cy}" rx="{round(rr + 0.75, 1)}" ry="{round(rr + 0.75, 1)}"/></clipPath>'
                        for side, cx, cy, rr, fur in lid_eyes)
    eye_clip = ('<clipPath id="clip-eyes">' + ''.join(f'<ellipse cx="{round(e[0], 3)}" cy="{round(e[1], 3)}" rx="{round(e[2], 3)}" ry="{round(e[3], 3)}"/>'
                                                     for e in eyes.values()) + '</clipPath>')
    clip_polygons = None
    if F.get('pupilClip') == 'whites':
        # Pupils stay inside the eye whites themselves (not a circle): the white shapes are the clip,
        # and the app gets them as outlines
        whites = [els[F['whites'][side]] for side in ('left', 'right')]
        eye_clip = '<clipPath id="clip-eyes">' + ''.join('<path d="%s"/>' % path_d(w) for w in whites) + '</clipPath>'
        clip_polygons = [outline_points(w) for w in whites]
    pupils = ('<g id="pupils" clip-path="url(#clip-eyes)">' + ''.join(
        f'<g id="pupil-{side}" data-rest="{rest[side][0]:g}" data-rest-y="{rest_y:g}">{els[F["pupils"][side]]}</g>' for side in ('left', 'right')) + '</g>')

    # ---- Brows tilt about their centres ----
    brow = {side: els[F['brows'][side]] for side in ('left', 'right')}
    brow_pivot = {side: rect_centre(b) if b.startswith('<rect') else None for side, b in brow.items()}
    brows = '<g id="brows">' + ''.join(f'<g id="brow-{side}" data-pivot="{p[0]:g} {p[1]:g}">{brow[side]}</g>' for side, p in brow_pivot.items()) + '</g>'

    # ---- Mouth: Nova's shapes, scaled to his drawn mouth and centred on it; his own mouth is the smile ----
    smile = pick(F['smile'])
    old = shapes_of(os.path.join(ROOT, 'art', NOVA_SMILE['original']), NOVA_SMILE['originalShapeCount'])
    box = lambda tags: [f(v) for f, v in zip((min, min, max, max), zip(*[path_box(t) for t in tags]))]
    nx0, ny0, nx1, ny1 = box([old[i] for i in NOVA_SMILE['originalSmile']])
    sx0, sy0, sx1, sy1 = box([els[i] for i in R(F['smile'])])
    s = (sx1 - sx0) / (nx1 - nx0)
    # (the talking shapes can sit a little lower than the drawn mouth, so a mustache doesn't hide them)
    tx, ty = (sx0 + sx1) / 2 - s * (nx0 + nx1) / 2, (sy0 + sy1) / 2 - s * (ny0 + ny1) / 2 + F.get('mouthDropY', 0)
    place = f'translate({tx:.3f} {ty:.3f}) scale({s:.4f})'
    shapes, clips = mouth_shapes('', F.get('lipColor', '#C8985A'), F.get('mouthColor', '#3D200A'))
    def thicken(b):
        # Thin lines (rest and closed mouths) get at least minStroke canvas units once scaled
        lo = F.get('minStroke', 0) / s
        return re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{max(float(m.group(1)), lo):.3g}"', b) if lo else b
    shapes = [(m, smile if m == 'smile' else f'<g transform="{place}">{thicken(b)}</g>') for m, b in shapes]
    mouth = '<g id="mouth">' + ''.join(mouth_group(m, b, vis=(m == 'smile')) for m, b in shapes) + '</g>'

    # ---- Outfits: legs, the body behind the arms, arms, body and hat ----
    outfits = C['outfits']
    for o in outfits.values():
        o['legs_svg'] = pick(o['legs'])
        o['body_back_svg'] = pick(o.get('body_back', []))
        o['body_svg'] = pick(o['body'])
        o['hat_svg'] = pick(o.get('hat', []))
        o['hat_back_svg'] = pick(o.get('hat_back', []))
        if 'armPoses' in o:
            # One arm drawn three ways (resting, raised straight, raised with the elbow bent): its shoulder and
            # elbow are the points the art turns about between the drawings. The other arm is its mirror image.
            P = o['armPoses']; ps = P['side']; pa = o[f'arm_{ps}']
            load = lambda f: shapes_of(os.path.join(ROOT, 'art', f), C['shapeCount'])
            fit = arm_from_three(els, load(P['raised']), load(P['bent']), R(pa['shapes']), R(pa['forearm']), ps)
            assert abs(fit['raised'] - P['raisedDegrees']) < 0.1 and abs(fit['bent'] + P['bentOutDegrees']) < 0.1, fit
            axis = (placement(els[o['arm_left']['capsule']])[4] + placement(els[o['arm_right']['capsule']])[4]) / 2
            arm_fits = {ps: fit, ('left' if ps == 'right' else 'right'): dict(fit, pivot=mirrored(fit['pivot'], axis),
                                                                                elbow=mirrored(fit['elbow'], axis))}
        for side in ('left', 'right'):
            a = o[f'arm_{side}']
            fore = set(R(a.get('forearm', [])))
            o[f'arm_{side}_svg'] = ''.join(els[i] for i in R(a['shapes']) if i not in fore)
            o[f'forearm_{side}_svg'] = pick(a.get('forearm', []))
            if fore and 'armsDown' in o:
                # Two-piece arm, with the same arms drawn straight down in another export: the pivots are the
                # points the art turns about between the two drawings, so both poses come out exactly
                down = shapes_of(os.path.join(ROOT, 'art', o['armsDown']), C['shapeCount'])
                (o[f'pivot_{side}'], o[f'elbow_{side}'], shoulder, bend,
                 o[f'down_{side}']) = arm_from_poses(els[a['capsule']], els[a['forearmCapsule']],
                                                     down[a['capsule']], down[a['forearmCapsule']], side)
                o[f'rest_{side}'] = (shoulder, bend)
            elif fore and 'armPoses' in o:
                f = arm_fits[side]
                o[f'pivot_{side}'], o[f'elbow_{side}'], o[f'rest_{side}'] = f['pivot'], f['elbow'], f['rest']
                o[f'down_{side}'] = f['rest'][0]   # the drawn arms hang down: [arms down] is the resting pose
            elif fore and 'armsLike' in o:
                # Arms drawn like another character's (the same capsules, scaled): his straight pose carries over
                like = json.load(open(os.path.join(ROOT, 'tools', 'characters', o['armsLike'] + '.json')))
                lo = next(iter(like['outfits'].values()))
                la = lo[f'arm_{side}']
                lrest = shapes_of(os.path.join(ROOT, 'art', like['source']), like['shapeCount'])
                ldown = shapes_of(os.path.join(ROOT, 'art', lo['armsDown']), like['shapeCount'])
                upper, forearm = straight_like(els[a['capsule']], els[a['forearmCapsule']], lrest[la['capsule']],
                                               ldown[la['capsule']], ldown[la['forearmCapsule']])
                (o[f'pivot_{side}'], o[f'elbow_{side}'], shoulder, bend,
                 o[f'down_{side}']) = arm_from_placements(placement(els[a['capsule']]), placement(els[a['forearmCapsule']]),
                                                          upper, forearm, side)
                o[f'rest_{side}'] = (shoulder, bend)
            elif fore:
                # Two-piece arm: the forearm (and hand) bends at the elbow. The art's pose is his rest pose.
                o[f'pivot_{side}'], o[f'elbow_{side}'], shoulder, bend = arm_joints(els[a['capsule']], els[a['forearmCapsule']], side)
                o[f'rest_{side}'] = (shoulder, bend)
            elif 'pivotDot' in a:
                # One-piece arm (like Nova's) turning at the shoulder dot in the art; the dot isn't drawn
                cx, cy, _, _ = round_rect_centre(els[a['pivotDot']])
                o[f'pivot_{side}'] = (round(cx, 2), round(cy, 2))
            else:
                o[f'pivot_{side}'] = tuple(a['pivot']) if 'pivot' in a else capsule_top(els[a['capsule']])
        for check in o.get('poseChecks', []):
            # Another export with one arm raised: the rig must reproduce its upper arm and forearm
            other = shapes_of(os.path.join(ROOT, 'art', check['file']), C['shapeCount'])
            x0, y0 = (float(v) for v in re.search(r'd="M(-?[\d.]+) (-?[\d.]+)', other[0]).groups())
            x1, y1 = (float(v) for v in re.search(r'd="M(-?[\d.]+) (-?[\d.]+)', els[0]).groups())
            back = (1, 0, 0, 1, x1 - x0, y1 - y0)   # the export may be wider, with everything shifted
            side, a = check['side'], o[f'arm_{check["side"]}']
            out = 1 if side == 'right' else -1
            def about(p, deg):   # turn by deg clockwise on screen about p
                r = math.radians(deg); c, s_ = math.cos(r), math.sin(r)
                return (c, s_, -s_, c, p[0] - c * p[0] + s_ * p[1], p[1] - s_ * p[0] - c * p[1])
            lift = about(o[f'pivot_{side}'], -out * (check['shoulder'] - o[f'rest_{side}'][0]))
            straighten = about(o[f'elbow_{side}'], -out * o[f'rest_{side}'][1])
            for part, move in (('capsule', lift), ('forearmCapsule', compose(lift, straighten))):
                want, got = compose(back, placement(other[a[part]])), compose(move, placement(els[a[part]]))
                assert max(abs(u - v) for u, v in zip(want, got)) < 0.1, (check, part, want, got)
        for kk in ('legs', 'body_back', 'arm_left', 'arm_right', 'forearm_left', 'forearm_right', 'body', 'hat', 'hat_back'):
            o[f'{kk}_ol_svg'] = whiten(o[f'{kk}_svg'])
        for side in ('left', 'right'):
            # In the rig, the forearm is a group inside the arm that turns about the elbow
            for ol in ('', '_ol'):
                if o[f'forearm_{side}_svg']:
                    e = o[f'elbow_{side}']
                    fore_g = f'<g class="forearm" data-pivot="{e[0]:g} {e[1]:g}">{o[f"forearm_{side}{ol}_svg"]}</g>'
                    # (a forearm can sit behind the upper arm and its sleeve, as drawn)
                    o[f'arm_{side}{ol}_rig'] = (fore_g + o[f'arm_{side}{ol}_svg'] if o[f'arm_{side}'].get('forearmBehind')
                                                else o[f'arm_{side}{ol}_svg'] + fore_g)
                else:
                    o[f'arm_{side}{ol}_rig'] = o[f'arm_{side}{ol}_svg']
    default = C['defaultOutfit']
    def per_outfit(key, pivot=None):
        out = ''
        for oname, o in outfits.items():
            attrs = f' data-pivot="{o[pivot][0]:g} {o[pivot][1]:g}"' if pivot else ''
            hide = '' if oname == default else ' style="display:none"'
            out += f'<g class="outfit" data-outfit="{oname}" data-label="{o["label"]}"{attrs}{hide}>{o[key]}</g>'
        return out

    # ---- Head, back to front, from the layer list ----
    rig_layers = {'pupils': pupils, 'lids': eyelids, 'brows': brows, 'mouth': mouth,
                  'hat': '<g id="hat">' + per_outfit('hat_svg') + '</g>', 'hat_back': '<g id="hat-back">' + per_outfit('hat_back_svg') + '</g>'}
    hp = C['headPivot']
    head = (f'<g id="head" class="part" data-pivot="{hp[0]:g} {hp[1]:g}">'
            + ''.join(rig_layers[l[0]] if len(l) == 1 else pick(l[1]) for l in C['head']) + '</g>')
    head_ol = whiten(pick(C['headOutline']))
    # Head parts drawn behind the body and arms (like hair hanging down the back) still turn with the head
    head_behind = ''.join(pick(l[1]) for l in C.get('headBehind', []))
    head_behind_g = (f'<g id="head-behind" class="part" data-pivot="{hp[0]:g} {hp[1]:g}">{head_behind}</g>\n' if head_behind else '')
    d = outfits[default]
    # data-rest: the arm's resting pose as drawn (shoulder out from straight down, elbow bend), when it has an elbow
    rest_attr = lambda side: ((f' data-rest="{d["rest_" + side][0]:g} {d["rest_" + side][1]:g}"' if ('rest_' + side) in d else '')
                              + (f' data-down="{d["down_" + side]:g}"' if ('down_' + side) in d else ''))
    arms = ''.join(f'<g id="arm-{side}" class="part" data-pivot="{d["pivot_" + side][0]:g} {d["pivot_" + side][1]:g}"{rest_attr(side)}>'
                   + per_outfit(f'arm_{side}_rig', f'pivot_{side}') + '</g>' for side in ('left', 'right'))
    outline = ('<g id="outline">'
               + '<g id="legs-ol">' + per_outfit('legs_ol_svg') + '</g><g id="upper-ol">'
               + '<g id="body-back-ol">' + per_outfit('body_back_ol_svg') + '</g>'
               + ''.join(f'<g id="arm-{side}-ol">' + per_outfit(f'arm_{side}_ol_rig') + '</g>' for side in ('left', 'right'))
               + '<g id="body-ol">' + per_outfit('body_ol_svg') + '</g>'
               + '<g id="head-ol"><g id="hat-back-ol">' + per_outfit('hat_back_ol_svg') + '</g>' + head_ol
               + '<g id="hat-ol">' + per_outfit('hat_ol_svg') + '</g></g></g></g>')
    ax, ay = C['anchor']
    svg = (f'<svg id="{name}" data-anchor-x="{ax:g}" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
           f'<defs>{eye_clip}{lid_clips}{"".join(clips)}</defs>\n'
           '<g id="character">\n'
           f'{outline}\n<g id="legs">{per_outfit("legs_svg")}</g>\n<g id="upper">\n'
           f'{head_behind_g}<g id="body-back">{per_outfit("body_back_svg")}</g>\n{arms}\n<g id="body">{per_outfit("body_svg")}</g>\n{head}\n</g>\n'
           '</g>\n</svg>\n')
    out_dir = os.path.join(ROOT, 'art', name)
    out = os.path.join(out_dir, f'{C["label"]}-rigged.svg')
    open(out, 'w').write(svg)

    # ---- Part files for the app, each on the full canvas ----
    parts_dir = os.path.join(out_dir, 'parts')
    shutil.rmtree(parts_dir, ignore_errors=True)
    part = part_writer(parts_dir, W, H)
    for oname, o in outfits.items():
        for kk in ('legs', 'body_back', 'arm_left', 'arm_right', 'forearm_left', 'forearm_right', 'body', 'hat', 'hat_back'):
            if o[f'{kk}_svg']:
                part(f'outfits/{oname}/{kk}', o[f'{kk}_svg'])
                part(f'outfits/{oname}/{kk}_outline', o[f'{kk}_ol_svg'])
    part('base/head_outline', head_ol)
    for l in C['head'] + C.get('headBehind', []):
        if len(l) == 2: part(f'base/{l[0]}', pick(l[1]))
    for side in ('left', 'right'):
        part(f'base/pupil_{side}', els[F['pupils'][side]])
        part(f'base/brow_{side}', brow[side])
    part('base/lids_half', lid_parts(lid_eyes, 'half', half_y), lid_clips)
    part('base/lids_closed', lid_parts(lid_eyes, 'closed', half_y), lid_clips)
    for m, b in shapes:
        part(f'base/mouth_{m}', b, clips_used(clips, b))

    # ---- What the app needs to place and move the parts ----
    rig = {
        'label': C['label'],
        'canvas': {'width': W, 'height': H},
        'anchor': {'x': ax, 'y': ay},
        'pivots': {'head': hp},
        'outfits': {oname: {'label': o['label'], 'hat': bool(o['hat_svg']),
                            **({'forearmBehind': True} if o['arm_left'].get('forearmBehind') else {}), 'hatBack': bool(o['hat_back_svg']), 'bodyBack': bool(o['body_back_svg']),
                            'pivots': {'armLeft': list(o['pivot_left']), 'armRight': list(o['pivot_right']),
                                       **({'elbowLeft': list(o['elbow_left']), 'elbowRight': list(o['elbow_right'])} if 'elbow_left' in o else {})},
                            # Resting pose of each arm as drawn: (shoulder out from straight down, elbow bend), in degrees
                            **({'armRest': {'left': list(o['rest_left']), 'right': list(o['rest_right'])}} if 'rest_left' in o else {}),
                            # Straight down, as drawn: the shoulder's angle out from vertical
                            **({'armDown': {'left': o['down_left'], 'right': o['down_right']}} if 'down_left' in o else {})}
                    for oname, o in outfits.items()},
        'defaultOutfit': default,
        'eyes': {'centers': [[round(e[0], 3), round(e[1], 3)] for e in eyes.values()], 'radius': r,
                 'pupilRest': [rest['left'][0], rest['right'][0]], 'pupilRestY': rest_y,
                 # the pupils' clip when the eye whites aren't round: each white's outline, as points
                 **({'clipPolygons': clip_polygons} if clip_polygons else {})},
        'browPivots': {side: list(p) for side, p in brow_pivot.items()},
        # The head's layers, back to front: part files in base/, or the face rig (pupils, lids, brows, mouth, hat)
        'headLayers': [l[0] for l in C['head']],
        # Head parts drawn behind the body and arms, turning with the head (part files in base/)
        **({'headBehindLayers': [l[0] for l in C['headBehind']]} if C.get('headBehind') else {}),
        'settings': C.get('settings', {}),
    }
    json.dump(rig, open(os.path.join(out_dir, 'rig.json'), 'w'), indent=1)
    print('wrote', out, len(svg), 'bytes and', sum(len(f) for _, _, f in os.walk(parts_dir)), 'part files;',
          f'mouth scale {s:.3f}, eye radius {r}, arm pivots {d["pivot_left"]} {d["pivot_right"]}')

if __name__ == '__main__':
    for p in sys.argv[1:]: build(p)
