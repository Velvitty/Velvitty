#!/usr/bin/env python3
"""Add French/Spanish outlines without changing the existing Latin glyphs.

Requires fonttools. Usage: python tools/profile/extend_latin_glyphs.py FONT_DIR
FONT_DIR: NotoSans-Regular.ttf, NotoSans-Bold.ttf, DejaVuSansMono.ttf.
Normal profile builds use the checked-in JSON and the standard library only.
"""
from pathlib import Path
import sys,json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
root=Path(__file__).resolve().parent
source=Path(sys.argv[1])
fonts=json.loads((root/'latin-glyphs.json').read_text())
strings=[]
for lang in ['fr','es']:
    d=json.loads((root/f'locales/{lang}.json').read_text())
    strings.extend(list(d['art'].values())+[d['name']])
    strings.extend(p['text'] for p in d['principles'])
    for group in d['principles_groups']:
        strings.extend(group[k] for k in ['short_title','question','footer','eyebrow'])
chars=set(''.join(strings))
for family,filename in [('regular','NotoSans-Regular.ttf'),('bold','NotoSans-Bold.ttf'),('mono','DejaVuSansMono.ttf')]:
    font=TTFont(source/filename)
    assert font['head'].unitsPerEm==fonts[family]['units']
    gs=font.getGlyphSet();cmap=font.getBestCmap()
    for ch in sorted(chars-set(fonts[family]['chars'])):
        if ord(ch) not in cmap:raise ValueError((family,ch))
        name=cmap[ord(ch)];pen=SVGPathPen(gs);gs[name].draw(pen)
        fonts[family]['chars'][ch]={'d':pen.getCommands(),'advance':font['hmtx'][name][0]}
    font.close()
(root/'latin-glyphs.json').write_text(json.dumps(fonts,ensure_ascii=False,separators=(',',':'))+'\n')
print('Latin glyphs:',{k:len(v['chars']) for k,v in fonts.items()})
