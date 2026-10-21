#!/usr/bin/env python3
"""Regenerate CJK SVG outlines from the official Noto Sans CJK OTF files.

Requires fonttools. Usage: python tools/profile/subset_fonts.py /path/to/otfs
Download locations and license are documented in README.md.
The normal artwork build uses the checked-in JSON and only Python's stdlib.
"""
from pathlib import Path
import sys,json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.roundingPen import RoundingPen
root=Path(__file__).resolve().parent
source=Path(sys.argv[1])
locales={l:json.loads((root/f'locales/{l}.json').read_text()) for l in ['ko','en','ja','zh']}
result={}
for lang,tag in [('ko','kr'),('ja','jp'),('zh','sc')]:
    d=locales[lang]
    strings=list(d['art'].values())+[d['name']]
    for group in d['principles_groups']:strings.extend([group['short_title'],group['question'],group['footer'],group['eyebrow']])
    strings.extend(x['text'] for x in d['principles'])
    if lang=='ko':
        strings.extend(x['text'] for x in locales['en']['principles'])
        for group in locales['en']['principles_groups']:strings.extend(group.values())
    chars=set(''.join(strings))|set('0123456789 /.,:;?!-')
    for weight in ['Regular','Bold']:
        font=TTFont(source/f'NotoSansCJK{tag}-{weight}.otf')
        gs=font.getGlyphSet();cmap=font.getBestCmap();glyphs={}
        for ch in sorted(chars):
            if ord(ch) not in cmap:raise ValueError((lang,ch))
            name=cmap[ord(ch)];pen=SVGPathPen(gs)
            gs[name].draw(RoundingPen(pen))
            glyphs[ch]={'d':pen.getCommands(),'advance':font['hmtx'][name][0]}
        result['cjk-'+lang+('-bold' if weight=='Bold' else '')]={'units':font['head'].unitsPerEm,'chars':glyphs}
        font.close()
(root/'cjk-glyphs.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
print('CJK outline glyphs:',sum(len(v['chars']) for v in result.values()))
