from zipfile import ZipFile
from lxml import etree
p=r'C:\Users\achyu\Downloads\cc report task 1.docx'; z=ZipFile(p); ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for f in ['word/document.xml']+[x for x in z.namelist() if x.startswith('word/header') or x.startswith('word/footer')]:
 root=etree.fromstring(z.read(f)); tx=root.xpath('.//w:txbxContent',namespaces=ns)
 for i,x in enumerate(tx):
  text=''.join(x.xpath('.//w:t/text()',namespaces=ns))
  if text: print(f,i,repr(text[:220]))
