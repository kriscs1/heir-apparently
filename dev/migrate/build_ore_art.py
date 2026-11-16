"""The ores and the bars (the owner's wish: the old pictures weren't ours to use). Each ore a lump or two of broken
rock (rock_art.py's chipped faces) with its ore showing in nuggets, coal a black lump with a sheen; each bar an ingot
seen from above and in front, its top lit, its sloping front in half light, its ends in shade, a maker's mark
stamped in the top. All see-through, with the 1 px dark outline (build_wolf.py's way), sitting on the same line.

Safe to run again.

  python -I "dev\\migrate\\build_ore_art.py" [--preview]
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rock_art                                  # noqa: E402
import sprite_kit as K                           # noqa: E402
from common import p                             # noqa: E402

S = 32
OUTLINE = (30, 26, 24)
ROCK = ((146, 140, 132), (110, 104, 98), (70, 66, 62))             # lit, mid, dark
# ore: (its colours: base, light, dark), the rock it's in (None: grey), how many nuggets
ORES = {
    "Iron_Ore": (((178, 100, 52), (220, 146, 86), (124, 62, 32)), ((136, 116, 104), (102, 86, 78), (64, 54, 50)), 9),
    "Copper_Ore": (((64, 168, 126), (130, 226, 176), (196, 112, 60)), None, 12),
    "Tin_Ore": (((190, 196, 190), (236, 240, 234), (120, 126, 122)), ((128, 122, 114), (96, 90, 84), (60, 56, 52)), 8),
    "Gold_Ore": (((226, 184, 50), (255, 238, 136), (150, 110, 20)), None, 8),
    "Silver_Ore": (((214, 220, 232), (255, 255, 255), (130, 138, 156)), ((118, 112, 108), (86, 82, 80), (52, 48, 46)), 8),
    "Mithril_Ore": (((56, 170, 176), (150, 240, 236), (26, 92, 120)), ((100, 100, 122), (70, 70, 88), (40, 40, 54)), 9),
}
COAL = ((84, 84, 92), (44, 44, 50), (20, 20, 24))
# bar: (lit top, mid front, shade, shine)
BARS = {
    "Iron_Bar": ((132, 134, 140), (96, 98, 104), (60, 62, 68), (176, 178, 184)),
    "Copper_Bar": ((226, 140, 88), (184, 98, 56), (120, 58, 32), (252, 196, 150)),
    "Bronze_Bar": ((212, 160, 84), (168, 118, 56), (106, 70, 32), (244, 212, 140)),
    "Steel_Bar": ((196, 206, 216), (150, 162, 176), (92, 102, 116), (236, 242, 248)),
    "Gold_Bar": ((250, 214, 90), (218, 166, 40), (144, 100, 18), (255, 246, 190)),
    "Silver_Bar": ((228, 232, 240), (180, 186, 198), (116, 122, 138), (255, 255, 255)),
    "Mithril_Bar": ((112, 214, 222), (56, 164, 180), (24, 92, 116), (200, 252, 250)),
}


def lump(img, rng, cx, cy, rx, ry, cols, faces=5):
    """A chipped lump of rock drawn on img (None = see-through); returns the pixels that are the lump."""
    lit, mid, dark = cols
    canvas = [[(0, 0, 0)] * S for _ in range(S)]
    marks = {}
    rock_art.faceted_rock(canvas, rng, cx, cy, rx, ry, lit, mid, dark, K.mul(dark, 0.7), faces=faces, marks=marks)
    mine = [xy for xy, what in marks.items() if what == "rock"]
    for x, y in mine:
        img[y][x] = canvas[y][x]
    return mine


def ore(name, seed):
    (fb, fl, fd), rock, count = ORES[name]
    rng = random.Random(seed)
    img = K.new()
    rock = rock or ROCK
    spots = lump(img, rng, 14, 18, 9, 8.5, rock, faces=7) + lump(img, rng, 23.5, 21.5, 5.5, 5, rock, faces=3)
    spots = set(spots)
    n = 0
    while n < count:                                       # (the ore: angular nuggets, kept in from the edge)
        x, y = rng.choice(sorted(spots))
        if not all((x + a, y + c) in spots for a in (-1, 0, 1) for c in (-1, 0, 1)):
            continue
        img[y][x] = fb
        K.put(img, x + 1, y, fd)
        if rng.random() < 0.7:
            K.put(img, x, y - 1, fl)
        if rng.random() < 0.5:
            K.put(img, x - 1, y, fb)
        n += 1
    return finish(img)


def coal(seed=731):
    rng = random.Random(seed)
    img = K.new()
    spots = lump(img, rng, 14, 18, 9, 8.5, COAL, faces=7) + lump(img, rng, 23.5, 21.5, 5.5, 5, COAL, faces=3)
    for _ in range(6):                                     # (its sheen: a glint on a few faces)
        x, y = rng.choice(spots)
        if y < 19:
            img[y][x] = (150, 152, 168)
    return finish(img)


def bar(name):
    top, mid, shade, shine = BARS[name]
    img = K.new()
    rng = random.Random(sum(map(ord, name)))
    for y in range(11, 16):                                # (its top: flat and lit)
        for x in range(9, 24):
            img[y][x] = K.jitter(top, rng, 3)
    for x in range(10, 23):
        img[12][x] = shine                                 # (the light along it)
    for y in range(16, 23):                                # (its front, sloping out to the foot)
        k = (y - 15) * 0.5
        x0, x1 = int(round(9 - k)), int(round(23 + k))
        for x in range(x0, x1 + 1):
            img[y][x] = K.jitter(mid, rng, 3)
        img[y][x1] = shade                                 # (the right end, in shade)
        K.put(img, x1 - 1, y, K.mix(mid, shade, 0.5))
        img[y][x0] = K.mix(top, mid, 0.5)                  # (the left end, catching the light)
    for x in range(9, 24):
        img[15][x] = K.mix(top, shade, 0.35)               # (the edge between top and front)
    for x in range(int(round(9 - 3.5)), int(round(23 + 3.5)) + 1):
        img[22][x] = shade                                 # (its foot)
    for x, y in ((15, 13), (16, 13), (17, 13), (16, 14)):  # (the maker's mark, stamped in)
        img[y][x] = K.mix(top, shade, 0.6)
    return finish(img)


def finish(img):
    return K.outline_img(img, OUTLINE)


def pictures():
    made = {name: ore(name, 700 + i * 7) for i, name in enumerate(ORES)}
    made["Coal"] = coal()
    made.update({name: bar(name) for name in BARS})
    return made


def main():
    made = pictures()
    for name, img in made.items():
        print(("wrote " if K.save("Entities", name, img) else "unchanged ") + name)
    if "--preview" in sys.argv:
        K.sheet(p("dev", "Renders", "Ores and bars.png"), list(made.values()), scale=4, cols=7)


if __name__ == "__main__":
    main()
