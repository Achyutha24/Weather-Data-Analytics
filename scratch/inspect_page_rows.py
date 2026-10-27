from PIL import Image

for page in (4, 6, 7, 13):
    path = fr'C:\Users\achyu\Desktop\BDA\scratch\footer-check-{page:02d}.png' if page != 13 else r'C:\Users\achyu\Desktop\BDA\scratch\footer-check-last-13.png'
    im = Image.open(path).convert('RGB')
    print('page', page, im.size)
    for y in range(0, 170):
        dark = red = 0
        for x in range(70, im.width - 70):
            r, g, b = im.getpixel((x, y))
            if max(r, g, b) < 120:
                dark += 1
            if r > g * 1.15 and r > b * 1.15 and r > 70:
                red += 1
        if dark > 12 or red > 12:
            print(y, 'dark', dark, 'red', red)
