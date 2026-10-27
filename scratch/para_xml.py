from docx import Document
from lxml import etree
from docx.oxml.ns import qn
p=Document(r'C:\Users\achyu\Downloads\cc report task 1.docx').paragraphs
for i in [0,5,21,41,85,124,148,237,343]:
 x=p[i]._p
 print('\nIDX',i,'TEXT',repr(p[i].text),'xmllen',len(x.xml))
 print(x.xml[:1200])
