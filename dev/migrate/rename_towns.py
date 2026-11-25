"""The towns get names that fit the game's comedy (the owner's choice: a little funny, not too obviously so, and a few
kept plain), and the Isle gets a name of its own, Muddlesey.

  Northport -> Drizzleport     Ashford -> Puddleford      Frosthold -> Chillingham    Wardhaven -> Sulkhaven
  Oakhollow -> Acornby         Thornwick -> Nettlewick    Greyford -> Dullford       Saltmarsh -> Brinebottom
  Highwatch -> Squintwatch     Ravensgate -> Crowgate (the town long gone; its mark is a crow now)
  the Isle -> Muddlesey (what's said: the Isle's Ids, Isle_Bank and the rest, keep their names)
Kept: Galaith, King Rupert's Keep, the Wizards' Court, Fenwick, Emberwatch, Wildwood and Dunerest.

Every place Id, thing's Id, script (and its file's name), label, shardstone and word that said a town says the new name
(the lowercase names in the builders' own workings and the music's file names stay). In every language's catalogue the
line's English and its translation change together: the Latin-lettered names in each, and in Japanese and Korean the
names as written there (Korean's particles after a name ending in a consonant put right). The translations give Muddlesey its
name too (Muddlesey, マドルジー, 머들지) where the English says it.
Characters saved before keep what they had: an attribute named for an old name (Waystone.Northport, Secret_Ashford) is
read under the new one as they load (dsengine/renames.py RENAMED_WORDS).
Safe to run again (a second run finds nothing to rename).
Usage: python -I dev/migrate/rename_towns.py"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOWNS = {"Northport": "Drizzleport", "Ashford": "Puddleford", "Frosthold": "Chillingham", "Wardhaven": "Sulkhaven",
         "Oakhollow": "Acornby", "Thornwick": "Nettlewick", "Greyford": "Dullford", "Saltmarsh": "Brinebottom",
         "Highwatch": "Squintwatch", "Ravensgate": "Crowgate"}
JA = {"ノースポート": "ドリズルポート", "アシュフォード": "パドルフォード", "フロストホールド": "チリンガム",
      "ウォードヘイヴン": "サルクヘイヴン", "オークホロウ": "エイコーンビー", "ソーンウィック": "ネトルウィック",
      "グレイフォード": "ダルフォード", "ソルトマーシュ": "ブラインボトム", "ハイウォッチ": "スクイントウォッチ",
      "レイヴンズゲート": "クロウゲート"}
KO = {"노스포트": "드리즐포트", "애시퍼드": "퍼들퍼드", "프로스트홀드": "칠링엄", "워드헤이븐": "설크헤이븐",
      "오크할로": "에이콘비", "손윅": "네틀윅", "그레이퍼드": "덜퍼드", "솔트마시": "브라인보텀",
      "하이워치": "스퀸트워치", "레이븐스게이트": "크로게이트"}
KO_PARTICLES = (("를", "을"), ("는", "은"), ("가", "이"), ("로", "으로"), ("와", "과"), ("야", "이야"), ("여", "이여"))
ISLE = [("A raven is carved where a name should be", "A crow is carved where a name should be"),
        ("the Isle's", "Muddlesey's"), ("The Isle's", "Muddlesey's"), ("THE ISLE", "MUDDLESEY"),
        ("the Isle", "Muddlesey"), ("The Isle", "Muddlesey")]
ISLE_NAME = {"ja": "マドルジー", "ko": "머들지"}
SKIP = ("dev/Archive/", "dev/Log.txt", "dev/Roadmap", "dev/QA ", "dev/Break Test", "dev/Code Issues", "web/assets/",
        ".claude/", "dev/migrate/generated.json", "data/Lang/", "CREDITS.md")
TEXT = (".ini", ".txt", ".script", ".map", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".java")
WIDE = ("ja", "ko", "zh")


def english(s):
    for old, new in ISLE:
        s = re.sub(r"(?<!\w)%s(?!\w)" % re.escape(old), new, s)
    for old, new in TOWNS.items():
        s = re.sub(r"(?<![A-Za-z])%s(?![a-z])" % old, new, s)        # (Secret_Ashford_2 too)
        s = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % old.upper(), new.upper(), s)
    return s


def said(v, code):
    for old, new in TOWNS.items():
        v = re.sub(r"(?<![A-Za-z])%s(?![a-z])" % old, new, v)
        v = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % old.upper(), new.upper(), v)     # (the signposts)
    if code == "fr":                                    # (Ashford's d' before the new names' consonants)
        v = re.sub(r"d'(%s)" % "|".join(n for n in TOWNS.values() if n != "Acornby"), r"de ", v)
    if code == "ja":
        for old, new in JA.items():
            v = v.replace(old, new)
    if code == "ko":
        for old, new in KO.items():
            v = v.replace(old, new)
        for name in ("칠링엄", "브라인보텀"):           # (they end in a consonant)
            for a, b in KO_PARTICLES:
                v = v.replace(name + a, name + b)
    return v


def read(path):
    b = open(path, "rb").read()
    try:
        return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return b.decode("cp1252"), "cp1252"


def files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    for f in out:
        base = os.path.basename(f)
        if f.startswith(SKIP) or base.startswith("rename_") or base == "renames.py" or not f.endswith(TEXT):
            continue
        yield f


def texts():
    n = 0
    for f in files():
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path):
            continue
        s, enc = read(path)
        t = english(s)
        if t != s:
            open(path, "wb").write(t.encode(enc))
            n += 1
    return n


def catalogues():
    n = 0
    folder = os.path.join(ROOT, "data", "Lang")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".txt"):
            continue
        code = name[:-4]
        path = os.path.join(folder, name)
        enc = "utf-8" if code in WIDE else "cp1252"
        s = open(path, "rb").read().decode(enc)
        lines = s.split("\r\n")
        for i, line in enumerate(lines):
            if "\t" not in line:
                continue
            k, v = line.split("\t", 1)
            nk = english(k)
            if nk != k:
                nv = ISLE_NAME.get(code, "Muddlesey") if nk == "Muddlesey" else said(v, code)
                lines[i] = nk + "\t" + nv
        t = "\r\n".join(lines)
        if t != s:
            open(path, "wb").write(t.encode(enc))
            n += 1
    return n


def scripts():
    moved = 0
    folder = os.path.join(ROOT, "data", "Scripts")
    for f in sorted(os.listdir(folder)):
        new = english(f)
        if new != f:
            src, dst = os.path.join(folder, f), os.path.join(folder, new)
            if os.path.exists(dst):
                os.remove(src)
            elif subprocess.run(["git", "mv", src, dst], cwd=ROOT, capture_output=True).returncode:
                os.rename(src, dst)
            moved += 1
    return moved


def main():
    print("Towns: %d files, %d catalogues, %d scripts renamed" % (texts(), catalogues(), scripts()))


if __name__ == "__main__":
    main()
