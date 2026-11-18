"""Other languages: data/Lang/<code>.txt, each line English, a tab, then the same in that language (tools/lang.py
lists what's missing and fills them in). The browser translates what it draws itself (its words, the names, the
engine's messages: web/js/util.js coined); the server translates what only it can, before a script's $variables
are filled in: the scripts' words and the quests' stages and notes. English is the key: a line not there yet is
said in English."""
import os
import time

LANG_DIR = ("data", "Lang")
RECHECK = 3.0                                   # (seconds between looks at a catalogue for changes)


def read_catalogue(path, areas=None):
    """{English: translation} from one language's file (areas: only those [sections]), and its Name=."""
    words, name, area = {}, "", ""
    with open(path, encoding="cp1252", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or line[0] == ";":
                continue
            if line[0] == "[" and line.endswith("]") and "\t" not in line:
                area = line[1:-1].strip().upper()
                continue
            if "\t" not in line:
                if area == "LANGUAGE" and line[:5].lower() == "name=":
                    name = line[5:].strip()
                continue
            if areas is not None and area not in areas:
                continue
            en, _, said = line.partition("\t")
            if en and said:
                words[en] = said
    return words, name


class Languages:
    def __init__(self, root):
        self.folder = os.path.join(root, *LANG_DIR)
        self._cats = {}                         # code -> [words, mtime, last looked]

    def codes(self):
        """Every language there's a catalogue for (en is always there: it's the game's own)."""
        try:
            files = os.listdir(self.folder)
        except OSError:
            return ["en"]
        return ["en"] + sorted(f[:-4].lower() for f in files if f.lower().endswith(".txt") and len(f) <= 9)

    def known(self, code):
        code = str(code or "").lower()[:5]
        return code if code in self.codes() else "en"

    def words(self, code):
        if not code or code == "en":
            return None
        cat = self._cats.get(code)
        now = time.monotonic()
        if cat is not None and now - cat[2] < RECHECK:
            return cat[0]
        path = os.path.join(self.folder, code + ".txt")
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            self._cats[code] = [None, 0, now]
            return None
        if cat is None or cat[1] != mtime:
            cat = self._cats[code] = [read_catalogue(path)[0], mtime, now]
        cat[2] = now
        return cat[0]

    def say(self, code, text):
        """text in the language code, if the catalogue has it; else as it is."""
        words = self.words(code)
        if not words or not text:
            return text
        return words.get(text, text)

    def say_answer(self, code, text):
        """A conversation's answer: its words translated, its [if CONDITION] kept as it is."""
        words = self.words(code)
        if not words or not text:
            return text
        t = text.strip()
        p = t.lower().rfind("[if ")
        if p >= 0 and t.endswith("]"):
            head = t[:p].rstrip()
            return words.get(head, head) + " " + t[p:]
        return words.get(t, t)
