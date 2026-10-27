from PIL import Image,ImageDraw
from pathlib import Path
fs=sorted(Path('scratch').glob('original-page-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[-1]))
w,h=210,300; cols=5
out=Image.new('RGB',(cols*w,((len(fs)+cols-1)//cols)*h),'#d8d8d8'); d=ImageDraw.Draw(out)
for i,f in enumerate(fs):
 im=Image.open(f); im.thumbnail((w-12,h-30)); x=(i%cols)*w+6; y=(i//cols)*h+5; out.paste(im,(x,y)); d.text((x,y+h-24),f'Page {i+1}',fill='black')
out.save('scratch/original-contact.png'); print('pages',len(fs))
