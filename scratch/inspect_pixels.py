from PIL import Image
path = r'C:\Users\achyu\Desktop\BDA\scratch\margin-check-04.png'
im = Image.open(path).convert('RGB')
print('image', im.size)
for start, end in ((0, 160), (1240, 1404)):
    rows = []
    for y in range(start, end):
        count = 0
        for x in range(50, im.width - 50):
            r, g, b = im.getpixel((x, y))
            if r > g * 1.15 and r > b * 1.15 and r > 70:
                count += 1
        if count > 20:
            rows.append((y, count))
    print(rows[:20], '...', rows[-20:])
