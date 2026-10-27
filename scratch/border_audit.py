from docx import Document
from docx.oxml.ns import qn
for name in [r'C:\Users\achyu\Downloads\cc report task 1.docx',r'output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx']:
 d=Document(name); print('\n',name)
 for i,p in enumerate(d.paragraphs):
  ppr=p._p.pPr
  if ppr is not None and ppr.find(qn('w:pBdr')) is not None:
   print(i,p.style.name,repr(p.text[:90]),ppr.find(qn('w:pBdr')).xml[:250])
