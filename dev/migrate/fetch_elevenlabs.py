"""People's greetings and goodbyes spoken by ElevenLabs voices (elevenlabs.io, the owner's Starter plan: commercial
use allowed), each kind of speaker a voice designed for it from a description (KINDS). What comes back is kept as it
came, in dev\\elevenlabs\\<Kind>\\ (in git: a voice made again is never quite the same), with a line in
dev\\elevenlabs\\takes.json for each (what it says, which voice, when it was downloaded) and Downloaded.md, the same
for reading. build_voices.py makes the game's Voice_/Bye_ sounds from them.

  python -I "dev\\migrate\\fetch_elevenlabs.py" [--env <file with ELEVENLABS_API_KEY=...>] [Kind ...]

Needs the elevenlabs package (pip install elevenlabs) and an API key, from ELEVENLABS_API_KEY or the --env file (never
in git). Safe to run again: only the lines not yet downloaded are fetched (a new line in KINDS, or a new kind). A kind's
voice is designed once and its id kept (voices.json); the account has 10 voice slots, so once a kind's lines are all
in its voice is deleted from the account (designed again, from the same description and seed, if more lines come)."""
import base64
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR = os.path.join(ROOT, "dev", "elevenlabs")
TAKES = os.path.join(DIR, "takes.json")
VOICES = os.path.join(DIR, "voices.json")
MODEL = "eleven_v4"                     # (speech: the latest, most natural)
DESIGN_MODEL = "eleven_ttv_v3"          # (voice design)
SEED = 4207                             # (a design made again from the same description comes out the same)

# each kind of speaker: the voice asked for, then its greetings and its goodbyes (a few words each: said as a talk
# opens, and as it closes). Old_Man is a real old man's (Common Voice: build_voices.py), liked as he is
KINDS = {
    "Man": dict(
        voice="A friendly English townsman in his late thirties, warm and natural, with a soft rural West Country "
              "accent; an ordinary shopkeeper or farmer in a medieval market town. Clear, close, dry recording.",
        hello=["Hello there!", "Good day to you.", "Well met, friend.", "Morning! What can I do for you?",
               "Ah, welcome, welcome.", "How can I help?"],
        bye=["Safe travels.", "Mind how you go.", "Good day, then.", "Come back any time."]),
    "Young_Man": dict(
        voice="A cheerful young Englishman of about twenty, light and eager, a little breathless; an apprentice or a "
              "courier in a medieval town. Natural, unpolished, clear dry recording.",
        hello=["Oh! Hello!", "Hey there.", "Hi! Need something?", "Good day!", "Welcome!"],
        bye=["See you around!", "Take care!", "Good luck out there!", "Bye now!"]),
    "Woman": dict(
        voice="A warm, friendly Englishwoman in her late thirties with a gentle Yorkshire accent; a tailor or a "
              "herbalist in a medieval town. Natural and kind, clear, close, dry recording.",
        hello=["Hello, love.", "Good day to you.", "Oh, hello there!", "Welcome! What can I get you?", "Morning!",
               "How can I help you?"],
        bye=["Take care now.", "Safe travels.", "Mind how you go.", "Come again!"]),
    "Young_Woman": dict(
        voice="A bright, cheerful young Englishwoman of about twenty, quick and friendly with a light country accent; a "
              "milkmaid or a barmaid in a medieval village. Natural, clear, dry recording.",
        hello=["Hi there!", "Oh, hello!", "Good morning!", "Welcome in!", "Hey! What can I do for you?"],
        bye=["Bye now!", "See you soon!", "Good luck!", "Take care of yourself!"]),
    "Old_Woman": dict(
        voice="A kindly old Englishwoman in her late seventies, soft, slightly frail and a little croaky, with a "
              "country accent; a village grandmother or a hedge witch. Natural, clear, close, dry recording.",
        hello=["Ah, hello, dearie.", "Good day to you.", "Well now, who's this?", "Come in, come in.",
               "Hello, pet."],
        bye=["Off you go, then.", "Mind yourself out there.", "Take care, dearie.", "Wrap up warm."]),
    "Deep": dict(
        voice="A big, broad-chested Englishman in his fifties with a naturally very deep, rumbling voice and a "
              "northern accent; a blacksmith, a butcher or a sea captain. Slow and steady. Clear, dry recording.",
        hello=["Aye?", "Well met.", "What'll it be?", "Greetings.", "Good day.", "Need something?"],
        bye=["Fare well.", "Off with you, then.", "Good luck.", "Aye. Take care."]),
    "Guard": dict(
        voice="A stern English town guard in his forties, firm, clipped and official, a voice used to giving orders; "
              "a soldier of a medieval city watch. Clear, dry recording.",
        hello=["Halt.", "Citizen.", "What is it?", "Speak up.", "Keep the peace."],
        bye=["Move along.", "On your way.", "Stay out of trouble.", "Keep your nose clean."]),
    "Noble_Man": dict(
        voice="A proud English nobleman in his fifties, rich, measured and commanding, with a refined accent; a king "
              "or a chancellor at court. Unhurried. Clear, dry recording.",
        hello=["Ah. You may speak.", "Greetings.", "Welcome.", "Well? What is it?", "Good day to you."],
        bye=["You may go.", "That will be all.", "Farewell.", "Go well."]),
    "Noble_Woman": dict(
        voice="A gracious English noblewoman in her forties, poised, cool and elegant, with a refined accent; a "
              "duchess at court. Unhurried. Clear, dry recording.",
        hello=["Ah, welcome.", "Good day.", "You may approach.", "Greetings, traveller."],
        bye=["That will be all.", "Farewell.", "You may go.", "Go safely."]),
    "Gruff": dict(
        voice="A rough, gravelly-voiced Englishman in his forties, surly and suspicious, with a coarse working "
              "accent; a bandit or a smuggler. Clear, dry recording.",
        hello=["What d'you want?", "Hmph. Yeah?", "Oi.", "Well? Spit it out.", "Eh?"],
        bye=["Get lost.", "Clear off.", "Hmph. Go on, then.", "Watch yourself."]),
    "Ghost": dict(                      # (a voice of the account's own, whispering: build_voices.py adds the echo)
        voice_id="EXAVITQu4vr4xnSDxMaL", voice="ElevenLabs' Sarah (soft), whispering",
        hello=["[whispers] Hello...?", "[whispers] Who comes...?", "[whispers] Ah... one of the living...",
               "[whispers] Closer..."],
        bye=["[whispers] Go...", "[whispers] Farewell...", "[whispers] Remember..."]),
    "Boy": dict(                        # (waits for a free voice slot: the account has 10)
        voice="A cheerful English boy of about ten, curious and lively, a child's high voice; a village boy in a "
              "medieval town. Natural, clear, dry recording.",
        hello=["Hello!", "Hi! Who are you?", "Oh! Hello!", "Hiya!"],
        bye=["Bye!", "See you!", "Bye bye!"]),
    "Girl": dict(                       # (a voice of the account's own, from the Voice Library)
        voice_id="nDJIICjR9zfJExIFeSCN", voice="ElevenLabs' Emmaline (a young British girl)",
        hello=["Hello!", "Hi! Who are you?", "Oh! Hello there!", "Hiya!"],
        bye=["Bye!", "See you later!", "Bye bye!"]),
}


def load(path, empty):
    if not os.path.exists(path):
        return empty
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def api_key(argv):
    if "--env" in argv:
        path = argv[argv.index("--env") + 1]
        with open(path, encoding="utf-8") as f:
            for ln in f:
                k, _, v = ln.strip().partition("=")
                if k == "ELEVENLABS_API_KEY":
                    return v.strip().strip('"').strip("'")
    return os.environ.get("ELEVENLABS_API_KEY")


def design(client, kind, k, voices):
    """The kind's voice in the account: designed from its description the first time (the first of the previews)."""
    if k.get("voice_id"):                                       # (one the account has already: never deleted)
        voices[kind] = {"voice_id": k["voice_id"], "description": k["voice"], "design_model": "-", "seed": "-",
                        "designed": "-", "own": True}
        return k["voice_id"]
    v = voices.get(kind)
    if v and v.get("voice_id"):
        return v["voice_id"]
    sample = " ".join(k["hello"] + k["bye"])
    sample = (sample + " ") * (1 + 100 // len(sample))           # (a preview's text: 100 characters or more)
    r = client.text_to_voice.design(voice_description=k["voice"], model_id=DESIGN_MODEL, text=sample.strip(),
                                    seed=SEED, output_format="mp3_44100_128")
    pv = r.previews[0]
    os.makedirs(os.path.join(DIR, kind), exist_ok=True)
    with open(os.path.join(DIR, kind, "_voice_preview.mp3"), "wb") as f:
        f.write(base64.b64decode(pv.audio_base_64))
    made = client.text_to_voice.create(voice_name="Shards of Ashen - " + kind, voice_description=k["voice"],
                                       generated_voice_id=pv.generated_voice_id)
    voices[kind] = {"voice_id": made.voice_id, "description": k["voice"], "design_model": DESIGN_MODEL, "seed": SEED,
                    "designed": now()}
    save(VOICES, voices)
    print("  %s: voice designed (%s)" % (kind, made.voice_id))
    return made.voice_id


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write_md(takes, voices):
    lines = ["# ElevenLabs voices", "",
             "Every line downloaded from ElevenLabs (elevenlabs.io, the owner's Starter plan: commercial use allowed), "
             "as it came. `dev/migrate/fetch_elevenlabs.py` downloads them and writes this file; "
             "`dev/migrate/build_voices.py` makes the game's sounds from them.", ""]
    for kind in KINDS:
        mine = [t for t in takes if t["kind"] == kind]
        if not mine:
            continue
        v = voices.get(kind, {})
        lines += ["## %s" % kind, "", "Voice designed %s from: *%s* (%s, seed %s)" %
                  (v.get("designed", "?"), v.get("description", "?"), v.get("design_model", "?"), v.get("seed", "?")),
                  "", "| File | Says | Downloaded | Model |", "|---|---|---|---|"]
        for t in mine:
            lines.append("| `%s` | %s: \"%s\" | %s | %s |" % (t["file"], t["said"], t["text"], t["downloaded"],
                                                              t["model"]))
        lines.append("")
    with open(os.path.join(DIR, "Downloaded.md"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines))


def main(argv):
    from elevenlabs import ElevenLabs, VoiceSettings
    key = api_key(argv)
    if not key:
        raise SystemExit("No ELEVENLABS_API_KEY (set it, or give --env <file>)")
    client = ElevenLabs(api_key=key)
    os.makedirs(DIR, exist_ok=True)
    takes, voices = load(TAKES, []), load(VOICES, {})
    have = {(t["kind"], t["said"], t["text"]) for t in takes}
    only = [a for a in argv if a in KINDS]
    for kind, k in KINDS.items():
        if only and kind not in only:
            continue
        want = [(said, text) for said in ("hello", "bye") for text in k[said] if (kind, said, text) not in have]
        if not want:
            continue
        voice_id = design(client, kind, k, voices)
        for said, text in want:
            n = sum(1 for t in takes if t["kind"] == kind and t["said"] == said) + 1
            name = "%s/%s_%02d_%s.mp3" % (kind, said, n, slug(text))
            audio = client.text_to_speech.convert(voice_id, text=text, model_id=MODEL, output_format="mp3_44100_128",
                                                  voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75))
            os.makedirs(os.path.join(DIR, kind), exist_ok=True)
            with open(os.path.join(DIR, name), "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            takes.append({"kind": kind, "said": said, "text": text, "file": name, "voice_id": voice_id,
                          "model": MODEL, "downloaded": now()})
            save(TAKES, takes)
            print("  %s %s: %s" % (kind, said, text))
        if voices[kind].get("own"):
            save(VOICES, voices)
            continue
        try:
            client.voices.delete(voice_id)                        # (a slot free for the next kind)
        except Exception as e:                                    # (a key without voices_write: it stays, and is used
            print("  (%s's voice kept in the account: %s)" % (kind, str(e)[-120:]))   # again for new lines)
            continue
        voices[kind]["voice_id"] = ""
        voices[kind]["deleted"] = now()
        save(VOICES, voices)
    write_md(takes, voices)
    print("%d lines in all, in dev\\elevenlabs" % len(takes))


if __name__ == "__main__":
    main(sys.argv[1:])
