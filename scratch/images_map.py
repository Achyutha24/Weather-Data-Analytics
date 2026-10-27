import zipfile
from lxml import etree
p='output/Weather_Data_Storage_and_Analysis_MongoDB_Report.docx'; z=zipfile.ZipFile(p); root=etree.fromstring(z.read('word/document.xml')); rr=etree.fromstring(z.read('word/_rels/document.xml.rels')); rels={x.get('Id'):x.get('Target') for x in rr}; ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
for i,p in enumerate(root.xpath('.//w:body/w:p',namespaces=ns)):
 ids=p.xpath('.//a:blip/@r:embed',namespaces=ns)
 if ids: print(i,[rels.get(x) for x in ids])
