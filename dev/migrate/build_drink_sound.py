"""sounds\\ui\\Drink.wav: a drink going down - three gulps, each a low knock in the throat with the liquid's glug over it
(a bubble's note, rising as it closes), the last one slower. Played as you drink a potion, a draught, a cure or an ale
(the engine; the drink scripts' messages). Run it again to make it again.

  python -I "dev\\migrate\\build_drink_sound.py"      (then export_web_assets.py)
"""
import math
import os
import random
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import sound_file  # noqa: E402
RATE = 22050


def gulp(out, at, f0, rise, size, rng):
    """A gulp at `at` seconds: the throat's knock (a low thud) and the glug (a bubble's note rising f0 -> f0*rise)."""
    n = int(RATE * 0.16)
    i0 = int(RATE * at)
    ph_g = ph_k = 0.0
    for i in range(n):
        t = i / RATE
        f = f0 * (1 + (rise - 1) * min(1.0, t / 0.07))
        ph_g += 2 * math.pi * f / RATE
        ph_k += 2 * math.pi * (95 - 180 * t) / RATE
        glug = math.sin(ph_g) * min(1.0, t / 0.006) * math.exp(-t / 0.035)
        knock = math.sin(ph_k) * min(1.0, t / 0.004) * math.exp(-t / 0.045)
        wet = (rng.random() * 2 - 1) * math.exp(-t / 0.012) * 0.08      # (the click of it starting)
        out[i0 + i] += size * (0.55 * glug + 0.6 * knock + wet)


def main():
    rng = random.Random(3)
    secs = 0.95
    out = [0.0] * int(RATE * secs)
    for at, f0, rise, size in ((0.02, 340, 1.9, 0.9), (0.27, 310, 2.0, 0.85), (0.56, 280, 2.2, 1.0)):
        gulp(out, at, f0, rise, size, rng)
    smooth, k = [], 0.0
    for v in out:                                       # (a soft low-pass: wet and muffled, never a clean tone)
        k += (v - k) * 0.45
        smooth.append(k)
    peak = max(abs(v) for v in smooth) or 1
    path = sound_file("Drink")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(v / peak * 0.8 * 30000)) for v in smooth))
    print("Made " + os.path.relpath(path, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


if __name__ == "__main__":
    main()
