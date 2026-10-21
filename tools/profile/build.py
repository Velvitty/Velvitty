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

INK = '#fff9ff'
MUTED = '#c6c5df'
PINK = '#ffc8e4'
SKY = '#b9e8ff'
GOLD = '#ffe5a8'
LILAC = '#bfa9ff'
LINE = '#57496f'
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
        if color.startswith('url('):
            # Paint the complete word with one gradient, not a gradient per glyph.
            cid=f'text-clip-{len(self.defs)}'
            self.defs.append(f'<clipPath id="{cid}">'+''.join(paths)+'</clipPath>')
            content=rect(-size*.15,-size,cursor+size*.3,size*1.5,color,extra=f'clip-path="url(#{cid})"')
        else:content=''.join(paths)
        return f'<g aria-label="{escape(s,quote=True)}" fill="{color}" transform="translate({x:.3f} {y:.3f})">'+content+'</g>'
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
    s.defs += [f'<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#161731"/><stop offset=".5" stop-color="#252041"/><stop offset="1" stop-color="#101f35"/></linearGradient>',
      f'<radialGradient id="wash"><stop stop-color="{accent}" stop-opacity=".5"/><stop offset=".44" stop-color="#8564b1" stop-opacity=".28"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>',
      f'<radialGradient id="blue-haze"><stop stop-color="#77c9f4" stop-opacity=".34"/><stop offset="1" stop-color="#6488ef" stop-opacity="0"/></radialGradient>',
      f'<linearGradient id="pearl" x1="0" y1=".2" x2="1" y2=".8"><stop stop-color="{PINK}"/><stop offset=".48" stop-color="{SKY}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>',
      f'<linearGradient id="rim" x2="1" y2="1"><stop stop-color="{PINK}" stop-opacity=".65"/><stop offset=".4" stop-color="{LILAC}" stop-opacity=".15"/><stop offset="1" stop-color="{SKY}" stop-opacity=".55"/></linearGradient>',
      '<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="6"/></filter>',
      '<filter id="shadow" x="-30%" y="-40%" width="160%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>',
      f'<clipPath id="bounds">{rect(0,0,w,h,"white",26)}</clipPath>']
    art='<g clip-path="url(#bounds)">'+rect(0,0,w,h,'url(#bg)',26)
    art+=f'<ellipse cx="{w*.78}" cy="{h*.45}" rx="{w*.54}" ry="{h*.85}" fill="url(#wash)"/>'
    art+=f'<ellipse cx="{w*.26}" cy="{h*1.15}" rx="{w*.55}" ry="{h*.75}" fill="url(#blue-haze)"/>'
    # Broad, coloured light paths are part of the composition, not random particles.
    for i in range(4):
        art+=path(f'M{w*.36+i*26:.1f} {h+40}C{w*.69:.1f} {h*.23-i*24:.1f} {w*.71:.1f} {h*1.05:.1f} {w+90} {-h*.25+i*42:.1f}',accent,1.1,extra=f'opacity="{.045+i*.018}"')
    art+=rect(.75,.75,w-1.5,h-1.5,'none',25.5,'stroke="url(#rim)" stroke-width="1.5"')+'</g>'
    s.add(art)

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
            content=rect(0,0,1200,120,'url(#belt-pearl)' if not edge else 'url(#belt-edge)')
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
                e.set('filter','url(#pearl-light)');e.set('opacity','.27')
            if e.tag in (q('animate'),q('animateTransform')):
                if e.get('dur')=='16.8s':e.set('dur','5.6s')
                if e.get('dur')=='30s':e.set('dur','9s')
            if e.get('class')=='mobius-solid':
                e.set('aria-label','A continuous half-twist in pale white-pink, white-sky and white-yellow; six subtle inlays circulate along its surface.')
    defs.extend([ET.fromstring(f'<linearGradient xmlns="{NS}" id="belt-pearl" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#ffc1e2"/><stop offset=".16" stop-color="#fff0f7"/><stop offset=".34" stop-color="#a9dcff"/><stop offset=".49" stop-color="#eaf7ff"/><stop offset=".67" stop-color="#ffdfa0"/><stop offset=".83" stop-color="#fff5da"/><stop offset="1" stop-color="#ffc1e2"/></linearGradient>'),
      ET.fromstring(f'<linearGradient xmlns="{NS}" id="belt-edge"><stop stop-color="#df9bcf"/><stop offset=".45" stop-color="#97c8f8"/><stop offset="1" stop-color="#fff0be"/></linearGradient>'),
      ET.fromstring(f'<linearGradient xmlns="{NS}" id="belt-satin" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".30"/><stop offset=".44" stop-color="#fff" stop-opacity="0"/><stop offset=".83" stop-color="#626b83" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity=".36"/></linearGradient>'),
      ET.fromstring(f'<filter xmlns="{NS}" id="pearl-light" color-interpolation-filters="sRGB"><feColorMatrix values=".28 .50 .13 0 .07 .26 .47 .12 0 .05 .31 .55 .14 0 .12 0 0 0 1 0"/></filter>')])
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
    s.add(s.text('Yeony.',x-8,172 if mobile else 220,142 if mobile else 180,'url(#pearl)','bold',-6))
    for t,y in [('Small ideas.',231 if mobile else 299),('Useful possibilities.',279 if mobile else 355)]:
        s.add(s.text(t,x,y,39 if mobile else 47,INK if t=='Small ideas.' else SKY,'bold',-1))
    s.add(s.text('AUDIO / IMAGING / CODE',x,320 if mobile else 405,12 if mobile else 14,MUTED,'mono',1.2))
    cx,cy=(320,510) if mobile else (925,263)
    s.add(f'<g transform="translate({cx} {cy}) rotate(-22)"><ellipse rx="265" ry="142" fill="url(#wash)"/>'+path('M-270 12C-138 -169 168 -181 267 -19',PINK,2,extra='opacity=".35"')+path('M-258 40C-96 196 176 133 270 -8',SKY,1.5,extra='opacity=".35"')+'</g>')
    s.css.append('.hero-orbit{animation:hero-orbit 4.2s ease-in-out infinite}@keyframes hero-orbit{0%,100%{transform:translateY(8px) rotate(-4deg)}50%{transform:translateY(-12px) rotate(4deg)}}')
    s.add(f'<g transform="translate({cx} {cy}) scale(1.04)"><g class="hero-orbit">{art}</g></g>')
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
    w,h=(600,640) if mobile else (1200,416)
    s=SVG(w,h,name+' — '+tagline,'Original conceptual project artwork, not a screenshot or a measured result. '+artfn.__doc__)
    background(s,accent)
    s.add(rect(36 if mobile else 48,25,43,27,accent,13,'fill-opacity=".16"'))
    s.add(s.text(f'{number:02}',47 if mobile else 59,44,12,accent,'mono',1))
    s.add(s.text('YEONY TOOLS',96 if mobile else 110,44,11,MUTED,'mono',1.4))
    if mobile and name=='Film Filter Studio':
        s.add(s.text('Film Filter Studio',34,103,48,INK,'bold',-1.8))
    else:s.add(s.text(name,34 if mobile else 45,114 if mobile else 154,58 if mobile else (66 if name!='Film Filter Studio' else 57),INK,'bold',-1.8))
    s.add(s.text(tagline,36 if mobile else 48,158 if mobile else 201,23 if mobile else 25,MUTED,'regular',-.2))
    # Coloured material swatches connect the typography to each illustration.
    for i,col in enumerate((PINK,SKY,GOLD)):
        s.add(rect((36 if mobile else 48)+i*26,185 if mobile else 243,18,4,col,2))
    s.add(path(f'M{36 if mobile else 48} {h-61}H{w-(36 if mobile else 48)}',LINE,1))
    s.add(s.text(category,36 if mobile else 48,h-27,11 if mobile else 12,accent,'mono',.5))
    s.add(arrow(w-55,h-34,accent))
    art=artfn(s)
    s.add(f'<g transform="translate({300 if mobile else 906} {381 if mobile else 190}) scale({1.04 if mobile else 1.08})">{art}</g>')
    slug=name.lower().replace(' ','-')
    s.write(slug+('-mobile' if mobile else '')+'.svg')

def illustracy(s):
    """A 2.6-second spring: four coloured illustration planes squash to 36% height, release across a 200-pixel vertical span, overshoot, and settle."""
    shape='M0 -41L172 0L0 41L-172 0Z'
    s.defs.extend([
      f'<linearGradient id="plane" x2=".8" y2="1"><stop stop-color="#ffd9ee"/><stop offset=".5" stop-color="#93b8f5"/><stop offset="1" stop-color="#7f6dca"/></linearGradient>',
      f'<linearGradient id="ridge" x2="1" y2="1"><stop stop-color="#f5b8d7"/><stop offset=".55" stop-color="#a992dd"/><stop offset="1" stop-color="#5e75b7"/></linearGradient>',
      f'<linearGradient id="glass" x2="1" y2="1"><stop stop-color="#e0c7ff" stop-opacity=".65"/><stop offset="1" stop-color="#83c6e9" stop-opacity=".08"/></linearGradient>'])
    arts=[path(shape,SKY,1.4,'url(#plane)'),
      path('M-160 3L-46 -24L-8 6L43 -11L162 3L0 40Z','none',0,'url(#ridge)')+circle(66,-10,12,GOLD)+path('M-95 18Q0 -10 99 20',PINK,1.1,extra='opacity=".5"'),
      path('M-160 3L-46 -24L-21 0L-5 2L0 40Z','none',0,'#c69be3')+path('M0 40L43 -11L65 8L162 3Z','none',0,'#7bb2e5')+path('M-46 -24L-62 -7L-45 -9L-30 -3Z','none',0,PINK),
      path('M-124 14L-46 -24L-8 6L43 -11L137 22',PINK,2)+path('M54 -10H78M66 -22V2',GOLD,1.5)+circle(-46,-24,3,INK)+circle(43,-11,3,SKY)]
    parts=[]
    for i,(off,col,a) in enumerate(zip([78,26,-26,-78],[SKY,SKY,PINK,GOLD],arts)):
        body=path(shape,col,1.5,'url(#glass)')+a
        body+=path('M-172 0L0 41L172 0',col,3.2,extra='opacity=".7"')
        cls=f'layer-{i}'
        dx=(i-1.5)*14
        s.css.append(f'.{cls}{{transform:translate(0,{off}px);animation:{cls} 2.6s infinite}}@keyframes {cls}{{0%,7%,100%{{transform:translate(0,{off}px) scale(1);animation-timing-function:cubic-bezier(.45,0,.8,.4)}}23%{{transform:translate(0,{30-i*3}px) scale(1.13,.36);animation-timing-function:cubic-bezier(.18,.72,.25,1)}}40%{{transform:translate({dx}px,{off*1.24-6}px) scale(.95,1.1);animation-timing-function:ease-in-out}}54%{{transform:translate({-dx*.18}px,{off*.88+3}px) scale(1.035,.95)}}67%{{transform:translate(0,{off*1.035}px) scale(.99,1.025)}}79%{{transform:translate(0,{off}px) scale(1)}}}}')
        parts.append(f'<g class="{cls}">{body}</g>')
    return '<g><ellipse cx="0" cy="118" rx="180" ry="16" fill="#080b27" opacity=".6" filter="url(#shadow)"/>'+''.join(parts)+'</g>'

def landscape(negative=False):
    if negative: sky,m1,m2,sun='#a55d83','#ecd5b0','#b4addc','#38264c'
    else: sky,m1,m2,sun='url(#scene-sky)','#b4a2e5','#5d7cb2',GOLD
    a=rect(0,0,142,99,sky,7)+circle(106,27,14,sun)
    a+=path('M0 77L43 27L79 70L108 45L142 82V99H0Z','none',0,m1)
    a+=path('M30 43L43 27L58 45L44 39Z','none',0,'#f9e6f7' if not negative else '#9e86ac')
    a+=path('M0 86Q30 61 70 79T142 70V99H0Z','none',0,m2)
    a+=path('M0 92Q42 80 84 90T142 82',PINK if not negative else '#d6a8bd',1.4,extra='opacity=".7"')
    return a

def posity(s):
    """A 2.4-second film advance with a 70-pixel recoil and a full-width accelerating scan. The positive frame changes from negative colour to developed colour."""
    s.defs.extend(['<linearGradient id="scan-light"><stop stop-color="#ffdcae" stop-opacity="0"/><stop offset="1" stop-color="#fff4dd" stop-opacity=".7"/></linearGradient>',
      '<linearGradient id="scene-sky" x2=".4" y2="1"><stop stop-color="#80c4ee"/><stop offset="1" stop-color="#edc5e2"/></linearGradient>',
      '<linearGradient id="film-body" x2="1" y2="1"><stop stop-color="#544162"/><stop offset=".48" stop-color="#30223f"/><stop offset="1" stop-color="#7f4e62"/></linearGradient>'])
    frame=rect(-203,-88,406,181,'url(#film-body)',18,f'stroke="{PINK}" stroke-opacity=".6" stroke-width="1.5"')
    for x in range(-180,185,30):
        for y in [-75,72]:frame+=rect(x,y,13,7,GOLD,2,'opacity=".6"')
    frame+='<g transform="translate(-164 -48)">'+landscape(True)+'</g>'
    frame+='<g transform="translate(23 -48)">'+landscape(False)+'</g>'
    frame+='<g transform="translate(23 -48)"><g class="develop-negative">'+landscape(True)+'</g></g>'
    frame+=s.text('NEGATIVE',-94,66,10,PINK,'mono',1,anchor='middle')+s.text('POSITIVE',94,66,10,SKY,'mono',1,anchor='middle')
    frame+=path('M-12 -3H10M4 -9L10 -3L4 3',GOLD,1.3)
    scanner=rect(-55,-60,55,121,'url(#scan-light)')+rect(-3,-60,7,121,GOLD,3,'opacity=".5" filter="url(#glow)"')+rect(0,-60,2.8,121,INK,1)+circle(1.4,-65,3,GOLD)
    frame+=f'<g class="scan motion">{scanner}</g>'
    s.css.append('.film-gate{animation:gate 2.4s infinite}.scan{animation:scan 2.4s infinite}.develop-negative{opacity:0;animation:develop 2.4s infinite}@keyframes gate{0%,100%{transform:translateX(0) rotate(-3deg)}14%{transform:translateX(-30px) rotate(-5deg) scale(1.04,.87);animation-timing-function:cubic-bezier(.18,.8,.22,1)}29%{transform:translateX(40px) rotate(3deg) scale(.96,1.06)}42%{transform:translateX(-7px) rotate(-4deg)}56%,85%{transform:translateX(0) rotate(-3deg)}}@keyframes scan{0%,12%{transform:translateX(-178px);opacity:0}20%{transform:translateX(-178px);opacity:1;animation-timing-function:cubic-bezier(.55,.02,.8,.36)}53%{transform:translateX(178px);opacity:1}64%,100%{transform:translateX(178px);opacity:0}}@keyframes develop{0%,35%,100%{opacity:1}53%,88%{opacity:0}}')
    frame+=path('M-162 106H164',GOLD,1.5,extra='opacity=".35"')
    return f'<g class="film-gate">{frame}</g>'

def chordity(s):
    """Cmaj7, A7, Dm7, G7: simultaneous four-note strikes every 1.2 seconds. A 25-pixel key press, body compression, and a rising harmonic ribbon make each impact visible."""
    chords=[('Cmaj7',{'C4','E4','G4','B4'}),('A7',{'Cs4','E4','G4','A4'}),('Dm7',{'D4','F4','A4','C5'}),('G7',{'D4','F4','G4','B4'})]
    s.defs.extend(['<linearGradient id="piano-body" x2="1" y2="1"><stop stop-color="#73629e"/><stop offset=".4" stop-color="#39355e"/><stop offset="1" stop-color="#243b60"/></linearGradient>', '<clipPath id="harmonic-window">'+rect(-215,-78,430,74,'white')+'</clipPath>'])
    out=''
    for i,(name,notes) in enumerate(chords):
        x=-201+i*105
        out+=rect(x,-117,96,34,'#383451',9)
        body=rect(x,-117,96,34,'url(#pearl)',9)+s.text(name,x+48,-94,17,'#24243b','bold',anchor='middle')
        out+=s.text(name,x+48,-94,17,MUTED,'regular',anchor='middle')
        out+=f'<g class="chord-label-{i}">{body}</g>'
        start=i*25;end=(i+1)*25
        stops={0:1 if i==0 else 0,start:1,end:0,100:1 if i==0 else 0}
        label_frames=''.join(str(t)+'%{opacity:'+str(v)+'}' for t,v in sorted(stops.items()))
        s.css.append(f'.chord-label-{i}{{opacity:{1 if i==0 else 0};animation:label-{i} 4.8s steps(1,end) infinite}}'+'@keyframes label-'+str(i)+'{'+label_frames+'}')
    energy=''
    for i,col in enumerate((PINK,SKY,GOLD)):
        d=f'M-182 -18C-136 {-92+i*16} -85 {-12-i*10} -40 {-46+i*12}S60 {-76+i*16} 104 -34S160 -44 186 -16'
        energy+=path(d,col,8,extra='opacity=".23" filter="url(#glow)"')+path(d,col,2.6)
    out+='<g clip-path="url(#harmonic-window)"><g class="harmonic motion">'+energy+'</g></g>'
    out+='<g class="piano-impact">'+rect(-209,-42,418,145,'url(#piano-body)',18,f'stroke="{LILAC}" stroke-width="1.5"')
    whites=[n+str(o) for o in (4,5) for n in 'CDEFGAB']
    def key(note,x,black=False):
        base='#29213f' if black else '#d2cee9'
        home=note in chords[0][1];initial=(GOLD if black else SKY) if home else base
        w,h=(15,62) if black else (25,108)
        body=rect(x,-25,w,h,initial,4,f'class="key-fill-{note}"')
        body+=path(f'M{x+4} {-18}H{x+w-4}','#fff',.8,extra='opacity=".35"')
        body+=rect(x+3,h-34,w-6,3,'#101827',1,'opacity=".2"')
        times={}
        for i,(_,notes) in enumerate(chords):
            active=note in notes;pr=(i-1)%4;was=note in chords[pr][1];st=i*25
            # All notes of a chord share exactly these boundary timestamps.
            times[st]=(0,1,base)
            col=GOLD if black else [PINK,SKY,GOLD,LILAC][i]
            times[st+1.6]=(25,.74,col) if active else (-5,1.04,base) if was else (0,1,base)
            times[st+4.2]=(16,.82,col) if active else (0,1,base)
            times[st+23.6]=(16,.82,col) if active else (0,1,base)
            times[st+24.5]=(0,1,base)
        times[100]=times[0]
        frames=''.join(f'{t:g}%{{transform:translateY({v[0]}px) scaleY({v[1]});}}' for t,v in sorted(times.items()))
        fills=''.join(f'{t:g}%{{fill:{v[2]};}}' for t,v in sorted(times.items()))
        s.css.append(f'.key-{note}{{transform-origin:0 -25px;animation:key-{note} 4.8s linear infinite}}.key-fill-{note}{{animation:fill-{note} 4.8s linear infinite}}@keyframes key-{note}{{{frames}}}@keyframes fill-{note}{{{fills}}}')
        return f'<g class="key-{note}">{body}</g>'
    for i,n in enumerate(whites):out+=key(n,-195+i*28)
    for i,n in enumerate(whites):
        if n[0] in 'CDFGA':out+=key(n[0]+'s'+n[1],-195+i*28+20,True)
    out+='</g>'
    # A simultaneous impulse accompanies the chord boundary, not each beat.
    s.css.append('.piano-impact{transform-origin:0 105px;animation:piano-impact 1.2s infinite}.harmonic{animation:harmonic 1.2s infinite;transform-origin:0 -20px}@keyframes piano-impact{0%,100%{transform:scale(1)}9%{transform:scale(1.035,.84);animation-timing-function:cubic-bezier(.16,.8,.25,1)}24%{transform:scale(.99,1.055)}40%,85%{transform:scale(1)}}@keyframes harmonic{0%{transform:translateY(18px) scaleY(.12);opacity:0}10%{transform:translateY(14px) scaleY(.25);opacity:.5;animation-timing-function:cubic-bezier(.2,.8,.3,1)}36%{transform:translateY(-18px) scaleY(1.15);opacity:1}80%,100%{transform:translateY(-26px) scaleY(.8);opacity:0}}')
    for i in range(4):
        out+=circle(-24+16*i,125,3.7,SKY,f'class="beat-{i}" opacity=".25"')
        s.css.append(f'.beat-{i}{{animation:beat 1.2s {-i*.3}s steps(1,end) infinite}}')
    s.css.append('@keyframes beat{0%,24%{opacity:.9}25%,100%{opacity:.25}}')
    return out

def analog(s):
    """Every 1.8 seconds a coherent waveform compresses to 12% amplitude and springs to 158%; coloured traces, large meter needles, and a restrained afterglow follow the same impulse."""
    s.defs.append('<linearGradient id="audio-glass" x2="1" y2="1"><stop stop-color="#54436c"/><stop offset=".45" stop-color="#29304b"/><stop offset="1" stop-color="#214b64"/></linearGradient>')
    out=rect(-220,-115,440,227,'url(#audio-glass)',22,f'stroke="{SKY}" stroke-opacity=".5" stroke-width="1.4"')
    out+=path('M-197 -10H197',SKY,1,extra='opacity=".28"')
    for x in (-144,-72,0,72,144):out+=path(f'M{x} -96V91',SKY,.7,extra='opacity=".12"')
    signal=''
    for i in range(57):
        x=-193+i*6.9
        env=math.exp(-((i-28)/22)**2)
        amp=7+51*env*(.25+.75*abs(math.sin(i*1.37)))
        col=PINK if i<18 else SKY if i<39 else GOLD
        signal+=f'<path d="M{x:.2f} {-amp:.2f}V{amp:.2f}" stroke="{col}" stroke-width="3.2" stroke-linecap="round"/>'
    trace=''
    for j,col in enumerate((PINK,SKY,GOLD)):
        pts=[]
        for x in range(-195,196,3):
            env=math.exp(-(x/125)**2)
            yy=math.sin(x*.04+j*.65)*env*60
            pts.append(f'{x},{yy:.2f}')
        d='M'+'L'.join(pts)
        trace+=path(d,col,2.4,extra='opacity=".8"')
    out+='<g transform="translate(0 -10)"><g class="signal">'+path('M-194 0H194',SKY,16,extra='opacity=".12" filter="url(#glow)"')+signal+trace+'</g></g>'
    for i,(name,c) in enumerate([('TONE',PINK),('DYNAMICS',SKY),('SPACE',GOLD)]):
        x=-144+i*144
        out+=circle(x-34,133,13,'#3c3857',f'stroke="{c}" stroke-opacity=".6"')
        out+=f'<g transform="translate({x-34} 133)"><g class="audio-needle">'+path('M0 0L0 -9',c,2.4,extra='stroke-linecap="round"')+'</g></g>'
        out+=s.text(name,x-12,137,10,c,'mono',.3)
    s.css.append('.signal{animation:transient 1.8s infinite;transform-origin:0 0}.audio-needle{animation:needle 1.8s infinite}@keyframes transient{0%,100%{transform:scale(1,.88)}21%{transform:scale(.64,.12);animation-timing-function:cubic-bezier(.18,.8,.22,1)}38%{transform:scale(1.05,1.58)}51%{transform:scale(.97,.64)}66%{transform:scale(1,1.12)}81%{transform:scale(1,.88)}}@keyframes needle{0%,100%{transform:rotate(-38deg)}21%{transform:rotate(-62deg);animation-timing-function:cubic-bezier(.18,.8,.22,1)}38%{transform:rotate(64deg)}58%{transform:rotate(-16deg)}80%{transform:rotate(-38deg)}}')
    return out

def upscaly(s):
    """A 2.7-second reconstruction: the image contracts to 44% width before expanding to 112%, travelling 60 pixels as its pixel grid clears. This is conceptual, not a benchmark."""
    s.defs.extend(['<linearGradient id="up-sky" x2=".3" y2="1"><stop stop-color="#84c7f2"/><stop offset=".55" stop-color="#c3c3f0"/><stop offset="1" stop-color="#ffd5dd"/></linearGradient>',
      '<linearGradient id="up-ridge" x2="1" y2="1"><stop stop-color="#c9a2df"/><stop offset="1" stop-color="#537ab5"/></linearGradient>'])
    out=''
    pixels=['000000','000010','000000','001000','011101','111111']
    colors=['#b6d5f6','#9689cd']
    out+=rect(-215,-48,108,108,'#182033',9,f'stroke="{LINE}"')
    for y,row in enumerate(pixels):
        for x,v in enumerate(row):out+=rect(-209+x*16,y*16-42,15,15,colors[int(v)],1)
    out+=s.text('1x',-161,87,13,MUTED,'mono',anchor='middle')
    out+=path('M-91 -25L-42 -71M-91 43L-42 88','#7b849a',1,extra='stroke-dasharray="3 6" opacity=".55"')
    frame=rect(-70,-99,215,210,'#39466c',15,f'stroke="{SKY}" stroke-width="2"')
    frame+=rect(-61,-90,197,192,'url(#up-sky)',8)
    frame+=circle(86,-49,27,GOLD,'opacity=".2" filter="url(#glow)"')+circle(86,-49,19,GOLD)
    frame+=path('M-61 53L4 -27L53 44L90 10L136 57V102H-61Z','none',0,'url(#up-ridge)')
    frame+=path('M-11 -8L4 -27L24 2L6 -6Z','none',0,PINK)
    frame+=path('M-61 84Q-4 35 50 70T136 58V102H-61Z','none',0,'#50769e')
    frame+=path('M-61 94Q-12 53 51 83T136 73',SKY,2,extra='opacity=".6"')
    grid=''.join(path(f'M{x} -90V102','#eff8ff',.65,extra='opacity=".20"') for x in range(-61,137,16))
    grid+=''.join(path(f'M-61 {y}H136','#eff8ff',.65,extra='opacity=".20"') for y in range(-90,103,16))
    frame+=f'<g class="reconstruction-grid">{grid}</g>'
    frame+=s.text('4x',38,135,13,SKY,'mono',anchor='middle')
    out+=f'<g transform="translate(60 -9)"><g class="expansion">{frame}</g></g>'
    s.css.append('.expansion{transform-origin:35px 10px;animation:expand 2.7s infinite}.reconstruction-grid{animation:grid 2.7s infinite}@keyframes expand{0%,100%{transform:translateX(0) scale(1)}22%{transform:translateX(-52px) scale(.44,.58);animation-timing-function:cubic-bezier(.18,.7,.22,1)}41%{transform:translateX(8px) scale(1.12,1.1)}55%{transform:translateX(-3px) scale(.95,.97)}68%{transform:translateX(0) scale(1.025,1.015)}81%{transform:translateX(0) scale(1)}}@keyframes grid{0%,28%,100%{opacity:.85}45%,83%{opacity:0}}')
    return out

def film(s):
    """A 2.8-second optical impulse: eight iris blades travel 26 pixels and rotate 36 degrees, close around a small pupil, then spring open. Three filter frames fan out in response."""
    s.defs.extend([
      '<radialGradient id="lens" cx=".35" cy=".3" r=".8"><stop stop-color="#ffe9be"/><stop offset=".23" stop-color="#dcaddb"/><stop offset=".55" stop-color="#82bce6"/><stop offset="1" stop-color="#343254"/></radialGradient>',
      '<linearGradient id="blade" x2="1" y2="1"><stop stop-color="#eed5f1" stop-opacity=".65"/><stop offset=".48" stop-color="#9ca9dc" stop-opacity=".15"/><stop offset="1" stop-color="#4d4b7c" stop-opacity=".7"/></linearGradient>',
      '<radialGradient id="pupil" cx=".4" cy=".3"><stop stop-color="#4b497d"/><stop offset=".4" stop-color="#202346"/><stop offset="1" stop-color="#12162c"/></radialGradient>',
      '<clipPath id="lens-bound">'+circle(0,0,104,'white')+'</clipPath>'])
    out=''
    for i,col in enumerate([SKY,PINK,GOLD]):
        tilt=-22+i*14
        card=rect(-32,-42,76,105,'#413856',9,f'stroke="{col}" stroke-opacity=".8"')+rect(-24,-31,60,71,col,3)
        card+=circle(20,-14,9,GOLD if i!=2 else PINK)+path('M-24 26L-6 -1L13 24L36 8V40H-24Z','none',0,['#a095d1','#a77eab','#b595ad'][i])
        card+=path('M-22 50H17',col,2)
        out+=f'<g transform="translate({-162+i*18} {-28+i*10})"><g class="filter-{i}">{card}</g></g>'
        s.css.append(f'.filter-{i}{{transform:rotate({tilt}deg);animation:filter-{i} 2.8s infinite}}@keyframes filter-{i}{{0%,100%{{transform:translateX(0) rotate({tilt}deg)}}22%{{transform:translateX({12-i*8}px) rotate(-2deg) scale(.85,.93);animation-timing-function:cubic-bezier(.18,.8,.22,1)}}42%{{transform:translateX({(i-1)*14}px) rotate({tilt*1.7}deg) scale(1.04)}}58%{{transform:translateX(0) rotate({tilt*.85}deg)}}76%{{transform:translateX(0) rotate({tilt}deg)}}}}')
    out+='<g transform="translate(57 0)">'
    out+=circle(0,0,131,'#34334f',f'stroke="{PINK}" stroke-opacity=".6"')
    for r,stroke,op in [(125,SKY,.8),(118,PINK,.65),(110,SKY,.65)]:out+=circle(0,0,r,'none',f'stroke="{stroke}" stroke-width="1.4" opacity="{op}"')
    out+=circle(0,0,104,'url(#lens)')
    out+='<g clip-path="url(#lens-bound)">'
    for i in range(8):
        col=[PINK,SKY,GOLD,SKY][i%4]
        blade=path('M0 -105A105 105 0 0 1 75 -74L44 17L-12 -35Z',col,1.2,'url(#blade)',extra='stroke-opacity=".8"')
        out+=f'<g transform="rotate({i*45})"><g class="iris-blade">{blade}</g></g>'
    out+='</g><g class="iris-pupil">'+circle(0,0,38,'url(#pupil)',f'stroke="{PINK}" stroke-opacity=".65"')
    out+=circle(-11,-10,8,PINK,'opacity=".6"')+circle(10,12,3,GOLD,'opacity=".8"')+'</g>'
    out+='<g class="lens-flare motion">'+circle(0,0,37,GOLD,'opacity=".38" filter="url(#glow)"')+circle(0,0,9,INK,'opacity=".8"')+'</g>'
    for a in range(0,360,10):
        r=121;xx=math.cos(math.radians(a));yy=math.sin(math.radians(a));out+=path(f'M{xx*r:.2f} {yy*r:.2f}L{xx*(r+3):.2f} {yy*(r+3):.2f}',SKY,.8,extra='opacity=".5"')
    out+=path('M-94 -75A120 120 0 0 1 61 -103',GOLD,3,extra='stroke-linecap="round" opacity=".75"')
    out+=path('M102 64A120 120 0 0 1 -42 112',SKY,2.5,extra='stroke-linecap="round" opacity=".8"')
    out+='</g>'
    s.css.append('.iris-blade{transform-origin:0 0;animation:iris 2.8s infinite}.iris-pupil{animation:pupil 2.8s infinite}.lens-flare{opacity:0;animation:flare 2.8s infinite}@keyframes iris{0%,100%{transform:translateY(0) rotate(0deg)}24%{transform:translateY(26px) rotate(30deg);animation-timing-function:cubic-bezier(.16,.8,.22,1)}42%{transform:translateY(-8px) rotate(-6deg)}56%{transform:translateY(4px) rotate(4deg)}73%,90%{transform:translateY(0) rotate(0deg)}}@keyframes pupil{0%,100%{transform:scale(1)}24%{transform:scale(.24);animation-timing-function:cubic-bezier(.16,.8,.22,1)}42%{transform:scale(1.34)}56%{transform:scale(.87)}73%,90%{transform:scale(1)}}@keyframes flare{0%,21%,100%{opacity:0;transform:scale(.2)}29%{opacity:1;transform:scale(.8)}48%,90%{opacity:0;transform:scale(1.9)}}')
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
    s=SVG(w,h,'이용자 가치 지향 10계명 · 연이 개발 지향 10계명','The original twenty principles, word for word, in two colour-lit reading panels. Desktop places the panels side by side; mobile stacks them at a readable size. Full rationale remains in the README.')
    # Reuse the existing Korean outlines to preserve font-independent rendering.
    groups=[e for e in PRINCIPLES.iter() if e.get('data-principles-card')]
    for i,grp in enumerate(groups):
        x,y=(6,i*1062) if mobile else (i*612,0)
        accent=PINK if i==0 else SKY
        title='이용자 가치 지향' if i==0 else '연이 개발 지향'
        question='무엇을 위해 만드는가' if i==0 else '그 가치를 어떻게 지킬 것인가'
        footer='필요에서 시작해, 쓰임으로.' if i==0 else '근거로 구현하고, 오래 쓰이게.'
        s.defs.append(f'<linearGradient id="panel-{i}" x2=".7" y2="1"><stop stop-color="{ "#513b62" if i==0 else "#305471"}"/><stop offset=".2" stop-color="{ "#302640" if i==0 else "#26374f"}"/><stop offset="1" stop-color="#1b1c33"/></linearGradient>')
        s.defs.append(f'<linearGradient id="number-{i}" x2="1" y2="1"><stop stop-color="{accent}"/><stop offset="1" stop-color="{LILAC if i==0 else GOLD}"/></linearGradient>')
        card=rect(x+.7,y+.7,586.6,1042.6,f'url(#panel-{i})',24,f'stroke="{LINE}" stroke-width="1.4"')
        card+=path(f'M{x+34} {y+2}H{x+554}',accent,3.2,extra='opacity=".8"')
        card+=circle(x+504,y+76,59,'none',f'stroke="{accent}" stroke-opacity=".16"')
        card+=circle(x+504,y+76,68,'none',f'stroke="{accent}" stroke-opacity=".08"')
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
            card+=rect(x+22,ry-4,544,70,accent,12,f'fill-opacity="{.055 if j%2==0 else .015}"')
            card+=rect(x+34,ry+3,34,28,f'url(#number-{i})',8)
            card+=s.text(f'{j+1:02}',x+42,ry+22,14,'#2d2944','mono')
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
