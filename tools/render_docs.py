"""README artwork: docs/images/banner.png, items.png, colours.png and recipes.png.

Run from the repo root:  python3 tools/render_docs.py
Needs Pillow and the DejaVu fonts. Every picture is original pixel art drawn here
(the chests and the book are the add-on's own textures, from tools/render_textures.py).
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_textures import COLOURS, faces, guide_icon, hx, icon as chest_icon, shade  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "docs", "images")
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

BG_TOP, BG_BOTTOM = (52, 36, 22), (16, 10, 6)
CREAM, MUTED = (255, 236, 196), (204, 176, 132)
GOLD = (242, 193, 46)
CARD, CARD_EDGE = (44, 30, 18), (136, 98, 40)
COLOUR = dict(COLOURS)


# ---------- helpers ----------

def background(w, h_, sparkles=70):
    img = Image.new("RGB", (w, h_))
    d = ImageDraw.Draw(img)
    for y in range(h_):
        t = y / h_
        d.line([(0, y), (w, y)], fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)))
    rnd = random.Random(5)
    for _ in range(sparkles):
        x, y, s = rnd.randrange(w), rnd.randrange(h_), rnd.choice([2, 2, 2, 4])
        d.rectangle([x, y, x + s - 1, y + s - 1], fill=rnd.choice([(242, 193, 46), (170, 120, 50), (255, 240, 210)]))
    return img


def pixel_text(text, size, colour, scale):
    """Crisp blocky text: render small without antialiasing, then scale up."""
    font = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", size)
    l, t, r, b = font.getbbox(text)
    small = Image.new("RGBA", (r - l + 2, b - t + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(small)
    d.fontmode = "1"
    d.text((1 - l, 1 - t), text, font=font, fill=colour)
    return small.resize((small.width * scale, small.height * scale), Image.NEAREST)


def paste_text(img, text, size, colour, scale, centre_x, top, shadow=(26, 14, 4)):
    sh = pixel_text(text, size, shadow + (255,), scale)
    fg = pixel_text(text, size, colour + (255,), scale)
    x = int(centre_x - fg.width / 2)
    img.paste(sh, (x + scale, top + scale), sh)
    img.paste(fg, (x, top), fg)


def face_img(g):
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), hx(g[y][x]) + (255,))
    return im


def iso_chest(colour, px):
    """A big isometric chest built from the real textures, one block = 16 * px wide-ish."""
    front, side, top, _ = faces(COLOUR[colour])
    c, s = 0.8660254 * px, 0.5 * px
    W, H = int(32 * c) + 2, int(16 * px + 32 * s) + 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = W / 2, 0

    def quad(P, u, v, col):
        d.polygon([P(u, v), P(u + 1, v), P(u + 1, v + 1), P(u, v + 1)], fill=hx(col), outline=hx(col))

    for v in range(16):
        for u in range(16):
            quad(lambda a, b: (ox + (a - b) * c, oy + (a + b) * s), u, v, top[v][u])
    lx, ly = ox - 16 * c, oy + 16 * s
    for y in range(16):
        for u in range(16):
            quad(lambda a, b: (lx + a * c, ly + a * s + b * px), u, y, shade(front[y][u], 0.84))
    rx, ry = ox, oy + 32 * s
    for y in range(16):
        for u in range(16):
            quad(lambda a, b: (rx + a * c, ry - a * s + b * px), u, y, shade(side[y][u], 0.64))
    return img


def drop_shadow(img, im, pos, blur=6):
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 120), (0, 0), im)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)), (pos[0] + 8, pos[1] + 10))
    img.alpha_composite(im, pos)


def plank():
    """Oak floor planks for the banner."""
    rnd = random.Random(9)
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            base = (162, 130, 78) if y % 4 != 3 else (104, 80, 46)
            f = 1 + (rnd.random() - 0.5) * 0.16
            im.putpixel((x, y), tuple(int(v * f) for v in base) + (255,))
    for y in range(16):
        if y % 4 != 3:
            im.putpixel(((5 + (y // 4) * 7) % 16, y), (104, 80, 46, 255))
    return im


# ---------- banner ----------

def banner():
    W, H = 1280, 490
    img = background(W, H).convert("RGBA")
    B = 64
    top = H - 2 * B
    floor = plank().resize((B, B), Image.NEAREST)
    for row in range(2):
        for col in range(W // B + 1):
            tile = floor if row == 0 else Image.blend(floor, Image.new("RGBA", floor.size, (16, 10, 6, 255)), 0.45)
            img.paste(tile, (col * B, top + row * B))

    # a row of dyed chests standing on the floor, plus a stack on each side
    row = ["red", "yellow", "lime", "light_blue", "purple"]
    px = 5
    sample = iso_chest("undyed", px)
    cw, ch = sample.size
    start = (W - len(row) * (cw - 6)) // 2
    for i, name in enumerate(row):
        drop_shadow(img, iso_chest(name, px), (start + i * (cw - 6), top - ch + 44))
    big = 9
    for name, x in (("blue", 30), ("undyed", W - 30 - iso_chest("undyed", big).width)):
        im = iso_chest(name, big)
        drop_shadow(img, im, (x, top - im.height + 50))

    paste_text(img, "STORAGE", 22, CREAM, 4, W / 2, 30)
    paste_text(img, "CHESTS", 22, GOLD, 4, W / 2, 126)
    paste_text(img, "Keeps its items  ·  16 colours  ·  No End trip", 11, MUTED, 2, W / 2, 222)
    img.convert("RGB").save(os.path.join(IMAGES, "banner.png"))


# ---------- item cards ----------

def items():
    W, H = 1200, 400
    img = background(W, H, sparkles=36).convert("RGBA")
    d = ImageDraw.Draw(img)
    cw = W // 3
    cards = [
        (iso_chest("undyed", 6), "Storage Chest", "27 slots, keeps its items"),
        (None, "16 colours", "Use any dye on it"),
        (guide_icon(), "Storage Chests Guide", "Every player gets one"),
    ]
    for i, (ic, name, note) in enumerate(cards):
        cx = i * cw + cw // 2
        d.rounded_rectangle([i * cw + 16, 16, (i + 1) * cw - 16, H - 16], 18, fill=CARD, outline=CARD_EDGE, width=2)
        if ic is not None:
            if ic.width != 16:  # the big isometric render
                drop_shadow(img, ic, (cx - ic.width // 2, 50), blur=4)
            else:
                img.alpha_composite(ic.resize((176, 176), Image.NEAREST), (cx - 88, 64))
        else:
            names = [n for n, _ in COLOURS[1:]]
            for k, n in enumerate(names):  # 4 x 4 grid of small chests
                small = chest_icon(COLOUR[n]).resize((48, 48), Image.NEAREST)
                img.alpha_composite(small, (cx - 104 + (k % 4) * 52, 52 + (k // 4) * 50))
        paste_text(img, name, 13, CREAM, 2, cx, 282)
        paste_text(img, note, 10, MUTED, 2, cx, 336)
    img.convert("RGB").save(os.path.join(IMAGES, "items.png"))


# ---------- recipes ----------

SLOT_IN, SLOT_DARK, SLOT_LIGHT = (70, 50, 30), (28, 18, 10), (130, 98, 60)


def from_rows(rows, palette):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in palette:
                im.putpixel((x, y), palette[ch] + (255,))
    return im


def iron_ingot():
    return from_rows([
        "................", "................", "................", "................",
        ".......kkkkkk...", ".....kkWWWWLLk..", "...kkWWLLLLLMk..", "..kWWLLLLLLMMk..",
        "..kLLLLLLLMMDk..", "..kMMLLLLMMDDk..", "..kDMMMMMMDDk...", "...kkDDDDDkk....",
        ".....kkkkk......", "................", "................", "................",
    ], {"k": (40, 40, 44), "W": (246, 246, 246), "L": (214, 214, 214), "M": (170, 170, 170), "D": (118, 118, 122)})


def chest():
    """A vanilla-style wooden chest, drawn from scratch."""
    return from_rows([
        "................", "..kkkkkkkkkkkk..", ".kLLLLLLLLLLLLk.", ".kLOOOOOOOOOOLk.",
        ".kOOOOOOOOOOOOk.", ".kOOOOOOOOOOOOk.", ".kkkkkkIIkkkkkk.", ".kDDDDDIIDDDDDk.",
        ".kOOOOOkkOOOOOk.", ".kOOOOOOOOOOOOk.", ".kOOOOOOOOOOOOk.", ".kOOOOOOOOOOOOk.",
        ".kDDDDDDDDDDDDk.", ".kkkkkkkkkkkkkk.", "................", "................",
    ], {"k": (58, 36, 14), "L": (196, 146, 76), "O": (164, 112, 50), "D": (118, 78, 32), "I": (220, 220, 220)})


def book():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 2, 12, 13], fill=(120, 66, 36, 255))
    d.rectangle([11, 3, 13, 14], fill=(236, 228, 206, 255))
    d.rectangle([3, 2, 4, 13], fill=(84, 44, 22, 255))
    d.rectangle([6, 5, 9, 6], fill=(160, 100, 60, 255))
    return im


ICONS = {}


def icon(name, size):
    if not ICONS:
        ICONS.update({"iron": iron_ingot(), "chest": chest(), "book": book(),
                      "storage": iso_chest("undyed", 3), "guide": guide_icon()})
    im = ICONS[name]
    return im.resize((size, size), Image.NEAREST if im.width == 16 else Image.LANCZOS)


def slot(size, border=4):
    s = Image.new("RGBA", (size, size), SLOT_IN + (255,))
    d = ImageDraw.Draw(s)
    d.rectangle([0, 0, size - 1, border - 1], fill=SLOT_DARK)
    d.rectangle([0, 0, border - 1, size - 1], fill=SLOT_DARK)
    d.rectangle([0, size - border, size - 1, size - 1], fill=SLOT_LIGHT)
    d.rectangle([size - border, 0, size - 1, size - 1], fill=SLOT_LIGHT)
    return s


def arrow(size):
    a = from_rows([
        "................", "................", "................", "................",
        "........LL......", "........LLL.....", "..LLLLLLLLLL....", "..LLLLLLLLLLL...",
        "..LLLLLLLLLLL...", "..LLLLLLLLLL....", "........LLL.....", "........LL......",
        "................", "................", "................", "................",
    ], {"L": CREAM})
    return a.resize((size, size), Image.NEAREST)


def recipe_panel(grid, result, title, note):
    S, G = 76, 6
    W, H = 3 * S + 2 * G + 130 + S + 40, 3 * S + 2 * G + 120
    p = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle([0, 0, W - 1, H - 1], 16, fill=CARD, outline=CARD_EDGE, width=2)
    gx, gy = 20, 64
    for r in range(3):
        for c in range(3):
            s = slot(S)
            if grid[r][c]:
                s.alpha_composite(icon(grid[r][c], 56), (10, 10))
            p.alpha_composite(s, (gx + c * (S + G), gy + r * (S + G)))
    ax = gx + 3 * S + 2 * G + 22
    p.alpha_composite(arrow(80), (ax, gy + S + G - 2))
    out = slot(S + 16)
    out.alpha_composite(icon(result, 68), (12, 12))
    p.alpha_composite(out, (ax + 96, gy + S + G - 8))
    paste_text(p, title, 11, CREAM, 2, W / 2, 18)
    paste_text(p, note, 9, MUTED, 2, W / 2, H - 40)
    return p


def recipes():
    I, C, B = "iron", "chest", "book"
    panels = [
        recipe_panel([[None, I, None], [None, C, None], [None, I, None]], "storage", "Storage Chest", "2 Iron Ingots + 1 Chest"),
        recipe_panel([[B, C, None], [None, None, None], [None, None, None]], "guide", "Storage Chests Guide", "Book + Chest, any slots"),
    ]
    pw, ph = panels[0].size
    W = 2 * pw + 3 * 24
    img = background(W, ph + 48, sparkles=30).convert("RGBA")
    for i, p in enumerate(panels):
        img.alpha_composite(p, (24 + i * (pw + 24), 24))
    img.convert("RGB").save(os.path.join(IMAGES, "recipes.png"))


if __name__ == "__main__":
    os.makedirs(IMAGES, exist_ok=True)
    banner()
    items()
    recipes()
    print("rendered banner.png, items.png and recipes.png")
