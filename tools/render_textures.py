"""Draws every texture for Storage Chests.

Run from the repo root:  python3 tools/render_textures.py
Needs Pillow. Writes the chest textures, item icons and both pack icons.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "Storage_Chests_RP"
BP = ROOT / "Storage_Chests_BP"

# Index 0 is the undyed chest; 1-16 follow Minecraft's dye order (same order as scripts/colours.js).
COLOURS = [
    ("undyed", "#d9d6cc"),
    ("white", "#f4f4ef"), ("orange", "#f07a1c"), ("magenta", "#bd44b3"), ("light_blue", "#3aafd9"),
    ("yellow", "#f2c12e"), ("lime", "#70b919"), ("pink", "#ed8dac"), ("gray", "#4c5357"),
    ("light_gray", "#9d9d95"), ("cyan", "#158991"), ("purple", "#7a2fae"), ("blue", "#3b4aa8"),
    ("brown", "#7a4c2c"), ("green", "#4e6b1e"), ("red", "#a83a32"), ("black", "#26262b"),
]
LATCH, LATCH_DARK = "#e9e4d4", "#a39e8c"


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    r, g, b = hx(c)
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f))) for v in (r, g, b))


def grid(fill):
    return [[fill] * 16 for _ in range(16)]


def speckle(g, rng, palette, chance):
    for y in range(16):
        for x in range(16):
            if rng.random() < chance:
                g[y][x] = rng.choice(palette)


def faces(col):
    """The four 16x16 faces of one chest: front (with latch), side, top and bottom."""
    rng = random.Random(4)  # same speckle pattern for every colour, so the set reads as one family
    lid, edge, base_dark = shade(col, 1.08), shade(col, 0.72), shade(col, 0.85)

    side = grid(col)
    speckle(side, rng, [shade(col, 0.93), shade(col, 1.06)], 0.25)
    for y in range(6):
        for x in range(16):
            if rng.random() < 0.7:
                side[y][x] = lid
    for x in range(16):
        side[0][x] = shade(col, 1.18)  # lit top edge
        side[6][x] = edge              # the lid seam
        side[7][x] = base_dark
        side[15][x] = edge
    for (x, y) in [(0, 0), (15, 0), (0, 15), (15, 15)]:
        side[y][x] = edge              # rounded corners

    front = [row[:] for row in side]
    for y in range(5, 9):
        for x in (7, 8):
            front[y][x] = LATCH
    front[8][7] = front[8][8] = LATCH_DARK

    top = grid(lid)
    speckle(top, rng, [col, shade(col, 1.18)], 0.25)
    for i in range(16):
        top[0][i] = top[15][i] = top[i][0] = top[i][15] = edge
    for i in range(3, 13):
        top[3][i] = top[12][i] = top[i][3] = top[i][12] = col

    bottom = grid(base_dark)
    speckle(bottom, rng, [edge, col], 0.2)
    for i in range(16):
        bottom[0][i] = bottom[15][i] = bottom[i][0] = bottom[i][15] = edge
    return front, side, top, bottom


def to_image(g):
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), hx(g[y][x]) + (255,))
    return im


def chest_texture(col):
    """64x16 strip: front | side | top | bottom, matching models/entity/storage_chest.geo.json."""
    strip = Image.new("RGBA", (64, 16))
    for i, face in enumerate(faces(col)):
        strip.paste(to_image(face), (i * 16, 0))
    return strip


def icon(col):
    """16x16 inventory icon: a small isometric chest, lit from the top left."""
    front, side, top, _ = faces(col)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    # Each icon pixel looks up the face it falls on. The cube's corners: top (8,1), left (1,4)/(1,12),
    # right (15,4)/(15,12), centre (8,8) at the top and (8,15) at the bottom.
    for y in range(16):
        for x in range(16):
            dx = x - 7.5
            if abs(dx) > 7:
                continue
            top_edge = 1 + abs(dx) * 3.5 / 7      # upper outline of the diamond
            mid = 8 - abs(dx) * 3.5 / 7               # where the top face meets the sides
            bottom = 15 - abs(dx) * 3.5 / 7
            if y < top_edge or y > bottom:
                continue
            if y < mid:
                u = int(min(15, max(0, (x - 1) * 16 / 14)))
                v = int(min(15, max(0, (y - top_edge) / max(1, mid - top_edge) * 16)))
                c = shade(top[v][u], 1.0)
            else:
                v = int(min(15, max(0, (y - mid) / max(1, bottom - mid) * 16)))
                if dx < 0:
                    u = int(min(15, max(0, (x - 1) * 16 / 7)))
                    c = shade(front[v][u], 0.86)
                else:
                    u = int(min(15, max(0, (x - 8) * 16 / 7)))
                    c = shade(side[v][u], 0.66)
            px[x, y] = hx(c) + (255,)
    px[4, 9] = px[4, 10] = hx(LATCH) + (255,)  # the latch, on the front face
    px[5, 10] = hx(LATCH_DARK) + (255,)
    # dark outline so the icon reads on any slot background
    out = im.copy()
    opx = out.load()
    rim = hx(shade(col, 0.45)) + (255,)
    for y in range(16):
        for x in range(16):
            if px[x, y][3]:
                continue
            if any(0 <= x + a < 16 and 0 <= y + b < 16 and px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                opx[x, y] = rim
    return out


def guide_icon():
    """A brown book with a gold storage chest on the cover."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 1, 13, 14], fill=hx("#3a2414"))
    d.rectangle([3, 2, 12, 13], fill=hx("#7a4c2c"))
    d.rectangle([3, 2, 4, 13], fill=hx("#5a3820"))
    d.rectangle([12, 2, 13, 14], fill=hx("#ece4ce"))
    d.line([(12, 14), (13, 14)], fill=hx("#beb4a0"))
    # chest emblem
    d.rectangle([6, 6, 10, 10], fill=hx("#f2c12e"))
    d.line([(6, 8), (10, 8)], fill=hx("#9a7414"))
    d.point([(8, 8), (8, 9)], fill=hx(LATCH))
    d.rectangle([5, 5, 11, 11], outline=hx("#9a7414"))
    return im


def pack_icon():
    """Four dyed chests on a warm dark background."""
    W = 128
    im = Image.new("RGBA", (W, W), hx("#2a1d14") + (255,))
    d = ImageDraw.Draw(im)
    for y in range(W):
        t = y / W
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(hx("#3d2a1c"), hx("#140d08"))) + (255,))
    spots = [("yellow", 34, 6), ("blue", 70, 22), ("red", 4, 54), ("undyed", 40, 58)]
    lookup = dict(COLOURS)
    for name, x, y in spots:
        big = icon(lookup[name]).resize((80, 80), Image.NEAREST) if name == "undyed" else icon(lookup[name]).resize((56, 56), Image.NEAREST)
        im.alpha_composite(big, (x, y))
    return im


def main():
    (RP / "textures/entity/storage_chest").mkdir(parents=True, exist_ok=True)
    (RP / "textures/items").mkdir(parents=True, exist_ok=True)
    for name, col in COLOURS:
        chest_texture(col).save(RP / f"textures/entity/storage_chest/{name}.png")
        icon(col).save(RP / f"textures/items/stc_{name}_storage_chest.png")
    guide_icon().save(RP / "textures/items/stc_guide.png")
    for pack in (RP, BP):
        pack.mkdir(exist_ok=True)
        pack_icon().save(pack / "pack_icon.png")
    print(f"drew {len(COLOURS)} chest textures, {len(COLOURS) + 1} item icons and 2 pack icons")


if __name__ == "__main__":
    main()
