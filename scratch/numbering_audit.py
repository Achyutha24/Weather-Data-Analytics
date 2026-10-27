from zipfile import ZipFile
from lxml import etree
p=r'C:\Users\achyu\Downloads\cc report task 1.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(p) as z:
    styles=etree.fromstring(z.read('word/styles.xml'))
    doc=etree.fromstring(z.read('word/document.xml'))
    for sid in ['Heading1','Heading2','Heading3','TOC2']:
        x=styles.xpath(f'.//w:style[@w:styleId="{sid}"]',namespaces=ns)
        print('\nSTYLE',sid,etree.tostring(x[0],encoding='unicode')[:1100] if x else 'missing')
    ps=doc.xpath('.//w:body/w:p',namespaces=ns)
    for i in [28,29,30,31,32,33,38,84,123,147,236,342]:
        print('\nP',i,etree.tostring(ps[i],encoding='unicode')[:1300])
