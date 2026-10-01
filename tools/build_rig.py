"""Build art/Character-rigged.svg from art/Character.svg.

Adds eyelids (half and closed frames) and the mouth set (Rhubarb shapes A-H, X,
plus the original smile). Element indexes refer to the flat Figma export, so
re-check them if the source art is re-exported.

Usage: python3 tools/build_rig.py
"""
import re, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'art','Character.svg'); OUT=os.path.join(ROOT,'art','Character-rigged.svg')
s=open(SRC).read()
els=re.findall(r'<(?:path|rect|ellipse)[^>]*?/>',s)
assert len(els)==60, len(els)
CLIPS=[]
D='#3D200A'; T='#D64327'; W='#FEF4DA'; CX=224.7

def lid(cx,cy,r,fur,side):
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

# mouth shapes, Rhubarb Lip Sync naming (A-H, X) + original smile
def m(id_, body, vis=False):
    hid='' if vis else ' style="display:none"'
    return f'<g id="mouth-{id_}" class="mouth"{hid}>{body}</g>'
def dshape(x0,x1,top,bot):
    w=x1-x0
    return f'M{x0} {top} H{x1} C{x1} {top+(bot-top)*0.62:.1f} {CX+w*0.27:.1f} {bot} {CX} {bot} C{CX-w*0.27:.1f} {bot} {x0} {top+(bot-top)*0.62:.1f} {x0} {top}Z'
def clipped(cid,d,inner):
    CLIPS.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
    return f'<path d="{d}" fill="{D}"/><g clip-path="url(#{cid})">{inner}</g>'

dB=dshape(204.5,244.9,508,519.5)
dC=dshape(200.2,249.2,508,528)
dD=dshape(196.8,252.6,507.8,541)
dE=f'M207.2 510.5 C207.2 506.2 216 505.2 {CX} 505.2 C233.4 505.2 242.2 506.2 242.2 510.5 C242.2 523 234.5 532 {CX} 532 C214.9 532 207.2 523 207.2 510.5Z'
dG=dshape(205.5,243.9,508,517)
dH=dshape(200.2,249.2,508,528)
shapes = [
 ('X', f'<path d="M204 510.5 Q{CX} 523 245.4 510.5" stroke="{D}" stroke-width="4.2" fill="none" stroke-linecap="round"/>'),
 ('A', f'<path d="M206 513 Q{CX} 518.5 243.4 513" stroke="{D}" stroke-width="5.6" fill="none" stroke-linecap="round"/>'),
 ('B', clipped('mc-B',dB,f'<rect x="200" y="508" width="50" height="5.4" fill="{W}" class="teeth"/><rect x="200" y="516.2" width="50" height="5" fill="{W}" class="teeth"/>')),
 ('C', clipped('mc-C',dC,f'<ellipse cx="{CX}" cy="530" rx="17" ry="8.5" fill="{T}"/>')),
 ('D', clipped('mc-D',dD,f'<rect x="195" y="507.8" width="60" height="4.6" fill="{W}" class="teeth"/><ellipse cx="{CX}" cy="543" rx="20" ry="10.5" fill="{T}"/>')),
 ('E', clipped('mc-E',dE,f'<ellipse cx="{CX}" cy="533" rx="13" ry="7.5" fill="{T}"/>')),
 ('F', f'<ellipse cx="{CX}" cy="516" rx="10.5" ry="11" fill="{D}" stroke="#C8985A" stroke-width="3"/>'),
 ('G', clipped('mc-G',dG,f'<rect x="200" y="508" width="50" height="6.2" fill="{W}" class="teeth"/>')),
 ('H', clipped('mc-H',dH,f'<rect x="195" y="508" width="60" height="4.4" fill="{W}" class="teeth"/><ellipse cx="{CX}" cy="515" rx="13" ry="5.5" fill="{T}"/>')),
 ('smile', els[47]+els[48]),
]
mouth='<g id="mouth">'+''.join(m(k,b,vis=(k=='smile')) for k,b in shapes)+'</g>'

out=els[:]
out[47]=mouth; out[48]=''
out[37]=els[37]+'\n<g id="eyelids">'+lid(178.875,437.312,24.654,'#983820','left')+lid(270.259,437.312,24.654,'#84270F','right')+'</g>'
# wrap eyes
out[32]='<g id="eye-left">'+els[32]; out[34]=els[34]  # keep order; simple id grouping not required for anim
out[32]=els[32]
body='\n'.join(e for e in out[:59] if e)
head,rest=s.split(els[0],1)
tail=rest[rest.index(els[58])+len(els[58]):]
clips=f'<clipPath id="clip-eye-left"><ellipse cx="178.875" cy="437.312" rx="25.4" ry="25.4"/></clipPath><clipPath id="clip-eye-right"><ellipse cx="270.259" cy="437.312" rx="25.4" ry="25.4"/></clipPath>'+''.join(CLIPS)
svg=head+body+tail
svg=svg.replace('<defs>','<defs>'+clips,1)
svg=svg.replace('<svg ','<svg id="bear" ',1)
open(OUT,'w').write(svg)
print(len(svg))
