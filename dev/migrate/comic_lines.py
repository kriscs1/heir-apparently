"""The comic pass (dev/Rules.md, Writing: the game is comic fantasy) for the scripts whose builders don't run any more
(build_heir_mainland.py is superseded, Talk to Guard and Talk to Shopkeeper were written by hand before the builders):
a line of theirs, as it was, and as it is now. What to do is still said plainly; the joke comes before it or after.

Bert grumbles, the guards have opinions, the jester is right more often than a jester should be, the Ashen Hand's
acolyte says what the handbook says, and the dragon gives its name, Vorgalath, and talks like a creditor.

Safe to run again (a line already changed is left; one that's gone is reported).
Usage: python -I dev/migrate/comic_lines.py     (then validate.py, export_web_assets.py)"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LINES = {
    "Talk to Bert": [
        ("Take these.\\Read a scroll and its spell is yours for good; casting it spends Shards. And a draught or two: "
         "magic won't mend you.",
         "Take these. I've far too many; I keep buying them.\\Read a scroll and its spell is yours for good; casting "
         "it spends Shards. And a draught or two: magic won't mend you. I've tried. Ask my knees."),
        ("But even I need the proper things.", "But even I need the proper things. Even I. It's very annoying."),
        ("Bring me all three, and we'll see about that barrier.",
         "Bring me all three, and we'll see about that barrier. And wipe your feet when you do."),
        ("the ring from the Ashen Priest. All three, mind.",
         "the ring from the Ashen Priest. All three, mind. Two is not three. People keep trying two."),
        ("I study the arcane arts up here, far from the noise of the court.\\I sell spell scrolls, though they don't "
         "come cheap.",
         "I study the arcane arts up here, far from the noise of the court. Mostly far from the court.\\I sell spell "
         "scrolls, though they don't come cheap. I set the prices by how my day's going."),
        ("\tBert\tWhere to?\t", "\tBert\tWhere to? Keep your arms in.\t"),
    ],
    "The Dragon Speaks": [
        ("So. The heir of Galmere comes to me at last, and on foot.\\Eighteen winters I have waited at these walls. "
         "Eighteen winters the city has starved for want of the road, and all for one small debt.",
         "So. The heir of Galmere comes to Vorgalath at last, and on foot. Eighteen winters late.\\Eighteen winters I "
         "have waited at these walls. Eighteen winters the city has starved for want of the road, and all for one "
         "small debt. With the interest, it is not so small now."),
        ("They signed in blood. Your mother broke it, and ran.",
         "They signed in blood. I kept a copy. I always keep a copy. Your mother broke it, and ran."),
        ("Three fires, and the old knights' sting woken after all. No matter:",
         "Three fires, and the old knights' sting woken after all. How tiresome. No matter:"),
    ],
    "Talk to Ashen_Acolyte": [
        ("The dragon of Galaith will have its due. It always does.\t",
         "The dragon of Galaith will have its due. It always does.\\...Sorry. We have to say that to everyone. It's in "
         "the handbook.\t"),
    ],
    "Talk to Jester": [
        ("What did the Shard say to the other Shard? Nothing. They're Shards. But I think about it a lot.",
         "What did the Shard say to the other Shard? 'Haven't we met?' ...Nobody laughs at that one. I think it's "
         "because it's true."),
    ],
    "Talk to Guard": [
        ("Mind your manners, and keep your blade sheathed.",
         "Mind your manners, and keep your blade sheathed. If one of them turns you into a frog, don't come crying "
         "to me. You won't be able to."),
        ("The hobgoblins down there would gut you.\\Unless",
         "The hobgoblins down there would gut you. I've seen it. I didn't care for it.\\Unless"),
        ("In your pack it won't stop a hobgoblin's axe.",
         "In your pack it won't stop a hobgoblin's axe. You'd be surprised how many ask."),
        ("pays well for hobgoblin ears.\\", "pays well for hobgoblin ears. Don't ask me what he does with them.\\"),
        ("Halt! ...ah, you look honest enough. Go on in.\\", "Halt! ...ah, you look honest enough. Honest-ish. Go on "
                                                              "in.\\"),
        ("The herbalist is trying to brew something for them.",
         "The herbalist is trying to brew something for them. One of them's still screaming. That's Dennis. Dennis "
         "screams at moths."),
        ("Mad, if you ask me.", "Mad, if you ask me. Nobody does ask me. That's the trouble with this job."),
    ],
    "Talk to Shopkeeper": [
        ("Tools, buckets, fishing gear: if you need it, I've got it.",
         "Tools, buckets, fishing gear: if you need it, I've got it. If I haven't got it, you don't need it."),
    ],
}


EXAMINE = [   # (Entities.ini, what build_content.py wrote: every thing with that line)
    ("A furnace, roaring hot. Smelt ore into bars here.",
     "A furnace, roaring hot. Smelt ore into bars here. Eyebrows are optional."),
    ("A cooking range. Cook raw food on it, or bake.",
     "A cooking range. Cook raw food on it, or bake. It has seen things. Mostly burnt things."),
    ("A sturdy workbench for leather, wool and jewellery.",
     "A sturdy workbench for leather, wool and jewellery. Someone has carved TOM WOZ ERE in the corner."),
    ("Ripe golden wheat.", "Ripe golden wheat. Bread, in its early days."),
]


def examine():
    path = os.path.join(ROOT, "data", "Entities.ini")
    s = open(path, "rb").read().decode("cp1252")
    t = s
    for old, new in EXAMINE:
        t = t.replace("\r\nExamine.Info=%s\r\n" % old, "\r\nExamine.Info=%s\r\n" % new)
    if t != s:
        open(path, "wb").write(t.encode("cp1252"))
    return t != s


def main():
    print("Entities.ini: %s" % ("changed" if examine() else "as it was"))
    changed = gone = 0
    for name, pairs in LINES.items():
        path = os.path.join(ROOT, "data", "Scripts", name + ".script")
        s = open(path, "rb").read().decode("cp1252")
        t = s
        for old, new in pairs:
            if new in t:
                continue
            if old not in t:
                print("%s: gone: %s" % (name, old[:60]))
                gone += 1
                continue
            t = t.replace(old, new, 1)
        if t != s:
            open(path, "wb").write(t.encode("cp1252"))
            changed += 1
    print("The comic lines: %d scripts changed, %d lines not found" % (changed, gone))


if __name__ == "__main__":
    main()
