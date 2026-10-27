from pathlib import Path
p=Path('scratch/edit_report.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("path=Path('output/Weather_Data_Storage_and_Analysis_MongoDB_Report.docx')", "path=Path('output/Weather_Data_Storage_and_Analysis_MongoDB_Report.docx')")
old="""# Paragraph copy helper: keep paragraph properties and first-run typography.
def put(i,text):
 p=P[i]
 rpr=None
 if p.runs and p.runs[0]._r.rPr is not None:
  rpr=p.runs[0]._r.rPr
 p.clear()
 r=p.add_run(text)
 if rpr is not None: r._r.insert(0,rpr)
"""
new="""# Replace text nodes in place so Word drawings, section properties, run formatting, and page furniture survive.
def set_paragraph_text(p,text):
 nodes=[]
 for run in p._p.findall(qn('w:r')):
  if run.find(qn('w:drawing')) is not None or run.find(qn('w:pict')) is not None:
   continue
  nodes.extend(run.findall(qn('w:t')))
 if not nodes:
  run=OxmlElement('w:r'); node=OxmlElement('w:t'); run.append(node); p._p.append(run); nodes=[node]
 nodes[0].text=text
 if text[:1].isspace() or text[-1:].isspace(): nodes[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 else: nodes[0].attrib.pop('{http://www.w3.org/XML/1998/namespace}space',None)
 for node in nodes[1:]: node.text=''
def put(i,text):
 set_paragraph_text(P[i],text)
"""
if old not in s: raise SystemExit('put block not found')
s=s.replace(old,new)
s=s.replace('  p.clear()\n# Replace legacy project-title text in headers/footers and drawing captions while preserving other admin details.\nfor sec in doc.sections:\n for area in [sec.header,sec.footer,sec.first_page_header,sec.first_page_footer]:\n  for p in area.paragraphs:\n   if p.text.strip():\n    s=p.text\n    s=re.sub(r\'(?i)Virtual Machine Installation\',\'Weather Data Storage and Analysis Using MongoDB\',s)\n    s=re.sub(r\'(?i)Ubuntu|VirtualBox|Guest Additions\',\'\',s)\n    if s!=p.text: p.text=s\n# Remove legacy non-logo illustrations, but preserve VTU and SVCE logos. Replace the old design figure in place.\ndoc.save(path)', '''  set_paragraph_text(p,'')
# Remove obsolete page-only section breaks left by the old screenshot sequence; preserve all section breaks that separate report parts.
for idx in (54,243,348):
 p=P[idx]
 if p._p.pPr is not None and p._p.pPr.sectPr is not None:
  p._p.pPr.remove(p._p.pPr.sectPr)
# Start the conclusion cleanly on a new page.
conclusion=P[343]
if conclusion._p.pPr is None:
 conclusion._p.insert(0,OxmlElement('w:pPr'))
if conclusion._p.pPr.find(qn('w:pageBreakBefore')) is None:
 conclusion._p.pPr.append(OxmlElement('w:pageBreakBefore'))
# Save text-only edits before image-part substitution.
doc.save(path)''')
# Change table header fill to white and make borders/padding/type match source report tables.
s=s.replace("  for c in table.rows[0].cells:\n   shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'D9EAF7'); c._tc.get_or_add_tcPr().append(shd)", """  widths=({4:[0.45,1.25,2.35,2.35],3:[0.45,1.55,4.4],2:[2.25,4.15]}[len(headers)])
  table.autofit=False
  for row in table.rows:
   for col,cell in enumerate(row.cells):
    cell.width=Inches(widths[col])
    tcPr=cell._tc.get_or_add_tcPr()
    margins=OxmlElement('w:tcMar')
    for side,val in [('top','65'),('start','90'),('bottom','65'),('end','90')]:
     el=OxmlElement('w:'+side); el.set(qn('w:w'),val); el.set(qn('w:type'),'dxa'); margins.append(el)
    tcPr.append(margins)
    for par in cell.paragraphs:
     par.alignment=WD_ALIGN_PARAGRAPH.CENTER if col==0 or row is table.rows[0] else WD_ALIGN_PARAGRAPH.LEFT
     for run in par.runs:
      run.font.name='Times New Roman'; run.font.size=Pt(9); run.bold=(row is table.rows[0])
""")
# Remove obsolete image drawing nodes only in the specified screenshot/table paragraphs.
s=s.replace("# Remove drawings for all old Ubuntu/web screenshots; retain logos and the replacement architecture figure.\nfor p in doc.paragraphs:\n target=image_target(p)\n if target and any(x in target.lower() for x in ('image3.png','image4.png','image9.png','image10.png','image11.png','image12.png','image13.png')):", "# Remove only obsolete screenshot drawings; keep the university logos and the replaced architecture image.\nfor p in doc.paragraphs:\n target=image_target(p)\n if target and any(x in target.lower() for x in ('image3.png','image4.png','image9.png','image10.png','image11.png','image12.png','image13.png')):")
# Add whitespace pruning after screenshot removal before settings.
needle="# Correct old image content types / relationships that no longer have media targets.\nrels=doc.part.rels"
repl="""# Remove empty screenshot spacer paragraphs after the front matter while preserving page/section breaks and drawings.
for p in list(doc.paragraphs):
 if p.text.strip(): continue
 if p._p.pPr is not None:
  if p._p.pPr.sectPr is not None or p._p.pPr.find(qn('w:pageBreakBefore')) is not None: continue
 if p._p.xpath('.//w:br[@w:type="page"]'): continue
 if b'<w:drawing' in p._p.xml or b'<w:pict' in p._p.xml: continue
 # Front matter spacing is part of the original cover/abstract/contents layout.
 bodyparas=doc.paragraphs
 if bodyparas.index(p) < 37: continue
 p._p.getparent().remove(p._p)
# Correct obsolete text in header/footer text boxes without reconstructing their drawing objects.
# The short running title fits the original header text box.
with zipfile.ZipFile(path,'r') as zin:
 package={n:zin.read(n) for n in zin.namelist()}
for name,blob in list(package.items()):
 if name.endswith('.xml'):
  package[name]=blob.replace(b'Virtual Machine Installation',b'Weather Data Analytics')
tmp=path.with_suffix('.pkg.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
 for name,blob in package.items(): zout.writestr(name,blob)
tmp.replace(path)
# Correct old image content types / relationships that no longer have media targets.
rels=doc.part.rels"""
if needle not in s: raise SystemExit('prune insertion not found')
s=s.replace(needle,repl)
# Remove accidentally stale source pointer comment and then save final.
p.write_text(s,encoding='utf-8')
