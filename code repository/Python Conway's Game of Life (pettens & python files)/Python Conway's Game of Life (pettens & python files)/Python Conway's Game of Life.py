import tkinter as tk
import random

# ===== 설정 =====
CELL_SIZE = 5
WIDTH = 19953
HEIGHT = 19953
DELAY = 50
RLE_FILE = r"E:\⟪👨🏻‍💻태민파일✨⟫\code diractory\Python Conway's Game of Life (pettens & python files)\Python Conway's Game of Life (pettens & python files)\[{}-大韓 Multiverse Empire • Established 1995 • 건양(建陽) 원년 314x314px life of game logo-{}] 001.rle"

FILL_COLOR = "#ffcc00"   # 👑 황제색 (원하면 "#00ffcc")

# ===== 그리드 =====
grid = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

# ===== RLE 로더 =====
def load_rle(path, offset_x=0, offset_y=0):
    global grid
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("❌ RLE 파일을 찾을 수 없음")
        return False

    data = ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("x"):
            continue
        data += line

    x = offset_x
    y = offset_y
    count = ""

    for ch in data:
        if ch.isdigit():
            count += ch
            continue

        n = int(count) if count else 1
        count = ""

        if ch == "o":
            for _ in range(n):
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    grid[y][x] = 1
                x += 1
        elif ch == "b":
            x += n
        elif ch == "$":
            y += n
            x = offset_x
        elif ch == "!":
            break

    print("✅ RLE 로드 완료")
    return True

# ===== 생명 규칙 =====
def next_generation():
    global grid
    new_grid = [[0]*WIDTH for _ in range(HEIGHT)]

    for y in range(HEIGHT):
        for x in range(WIDTH):
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                        neighbors += grid[ny][nx]

            if grid[y][x] == 1 and neighbors in (2, 3):
                new_grid[y][x] = 1
            elif grid[y][x] == 0 and neighbors == 3:
                new_grid[y][x] = 1

    grid = new_grid

# ===== GUI =====
root = tk.Tk()
root.title("Conway's Game of Life — Multiverse Empire")

canvas = tk.Canvas(
    root,
    width=WIDTH * CELL_SIZE,
    height=HEIGHT * CELL_SIZE,
    bg="black"
)
canvas.pack()

def draw():
    canvas.delete("all")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x]:
                canvas.create_rectangle(
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    (x + 1) * CELL_SIZE,
                    (y + 1) * CELL_SIZE,
                    fill=FILL_COLOR,
                    outline=""
                )

def update():
    draw()
    next_generation()
    root.after(DELAY, update)

# ===== 마우스 =====
def toggle_cell(event):
    x = event.x // CELL_SIZE
    y = event.y // CELL_SIZE
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        grid[y][x] ^= 1

canvas.bind("<Button-1>", toggle_cell)

# ===== 단축키 =====
def clear():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            grid[y][x] = 0

root.bind("c", lambda e: clear())           # 초기화
root.bind("space", lambda e: random_init()) # 랜덤

def random_init():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            grid[y][x] = random.choice([0, 1])

root.bind("r", lambda e: load_rle(RLE_FILE, 0, 0))

# ===== 시작 =====
if not load_rle(RLE_FILE, 0, 0):
    random_init()

update()
root.mainloop()
