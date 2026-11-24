"""The kingdom of Galmere becomes Brambleton (the owner's choice), wherever it's shown or said: the data, the scripts,
the maps' words, the page, the server, the builders, the tests, the docs and every language's catalogue (both sides of
each line). It takes over from rename_galmere.py, which now refuses to run.

The game's workings keep their names (Staff_of_Ashen and the rest); the Staff is shown as the Staff of Brambleton and
its quest is The Staff of Brambleton (dsengine/renames.py RENAMED_QUESTS). In the translations: ガルミア is
ブランブルトン, 갈미어 is 브램블턴 (it ends in a consonant, so it takes 을/은/이: the lines that had 을/은 after 갈미어
were wrong before and are right now), German Galmeres is Brambletons, and Chinese keeps names in Latin letters.

Safe to run again (a second run finds nothing to rename).
Usage: python -I dev/migrate/rename_brambleton.py"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP = ("dev/Archive/", "dev/Log.txt", "dev/Roadmap", "dev/QA ", "dev/Break Test", "dev/Code Issues", "web/assets/",
        ".claude/")
TEXT = (".ini", ".txt", ".script", ".map", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".java")
SAID = [(re.compile(r"\bGalmeres\b"), "Brambletons"), (re.compile(r"\bGalmere\b"), "Brambleton"),
        (re.compile("ガルミア"), "ブランブルトン"), (re.compile("갈미어를"), "브램블턴을"),
        (re.compile("갈미어는"), "브램블턴은"), (re.compile("갈미어가"), "브램블턴이"),
        (re.compile("갈미어로"), "브램블턴으로"), (re.compile("갈미어와"), "브램블턴과"), (re.compile("갈미어"), "브램블턴")]


def said(s):
    for pat, rep in SAID:
        s = pat.sub(rep, s)
    return s


def read(path):
    b = open(path, "rb").read()
    try:
        return b.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return b.decode("cp1252"), "cp1252"


def files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    for f in out:
        if f.startswith(SKIP) or os.path.basename(f).startswith("rename_") or not f.endswith(TEXT):
            continue
        yield f


def main():
    n = 0
    for f in files():
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path):
            continue
        s, enc = read(path)
        t = said(s)
        if t != s:
            open(path, "wb").write(t.encode(enc))
            n += 1
    print("Brambleton: %d files" % n)


if __name__ == "__main__":
    main()
