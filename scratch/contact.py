from PIL import Image,ImageDraw
import glob,os
fs=glob.glob('scratch/media/*')
out=Image.new('RGB',(900,((len(fs)+2)//3)*240),'white')
d=ImageDraw.Draw(out)
for i,f in enumerate(fs):
 im=Image.open(f); size=im.size; im.thumbnail((285,200)); x=(i%3)*300; y=(i//3)*240; out.paste(im,(x,y)); d.text((x,y+204),os.path.basename(f)+' '+str(size),fill='black')
out.save('scratch/contact.png')
