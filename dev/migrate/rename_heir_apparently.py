"""The game is Heir Apparently (the owner's choice; it was Shards of Ashen), everywhere: what players see and read in
every language, the docs, and the names in its workings:

  * the GitHub repository is kriscs1/heir-apparently (a new one, with the whole history), the Docker image
    ghcr.io/kriscs1/heir-apparently, the compose projects, folders, systemd unit and Unraid template heir-apparently
    (HeirApparently), the central server https://heir-apparently.hallisium.com;
  * the Android app is io.github.kriscs1.heirapparently (a new app), the games on the network answer as
    "heirapparently", and the desktop app's Steam identity is "heirapparently";
  * the editor is "Heir Apparently Editor.py".

Not renamed: the Ashen Hand (the cult keeps its name), the Python package ashen/ and the database ashen.db (named for
the cult's word now), dsengine/, dsedit/ and the DS_ settings, and the archive (dev/Archive, dev/Log.txt, the
roadmaps and audits: what they say was so then). The setup scripts name the old folders and volumes on purpose: they
move a server set up before onto the new names.

Safe to run again (a second run finds nothing to rename).
Usage: python -I dev/migrate/rename_heir_apparently.py"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JAVA = "android/app/src/main/java/io/github/kriscs1/"
MOVES = [("Shards of Ashen Editor.py", "Heir Apparently Editor.py"),
         ("deploy/shards-of-ashen.service", "deploy/heir-apparently.service"),
         ("deploy/unraid/shards-of-ashen.xml", "deploy/unraid/heir-apparently.xml"),
         (JAVA + "shardsofashen", JAVA + "heirapparently")]
SKIP = ("dev/Archive/", "dev/Log.txt", "dev/Roadmap", "dev/QA ", "dev/Break Test", "dev/Code Issues", "web/assets/",
        "dev/migrate/generated.json", "android/app/build/", "deploy/central-setup.sh", "deploy/cloud-setup.sh")
TEXT = (".py", ".md", ".txt", ".script", ".map", ".ini", ".js", ".html", ".css", ".yml", ".yaml", ".xml", ".java",
        ".gradle", ".properties", ".bat", ".service", ".env", ".json", ".toml", ".cfg", ".sh", ".example",
        ".webmanifest", "Caddyfile", "Dockerfile")
SUBS = [   # (pattern, replacement), the specific first
    (r"shardsofashen(\.hallisium\.com|@hallisium\.com)", r"heir-apparently\1"),
    (r"(kriscs1|<you>|yourname|\}\}|packages/container|pkgs/container)/shardsofashen", r"\1/heir-apparently"),
    (r"\(e\.g\. shardsofashen\)", "(e.g. heir-apparently)"),
    (r"io\.github\.kriscs1\.shardsofashen", "io.github.kriscs1.heirapparently"),
    (r'"kriscs1", "shardsofashen"', '"kriscs1", "heirapparently"'),
    (r"SHARDSOFASHEN", "HEIRAPPARENTLY"),
    (r"shardsofashen", "heirapparently"),
    (r"shards-of-ashen", "heir-apparently"),
    (r"ShardsOfAshen", "HeirApparently"),
    (r"\bA Shards of Ashen\b", "An Heir Apparently"),
    (r"\ba Shards of Ashen\b", "an Heir Apparently"),
    (r"Shards of Ashen", "Heir Apparently"),
    (r"shards of ashen", "heir apparently"),
    (r"SHARDS OF ASHEN", "HEIR APPARENTLY"),
]
PROTECT = ("a ShardsOfAshen container, `ghcr.io/kriscs1/shardsofashen`", "`/mnt/user/appdata/shards-of-ashen`",
           "it was Shards of Ashen")
KO = [("Heir Apparently은", "Heir Apparently는"), ("Heir Apparently을", "Heir Apparently를"),
      ("Heir Apparently이 ", "Heir Apparently가 "), ("Heir Apparently으로", "Heir Apparently로"),
      ("Heir Apparently과", "Heir Apparently와")]       # ("Apparently" ends in a vowel; "Ashen" didn't)


def at(*p):
    return os.path.join(ROOT, *p)


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def move():
    for old, new in MOVES:
        if os.path.exists(at(old)) and not os.path.exists(at(new)):
            r = git("mv", old, new)
            if r.returncode:
                raise SystemExit("git mv %s: %s" % (old, r.stderr))
            print("moved", old, "->", new)


def rename(t, ko=False):
    for i, p in enumerate(PROTECT):                     # (README's note on moving an old Unraid container over)
        t = t.replace(p, "\x00%d\x00" % i)
    for pat, rep in SUBS:
        t = re.sub(pat, rep, t)
    for i, p in enumerate(PROTECT):
        t = t.replace("\x00%d\x00" % i, p)
    if ko:
        for a, b in KO:
            t = t.replace(a, b)
    return t


def texts():
    n = 0
    for f in git("ls-files").stdout.splitlines():
        base = os.path.basename(f)
        if (f.startswith(SKIP) or base.startswith("rename_") or not (f.endswith(TEXT))
                or not os.path.isfile(at(f))):
            continue
        raw = open(at(f), "rb").read()
        try:
            t, enc = raw.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            t, enc = raw.decode("cp1252"), "cp1252"
        new = rename(t, ko=f.endswith("ko.txt"))
        if new != t:
            open(at(f), "wb").write(new.encode(enc))
            n += 1
    return n


def main():
    move()
    print("Heir Apparently: %d files" % texts())


if __name__ == "__main__":
    main()
