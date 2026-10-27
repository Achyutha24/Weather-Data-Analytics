from docx import Document
from docx.oxml.ns import qn
ns={'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
d=Document(r'C:\Users\achyu\Downloads\cc report task 1.docx')
for i,p in enumerate(d.paragraphs):
 if i<37: continue
 draws=p._p.xpath('.//w:drawing')
 if draws:
  for dr in draws:
   names=dr.xpath('.//wp:docPr/@name')
   descr=dr.xpath('.//wp:docPr/@descr')
   positions=[]
   for a in dr.xpath('.//wp:anchor'):
    for t in ['H','V']:
     vals=a.xpath(f'./wp:position{t}/wp:posOffset/text()')
     positions.append(t+('='.join(vals) if vals else ''))
   blip=dr.xpath('.//a:blip/@r:embed')
   print(i,repr(p.text[:45]),'name',names,'descr',descr,'pos',positions,'blip',blip,'ptextchildren',len(p._p))
