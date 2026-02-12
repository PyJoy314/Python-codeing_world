from PIL import Image

THRESHOLD = 128  # 흑/백 기준

def image_to_rle(path):
    img = Image.open(path).convert("L")
    w, h = img.size
    px = img.load()

    lines = []
    for y in range(h):
        run = 0
        last = None
        row = ""
        for x in range(w):
            cell = 'A' if px[x, y] < THRESHOLD else '.'
            if cell == last:
                run += 1
            else:
                if last:
                    row += (str(run) if run > 1 else "") + last
                last = cell
                run = 1
        row += (str(run) if run > 1 else "") + last
        lines.append(row + "$")

    rle = f"x = {w}, y = {h}, rule = B3/S23\n"
    rle += "\n".join(lines)
    return rle

with open(r"C:\Users\JOY\Desktop\태민이 휴대폰\⟪👨🏻‍💻태민파일✨⟫\파이썬 작품\Python Conway's Game of Life (pettens & python files)\Python Conway's Game of Life (pettens & python files)\⟪大韓 Multiverse Empire • Established 1995 • 건양(建陽) 원년 314x314px life of game logo⟫ 001.rle", "w") as f:
    f.write(image_to_rle(r"C:\Users\JOY\Desktop\태민이 휴대폰\⟪👨🏻‍💻태민파일✨⟫\작품모음\태민작품\⟪大韓 Multiverse Empire • Established 1995 • 건양(建陽) 1024x1024px 원년 logo⟫.png"))
