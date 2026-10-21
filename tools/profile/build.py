#!/usr/bin/env python3
"""Rebuild the profile's self-contained SVG artwork (Python 3, stdlib only).

Run from any directory: python tools/profile/build.py
The original studio assets provide the Möbius geometry and Korean outlines.
All motion is declarative SVG/CSS; no script, network or external font is used.
"""
from pathlib import Path
from copy import deepcopy
import json, math, re, xml.etree.ElementTree as ET
from html import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/aurora'
OLD = ROOT / 'assets/studio'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
def q(n): return '{'+NS+'}'+n
def serialize(e): return ET.tostring(e, encoding='unicode')

INK = '#f8f7fb'
MUTED = '#b2b9ca'
PINK = '#ffeaf2'
SKY = '#e4f4ff'
GOLD = '#fff6dc'
LINE = '#353a4b'
FONTS = json.loads((ROOT/'tools/profile/latin-glyphs.json').read_text())
PRINCIPLES = ET.parse(OLD/'principles-glass-readable.svg').getroot()
KO = {e.get('id')[5:]:e.get('d') for e in PRINCIPLES.iter() if e.get('id','').startswith('g-ko-')}

def glyph(ch, family):
    if family == 'ko':
        if ch == ' ': return '', 280, 1000
        key = format(ord(ch),'x')
        if key not in KO: raise ValueError('Missing Korean outline: '+ch)
        return KO[key], 940 if ord(ch)>0x2fff else (280 if ch=='.' else 583), 1000
    v = FONTS[family]
    g = v['chars'][ch]
    return g['d'], g['advance'], v['units']

def text_width(s,size,family='regular',tracking=0):
    return sum(glyph(c,family)[1]*size/glyph(c,family)[2]+tracking for c in s)

class SVG:
    def __init__(self,w,h,title,desc):
        self.w,self.h,self.title,self.desc=w,h,title,desc
        self.defs=[];self.body=[];self.css=[];self.glyphs={}
    def add(self,s): self.body.append(s)
    def text(self,s,x,y,size=22,color=INK,family='regular',tracking=0,anchor='start'):
        if anchor=='end': x-=text_width(s,size,family,tracking)
        if anchor=='middle': x-=text_width(s,size,family,tracking)/2
        paths=[];cursor=0
        for c in s:
            d,adv,u=glyph(c,family);gid=f't-{family}-{ord(c):x}'
            if d:
                self.glyphs[gid]=d
                paths.append(f'<use href="#{gid}" transform="translate({cursor:.3f} 0) scale({size/u:.7f} {-size/u:.7f})"/>')
            cursor+=adv*size/u+tracking
        return f'<g aria-label="{escape(s,quote=True)}" fill="{color}" transform="translate({x:.3f} {y:.3f})">'+''.join(paths)+'</g>'
    def write(self,name):
        defs=''.join(self.defs)+''.join(f'<path id="{key}" d="{d}"/>' for key,d in sorted(self.glyphs.items()))
        css=''.join(self.css)+'@media(prefers-reduced-motion:reduce){.motion{display:none!important}.still{display:inline!important}*{animation:none!important}}'
        out=f'<svg xmlns="{NS}" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc"><title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.desc)}</desc><defs>{defs}</defs><style>.still{{display:none}}{css}</style>'+''.join(self.body)+'</svg>\n'
        ET.fromstring(out)
        (OUT/name).write_text(out)

def rect(x,y,w,h,fill,rx=0,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'
def path(d,stroke=SKY,width=1.2,fill='none',extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {extra}/>'
def circle(x,y,r,fill,extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {extra}/>'

def background(s,accent=SKY):
    w,h=s.w,s.h
    s.defs += [f'<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#171b28"/><stop offset="1" stop-color="#10131d"/></linearGradient>',
      f'<radialGradient id="wash"><stop stop-color="{accent}" stop-opacity=".11"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>',
      f'<linearGradient id="pearl" x1="0" y1=".2" x2="1" y2=".8"><stop stop-color="{PINK}"/><stop offset=".48" stop-color="{SKY}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>',
      f'<clipPath id="bounds">{rect(0,0,w,h,"white",26)}</clipPath>']
    s.add('<g clip-path="url(#bounds)">'+rect(0,0,w,h,'url(#bg)',26)+circle(w*.84,h*.5,w*.5,'url(#wash)')+rect(.75,.75,w-1.5,h-1.5,'none',25.5,f'stroke="{LINE}" stroke-width="1.5"')+'</g>')

def mobius():
    r=ET.parse(OLD/'hero-mobius-smooth.svg').getroot()
    scene=deepcopy(next(e for e in r.iter() if e.get('transform')=='translate(956 320)'))
    scene.attrib.pop('transform')
    defs=[]
    for d in r.findall('.//'+q('defs')):
        for e in d:
            if e.get('id','').startswith('mb-') or e.get('id')=='axis-focus': defs.append(deepcopy(e))
    for parent in scene.iter():
        for child in list(parent):
            if child.tag == q('defs'): parent.remove(child)
    # Replace the original green bitmap material with a continuous pearl vector material.
    for i,e in enumerate(defs):
        if e.get('id') in ('mb-surface-motif','mb-edge-motif'):
            edge=e.get('id')=='mb-edge-motif';gid=e.get('id')
            content=rect(0,0,1200,120,'url(#belt-pearl)' if not edge else '#9baabc')
            content+=rect(0,0,1200,120,'url(#belt-satin)')
            content+=''.join(path(f'M0 {y}H1200','#ffffff',.5,extra='opacity=".16"') for y in (4,7,111,115))
            # Six low-contrast inlays travel along the same continuous surface.
            for x in range(60,1200,200):
                content+=rect(x,4,8,112,'#ffffff',3,'opacity=".52"')
                content+=path(f'M{x+22} 0V120','#7a8298',.5,extra='opacity=".20"')
            defs[i]=ET.fromstring(f'<g xmlns="{NS}" id="{gid}">{content}</g>')
    cmap={'#d5ff83':GOLD,'#e8bfff':PINK,'#d8f89c':GOLD,'#e7ffb1':GOLD,'#47b1b5':'#e5edf7','#8ad9b5':'#d9e7fa','#06191f':'#111522'}
    for root in [scene]+defs:
        for e in root.iter():
            for k,v in list(e.attrib.items()):
                if k in ('fill','stroke','stop-color','flood-color'):
                    if v in cmap:e.set(k,cmap[v])
                    elif re.fullmatch('#[0-9a-fA-F]{6}',v):
                        rr,gg,bb=[int(v[j:j+2],16) for j in (1,3,5)]
                        if max(rr,gg,bb)-min(rr,gg,bb)>45:
                            e.set(k, PINK if rr>gg and bb>gg else (GOLD if rr>bb and gg>bb else SKY))
            if e.get('data-continuous-lighting'):
                e.set('filter','url(#neutral-light)');e.set('opacity','.66')
            if e.get('class')=='mobius-solid':
                e.set('aria-label','A continuous half-twist in pale white-pink, white-sky and white-yellow; six subtle inlays circulate along its surface.')
    defs.extend([ET.fromstring(f'<linearGradient xmlns="{NS}" id="belt-pearl" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{PINK}"/><stop offset=".32" stop-color="{SKY}"/><stop offset=".67" stop-color="{GOLD}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'),
      ET.fromstring(f'<linearGradient xmlns="{NS}" id="belt-satin" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".30"/><stop offset=".44" stop-color="#fff" stop-opacity="0"/><stop offset=".83" stop-color="#626b83" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity=".36"/></linearGradient>'),
      ET.fromstring(f'<filter xmlns="{NS}" id="neutral-light" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/></filter>')])
    return ''.join(map(serialize,defs)),serialize(scene)

def hero(mobile=False):
    w,h=(640,820) if mobile else (1200,580)
    s=SVG(w,h,'Yeony — Small ideas. Useful possibilities.','A pale aurora Möbius belt with a continuous half-twist and travelling material. Observe, experiment, create. Reduced motion keeps the same complete still composition.')
    background(s,PINK)
    ds,art=mobius();s.defs.append(ds)
    s.css.append('.mobius-axes-still,.belt-texture-still{display:none}@media(prefers-reduced-motion:reduce){.mobius-axes-motion,.belt-texture-motion{display:none}.mobius-axes-still,.belt-texture-still{display:inline}}')
    x=36 if mobile else 52
    s.add(s.text('YEONY / DIGITAL WORKSHOP',x,48,13,MUTED,'mono',1.2))
    s.add(circle(w-x-4,43,3.5,PINK))
    s.add(s.text('Yeony.',x-8,172 if mobile else 220,142 if mobile else 180,INK,'bold',-6))
    for t,y in [('Small ideas.',231 if mobile else 299),('Useful possibilities.',279 if mobile else 355)]:
        s.add(s.text(t,x,y,39 if mobile else 47,'url(#pearl)','bold',-1))
    s.add(s.text('AUDIO / IMAGING / CODE',x,320 if mobile else 405,12 if mobile else 14,MUTED,'mono',1.2))
    s.add(f'<g transform="translate({320 if mobile else 925} {510 if mobile else 263}) scale({1.05 if mobile else 1.05})">{art}</g>')
    y=717 if mobile else 473
    s.add(path(f'M{x} {y}H{w-x}',LINE,1))
    cols=[('01 / OBSERVE','Find the friction.',PINK),('02 / EXPERIMENT','Follow the evidence.',SKY),('03 / CREATE','Make it useful.',GOLD)]
    for i,(a,b,c) in enumerate(cols):
        px=x+i*(w-2*x)/3
        s.add(s.text(a,px,y+32,10 if mobile else 12,c,'mono',.6))
        s.add(s.text(b,px,y+64,16 if mobile else 25,INK,'regular',-.25))
        if i:s.add(path(f'M{px-16} {y+22}V{y+66}',LINE,1))
    s.write('hero-mobile.svg' if mobile else 'hero.svg')

def arrow(x,y,color=SKY): return path(f'M{x-16} {y+16}L{x+16} {y-16}M{x-10} {y-16}H{x+16}V{y+10}',color,2.1,extra='stroke-linecap="round" stroke-linejoin="round"')

def project(name,number,tagline,category,artfn,accent,mobile=False):
    w,h=(600,510) if mobile else (1200,338)
    s=SVG(w,h,name+' — '+tagline,'Original conceptual project artwork, not a screenshot or a measured result. '+artfn.__doc__)
    background(s,accent)
    s.add(s.text(f'{number:02} / YEONY TOOLS',36 if mobile else 48,42 if mobile else 44,12,accent,'mono',1.1))
    if mobile and name=='Film Filter Studio':
        s.add(s.text('Film Filter Studio',34,103,48,INK,'bold',-1.8))
    else:s.add(s.text(name,34 if mobile else 45,104 if mobile else 130,58 if mobile else (62 if name!='Film Filter Studio' else 57),INK,'bold',-1.8))
    s.add(s.text(tagline,36 if mobile else 48,145 if mobile else 178,23 if mobile else 25,MUTED,'regular',-.2))
    s.add(path(f'M{36 if mobile else 48} {h-61}H{w-(36 if mobile else 48)}',LINE,1))
    s.add(s.text(category,36 if mobile else 48,h-27,11 if mobile else 12,accent,'mono',.5))
    s.add(arrow(w-55,h-34,accent))
    art=artfn(s)
    s.add(f'<g transform="translate({300 if mobile else 907} {302 if mobile else 144}) scale({.92 if mobile else 1.0})">{art}</g>')
    slug=name.lower().replace(' ','-')
    s.write(slug+('-mobile' if mobile else '')+'.svg')

def illustracy(s):
    """Four illustration planes compress into one image, then accelerate apart, overshoot, and settle. The separated state remains visible for reading."""
    shape='M0 -49L172 0L0 49L-172 0Z'
    s.defs.append(f'<linearGradient id="plane" x2="1" y2="1"><stop stop-color="#6c7a94" stop-opacity=".48"/><stop offset="1" stop-color="#343a50" stop-opacity=".62"/></linearGradient>')
    arts=[path('M-170 0L0 -48L170 0L0 48Z',SKY,1.4,'url(#plane)'),
      path('M-160 3L-46 -24L-8 6L43 -11L162 5L0 47Z','none',0,'#a7c0d5')+circle(66,-10,10,GOLD),
      path('M-160 3L-46 -24L-21 0L-5 2L0 47Z','none',0,'#7a839e')+path('M0 47L43 -11L65 8L162 5Z','none',0,'#6e778f'),
      path('M-124 14L-46 -24L-8 6L43 -11L137 22',PINK,1.5)+path('M56 -10H76M66 -20V0',GOLD,1.2)]
    parts=[]
    for i,(off,col,a) in enumerate(zip([66,22,-22,-66],[SKY,SKY,PINK,GOLD],arts)):
        body=path(shape,col,1.2,'#1f2537',extra='fill-opacity=".46"')+a
        cls=f'layer-{i}'
        s.css.append(f'.{cls}{{transform:translateY({off}px);animation:{cls} 7.2s infinite}}@keyframes {cls}{{0%,24%,100%{{transform:translateY({off}px) scale(1)}}38%{{transform:translateY(3px) scale(1.025,.9);animation-timing-function:cubic-bezier(.55,0,.85,.35)}}44%{{transform:translateY(9px) scale(1.065,.72);animation-timing-function:cubic-bezier(.18,.75,.22,1)}}58%{{transform:translateY({off*1.18-7}px) scale(.985,1.07);animation-timing-function:ease-in-out}}68%{{transform:translateY({off*.96}px) scale(1.006,.99)}}78%{{transform:translateY({off}px) scale(1)}}}}')
        parts.append(f'<g class="{cls}">{body}</g>')
    return '<g>'+path('M-190 65L0 120L190 65','#8995ac',.8,extra='opacity=".3"')+''.join(parts)+'</g>'

def landscape(negative=False):
    if negative: sky,m1,m2,sun='#8f6f83','#d0b6aa','#bfa6c0','#223044'
    else: sky,m1,m2,sun='#c6dce9','#6f879f','#3c526e',GOLD
    return rect(0,0,142,99,sky,7)+circle(106,27,12,sun)+path('M0 77L43 31L79 72L108 47L142 82V99H0Z','none',0,m1)+path('M0 86L50 69L94 83L142 70V99H0Z','none',0,m2)

def posity(s):
    """Negative and positive film frames retain the same scene. A scanning light anticipates, accelerates across, then decelerates into a quiet hold."""
    s.defs.append('<linearGradient id="scan-light"><stop stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".36"/></linearGradient>')
    frame=rect(-203,-88,406,181,'#101624',18,f'stroke="{LINE}" stroke-width="1.5"')
    for x in range(-180,185,30):
        for y in [-75,72]:frame+=rect(x,y,13,7,'#a9a4af',2)
    frame+='<g transform="translate(-164 -48)">'+landscape(True)+'</g>'
    frame+='<g transform="translate(23 -48)">'+landscape(False)+'</g>'
    frame+=s.text('NEGATIVE',-94,66,10,PINK,'mono',1,anchor='middle')+s.text('POSITIVE',94,66,10,SKY,'mono',1,anchor='middle')
    frame+=path('M-12 -3H10M4 -9L10 -3L4 3',GOLD,1.3)
    scanner=rect(-25,-52,25,107,'url(#scan-light)')+rect(0,-52,1.8,107,INK,1)+circle(.9,-57,2,INK)
    frame+=f'<g class="scan motion">{scanner}</g>'
    s.css.append('.film-gate{animation:gate 7.6s infinite}.scan{animation:scan 7.6s infinite}@keyframes gate{0%,20%,100%{transform:translateX(0)}26%{transform:translateX(-5px);animation-timing-function:cubic-bezier(.2,.8,.2,1)}39%{transform:translateX(3px)}49%,92%{transform:translateX(0)}}@keyframes scan{0%,18%{transform:translateX(-169px);opacity:0}23%{transform:translateX(-169px);opacity:1;animation-timing-function:cubic-bezier(.58,0,.82,.38)}30%{transform:translateX(-176px);opacity:1;animation-timing-function:cubic-bezier(.22,.7,.18,1)}61%{transform:translateX(170px);opacity:1}73%,100%{transform:translateX(170px);opacity:0}}')
    return f'<g class="film-gate">{frame}</g>'

def chordity(s):
    """Cmaj7, A7, Dm7, G7: one simultaneous four-note strike per 1.2-second, four-beat bar. Keys compress on contact and gently recover; no per-beat restrikes."""
    chords=[('Cmaj7',{'C4','E4','G4','B4'}),('A7',{'Cs4','E4','G4','A4'}),('Dm7',{'D4','F4','A4','C5'}),('G7',{'D4','F4','G4','B4'})]
    out=rect(-209,-42,418,145,'#111622',18,f'stroke="{LINE}" stroke-width="1.5"')
    for i,(name,notes) in enumerate(chords):
        x=-201+i*105
        out+=rect(x,-99,96,34,'#232938',9)
        body=rect(x,-99,96,34,'url(#pearl)',9)+s.text(name,x+48,-76,17,'#1b2230','bold',anchor='middle')
        out+=s.text(name,x+48,-76,17,MUTED,'regular',anchor='middle')
        out+=f'<g class="chord-label-{i}">{body}</g>'
        start=i*25;end=(i+1)*25
        stops={0:1 if i==0 else 0,start:1,end:0,100:1 if i==0 else 0}
        label_frames=''.join(str(t)+'%{opacity:'+str(v)+'}' for t,v in sorted(stops.items()))
        s.css.append(f'.chord-label-{i}{{opacity:{1 if i==0 else 0};animation:label-{i} 4.8s steps(1,end) infinite}}'+'@keyframes label-'+str(i)+'{'+label_frames+'}')
    whites=[n+str(o) for o in (4,5) for n in 'CDEFGAB']
    def key(note,x,black=False):
        base='#2a3346' if black else '#bfc9d8'
        home=note in chords[0][1];initial=(GOLD if black else INK) if home else base
        w,h=(15,62) if black else (25,108)
        body=rect(x,-25,w,h,initial,4,f'class="key-fill-{note}"')
        body+=path(f'M{x+4} {-18}H{x+w-4}','#fff',.8,extra='opacity=".35"')
        body+=rect(x+3,h-34,w-6,3,'#101827',1,'opacity=".2"')
        times={0:(6,.965,(GOLD if black else INK)) if home else (0,1,base),100:(6,.965,(GOLD if black else INK)) if home else (0,1,base)}
        for i,(_,notes) in enumerate(chords):
            active=note in notes;pr=(i-1)%4;was=note in chords[pr][1];st=i*25
            # All notes of a chord share exactly these boundary timestamps.
            times[st]=(0,1,base)
            times[st+.8]=(8,.94,(GOLD if black else INK)) if active else (-1.5,1.015,base) if was else (0,1,base)
            times[st+2.2]=(5,.97,(GOLD if black else INK)) if active else (0,1,base)
            times[st+23.6]=(5,.97,(GOLD if black else INK)) if active else (0,1,base)
            times[st+24.5]=(0,1,base)
        times[100]=times[0]
        frames=''.join(f'{t:g}%{{transform:translateY({v[0]}px) scaleY({v[1]});}}' for t,v in sorted(times.items()))
        fills=''.join(f'{t:g}%{{fill:{v[2]};}}' for t,v in sorted(times.items()))
        s.css.append(f'.key-{note}{{transform-origin:0 -25px;animation:key-{note} 4.8s linear infinite}}.key-fill-{note}{{animation:fill-{note} 4.8s linear infinite}}@keyframes key-{note}{{{frames}}}@keyframes fill-{note}{{{fills}}}')
        return f'<g class="key-{note}">{body}</g>'
    for i,n in enumerate(whites):out+=key(n,-195+i*28)
    for i,n in enumerate(whites):
        if n[0] in 'CDFGA':out+=key(n[0]+'s'+n[1],-195+i*28+20,True)
    # Four quiet beat indicators, independent from the held piano keys.
    for i in range(4):
        out+=circle(-18+12*i,121,2.3,SKY,f'class="beat-{i}" opacity=".25"')
        s.css.append(f'.beat-{i}{{animation:beat 1.2s {-i*.3}s steps(1,end) infinite}}')
    s.css.append('@keyframes beat{0%,24%{opacity:.9}25%,100%{opacity:.25}}')
    return out

def analog(s):
    """A coherent audio transient draws inward before expanding quickly; its waveform overshoots and settles, with a long quiet interval. Tone, dynamics and space remain readable."""
    out=rect(-216,-88,432,153,'#121826',18,f'stroke="{LINE}" stroke-width="1.4"')
    out+=path('M-195 -12H195','#626c80',1,extra='opacity=".35"')
    for x in (-144,-72,0,72,144):out+=path(f'M{x} -70V45','#3b4255',.7,extra='opacity=".3"')
    for i in range(57):
        x=-193+i*6.9
        env=math.exp(-((i-28)/22)**2)
        amp=7+51*env*(.25+.75*abs(math.sin(i*1.37)))
        col=PINK if i<18 else SKY if i<39 else GOLD
        out+=f'<g transform="translate({x:.2f} -12)"><path class="signal signal-{i%4}" d="M0 {-amp:.2f}V{amp:.2f}" stroke="{col}" stroke-width="2.8" stroke-linecap="round"/></g>'
    for i,(name,c) in enumerate([('TONE',PINK),('DYNAMICS',SKY),('SPACE',GOLD)]):
        x=-144+i*144
        out+=circle(x-34,101,12,'#2e3547',f'stroke="{LINE}"')
        out+=path(f'M{x-34} 101L{x-29} 94',c,2,extra='stroke-linecap="round"')
        out+=s.text(name,x-12,105,10,c,'mono',.3)
    s.css.append('.signal{animation:transient 6.4s infinite;transform-origin:0 0}.signal-1{animation-delay:-.025s}.signal-2{animation-delay:-.05s}.signal-3{animation-delay:-.075s}@keyframes transient{0%,15%,80%,100%{transform:scaleY(.86)}29%{transform:scaleY(.3);animation-timing-function:cubic-bezier(.63,0,.8,.25)}34%{transform:scaleY(.22);animation-timing-function:cubic-bezier(.14,.8,.2,1)}43%{transform:scaleY(1.16);animation-timing-function:ease-in-out}53%{transform:scaleY(.78)}64%{transform:scaleY(.9)}}')
    return out

def upscaly(s):
    """A sampled image becomes a larger, cleanly reconstructed contour. The larger frame compresses before accelerating outward and settling; the grid is an illustration, not a benchmark."""
    out=''
    pixels=['000000','000010','000000','001000','011101','111111']
    colors=['#c4d6e4','#7288a3']
    out+=rect(-215,-48,108,108,'#182033',9,f'stroke="{LINE}"')
    for y,row in enumerate(pixels):
        for x,v in enumerate(row):out+=rect(-209+x*16,y*16-42,15,15,colors[int(v)],1)
    out+=s.text('1x',-161,87,13,MUTED,'mono',anchor='middle')
    out+=path('M-91 -25L-42 -71M-91 43L-42 88','#7b849a',1,extra='stroke-dasharray="3 6" opacity=".55"')
    frame=rect(-70,-99,215,210,'#161d2d',15,f'stroke="{SKY}" stroke-opacity=".6" stroke-width="1.4"')
    frame+=rect(-61,-90,197,192,'#cbdfea',8)
    frame+=circle(86,-49,18,GOLD)
    frame+=path('M-61 53L4 -27L53 44L90 10L136 57V102H-61Z','none',0,'#829cb5')
    frame+=path('M-61 84Q-4 35 50 70T136 58V102H-61Z','none',0,'#506883')
    grid=''.join(path(f'M{x} -90V102','#eff8ff',.65,extra='opacity=".20"') for x in range(-61,137,16))
    grid+=''.join(path(f'M-61 {y}H136','#eff8ff',.65,extra='opacity=".20"') for y in range(-90,103,16))
    frame+=f'<g class="reconstruction-grid">{grid}</g>'
    frame+=s.text('4x',38,135,13,SKY,'mono',anchor='middle')
    out+=f'<g transform="translate(60 -9)"><g class="expansion">{frame}</g></g>'
    s.css.append('.expansion{transform-origin:35px 10px;animation:expand 7.8s infinite}.reconstruction-grid{animation:grid 7.8s infinite}@keyframes expand{0%,19%,80%,100%{transform:scale(1)}30%{transform:scale(.88,.94);animation-timing-function:cubic-bezier(.6,0,.82,.3)}35%{transform:scale(.85,.9);animation-timing-function:cubic-bezier(.15,.8,.2,1)}49%{transform:scale(1.065,1.035);animation-timing-function:ease-in-out}60%{transform:scale(.988,.994)}72%{transform:scale(1)}}@keyframes grid{0%,25%,100%{opacity:.75}48%,82%{opacity:0}}')
    return out

def film(s):
    """An optical iris gathers its blades, releases with a short recoil, and settles around a warm highlight. Concentric lens rings retain the original optical motif without constant spinning."""
    s.defs.append(f'<radialGradient id="lens"><stop stop-color="{GOLD}" stop-opacity=".8"/><stop offset=".16" stop-color="{PINK}" stop-opacity=".44"/><stop offset=".5" stop-color="#65728a" stop-opacity=".5"/><stop offset="1" stop-color="#151c2c"/></radialGradient>')
    out=''
    for i,col in enumerate([SKY,PINK,GOLD]):
        out+=f'<g transform="translate({-160+i*20} {-46+i*8}) rotate({-12+i*5})">'+rect(-32,-42,76,105,'#2a3246',9,f'stroke="{col}" stroke-opacity=".5"')+rect(-24,-31,60,71,col,3,'opacity=".24"')+'</g>'
    out+='<g transform="translate(57 0)">'
    for r,stroke,op in [(125,SKY,.28),(118,PINK,.5),(110,SKY,.26)]:out+=circle(0,0,r,'none',f'stroke="{stroke}" stroke-width="1" opacity="{op}"')
    out+=circle(0,0,104,'url(#lens)')
    for i in range(8):
        col=[PINK,SKY,GOLD,SKY][i%4]
        blade=path('M0 -102A102 102 0 0 1 72 -72L44 17L-12 -35Z',col,.8,col,extra='fill-opacity=".12" stroke-opacity=".58"')
        out+=f'<g transform="rotate({i*45})"><g class="iris-blade">{blade}</g></g>'
    out+=circle(0,0,36,'#111827',f'stroke="{PINK}" stroke-opacity=".45"')
    out+=circle(-11,-10,8,PINK,'opacity=".65"')+circle(10,12,3,GOLD,'opacity=".6"')
    for a in range(0,360,15):
        r=121;xx=math.cos(math.radians(a));yy=math.sin(math.radians(a));out+=path(f'M{xx*r:.2f} {yy*r:.2f}L{xx*(r+3):.2f} {yy*(r+3):.2f}',SKY,.8,extra='opacity=".5"')
    out+='</g>'
    s.css.append('.iris-blade{transform-origin:0 0;animation:iris 8.4s infinite}@keyframes iris{0%,20%,78%,100%{transform:rotate(0deg)}32%{transform:rotate(15deg);animation-timing-function:cubic-bezier(.65,0,.8,.3)}37%{transform:rotate(18deg);animation-timing-function:cubic-bezier(.16,.85,.2,1)}51%{transform:rotate(-5deg);animation-timing-function:ease-in-out}62%{transform:rotate(1.6deg)}74%{transform:rotate(0deg)}}')
    return out

def wrap(s,size,width,family='ko'):
    lines=[];line=''
    for word in s.split(' '):
        candidate=line+' '+word if line else word
        if text_width(candidate,size,family)>width and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines

def principles(mobile=False):
    w,h=(600,2112) if mobile else (1200,1044)
    s=SVG(w,h,'이용자 가치 지향 10계명 · 연이 개발 지향 10계명','The original twenty principles, word for word, in two quiet reading panels. Desktop places the panels side by side; mobile stacks them at a readable size. Full rationale remains in the README.')
    # Reuse the existing Korean outlines to preserve font-independent rendering.
    groups=[e for e in PRINCIPLES.iter() if e.get('data-principles-card')]
    for i,grp in enumerate(groups):
        x,y=(6,i*1062) if mobile else (i*612,0)
        accent=PINK if i==0 else SKY
        title='이용자 가치 지향' if i==0 else '연이 개발 지향'
        question='무엇을 위해 만드는가' if i==0 else '그 가치를 어떻게 지킬 것인가'
        footer='필요에서 시작해, 쓰임으로.' if i==0 else '근거로 구현하고, 오래 쓰이게.'
        s.defs.append(f'<linearGradient id="panel-{i}" x2="1" y2="1"><stop stop-color="{ "#24202e" if i==0 else "#1b2535"}"/><stop offset="1" stop-color="#121621"/></linearGradient>')
        card=rect(x+.7,y+.7,586.6,1042.6,f'url(#panel-{i})',24,f'stroke="{LINE}" stroke-width="1.4"')
        card+=s.text('01 / USER VALUE' if i==0 else '02 / DEVELOPMENT',x+34,y+40,11,accent,'mono',1)
        card+=s.text(title,x+32,y+94,31,INK,'ko')
        card+=s.text('10',x+548,y+105,78,accent,'regular',-4,anchor='end')
        card+=s.text(question,x+35,y+134,19,MUTED,'ko')
        card+=path(f'M{x+34} {y+160}H{x+554}',LINE,1.2)
        rows=[e for e in grp.iter() if e.get('data-principle')]
        assert len(rows)==10
        for j,row in enumerate(rows):
            txt=row.get('aria-label');ry=y+184+j*78
            lines=[e.get('aria-label') for e in row.iter() if e is not row and e.get('aria-label') and not re.fullmatch(r'\d+',e.get('aria-label'))]
            if not lines or max(text_width(line,23,'ko') for line in lines)>438:
                lines=wrap(txt,23,438)
            assert len(lines)<=2,(txt,lines)
            card+=f'<g data-principle="{j+1}" aria-label="{escape(txt,quote=True)}">'
            card+=s.text(f'{j+1:02}',x+35,ry+22,14,accent,'mono')
            for k,line in enumerate(lines):card+=s.text(line,x+86,ry+22+k*30,23,INK if k==len(lines)-1 else '#c4c8d5','ko')
            card+=path(f'M{x+86} {ry+63}H{x+552}',LINE,.7,extra='opacity=".65"')+'</g>'
        card+=s.text(footer,x+35,y+1006,19,accent,'ko')+circle(x+551,y+998,3,accent)
        s.add(card)
    s.write('principles-mobile.svg' if mobile else 'principles.svg')

def toolkit(mobile=False):
    w,h=(640,188) if mobile else (1200,124)
    s=SVG(w,h,'HTML · CSS · JavaScript — Browser first.','Browser-based tools, cross-platform, performance optimized, responsive by design.')
    background(s,SKY)
    s.add(s.text('BROWSER FIRST.',32 if mobile else 40,39 if mobile else 54,18,INK,'bold',.5))
    s.add(s.text('ONE WEB. MANY DEVICES.',32 if mobile else 40,64 if mobile else 80,10,MUTED,'mono',.6))
    for i,(label,c) in enumerate([('HTML',PINK),('CSS',SKY),('JavaScript',GOLD)]):
        x=32+i*195 if mobile else 556+i*202;y=93 if mobile else 34
        s.add(rect(x,y,180,58,'#202636',13,f'stroke="{LINE}"'))
        s.add(circle(x+22,y+29,3,c))
        s.add(s.text(label,x+41,y+37,21,c,'regular'))
    s.write('toolkit-mobile.svg' if mobile else 'toolkit.svg')

def footer(mobile=False):
    w,h=(640,208) if mobile else (1200,168)
    s=SVG(w,h,'A little curiosity. A useful thing. — Yeony','Curiosity made useful. Yeony.')
    s.defs.append(f'<linearGradient id="paper" x2="1" y2=".5"><stop stop-color="{PINK}"/><stop offset=".5" stop-color="{SKY}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>')
    s.add(rect(0,0,w,h,'url(#paper)',24))
    s.add(s.text('A little curiosity.',34 if mobile else 45,73 if mobile else 72,37,'#242a3a','bold',-1))
    s.add(s.text('A useful thing.',34 if mobile else 45,124 if mobile else 123,37,'#242a3a','regular',-.5))
    s.add(s.text('YEONY',w-37 if mobile else w-98,h-27 if mobile else 96,12 if mobile else 17,'#424858','mono',1.3,anchor='end'))
    s.add(arrow(w-50,60 if mobile else 84,'#424858'))
    s.write('footer-mobile.svg' if mobile else 'footer.svg')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    specs=[('Illustracy',1,'One image. New layers.','ILLUSTRATION / IMAGE TO PSD',illustracy,PINK),
      ('Posity',2,'Bring negatives to light.','FILM SCANS / COLOR / LIGHT',posity,GOLD),
      ('Chordity',3,'Find the harmony.','CHORDS / RHYTHM / PIANO',chordity,GOLD),
      ('Analog Soul',4,'Give sound a little soul.','AUDIO / TONE / DYNAMICS / SPACE',analog,SKY),
      ('Upscaly',5,'More room for every detail.','IMAGE / RECONSTRUCTION / SCALE',upscaly,SKY),
      ('Film Filter Studio',6,'A little analog nostalgia.','COLOR / GRAIN / HALATION',film,PINK)]
    for mobile in (False,True):
        hero(mobile)
        for spec in specs:project(*spec,mobile=mobile)
        principles(mobile);toolkit(mobile);footer(mobile)
    print('Built',len(list(OUT.glob('*.svg'))),'self-contained SVG assets.')

if __name__=='__main__':main()
