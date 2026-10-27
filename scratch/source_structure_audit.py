from docx import Document
from docx.oxml.ns import qn
from pathlib import Path
from lxml import etree
import zipfile,re
src=Path(r'C:\Users\achyu\Downloads\cc report task 1.docx')
d=Document(src)
for i,p in enumerate(d.paragraphs):
    texts=p.text.strip()
    drawings=p._p.findall('.//'+qn('w:drawing'))
    picts=p._p.findall('.//'+qn('w:pict'))
    sect=p._p.find(qn('w:pPr'))
    sect=sect.find(qn('w:sectPr')) if sect is not None else None
    br=p._p.findall('.//'+qn('w:br'))
    pb=p._p.find(qn('w:pPr'))
    pb=pb.find(qn('w:pageBreakBefore')) if pb is not None else None
    if texts or drawings or picts or sect is not None or br or pb is not None:
        if not texts and not drawings and not picts and sect is None and not br and pb is None: continue
        names=[]
        for dr in drawings:
            for x in dr.findall('.//'+qn('wp:docPr')):
                names.append(x.get('name','')+':'+x.get('descr',''))
            for x in dr.findall('.//'+qn('wp:extent')):
                names.append(f"{int(x.get('cx'))/914400:.2f}x{int(x.get('cy'))/914400:.2f}")
        st='sect' if sect is not None else ''
        if sect is not None:
            typ=sect.find(qn('w:type')); st+=(':'+typ.get(qn('w:val'),'default') if typ is not None else ':default')
        print(f'{i:03d}|{p.style.name}|{st}|br={len(br)}|drawing={len(drawings)} pict={len(picts)}|{texts[:155]!r}|{names}')
with zipfile.ZipFile(src) as z:
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
    rel=etree.fromstring(z.read('word/_rels/document.xml.rels'))
    relmap={x.get('Id'):x.get('Target') for x in rel}
    root=etree.fromstring(z.read('word/document.xml'))
    print('ALL DRAWING RELS')
    for pi,p in enumerate(root.xpath('.//w:body/w:p',namespaces=ns)):
        for d0 in p.xpath('.//w:drawing',namespaces=ns):
            docpr=d0.xpath('.//wp:docPr',namespaces=ns)
            blips=d0.xpath('.//a:blip',namespaces=ns)
            ext=d0.xpath('.//wp:extent',namespaces=ns)
            print('P',pi,'name',docpr[0].get('name') if docpr else '', 'descr',docpr[0].get('descr') if docpr else '', 'rel',relmap.get(blips[0].get('{'+ns['r']+'}embed')) if blips else 'none', 'extent',[(round(int(e.get('cx'))/914400,2),round(int(e.get('cy'))/914400,2)) for e in ext])
