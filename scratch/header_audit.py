from docx import Document
from lxml import etree
for f in [r'C:\Users\achyu\Downloads\cc report task 1.docx',r'output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx']:
 d=Document(f); print('\n',f)
 for i,s in enumerate(d.sections):
  hs=lambda a:[p.text for p in a.paragraphs]
  if hs(s.header) or hs(s.footer): print(i,'H',hs(s.header),'F',hs(s.footer),'FH',hs(s.first_page_header),'FF',hs(s.first_page_footer))
