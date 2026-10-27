from pathlib import Path
p=Path('scratch/edit_report.py'); s=p.read_text(encoding='utf-8-sig')
# Remove duplicate automatic numbering from headings and TOC labels.
repls={
"put(29,'1. INTRODUCTION ........................................................ 1')":"put(29,'INTRODUCTION ........................................................ 1')",
"put(30,'2. SYSTEM REQUIREMENTS AND SPECIFICATIONS ............................. 3')":"put(30,'SYSTEM REQUIREMENTS AND SPECIFICATIONS ............................. 3')",
"put(31,'3. SYSTEM DESIGN ..................................................... 5')":"put(31,'SYSTEM DESIGN ..................................................... 5')",
"put(32,'4. IMPLEMENTATION .................................................... 7')":"put(32,'IMPLEMENTATION .................................................... 7')",
"put(33,'5. RESULT ........................................................... 12')":"put(33,'RESULT ........................................................... 10')",
"put(34,'6. CONCLUSION ....................................................... 14')":"put(34,'CONCLUSION ....................................................... 12')",
"put(39,'1. INTRODUCTION')":"put(39,'INTRODUCTION')",
"put(85,'2. SYSTEM REQUIREMENTS AND SPECIFICATIONS')":"put(85,'SYSTEM REQUIREMENTS AND SPECIFICATIONS')",
"put(124,'3. SYSTEM DESIGN')":"put(124,'SYSTEM DESIGN')",
"put(148,'4. IMPLEMENTATION')":"put(148,'IMPLEMENTATION')",
}
for a,b in repls.items():
 if a not in s: raise SystemExit('missing: '+a)
 s=s.replace(a,b)
old="""# Remove obsolete page-only section breaks left by the old screenshot sequence; preserve all section breaks that separate report parts.
for idx in (54,243,348):
 p=P[idx]
 if p._p.pPr is not None and p._p.pPr.sectPr is not None:
  p._p.pPr.remove(p._p.pPr.sectPr)
"""
new="""# Turn only screenshot-only section breaks into continuous transitions. This keeps each page's original header/footer and page-number settings without forcing blank pages.
for idx in (54,243,348):
 p=P[idx]
 if p._p.pPr is not None and p._p.pPr.sectPr is not None:
  sec=p._p.pPr.sectPr
  typ=sec.find(qn('w:type'))
  if typ is None:
   typ=OxmlElement('w:type'); sec.insert(0,typ)
  typ.set(qn('w:val'),'continuous')
"""
if old not in s: raise SystemExit('section block missing')
s=s.replace(old,new)
s=s.replace("  caption.style='Heading 3'\n  p._p.addprevious(caption._p)","  caption.style='Heading 3'\n  if label=='Default System Configuration': caption.paragraph_format.page_break_before=True\n  p._p.addprevious(caption._p)")
needle="""# Remove empty screenshot spacer paragraphs after the front matter while preserving page/section breaks and drawings.
for pi,p in enumerate(list(doc.paragraphs)):
"""
repl="""# Remove obsolete body-floating diagrams and decorative marks whose screenshot anchors were deleted; recurring rules remain in the original header/footer parts.
for p in doc.paragraphs:
 if doc.paragraphs.index(p) < 37: continue
 for drawing in list(p._p.xpath('.//w:drawing')):
  if not drawing.xpath('.//a:blip'):
   drawing.getparent().remove(drawing)
 for pict in list(p._p.xpath('.//w:pict')):
  pict.getparent().remove(pict)
# Remove empty screenshot spacer paragraphs after the front matter while preserving page/section breaks and remaining images.
for pi,p in enumerate(list(doc.paragraphs)):
"""
if needle not in s: raise SystemExit('empty loop missing')
s=s.replace(needle,repl)
p.write_text(s,encoding='utf-8')
