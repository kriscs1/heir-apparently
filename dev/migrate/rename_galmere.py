"""The kingdom of Ashen becomes Galmere (the owner's choice: "Galaith" and "Vorgalath" are in it), in what's shown and
said: the data, the scripts, the maps' words, the page, the server, the builders, the tests, the docs and every
language's catalogue (data/Lang: the line's English and its translation together, so neither loses the other).

The cult keeps its name, now it's no longer the kingdom's: the Ashen Hand, the Ashen Priest, his acolytes and
cultists, the Ashen Omens, the Ashen Foundry, its shrines and its codex. So does the game's title, Shards of Ashen
(till the owner names it), and so does every name in the game's workings: Ids (Staff_of_Ashen, Ashen_Order), script
names and attributes. The Staff of Ashen is shown as the Staff of Galmere (Display.Name) and its quest is The Staff of
Galmere (dsengine/renames.py RENAMED_QUESTS).

In the translations: アシェン is ガルミア, 애셴 is 갈미어, French d'Ashen is de Galmere, German Ashens is Galmeres, and
the two that said Ashen as a word of their own (the amulet's "Aschenen Thronfolge", "Succession Cendrée") say Galmere.

Safe to run again (a second run finds nothing to rename).
Usage: python -I dev/migrate/rename_galmere.py"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CULT = ("Hand", "Hand's", "Priest", "Priest's", "Acolyte", "Acolytes", "Cultist", "Cultists", "Omens", "Foundry",
        "Shrine", "Shrines", "Codex", "Sigil", "Seal", "Order", "Ledger")
KINGDOM = re.compile(r"(?<!\w)Ashen\b(?! (?:%s)\b)" % "|".join(re.escape(c) for c in CULT))
PROTECT = ("Shards of Ashen", "Shards Of Ashen", "rename_ashen.py: the kingdom is Ashen")
SKIP = ("dev/Archive/", "dev/Log.txt", "dev/Roadmap", "dev/QA ", "dev/Break Test", "dev/Code Issues", "web/assets/",
        "web/home/lang.js", "android/app/src/main/assets/home/lang.js", "data/Lang/", ".claude/")
TEXT = (".ini", ".txt", ".script", ".map", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".java")
WIDE = ("ja", "ko", "zh")
SAID = [(re.compile("アシェン"), "ガルミア"), (re.compile("애셴"), "갈미어"), (re.compile(r"\bd['’]Ashen\b"), "de Galmere"),
        (re.compile(r"\bAshens\b"), "Galmeres"), (re.compile(r"(?<!\w)Ashen\b"), "Galmere"),
        (re.compile("der Aschenen Thronfolge"), "der Thronfolge von Galmere"),
        (re.compile("de Succession Cendrée"), "de Succession de Galmere")]


def kingdom(s):
    keep = {}
    for i, p in enumerate(PROTECT):
        if p in s:
            keep["\x00%d\x00" % i] = p
            s = s.replace(p, "\x00%d\x00" % i)
    s = KINGDOM.sub("Galmere", s)
    for k, p in keep.items():
        s = s.replace(k, p)
    return s


def said(v):
    for p in PROTECT:
        v = v.replace(p, p.replace("Ashen", "\x00"))
    for pat, rep in SAID:
        v = pat.sub(rep, v)
    return v.replace("\x00", "Ashen")


def read(path):
    b = open(path, "rb").read()
    try:
        return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return b.decode("cp1252"), "cp1252"


def files():
    me = os.path.relpath(os.path.abspath(__file__), ROOT).replace("\\", "/")
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    for f in out:
        if f == me or f.startswith(SKIP) or os.path.basename(f).startswith("rename_") or not f.endswith(TEXT):
            continue
        yield f


def texts():
    n = 0
    for f in files():
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path):
            continue
        s, enc = read(path)
        t = kingdom(s)
        if f == "data/Entities.ini" and "Display.Name=Staff of Galmere" not in t:
            t = re.sub(r"(\[Staff_of_Ashen\]\r?\n)", lambda m: m.group(1) + "Display.Name=Staff of Galmere"
                       + ("\r\n" if m.group(1).endswith("\r\n") else "\n"), t, count=1)
        if t != s:
            open(path, "wb").write(t.encode(enc))
            n += 1
    return n


def catalogues():
    n = 0
    folder = os.path.join(ROOT, "data", "Lang")
    for name in sorted(os.listdir(folder)):
        code = name[:-4]
        if not name.endswith(".txt"):
            continue
        path = os.path.join(folder, name)
        enc = "utf-8" if code in WIDE else "cp1252"
        s = open(path, "rb").read().decode(enc)
        lines = s.split("\r\n")
        for i, line in enumerate(lines):
            if "\t" not in line:
                continue
            k, v = line.split("\t", 1)
            nk = kingdom(k)
            if nk != k:
                lines[i] = nk + "\t" + said(v)
        t = "\r\n".join(lines)
        if t != s:
            open(path, "wb").write(t.encode(enc))
            n += 1
    return n


def main():
    print("Galmere: %d files, %d catalogues" % (texts(), catalogues()))


if __name__ == "__main__":
    main()
