"""Other languages: every word the game shows, gathered from where it's written, and each language's catalogue of them
(data/Lang/<code>.txt: English, a tab, the same in that language; cp1252, CRLF).

  python -I tools/lang.py                        how much of each language there is, and what's missing
  python -I tools/lang.py todo es OUT [N]        up to N (300) English lines es hasn't got, one a line, into OUT
  python -I tools/lang.py fill es OUT ANSWERS    ANSWERS: the same lines in Spanish, line for line with OUT
  python -I tools/lang.py export                 web/assets/lang/<code>.json and web/home/lang.js (the pages')
  python -I tools/lang.py check                  every catalogue line keeps its holes ({1}, $Player.Name, | and ..)

Who says what: the server says the scripts' words and the quests' stages in the player's language before their
$variables are filled in (dsengine/lang.py); the game page says everything else as it draws it (web/home/translate.js:
names, hover lines, the engine's messages with {1} where something goes in, and its own words); the start screen its
own (lang.js). A line in English is a line not translated yet. In a translation "12 gold" stays so: it's the coin."""
import ast
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dsengine.lang import read_catalogue  # noqa: E402
from dsengine.scripting import SAID_ARGS  # noqa: E402

LANG = os.path.join(ROOT, "data", "Lang")
NAMES = {"es": "Español", "de": "Deutsch", "fr": "Français", "pt": "Português (Brasil)"}
AREAS = ("SCRIPTS", "QUESTS", "DATA", "ENGINE", "PAGE", "HOME")
GAME_AREAS = ("DATA", "ENGINE", "PAGE")         # (the game page's catalogue; SCRIPTS and QUESTS are the server's)
HOLE = re.compile(r"\{\d+\}|\$[A-Za-z]+\.[A-Za-z0-9_.()']*[A-Za-z0-9_)](?<!'s)")    # (not an English "'s" after it)
# (a translation may say a plural its own way: {3:/n} is "" for one and "n" for more, where English put {3} = "s")
PLURAL = re.compile(r"\{(\d+):[^{}/]*/[^{}]*\}")
PARA = "¶"                                 # (a line break inside a line, as the catalogue writes it)


# =====================================================================================================================
# What's said: a line is kept if it reads like words, not a name in the code
# =====================================================================================================================
def said_like(s):
    if not s or "\t" in s or len(s) > 2000:
        return False
    bare = HOLE.sub(" ", s)
    words = re.findall(r"[A-Za-z][A-Za-z']*", bare)
    if not words or max(len(w) for w in words) < 2:
        return False
    if re.search(r"[_\\{}<>;]|=>|==|&&|\|\||https?:|www\.|\.(js|png|jpg|wav|ogg|json|ini|map|script|html|css|py)\b", bare):
        return False
    if re.search(r"\d(px|em|ms|s)\b|rgba?\(|^#|^\.|^--|\bvar\(|[a-z]\(|\.\{\d|\(pointer|frame-ancestors", s):
        return False
    if re.match(r"(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|PRAGMA|WITH|REPLACE)\b", s) or " FROM " in s:
        return False                            # (SQL)
    if re.search(r"\bNOT NULL\b|\bDEFAULT \d|\bORDER BY\b|max-age=|^use strict$|^[A-Z]+(, [A-Z]+)+$|^\{\d\}/|"
                 r"\ballow-[a-z]|^openid |prefers-|any-pointer|\}px\b|Palatino", s) or s in ("Bearer", "Lax", "Strict"):
        return False                            # (a column, a header, a cookie's or a frame's setting)
    t = bare.strip()
    if " " not in t:
        if not re.fullmatch(r"[A-Z][a-z']+(-[a-z']+)?[.!?:]*", t) and not re.fullmatch(r"[A-Z][a-z']*\.{2,3}", t):
            return False                        # (one word: Options, Close; not KeyW, SUCCESS, fontSize)
    elif len(words) == 2 and all(w.isupper() for w in words):
        return False
    try:
        s.encode("cp1252")
    except UnicodeEncodeError:
        return False
    return True


def holes_numbered(s):
    """'\\0' marks from the code -> {1}, {2}..."""
    n = 0
    out = []
    for part in s.split("\0"):
        out.append(part)
        n += 1
        out.append("{%d}" % n)
    return "".join(out[:-1])


def tidy(s):
    return re.sub(r"\s+", " ", s).strip()


# =====================================================================================================================
# Gathering: area -> [English], each once, in the order found
# =====================================================================================================================
class Gathered:
    def __init__(self):
        self.areas = {a: [] for a in AREAS}
        self.seen = {a: set() for a in AREAS}

    def add(self, area, s, raw=False):
        s = s if raw else tidy(s)
        ok = re.search(r"[A-Za-z]{2}", s or "") if raw else said_like(s)     # (a script's line is all words)
        if s and s not in self.seen[area] and ok:
            self.seen[area].add(s)
            self.areas[area].append(s)

    def all(self):
        """[(area, English)], each English once (filed under the first area it's in)."""
        done, out = set(), []
        for a in AREAS:
            for s in self.areas[a]:
                if s not in done:
                    done.add(s)
                    out.append((a, s))
        return out

    def of(self, areas):
        return {s for a in areas for s in self.areas[a]}


def read_ini(path):
    """[(section, [(key, value)])] with comments off."""
    out, cur = [], None
    with open(path, encoding="cp1252", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            st = line.strip()
            if not st or st[0] == ";":
                continue
            if st[0] == "[" and st.endswith("]"):
                cur = (st[1:-1], [])
                out.append(cur)
                continue
            if "=" in line and cur is not None:
                k, v = line.split("=", 1)
                p = v.find("  ;")
                cur[1].append((k.strip(), (v[:p] if p >= 0 else v).strip()))
    return out


def pretty(name):
    n = re.sub(r"\d{3}$", "", name) if len(name) > 3 else name
    return n.replace("_", " ")


def gather_scripts(g):
    folder = os.path.join(ROOT, "data", "Scripts")
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".script"):
            continue
        with open(os.path.join(folder, f), encoding="cp1252", errors="replace") as fh:
            for line in fh:
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) < 3:
                    continue
                cmd = parts[1].strip()
                args = parts[2:]
                if cmd in ("Quest.Note", "Quest.Note.Done") and len(args) > 1 and args[1].strip() != "*":
                    g.add("SCRIPTS", args[1].strip(), raw=True)
                for i in SAID_ARGS.get(cmd, ()):
                    if i - 1 < len(args):
                        a = args[i - 1].strip()
                        if cmd == "Display.Conversation" and i > 2:
                            a = re.sub(r"\s*\[if .*\]$", "", a, flags=re.I)
                        g.add("SCRIPTS", a, raw=True)


TEXT_KEYS = re.compile(r"^(Examine\.Info|Hover\.Info|Display\.Name|Name|Title|What|Taught\.Words|Whisper\.\d+|Words|"
                       r"Caught|Cured|Message|Start\.Message|Win\.Message|Lose\.Message|Refused(\.\d+)?|Rumour(\.\d+)?|"
                       r"Hint(\.\w+)?|Where|Trains|Says|Freeze\.Word|Welcome|Stranger|Trusted|Outlaw|Raid|Warn)$", re.I)
NAME_SECTIONS = ("Entities.ini", "Tiles.ini", "Quests.ini", "Spells.ini", "Skills.ini", "Diseases.ini", "Waves.ini")


def gather_data(g):
    data = os.path.join(ROOT, "data")
    for f in sorted(os.listdir(data)):
        if not f.endswith(".ini") or f == "TileSets.ini":     # (the editor's)
            continue
        for section, pairs in read_ini(os.path.join(data, f)):
            d = dict(pairs)
            if f in NAME_SECTIONS:
                g.add("DATA", d.get("Display.Name") or pretty(section))
            if f == "WorldMap.ini":
                for k, _ in pairs:
                    g.add("DATA", k)
            for k, v in pairs:
                if f == "Quests.ini" and re.fullmatch(r"(Stage|Ending)\d+", k, re.I):
                    g.add("QUESTS", v, raw=True)
                elif k == "Use.Words":
                    for w in v.split(","):
                        g.add("DATA", w)
                elif k == "Hover.Info":
                    for part in v.split("|"):
                        g.add("DATA", part)
                elif f == "Banter.ini" and re.fullmatch(r"Line\d+", k):
                    g.add("DATA", re.sub(r"^[A-Z]:", "", v))
                elif f == "Legend.ini":
                    g.add("DATA", v.split("|", 1)[-1])
                elif f == "Encounters.ini" and k in ("Say", "Goodbye", "Message"):
                    for part in v.split("|"):
                        g.add("DATA", part)
                elif f == "Carts.ini" and re.fullmatch(r"Point\d+", k):
                    g.add("DATA", v.split(",")[-1])
                elif TEXT_KEYS.match(k):
                    g.add("DATA", v)


# ----- Python: the engine's and the server's own words
LOGS = {"log", "debug", "info", "warning", "error", "exception", "critical", "print", "log_line", "warn", "err"}


def py_strings(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                skip.add(id(first.value))       # (docstrings)
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
            if name in LOGS:
                for a in ast.walk(node):
                    skip.add(id(a))
        if isinstance(node, ast.Raise):
            for a in ast.walk(node):
                skip.add(id(a))
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if k is not None:
                    skip.add(id(k))
        if isinstance(node, ast.Subscript):
            skip.add(id(node.slice))

    def text_of(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            out = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    out.append(str(v.value))
                else:
                    out.append("\0")
            return "".join(out)
        return None

    for node in ast.walk(tree):
        if id(node) in skip:
            continue
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            s = text_of(node.left)
            if s is not None:
                skip.add(id(node.left))
                yield re.sub(r"%[-+ #0]*\d*(\.\d+)?[sdifr]", "\0", s).replace("%%", "%")
            continue
        if isinstance(node, ast.JoinedStr):
            for v in node.values:
                skip.add(id(v))
        s = text_of(node)
        if s is not None:
            yield s


def gather_python(g, area, folders):
    for folder in folders:
        base = os.path.join(ROOT, folder)
        for f in sorted(os.listdir(base)):
            if f.endswith(".py"):
                for s in py_strings(os.path.join(base, f)):
                    if "\n" not in s.strip():
                        g.add(area, holes_numbered(tidy(s)))


# ----- JavaScript and HTML: the pages' words
REGEX_AFTER = set("(,=:[!&|?{};+-*%<>~^") | {"", "kw"}
KEYWORDS = {"return", "typeof", "case", "in", "of", "new", "delete", "void", "throw", "else", "do", "yield", "await"}
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def js_strings(src):
    """Every string in JavaScript: quoted ones as they are, templates with \\0 where ${...} goes."""
    out, n = [], len(src)

    def unescape(i, quote):
        buf = []
        while i < n and src[i] != quote:
            c = src[i]
            if c == "\\" and i + 1 < n:
                e = src[i + 1]
                if e == "u" and src[i + 2:i + 3] == "{":
                    j = src.index("}", i)
                    buf.append(chr(int(src[i + 3:j], 16)))
                    i = j + 1
                    continue
                if e == "u":
                    buf.append(chr(int(src[i + 2:i + 6], 16)))
                    i += 6
                    continue
                if e == "x":
                    buf.append(chr(int(src[i + 2:i + 4], 16)))
                    i += 4
                    continue
                buf.append(ESCAPES.get(e, "" if e == "\n" else e))
                i += 2
                continue
            if quote == "`" and src.startswith("${", i):
                buf.append("\0")
                i = scan(i + 2, True)
                continue
            if c == "\n" and quote != "`":
                break
            buf.append(c)
            i += 1
        out.append("".join(buf))
        return i + 1

    def scan(i, inner):
        depth, prev = 0, ""
        while i < n:
            c = src[i]
            if c in " \t\r\n":
                i += 1
                continue
            if src.startswith("//", i):
                j = src.find("\n", i)
                i = n if j < 0 else j
                continue
            if src.startswith("/*", i):
                j = src.find("*/", i + 2)
                i = n if j < 0 else j + 2
                continue
            if c in "'\"`":
                i = unescape(i + 1, c)
                prev = "a"
                continue
            if c == "/" and prev in REGEX_AFTER:
                i += 1
                klass = False
                while i < n and src[i] != "\n":
                    if src[i] == "\\":
                        i += 2
                        continue
                    if src[i] == "[":
                        klass = True
                    elif src[i] == "]":
                        klass = False
                    elif src[i] == "/" and not klass:
                        break
                    i += 1
                i += 1
                prev = "a"
                continue
            if inner and c == "{":
                depth += 1
            elif inner and c == "}":
                if depth == 0:
                    return i + 1
                depth -= 1
            if c.isalnum() or c in "_$":
                j = i
                while j < n and (src[j].isalnum() or src[j] in "_$"):
                    j += 1
                prev = "kw" if src[i:j] in KEYWORDS else "a"
                i = j
                continue
            prev = c if c not in ")]" else "a"
            i += 1
        return i

    scan(0, False)
    return out


TAG = re.compile(r"<[^<>]*>")
ATTR = re.compile(r"""\b(?:title|placeholder|aria-label|alt)=["']([^"'\0]*)["']""")


def page_pieces(s):
    """The bits of a string the page shows apart: the words between its tags, and its titles."""
    for m in ATTR.finditer(s):
        yield m.group(1)
    for part in TAG.split(s):
        yield holes_numbered(html.unescape(part))


def gather_js(g, area, paths):
    for path in paths:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if path.endswith(".html"):
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", src, flags=re.S)
            page = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<!--.*?-->", "", src, flags=re.S)
            for piece in page_pieces(page):
                g.add(area, piece)
            for s in scripts:
                for lit in js_strings(s):
                    for piece in page_pieces(lit):
                        g.add(area, piece)
        else:
            for lit in js_strings(src):
                for piece in page_pieces(lit):
                    g.add(area, piece)
                    for line in piece.split("\n"):   # (the page's own lines, drawn apart)
                        g.add(area, line)
                    for bit in piece.split("|"):     # (a hover's lines: "Journal and help (H)|...")
                        g.add(area, bit)


def gather():
    g = Gathered()
    gather_scripts(g)
    gather_data(g)
    gather_python(g, "ENGINE", ("dsengine", "server"))
    js = os.path.join(ROOT, "web", "js")
    gather_js(g, "PAGE", [os.path.join(js, f) for f in sorted(os.listdir(js)) if f.endswith(".js")] +
              [os.path.join(ROOT, "web", "index.html")])
    gather_js(g, "HOME", [os.path.join(ROOT, "web", "home", "index.html")])
    gather_python(g, "HOME", ("central",))
    return g


# =====================================================================================================================
# The catalogues
# =====================================================================================================================
def codes():
    return sorted(f[:-4] for f in os.listdir(LANG) if f.endswith(".txt")) if os.path.isdir(LANG) else []


def load(code):
    path = os.path.join(LANG, code + ".txt")
    if not os.path.exists(path):
        return {}, NAMES.get(code, code)
    words, name = read_catalogue(path)
    return {k.replace(PARA, "\n"): v.replace(PARA, "\n") for k, v in words.items()}, name or NAMES.get(code, code)


def save(code, words, g):
    """The catalogue again: each line under the area it's in now; lines the game no longer says are let go."""
    name = NAMES.get(code, code)
    out = ["; Shards of Ashen in %s. English, a tab, the same in %s: tools/lang.py. Written by it: change lines, not "
           "their order." % (name, name), "[Language]", "Name=" + name]
    area = None
    for a, en in g.all():
        if en in words:
            if a != area:
                out.append("[%s]" % a.title())
                area = a
            out.append(en.replace("\n", PARA) + "\t" + words[en].replace("\n", PARA))
    os.makedirs(LANG, exist_ok=True)
    with open(os.path.join(LANG, code + ".txt"), "wb") as f:
        f.write(("\r\n".join(out) + "\r\n").encode("cp1252"))


def holes(s):
    return sorted(set(HOLE.findall(PLURAL.sub(r"{\1}", s))))      # (a hole may be said twice: a plural and its verb)


def problem(en, said):
    """Why a translation won't do, or "": it keeps every hole, the | and \\ that split it, and the .. that joins it."""
    if not said.strip():
        return "empty"
    if holes(en) != holes(said):
        return "holes %s, not %s" % (holes(said), holes(en))
    for mark in ("|", "\\", "\n"):
        if en.count(mark) != said.count(mark):
            return "%d %r, not %d" % (said.count(mark), mark, en.count(mark))
    if en.startswith("..") != said.startswith(".."):
        return "the .. at its start"
    if en.rstrip().endswith("..") != said.rstrip().endswith(".."):
        return "the .. at its end"
    try:
        said.encode("cp1252")
    except UnicodeEncodeError as e:
        return "not cp1252: %s" % e
    return ""


def report(g):
    every = g.all()
    print("%d lines in English: %s" % (len(every), ", ".join("%s %d" % (a.title(), sum(1 for x, _ in every if x == a))
                                                           for a in AREAS)))
    for code in codes():
        words, name = load(code)
        missing = [a for a, en in every if en not in words]
        print("%s (%s): %d of %d%s" % (code, name, len(every) - len(missing), len(every),
                                      "" if not missing else "; missing %s" % ", ".join(
                                          "%s %d" % (a.title(), missing.count(a)) for a in AREAS if a in missing)))


def todo(g, code, out, n, area=None):
    words, _ = load(code)
    lines = [en for a, en in g.all() if en not in words and (not area or a == area.upper())][:n]
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(en.replace("\n", PARA) + "\n" for en in lines))
    print("%d lines for %s in %s" % (len(lines), code, out))


def fill(g, code, todo_path, answers_path):
    with open(todo_path, encoding="utf-8") as f:
        ens = [x.rstrip("\n").replace(PARA, "\n") for x in f if x.strip()]
    with open(answers_path, encoding="utf-8") as f:
        saids = [x.rstrip("\n").replace(PARA, "\n") for x in f if x.strip()]
    if len(ens) != len(saids):
        sys.exit("%d lines asked, %d answered: they must go line for line" % (len(ens), len(saids)))
    words, _ = load(code)
    bad = 0
    for en, said in zip(ens, saids):
        why = problem(en, said)
        if why:
            bad += 1
            print("NOT TAKEN (%s):\n  %s\n  %s" % (why, en, said))
            continue
        words[en] = said
    save(code, words, g)
    print("%s: %d taken, %d not" % (code, len(ens) - bad, bad))


def check():
    bad = []
    for code in codes():
        words, _ = load(code)
        for en, said in words.items():
            why = problem(en, said)
            if why:
                bad.append("%s.txt: %s: %r" % (code, why, en[:80]))
    return bad


def export(g=None):
    """The pages' catalogues: the game's (its words, the names, the engine's) and the start screen's."""
    g = g or gather()
    game, home = g.of(GAME_AREAS), g.of(("HOME",))
    out = os.path.join(ROOT, "web", "assets", "lang")
    os.makedirs(out, exist_ok=True)
    homes, made = {}, []
    for code in codes():
        words, name = load(code)
        mine = {en: s for en, s in words.items() if en in game}
        made.append(os.path.join(out, code + ".json"))
        with open(made[-1], "w", encoding="utf-8") as f:
            json.dump({"name": name, "words": mine}, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        homes[code] = {en: s for en, s in words.items() if en in home}
    body = ("// The start screen's words in the other languages. Made by tools/lang.py from data/Lang: never edited.\n"
            "window.DS_HOME_WORDS = %s;\n" % json.dumps(homes, ensure_ascii=False, sort_keys=True, indent=0))
    path = os.path.join(ROOT, "web", "home", "lang.js")
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if old != body:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    print("languages: %s exported" % (", ".join(codes()) or "none"))
    return made


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "check":
        bad = check()
        print("\n".join(bad) or "every line keeps its holes")
        sys.exit(1 if bad else 0)
    if cmd == "export":
        export()
        return
    g = gather()
    if cmd == "todo":
        todo(g, argv[2], argv[3], int(argv[4]) if len(argv) > 4 else 300, argv[5] if len(argv) > 5 else None)
    elif cmd == "fill":
        fill(g, argv[2], argv[3], argv[4])
    elif cmd == "list":                          # (every line of an area: python -I tools/lang.py list PAGE)
        for s in g.areas[argv[2].upper()]:
            print(s)
    else:
        report(g)


if __name__ == "__main__":
    main(sys.argv)
