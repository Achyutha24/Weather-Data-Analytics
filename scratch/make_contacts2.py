from PIL import Image,ImageDraw
from pathlib import Path
fs=sorted(Path('scratch/final-pages2').glob('page-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[-1]))
for start in range(0,len(fs),3):
 group=fs[start:start+3]; w,h=620,850; out=Image.new('RGB',(len(group)*w,h+30),'#ddd'); d=ImageDraw.Draw(out)
 for k,f in enumerate(group):
  im=Image.open(f).convert('RGB'); im.thumbnail((w-10,h-10)); out.paste(im,(k*w+5,5)); d.text((k*w+8,h+8),f'Page {start+k+1}',fill='black')
 out.save(f'scratch/final-pages2/contact-{start//3+1}.png')
print('rendered',len(fs))
