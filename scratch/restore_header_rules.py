from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree

path=Path(r'C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx')
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W}
with ZipFile(path) as z:
 files={n:z.read(n) for n in z.namelist()}
changed=[]
for name,data in list(files.items()):
 if not (name.startswith('word/header') or name.startswith('word/footer')) or not name.endswith('.xml') or name.endswith('.rels'):
  continue
 root=etree.fromstring(data)
 text=''.join(root.xpath('.//w:t/text()',namespaces=NS))
 edge=None
 if 'WEATHER DATA STORAGE AND ANALYSIS' in text:
  edge='bottom'
 elif 'DEPARTMENT OF CSE (AI)' in text:
  edge='top'
 if edge is None:
  continue
 # Select the header/footer's outer paragraph, not paragraphs nested inside a floating text box.
 paras=root.xpath('./w:p',namespaces=NS)
 if not paras: continue
 p=paras[0]
 if edge=='bottom':
  # Put the rule in a dedicated one-point paragraph below the floating title/year boxes.
  rulep=etree.Element('{'+W+'}p'); p.addnext(rulep); p=rulep
 ppr=p.find('{'+W+'}pPr')
 if ppr is None:
  ppr=etree.Element('{'+W+'}pPr'); p.insert(0,ppr)
 if edge=='bottom':
  spacing=etree.SubElement(ppr,'{'+W+'}spacing')
  spacing.set('{'+W+'}before','0'); spacing.set('{'+W+'}after','0'); spacing.set('{'+W+'}line','20'); spacing.set('{'+W+'}lineRule','exact')
 pb=ppr.find('{'+W+'}pBdr')
 if pb is None:
  pb=etree.SubElement(ppr,'{'+W+'}pBdr')
 rule=pb.find('{'+W+'}'+edge)
 if rule is None: rule=etree.SubElement(pb,'{'+W+'}'+edge)
 rule.set('{'+W+'}val','double'); rule.set('{'+W+'}sz','6'); rule.set('{'+W+'}space','2'); rule.set('{'+W+'}color','A35412')
 if edge=='bottom':
  run=etree.SubElement(p,'{'+W+'}r'); rp=etree.SubElement(run,'{'+W+'}rPr'); sz=etree.SubElement(rp,'{'+W+'}sz'); sz.set('{'+W+'}val','2')
  t=etree.SubElement(run,'{'+W+'}t'); t.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); t.text=' '
 files[name]=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
 changed.append(name)
tmp=path.with_suffix('.rules.docx')
with ZipFile(tmp,'w',ZIP_DEFLATED) as z:
 for n,b in files.items(): z.writestr(n,b)
tmp.replace(path)
print('restored rules in',', '.join(changed))
