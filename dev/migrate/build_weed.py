"""The weed: a see-through clump on any ground, like the flowers and the long grass (the owner's wish: it was an old ground
tile with its own grass painted round it, a square that didn't match the grass about it).

  * THE PICTURE (sprites\\Tiles\\Weed001): a low clump of broad, ragged dock leaves fanned out from a dark heart, lit
    up and to the left, drawn with build_herbs' leaf().
  * TILES.INI [Weed001]: Layer=Decor (no Blend: the ground under it blends), seen past, slows you a little and sways.
  * THE MAPS: every Weed001 laid as ground becomes Grass001+Decor(Weed001) (one that already had decor is left).

Run it again to draw it again.

  python -I "dev\\migrate\\build_weed.py"      (then validate.py, export_web_assets.py and build_minimaps.py)
"""
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import build_herbs as H  # noqa: E402
import sprite_kit as K  # noqa: E402
import story_kit  # noqa: E402

TILES = os.path.join(ROOT, "data", "Tiles.ini")
LEAF = ((118, 176, 70), (66, 128, 44), (34, 78, 28))       # (light, mid, dark: a deeper green than the herbs)
RIB = (96, 150, 58)


def weed():
    img = K.new()
    rng = random.Random(7)
    leaves = [(-1.95, 12), (-1.2, 12), (-2.55, 13), (-0.6, 13), (-3.0, 11), (-0.15, 11), (-1.6, 10)]
    edge = K.mul(LEAF[2], 0.75)
    for ang, ln in leaves:                              # (back leaves first: the ones further round sit over them)
        ang += rng.uniform(-0.08, 0.08)
        H.leaf(img, 16, 22, ang, ln + 0.8, 2.9, edge, edge, edge)      # (its dark edge: each leaf reads as one)
        H.leaf(img, 16, 22, ang, ln, 2.2, *LEAF, rib=RIB)
    for _ in range(14):                                 # (ragged edges: a nibble out here and there)
        x, y = rng.randrange(4, 28), rng.randrange(8, 24)
        if img[y][x] is not None and (img[y][x - 1] is None or img[y][x + 1] is None):
            img[y][x] = None
    for x in range(12, 21):                             # (the heart of the clump, dark against the ground)
        K.put(img, x, 22, LEAF[2])
        if 13 < x < 19:
            K.put(img, x, 23, K.mul(LEAF[2], 0.8))
    return K.outline_img(img, (22, 48, 18))


def tiles_ini():
    story_kit.set_section(TILES, "Weed001", [
        "Walkable.Data=" + "1" * 49, "Show.Name=0", "Use.Words=", "Examine.Info=A clump of dock leaves.",
        "Line.of.Sight=1", "Walk.Speed=0.85", "Layer=Decor", "Sway=1.6"])


def maps():
    n = 0
    for folder, _, names in os.walk(os.path.join(ROOT, "maps")):
        for f in names:
            if not re.fullmatch(r"-?\d+,-?\d+,-?\d+\.map", f):
                continue
            path = os.path.join(folder, f)
            text = open(path, "rb").read().decode("cp1252")
            lines = text.split("\r\n")
            out = []
            for ln in lines:
                cells = ln.split(":")
                for i, c in enumerate(cells):
                    parts = c.split("+")
                    if parts[0] == "Weed001" and not any(p.startswith("Decor(") for p in parts[1:]):
                        cells[i] = "+".join(["Grass001", "Decor(Weed001)"] + parts[1:])
                        n += 1
                out.append(":".join(cells))
            new = "\r\n".join(out)
            if new != text:
                open(path, "wb").write(new.encode("cp1252"))
    return n


def main():
    if K.save("Tiles", "Weed001", weed()):
        print("Drew Weed001")
    tiles_ini()
    n = maps()
    print("%d weed%s laid as ground put on grass" % (n, "" if n == 1 else "s"))


if __name__ == "__main__":
    main()
