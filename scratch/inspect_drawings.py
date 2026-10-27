from zipfile import ZipFile
from lxml import etree

source = r'C:\Users\achyu\Downloads\cc report task 1.docx'
z = ZipFile(source)
root = etree.fromstring(z.read('word/document.xml'))
ns = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}
anchors = root.xpath('.//wp:anchor', namespaces=ns)
print('anchors', len(anchors))
for i, anchor in enumerate(anchors):
    paragraph = anchor.getparent().getparent()
    text = ''.join(paragraph.xpath('.//w:t/text()', namespaces=ns))
    extent = anchor.find('wp:extent', ns)
    pos_h = anchor.find('wp:positionH', ns)
    pos_v = anchor.find('wp:positionV', ns)
    prop = anchor.find('wp:docPr', ns)
    line = anchor.find('.//a:ln', ns)
    size = tuple(round(int(extent.get(k)) / 914400, 3) for k in ('cx', 'cy')) if extent is not None else None
    offset_h = pos_h.find('wp:posOffset', ns).text if pos_h is not None and pos_h.find('wp:posOffset', ns) is not None else None
    offset_v = pos_v.find('wp:posOffset', ns).text if pos_v is not None and pos_v.find('wp:posOffset', ns) is not None else None
    color = line.find('.//a:srgbClr', ns).get('val') if line is not None and line.find('.//a:srgbClr', ns) is not None else None
    print(i, 'name=', prop.get('name') if prop is not None else None, 'text=', repr(text[:40],), 'size=', size,
          'H=', (pos_h.get('relativeFrom'), offset_h) if pos_h is not None else None,
          'V=', (pos_v.get('relativeFrom'), offset_v) if pos_v is not None else None,
          'blip=', bool(anchor.xpath('.//a:blip', namespaces=ns)), 'linecolor=', color)
