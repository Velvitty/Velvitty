#!/usr/bin/env python3
"""Build the white aurora GitHub profile. Python 3 standard library only.

The profile is an SVG image adaptation of the client-side portfolio. GitHub
does not execute page JavaScript in a README; each artwork opens its live demo.
"""
from pathlib import Path
from copy import deepcopy
from html import escape
import base64, json, math, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tools/portfolio'
OUT = ROOT / 'assets/portfolio'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
def q(tag): return '{'+NS+'}'+tag
def xml(el): return ET.tostring(el, encoding='unicode')
def esc(text): return escape(str(text), quote=True)
LANGS = ('ko','en','ja','zh','fr','es')
BASE = {lang:json.loads((ROOT/f'tools/profile/locales/{lang}.json').read_text()) for lang in LANGS}
COPY = json.loads((SOURCE/'editorial-copy.json').read_text())
EXTRA = json.loads((SOURCE/'project-additions.json').read_text())
FONTS = json.loads((ROOT/'tools/profile/latin-glyphs.json').read_text())
FONTS.update(json.loads((ROOT/'tools/profile/cjk-glyphs.json').read_text()))
PHOTOS = {name:'data:image/jpeg;base64,'+base64.b64encode((SOURCE/f'assets/{name}-profile.jpg').read_bytes()).decode() for name in ('coast','botanical')}
PROJECTS = [
 ('Illustracy','illustracy','Illustracy','One image. New layers.',0),
 ('Posity','posity','Scanner','Bring negatives to light.',0),
 ('Chordity','chordity','Chordity','Find the harmony.',1),
 ('Analog Soul','analog-soul','efx','Give sound a little soul.',1),
 ('Upscaly','upscaly','Upscaly','More room for every detail.',0),
 ('Film Filter Studio','film-filter-studio','Film_Sim','A little analog nostalgia.',0),
 ('MacGuard','macguard','MacGuard','A watchful browser.',2),
 ('Photo Scorer','photo-scorer','Photo_Scorer','A fresh perspective on every photo.',0)]
LABELS = {
 'ko': ['사진 · 창작','음향','보안','직접 체험하기','카드를 눌러 체험 페이지로','GitHub에서는 미리보기. 체험 페이지에서는 직접 조작.','전체 체험 페이지 열기','원본 저장소','여덟 가지 가능성','만드는 이유'],
 'en': ['IMAGE · CREATE','AUDIO','SECURITY','Explore the experience','Tap the card to open the demo','Preview here. Interact on the full website.','Open the full experience','Source repository','Eight possibilities','Why I build'],
 'ja': ['写真・創作','音響','セキュリティ','体験を開く','カードを押して体験ページへ','ここではプレビュー。操作は体験ページで。','体験ページを開く','ソースコード','八つの可能性','つくる理由'],
 'zh': ['影像 · 创作','音频','安全','开启体验','点击卡片，打开体验页面','此处预览，完整网页支持交互操作。','打开完整体验','源码仓库','八种可能','创作的理由'],
 'fr': ['IMAGE · CRÉATION','AUDIO','SÉCURITÉ',"Passer à l’expérience",'Cliquez sur la carte pour essayer','Un aperçu ici. Une expérience sur le site.','Ouvrir l’expérience complète','Code source','Huit possibilités','Pourquoi créer'],
 'es': ['IMAGEN · CREACIÓN','AUDIO','SEGURIDAD','Abrir la experiencia','Pulsa la tarjeta para probar','Una vista previa aquí. Interacción en la web.','Abrir la experiencia completa','Código fuente','Ocho posibilidades','Por qué crear']}
LINK = 'https://yeon.at/portfolio/'
INK='#303343'; MUTED='#747784'; PINK='#eabed1'; SKY='#b9dce9'; GOLD='#ead9ae'
BOUNDS=[]

def rect(x,y,w,h,fill,rx=0,more=''):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {more}/>'
def path(d,stroke=INK,width=1.5,fill='none',more=''):
 return f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}" {more}/>'
def circle(x,y,r,fill,more=''):
 return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {more}/>'
def image(name,x,y,w,h,more=''):
 return f'<image href="{PHOTOS[name]}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" {more}/>'

class SVG:
 def __init__(self,lang,w,h,title):
  self.lang,self.w,self.h,self.title=lang,w,h,title
  self.defs=[];self.body=[];self.css=[];self.glyphs={}
 def add(self,s):self.body.append(s)
 def text(self,text,x,y,size=24,color=INK,bold=False,width=None,anchor='start'):
  family=('cjk-'+self.lang+('-bold' if bold else '')) if self.lang in ('ko','ja','zh') else ('bold' if bold else 'regular')
  f=FONTS[family];chars=f['chars'];units=f['units']
  advances=[chars[c]['advance']/units if c in chars else (1 if ord(c)>0x2ff else .64) for c in text]
  measure=sum(advances)*size
  if width and measure>width:size*=width/measure;measure=width
  if anchor=='middle':x-=measure/2
  elif anchor=='end':x-=measure
  BOUNDS.append((self.lang,self.title,text,x,y,measure,self.w,self.h))
  parts=[];cursor=0
  for c,advance in zip(text,advances):
   if c in chars:
    gid=f't-{family}-{ord(c):x}';self.glyphs[gid]=chars[c]['d']
    parts.append(f'<use href="#{gid}" transform="translate({cursor:.3f} 0) scale({size/units:.7f} {-size/units:.7f})"/>')
   else:
    parts.append(f'<text x="{cursor:.3f}" font-size="{size:.3f}" font-weight="{700 if bold else 400}" font-family="Arial, Noto Sans CJK KR, Noto Sans CJK JP, Noto Sans CJK SC, Apple SD Gothic Neo, Malgun Gothic, sans-serif">{esc(c)}</text>')
   cursor+=advance*size
  return f'<g aria-label="{esc(text)}" fill="{color}" transform="translate({x:.2f} {y:.2f})">'+''.join(parts)+'</g>'
 def write(self,name):
  defs=''.join(self.defs)+''.join(f'<path id="{key}" d="{d}"/>' for key,d in self.glyphs.items())
  css=''.join(self.css)+'@media(prefers-reduced-motion:reduce){*{animation:none!important}.flow{display:none}.still{display:inline}}'
  data=f'<svg xmlns="{NS}" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc" lang="{self.lang}"><title id="title">{esc(self.title)}</title><desc id="desc">{esc(LABELS[self.lang][5])}</desc><defs>{defs}</defs><style>.still{{display:none}}{css}</style>'+''.join(self.body)+'</svg>\n'
  ET.fromstring(data)
  p=OUT/self.lang/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)

def backdrop(s):
 s.defs += ['<linearGradient id="paper" x2="1" y2="1"><stop stop-color="#fffafd"/><stop offset=".52" stop-color="#f4f9fd"/><stop offset="1" stop-color="#fffbf1"/></linearGradient>',
  '<radialGradient id="pink"><stop stop-color="#f3dbe8" stop-opacity=".88"/><stop offset="1" stop-color="#f3dbe8" stop-opacity="0"/></radialGradient>',
  '<radialGradient id="sky"><stop stop-color="#d4eaf8" stop-opacity=".92"/><stop offset="1" stop-color="#d4eaf8" stop-opacity="0"/></radialGradient>',
  '<linearGradient id="pearl" x2="1" y2="1"><stop stop-color="#f6d0e4"/><stop offset=".5" stop-color="#c9e6f6"/><stop offset="1" stop-color="#f7e6bd"/></linearGradient>',
  '<linearGradient id="ink" x2="1" y2=".2"><stop stop-color="#aa708e"/><stop offset=".52" stop-color="#668aab"/><stop offset="1" stop-color="#ad9660"/></linearGradient>',
  '<radialGradient id="orb" cx=".28" cy=".24" r=".8"><stop stop-color="#fffef8"/><stop offset=".24" stop-color="#f0d4c9"/><stop offset=".6" stop-color="#baa5af"/><stop offset="1" stop-color="#778caa"/></radialGradient>',
  '<filter id="shadow" x="-40%" y="-40%" width="180%" height="190%"><feDropShadow dx="0" dy="18" stdDeviation="16" flood-color="#566077" flood-opacity=".18"/></filter>',
  f'<clipPath id="page">{rect(1,1,s.w-2,s.h-2,"white",32)}</clipPath>',
  '<filter id="negative" color-interpolation-filters="sRGB"><feComponentTransfer><feFuncR type="table" tableValues=".94 .2"/><feFuncG type="table" tableValues=".7 .19"/><feFuncB type="table" tableValues=".52 .28"/></feComponentTransfer></filter>',
  '<filter id="blur"><feGaussianBlur stdDeviation="2.4"/></filter>']
 s.add(rect(1,1,s.w-2,s.h-2,'url(#paper)',32,'stroke="#e4e3e8"'))
 s.add(f'<g clip-path="url(#page)"><ellipse cx="{s.w*.75}" cy="{s.h*.17}" rx="{s.w*.52}" ry="{s.h*.65}" fill="url(#pink)"/><ellipse cx="{s.w*.16}" cy="{s.h*.86}" rx="{s.w*.45}" ry="{s.h*.56}" fill="url(#sky)"/></g>')
 s.css += ['@keyframes levitate{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}.float{animation:levitate 5.6s ease-in-out infinite}',
 '@keyframes pulse{0%,100%{opacity:.18}50%{opacity:.7}}.pulse{animation:pulse 4s ease-in-out infinite}',
 '@keyframes orbitdash{to{stroke-dashoffset:-180}}.trace{stroke-dasharray:8 14;animation:orbitdash 8s linear infinite}']

def photo_print(s,name,x,y,w,h,rotation=0):
 cid=f'photo-{len(s.defs)}';s.defs.append(f'<clipPath id="{cid}">{rect(x,y,w,h,"white",5)}</clipPath>')
 return f'<g transform="rotate({rotation} {x+w/2} {y+h/2})">'+rect(x-10,y-10,w+20,h+32,'#fff',8,'filter="url(#shadow)"')+image(name,x,y,w,h,f'clip-path="url(#{cid})"')+'</g>'

def mobius(s):
 r=ET.parse(SOURCE/'mobius-reference.svg').getroot()
 # Replace referenced animated groups with animated paint servers. Each face
 # keeps its exact clip and UV affine transform; no outer transform rotates.
 defs=r.find(q('defs'))
 for kind in ('surface','edge'):
  motif=next(e for e in defs if e.get('id')==f'mb-{kind}-motif')
  p=ET.Element(q('pattern'),{'id':f'profile-{kind}','patternUnits':'userSpaceOnUse','width':'1200','height':'120'})
  for child in list(motif):p.append(deepcopy(child))
  p.append(ET.Element(q('animateTransform'),{'attributeName':'patternTransform','type':'translate','values':'0 0;1200 0','dur':'5.6s','repeatCount':'indefinite'}))
  defs.append(p)
 for e in r.iter():
  if e.get('data-material-face'):
   uv=list(e)[0];use=list(uv)[0];kind='edge' if 'edge' in use.get('href','') else 'surface';uv.remove(use)
   ET.SubElement(uv,q('rect'),{'x':'-2400','y':'0','width':'6000','height':'120','fill':f'url(#profile-{kind})'})
 # Reduced motion changes only the face paint server, retaining one fixed mesh.
 for e in r.iter():
  if e.get('fill') in ('url(#profile-surface)','url(#profile-edge)'):
   kind='edge' if 'edge' in e.get('fill') else 'surface'
   e.set('class','belt-'+kind)
 for kind in ('surface','edge'):
  p=deepcopy(next(e for e in defs if e.get('id')==f'profile-{kind}'));p.set('id',f'profile-{kind}-still')
  for child in list(p):
   if child.tag==q('animateTransform'):p.remove(child)
  defs.append(p)
 s.defs.extend(xml(e) for e in defs)
 s.css.append('@media(prefers-reduced-motion:reduce){.belt-surface{fill:url(#profile-surface-still)}.belt-edge{fill:url(#profile-edge-still)}}')
 return xml(r.find(q('g')))

def hero(lang,mobile=False):
 c=COPY[lang];base=BASE[lang];w,h=(640,820) if mobile else (1200,580)
 s=SVG(lang,w,h,base['display_name']+' · '+c['art']['Small ideas.']+' '+c['art']['Useful possibilities.']);backdrop(s)
 s.add(s.text(base['display_name'],44,66,30,bold=True,width=250));s.add(s.text('VELVITTY',w-44,63,16,MUTED,True,width=180,anchor='end'))
 x=44;y=155 if mobile else 210;size=68 if mobile else 72
 s.add(s.text(c['art']['Small ideas.'],x,y,size,bold=True,width=545 if mobile else 530))
 s.add(s.text(c['art']['Useful possibilities.'],x,y+size*1.17,size,'url(#ink)',True,width=545 if mobile else 530))
 s.add(s.text(c['source']['promise'],44,y+size*1.17+55,30 if mobile else 24,MUTED,width=545 if mobile else 510))
 mx,my,scale=(320,515,1.12) if mobile else (875,287,1.12)
 s.add(f'<g transform="translate({mx} {my}) scale({scale})">'+mobius(s)+'</g>')
 s.add('<g class="float">'+photo_print(s,'coast',44 if mobile else 687,365 if mobile else 100,128,88,-10)+'</g>')
 s.add('<g class="float" style="animation-delay:-2.8s">'+photo_print(s,'botanical',463 if mobile else 1001,639 if mobile else 395,128,88,9)+'</g>')
 by=h-43
 s.add(s.text('08',44,by,27,bold=True));s.add(s.text(c['ui']['statProjects'],93,by,17,MUTED,width=125))
 s.add(s.text('06',238,by,27,bold=True));s.add(s.text(c['ui']['statLanguages'],287,by,17,MUTED,width=130))
 s.add(s.text('01',448,by,27,bold=True));s.add(s.text(c['ui']['statBrowser'],497,by,17,MUTED,width=110))
 if not mobile:s.add(s.text(LABELS[lang][3]+' ↗',w-44,by,22,bold=True,width=420,anchor='end'))
 s.write('hero-mobile.svg' if mobile else 'hero.svg')

def art(s,index):
 # All artwork uses a 500 x 370 coordinate system.
 if index==0:
  s.css.append('@keyframes layers{0%,18%,100%{transform:translateY(0)}48%,74%{transform:translateY(var(--spread))}}.layer{animation:layers 5.2s cubic-bezier(.3,.05,.2,1) infinite}')
  out=''
  for j in range(4):
   out+=f'<g class="layer" style="--spread:{(j-1.5)*43}px">'+f'<g transform="translate(45 {105+j*13}) matrix(1 .12 -.3 .65 0 0)">'+rect(0,0,382,225,'#ffffffa6',18,'stroke="#ffffff" stroke-width="2" filter="url(#shadow)"')
   if j==0:out+=rect(6,6,370,213,'url(#pearl)',14)+circle(290,70,31,'#fff4d5')
   elif j==1:out+=path('M7 201L90 60 198 180 280 98 376 200V219H7Z','none',0,'#a1adc3')+path('M6 214L135 131 240 205 376 151V219H6Z','none',0,'#86a7ab')
   elif j==2:out+=path('M35 213L57 95 78 213M305 213L322 135 342 213','#708e8c',2,'#86a7ab55')
   else:out+=path('M130 181H210M144 195H246','#fff',2)+circle(290,70,42,'none','stroke="#fff9dc" stroke-width="1.4"')
   out+='</g></g>'
  return out
 if index in (1,4):
  photo='coast' if index==1 else 'botanical'
  s.defs.append('<clipPath id="scan"><rect x="30" y="30" width="220" height="300"><animate attributeName="width" values="85;390;85" dur="6.4s" repeatCount="indefinite"/></rect></clipPath>')
  s.css.append('@keyframes divider{0%,100%{transform:translateX(-135px)}50%{transform:translateX(170px)}}.divider{animation:divider 6.4s linear infinite}')
  s.defs.append('<clipPath id="photo-frame">'+rect(30,30,440,300,'white',16)+'</clipPath>')
  out=rect(18,18,464,324,'#fff',22,'filter="url(#shadow)"')+'<g clip-path="url(#photo-frame)">'+image(photo,30,30,440,300,'filter="url(#negative)"' if index==1 else 'filter="url(#blur)"')+'<g clip-path="url(#scan)">'+image(photo,30,30,440,300)+'</g></g><g class="divider">'
  out+=rect(246.5,30,2,300,'#ffffff')+rect(248.5,30,3,300,'#5d646e')+rect(251.5,30,2,300,'#ffffff')
  for j in range(4):
   y=30+300*(.125+.25*j);x=260.5 if j%2==0 else 239.5
   out+=s.text('>>' if j%2==0 else '<<',x,y+5,15,'#fff',True,anchor='start' if j%2==0 else 'end')
  return out+'</g>'
 if index==2:
  s.css.append('@keyframes key{0%,18%,100%{transform:translateY(0);fill:#fff}28%,52%{transform:translateY(11px);fill:#d8d8ee}}.key{animation:key 4.8s ease-in-out infinite;animation-delay:var(--delay)}')
  out=''
  for j in range(3):out+=path(f'M0 {150+j*24}C95 {20+j*24} 130 310 245 165S410 15 510 135',('#c9b7d7','#a2c7dc','#dacba4')[j],2,more='class="trace"')
  for j,label in enumerate(['Cmaj7','Am7','Fmaj7','G7']):
   x=62+j*122;y=98+(j%2)*37
   out+=circle(x,y,45,'#ffffffd6','filter="url(#shadow)"')+s.text(label,x,y+7,20,bold=True,anchor='middle')
  out+=rect(12,245,476,96,'#e8e7ef',15,'filter="url(#shadow)"')
  for j in range(14):
   out+=f'<g class="key" style="--delay:{-(j%4)*1.2}s">'+rect(20+j*33,250,30,83,'#fff',5)+'</g>'
   if j%7 in (0,1,3,4,5):out+=rect(42+j*33,250,18,47,'#515468',3)
  return out
 if index==3:
  s.css.append('@keyframes resonance{0%,100%{transform:scale(.92);opacity:.3}50%{transform:scale(1.14);opacity:.65}}.resonance{transform-origin:250px 150px;animation:resonance 4s ease-in-out infinite}@keyframes wave{0%,100%{transform:scaleY(.48)}50%{transform:scaleY(1)}}.wave{transform-origin:0 303px;animation:wave 1.8s ease-in-out infinite;animation-delay:var(--delay)}')
  out=''.join(f'<ellipse class="resonance" cx="250" cy="150" rx="{92+j*39}" ry="{44+j*20}" fill="none" stroke="{[PINK,SKY,GOLD][j]}" stroke-width="2" style="animation-delay:{-j*.7}s" transform="rotate(-18 250 150)"/>' for j in range(3))
  out+=circle(250,150,96,'url(#orb)','filter="url(#shadow)"')
  for j in range(49):
   height=18+abs(math.sin(j*.55))*54
   out+=f'<g class="wave" style="--delay:{-j*.09}s">'+rect(7+j*10,303-height/2,4,height,'#b599a0',2)+'</g>'
  return out
 if index==5:
  s.css.append('@keyframes fan{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(3deg)}}.print{transform-origin:250px 180px;animation:fan 6s ease-in-out infinite}')
  return photo_print(s,'coast',66,69,365,239,8)+'<g class="print">'+photo_print(s,'coast',53,48,365,239,-4)+'</g>'
 if index==6:
  out=path('M0 56H80L120 96H375L420 50H500M0 300H76L114 264H373L410 305H500',SKY,2,more='class="trace"')+rect(70,57,360,260,'#ffffffbf',24,'stroke="#fff" stroke-width="2" filter="url(#shadow)"')
  for j in range(3):out+=circle(94+j*15,80,3.5,['#e9b7c5','#e7d4a1','#b1ccc9'][j])
  out+=path('M250 107L302 128V168C302 206 278 234 250 248C222 234 198 206 198 168V128Z','#87a6b0',2,'url(#pearl)')
  out+=path('M226 171L244 188 279 151','#718c9c',5,more='stroke-linecap="round" stroke-linejoin="round" class="pulse"')
  for j in range(6):out+=circle(202+j*19,280,3.8,'#a8aab5')
  return out
 out=photo_print(s,'botanical',45,29,410,280,-3)
 for x in (182,318):out+=path(f'M{x} 29V309','#fff',1.2,more='opacity=".8"')
 for y in (122,216):out+=path(f'M45 {y}H455','#fff',1.2,more='opacity=".8"')
 out+=rect(202,100,97,97,'none',16,'stroke="#fff" stroke-width="2" class="pulse"')
 for j in range(7):out+=rect(90+j*48,343-(j*13%31),30,12+j*13%31,[PINK,SKY,GOLD][j%3],5)
 return out

def project(lang,index,mobile=False):
 canonical,slug,repo,banner,category=PROJECTS[index];c=COPY[lang];b=BASE[lang];names=b['project_names']+EXTRA['locales'][lang]['project_names']
 w,h=(640,900) if mobile else (1200,500);s=SVG(lang,w,h,names[index]+': '+c['art'][banner]);backdrop(s)
 ax,ay,scale=(47,20,1.09) if mobile else (655,56,1.02)
 s.add(f'<g transform="translate({ax} {ay}) scale({scale})">'+art(s,index)+'</g>')
 x=42 if mobile else 48;y=465 if mobile else 83;tw=552 if mobile else 570
 s.add(s.text(f'{index+1:02} / '+LABELS[lang][category],x,y,18,MUTED,True,width=tw))
 s.add(s.text(names[index],x,y+65,49,bold=True,width=tw))
 s.add(s.text(c['art'][banner],x,y+122,30,'#79748e',True,width=tw))
 desc=c['source']['project_descriptions'][index]
 # Wrap by language-aware visual width instead of reducing paragraph type.
 chunks=[];current='';body_size=30 if mobile else 21
 family='cjk-'+lang if lang in ('ko','ja','zh') else 'regular';font=FONTS[family]
 def measure(text):return sum(font['chars'][ch]['advance']/font['units'] if ch in font['chars'] else (1 if ord(ch)>0x2ff else .64) for ch in text)*body_size
 for token in (list(desc) if lang in ('ko','ja','zh') else desc.split(' ')):
  nextline=current+(' ' if current and lang not in ('ko','ja','zh') else '')+token
  if measure(nextline)>tw:chunks.append(current);current=token
  else:current=nextline
 if current:chunks.append(current)
 for j,line in enumerate(chunks):s.add(s.text(line,x,y+170+j*(38 if mobile else 29),body_size,MUTED,width=tw))
 s.add(path(f'M{x} {h-82}H{w-42}', '#dcdfe7',1))
 s.add(s.text(LABELS[lang][4],x,h-39,20,bold=True,width=w-150));s.add(s.text('↗',w-54,h-38,29,anchor='middle'))
 s.write(slug+('-mobile' if mobile else '')+'.svg')

def gallery(lang,mobile=False):
 w,h=(640,1210) if mobile else (1200,390);s=SVG(lang,w,h,COPY[lang]['ui']['galleryTitle']);backdrop(s)
 for i,name in enumerate(['coast','botanical',None]):
  x,y,ww,hh=(32,28+i*391,576,357) if mobile else (25+i*394,24,362,342)
  cid=f'tile-{i}';s.defs.append(f'<clipPath id="{cid}">{rect(x,y,ww,hh,"white",21)}</clipPath>')
  if name:s.add(image(name,x,y,ww,hh,f'clip-path="url(#{cid})"'))
  else:
   s.add(rect(x,y,ww,hh,'url(#pearl)',21));s.add(circle(x+ww*.5,y+hh*.42,82,'url(#orb)','filter="url(#shadow)" class="float"'))
  s.add(rect(x+17,y+hh-68,ww-34,50,'#ffffffde',14))
  s.add(s.text(COPY[lang]['ui'][f'gallery{i}'],x+35,y+hh-35,24,bold=True,width=ww-73))
 s.write('gallery-mobile.svg' if mobile else 'gallery.svg')

def language_buttons(lang):
 for active in (False,True):
  for mobile in (False,True):
   w,h=(112,72) if mobile else (192,60);s=SVG(lang,w,h,BASE[lang]['name'])
   s.defs.append('<linearGradient id="button" x2="1" y2="1"><stop stop-color="#f5dbe8"/><stop offset=".5" stop-color="#e3f0f9"/><stop offset="1" stop-color="#fcf0d3"/></linearGradient>')
   s.add(rect(2,2,w-4,h-4,'url(#button)' if active else '#f8f9fc',16,'stroke="#dddfe8"'))
   s.add(s.text(BASE[lang]['name'],w/2,h/2+8,24 if mobile else 22,bold=active,width=w-14,anchor='middle'))
   s.write('language'+('-active' if active else '')+('-mobile' if mobile else '')+'.svg')

def picture(lang,slug,alt,href=None):
 base=f'assets/portfolio/{lang}/';body=f'<picture><source media="(max-width: 640px)" srcset="{base}{slug}-mobile.svg?v=1" /><img src="{base}{slug}.svg?v=1" width="100%" alt="{esc(alt)}" /></picture>'
 if href:body=f'<a href="{href}">{body}</a>'
 return '<p align="center">'+body+'</p>'

def readme(lang):
 b=BASE[lang];c=COPY[lang];labels=LABELS[lang];names=b['project_names']+EXTRA['locales'][lang]['project_names'];buttons=[]
 for dest in LANGS:
  href='https://github.com/Velvitty' if dest=='ko' else f'https://github.com/Velvitty/Velvitty/blob/main/README.{dest}.md'
  slug='language'+('-active' if dest==lang else '');base=f'assets/portfolio/{dest}/{slug}'
  buttons.append(f'<a href="{href}"><picture><source media="(max-width: 640px)" srcset="{base}-mobile.svg?v=1" /><img src="{base}.svg?v=1" width="16%" alt="{esc(BASE[dest]["name"])}" /></picture></a>')
 full=LINK+'?lang='+lang
 out=['<!-- Generated by python tools/profile/portfolio.py. Source: tools/portfolio/. -->','<p align="center">'+''.join(buttons)+'</p>',picture(lang,'hero',b['display_name']+' — '+c['art']['Small ideas.']+' '+c['art']['Useful possibilities.'],full),'<p align="center"><strong>'+c['source']['intro']+'</strong></p>',f'<p align="center"><a href="{full}"><strong>{labels[6]} ↗</strong></a></p>','<p align="center">'+labels[5]+'</p>',picture(lang,'gallery',c['ui']['galleryTitle'],full+'#projects'),'<a id="projects"></a>','## '+c['source']['projects_title'],c['source']['projects_intro']]
 for i,(_,slug,repo,banner,category) in enumerate(PROJECTS):out.append(picture(lang,slug,names[i]+' — '+c['art'][banner]+' '+c['source']['project_descriptions'][i],full+'#'+slug))
 out+=['<details>\n<summary><strong>'+b['project_details']+'</strong></summary>','| '+labels[7]+' | '+b['table_headers'][1]+' |\n| --- | --- |\n'+'\n'.join(f'| [{names[i]}](https://github.com/Velvitty/{p[2]}) | {c["source"]["project_descriptions"][i]} |' for i,p in enumerate(PROJECTS)),b['limitations'],'</details>','## '+c['source']['approach_title'],'**'+c['source']['principles_lead']+'**','<details>\n<summary><strong>'+b['principles_title']+'</strong></summary>',b['principles_intro']]
 for i,g in enumerate(b['principles_groups']):
  out += ['### '+g['title'],g['intro']]
  for j,p in enumerate(b['principles'][i*10:(i+1)*10]):out += [f'#### {j+1:02}. '+p['text'],'**'+b['reason_label']+'** — '+p['reason'],'**'+b['choice_label']+'** — '+p['choice']]
 out+=['</details>','<p align="center"><strong>'+c['source']['closing_lead']+'</strong></p>',f'<p align="center"><a href="{full}">{labels[6]} ↗</a> · <a href="https://github.com/Velvitty?tab=repositories">GitHub</a></p>']
 (ROOT/('README.md' if lang=='ko' else f'README.{lang}.md')).write_text('\n\n'.join(out)+'\n')

def main():
 for lang in LANGS:
  for mobile in (False,True):
   hero(lang,mobile);gallery(lang,mobile)
   for i in range(8):project(lang,i,mobile)
  language_buttons(lang);readme(lang)
 for lang,title,text,x,y,width,w,h in BOUNDS:
  assert x>=-1 and x+width<=w+1 and 0<=y<=h,(lang,title,text,x,y,width,w,h)
 print('Built 6 localized READMEs and 144 responsive SVG assets; text bounds passed.')

if __name__=='__main__':main()
