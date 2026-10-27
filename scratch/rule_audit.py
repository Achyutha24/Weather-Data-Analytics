from zipfile import ZipFile
from lxml import etree
from pathlib import Path
for f in [Path(r'C:\Users\achyu\Downloads\cc report task 1.docx'),Path(r'C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx')]:
 print('\nFILE',f)
 with ZipFile(f) as z:
  ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','v':'urn:schemas-microsoft-com:vml'}
  root=etree.fromstring(z.read('word/document.xml'))
  for pi,p in enumerate(root.xpath('.//w:body/w:p',namespaces=ns)):
   for d in p.xpath('.//w:drawing',namespaces=ns):
    dp=d.xpath('.//wp:docPr',namespaces=ns); ext=d.xpath('./wp:anchor/wp:extent',namespaces=ns)
    if ext and int(ext[0].get('cy')) < 100000:
     an=d.find('{'+ns['wp']+'}anchor'); pos=[]
     for side in ['H','V']:
      x=an.find('{'+ns['wp']+'}position'+side)
      if x is not None:
       rel=x.find('{'+ns['wp']+'}relativeFrom')
       off=x.find('{'+ns['wp']+'}posOffset')
       pos.append((side,rel.text if rel is not None else '',int(off.text)/914400 if off is not None else None))
     print('body',pi,'name',dp[0].get('name') if dp else '', 'extent',round(int(ext[0].get('cx'))/914400,2),round(int(ext[0].get('cy'))/914400,3),'pos',pos)
  for name in [n for n in z.namelist() if n.startswith('word/header') or n.startswith('word/footer')]:
   if not name.endswith('.xml') or name.endswith('.rels'):continue
   x=etree.fromstring(z.read(name))
   pbd=len(x.xpath('.//w:pBdr',namespaces=ns)); pict=len(x.xpath('.//w:pict',namespaces=ns)); anchors=len(x.xpath('.//wp:anchor',namespaces=ns))
   if pbd or pict or anchors: print(name,'pBdr',pbd,'pict',pict,'anchor',anchors)
  sects=root.xpath('.//w:sectPr',namespaces=ns)
  for si,s in enumerate(sects):
   pb=s.find('{'+ns['w']+'}pgBorders')
   if pb is not None: print('section pgBorders',si,etree.tostring(pb,encoding='unicode')[:350])
