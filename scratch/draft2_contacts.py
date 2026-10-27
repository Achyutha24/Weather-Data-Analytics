from PIL import Image,ImageDraw
from pathlib import Path
import sys
folder=Path(sys.argv[1]) if len(sys.argv)>1 else Path(r'C:\Users\achyu\Desktop\BDA\scratch\draft2-pages')
fs=sorted(folder.glob('page-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[-1]))
cols=4; tw=310; gap=14
ims=[Image.open(f).convert('RGB') for f in fs]
th=round(ims[0].height*tw/ims[0].width)
rows=(len(ims)+cols-1)//cols
out=Image.new('RGB',(cols*(tw+gap)+gap,rows*(th+34+gap)+gap),'#ddd'); d=ImageDraw.Draw(out)
for i,im in enumerate(ims):
 im.thumbnail((tw,th)); x=gap+(i%cols)*(tw+gap); y=gap+(i//cols)*(th+34+gap)
 out.paste(im,(x,y)); d.text((x,y+th+5),f'Page {i+1}',fill='black')
out.save(folder/'contact.png')
print('pages',len(fs),'contact',folder/'contact.png')
