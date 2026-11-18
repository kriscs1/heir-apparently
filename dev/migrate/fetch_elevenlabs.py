"""People's greetings and goodbyes spoken by ElevenLabs voices (elevenlabs.io, the owner's Starter plan: commercial
use allowed), each kind of speaker a voice designed for it from a description (KINDS). What comes back is kept as it
came, in dev\\elevenlabs\\<Kind>\\ (in git: a voice made again is never quite the same), with a line in
dev\\elevenlabs\\takes.json for each (what it says, which voice, when it was downloaded) and Downloaded.md, the same
for reading. build_voices.py makes the game's Voice_/Bye_ sounds from them.

The other languages (LANGS: the game's own, data/Lang) have voices of their own, each kind designed again as one of
their own people (its description said so: native), with greetings and goodbyes in their words (LINES), kept in
dev\\elevenlabs\\<lang>\\<Kind>\\; and an old man, who in English is a real one (build_voices.py).

  python -I "dev\\migrate\\fetch_elevenlabs.py" [--env <file with ELEVENLABS_API_KEY=...>] [Kind or lang ...]

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

# ----- the other languages: who their people are (each kind's description made theirs: native) and what they say
LANGS = {
    "es": dict(name="Spanish", man="Spaniard", woman="Spanish woman", adj="Spanish",
               accent="a natural accent from Castile, speaking Castilian Spanish"),
    "de": dict(name="German", man="German man", woman="German woman", adj="German",
               accent="a natural German accent, speaking standard German"),
    "fr": dict(name="French", man="Frenchman", woman="Frenchwoman", adj="French",
               accent="a natural accent from France, speaking French"),
    "pt": dict(name="Brazilian Portuguese", man="Brazilian man", woman="Brazilian woman", adj="Brazilian",
               accent="a natural Brazilian accent, speaking Brazilian Portuguese"),
}
# (the old man, a real one's recording in English, is one of ElevenLabs' in the others)
OLD_MAN = ("A kindly old Englishman in his late seventies, slow, warm and a little hoarse, with a country accent; a "
           "village elder or a hermit. Natural, clear, close, dry recording.")

# each language's greetings and goodbyes, kind by kind: (hello, bye)
LINES = {
    "es": {
        "Man": (["¡Hola!", "Buenos días.", "Bienvenido, amigo.", "¿En qué puedo ayudarle?", "¡Ah, bienvenido!"],
                ["Buen viaje.", "Cuídese.", "Vuelva cuando quiera.", "Que le vaya bien."]),
        "Young_Man": (["¡Oh! ¡Hola!", "¡Buenas!", "¿Necesitas algo?", "¡Bienvenido!"],
                      ["¡Hasta luego!", "¡Cuídate!", "¡Suerte ahí fuera!"]),
        "Woman": (["Hola, cariño.", "Buenos días.", "¡Oh, hola!", "¡Bienvenido! ¿Qué le pongo?",
                   "¿En qué puedo ayudarle?"], ["Cuídese.", "Buen viaje.", "¡Vuelva pronto!"]),
        "Young_Woman": (["¡Hola!", "¡Ay, hola!", "¡Buenos días!", "¡Pasa, pasa!", "¿Qué te pongo?"],
                        ["¡Adiós!", "¡Hasta pronto!", "¡Suerte!", "¡Cuídate mucho!"]),
        "Old_Woman": (["Ay, hola, hijo.", "Buenos días.", "Vaya, ¿quién eres tú?", "Pasa, pasa."],
                      ["Anda, ve con Dios.", "Cuídate ahí fuera.", "Abrígate bien."]),
        "Deep": (["¿Sí?", "Bien hallado.", "¿Qué va a ser?", "Saludos.", "¿Necesitas algo?"],
                 ["Que te vaya bien.", "Suerte.", "Venga. Cuídate."]),
        "Guard": (["¡Alto!", "Ciudadano.", "¿Qué pasa?", "Hable claro.", "Mantenga el orden."],
                  ["Circule.", "Siga su camino.", "No se meta en líos."]),
        "Noble_Man": (["Ah. Podéis hablar.", "Saludos.", "Bienvenido.", "¿Y bien? ¿Qué ocurre?"],
                      ["Podéis retiraros.", "Eso es todo.", "Id con Dios."]),
        "Noble_Woman": (["Ah, bienvenido.", "Buenos días.", "Podéis acercaros.", "Saludos, viajero."],
                        ["Eso es todo.", "Adiós.", "Id con cuidado."]),
        "Gruff": (["¿Qué quieres?", "Hmph. ¿Sí?", "Eh, tú.", "¿Y bien? Suéltalo."],
                  ["Lárgate.", "Fuera de aquí.", "Ándate con ojo."]),
        "Ghost": (["[whispers] ¿Hola...?", "[whispers] ¿Quién viene...?", "[whispers] Ah... uno de los vivos...",
                   "[whispers] Acércate..."], ["[whispers] Vete...", "[whispers] Adiós...", "[whispers] Recuerda..."]),
        "Boy": (["¡Hola!", "¡Hola! ¿Quién eres?", "¡Anda! ¡Hola!"], ["¡Adiós!", "¡Hasta luego!", "¡Chao!"]),
        "Girl": (["¡Hola!", "¡Hola! ¿Quién eres?", "¡Oh! ¡Hola!"], ["¡Adiós!", "¡Hasta luego!", "¡Chao, chao!"]),
        "Old_Man": (["Buenas tardes.", "Hola.", "¡Hola! ¡Qué alegría verte!", "Buenas noches.", "Buenos días."],
                    ["Ve con Dios.", "Cuídate, muchacho.", "Hasta otra."]),
    },
    "de": {
        "Man": (["Hallo!", "Guten Tag.", "Sei gegrüßt, Freund.", "Morgen! Was kann ich für Euch tun?",
                 "Ah, willkommen, willkommen."], ["Gute Reise.", "Passt auf Euch auf.", "Kommt jederzeit wieder."]),
        "Young_Man": (["Oh! Hallo!", "Na, du?", "Hallo! Brauchst du was?", "Willkommen!"],
                      ["Bis bald!", "Mach's gut!", "Viel Glück da draußen!"]),
        "Woman": (["Hallo, Schätzchen.", "Guten Tag.", "Oh, hallo!", "Willkommen! Was darf's sein?",
                   "Wie kann ich helfen?"], ["Pass auf dich auf.", "Gute Reise.", "Komm bald wieder!"]),
        "Young_Woman": (["Hallo!", "Oh, hallo!", "Guten Morgen!", "Komm rein!", "Was darf's sein?"],
                        ["Tschüss!", "Bis bald!", "Viel Glück!"]),
        "Old_Woman": (["Ach, hallo, Kindchen.", "Guten Tag.", "Na, wer bist denn du?", "Komm rein, komm rein."],
                      ["Na, dann geh mal.", "Pass gut auf dich auf.", "Zieh dich warm an."]),
        "Deep": (["Ja?", "Sei gegrüßt.", "Was darf's sein?", "Grüß dich.", "Brauchst du was?"],
                 ["Leb wohl.", "Viel Glück.", "Ja. Mach's gut."]),
        "Guard": (["Halt!", "Bürger.", "Was gibt's?", "Sprich lauter.", "Ruhe bewahren."],
                  ["Weitergehen.", "Geht Eures Weges.", "Keinen Ärger machen."]),
        "Noble_Man": (["Ah. Ihr dürft sprechen.", "Seid gegrüßt.", "Willkommen.", "Nun? Was gibt es?"],
                      ["Ihr dürft gehen.", "Das wäre alles.", "Lebt wohl."]),
        "Noble_Woman": (["Ah, willkommen.", "Guten Tag.", "Ihr dürft näher treten.", "Seid gegrüßt, Reisender."],
                        ["Das wäre alles.", "Lebt wohl.", "Geht mit Gott."]),
        "Gruff": (["Was willst du?", "Hmpf. Ja?", "He, du.", "Na? Raus damit."],
                  ["Verschwinde.", "Hau ab.", "Pass bloß auf."]),
        "Ghost": (["[whispers] Hallo...?", "[whispers] Wer kommt da...?", "[whispers] Ah... einer der Lebenden...",
                   "[whispers] Näher..."], ["[whispers] Geh...", "[whispers] Lebe wohl...", "[whispers] Erinnere dich..."]),
        "Boy": (["Hallo!", "Hallo! Wer bist du?", "Oh! Hallo!"], ["Tschüss!", "Bis dann!", "Tschüssi!"]),
        "Girl": (["Hallo!", "Hallo! Wer bist du?", "Oh! Hallo du!"], ["Tschüss!", "Bis später!", "Tschüssi!"]),
        "Old_Man": (["Guten Tag.", "Hallo.", "Hallo! Schön, dich zu sehen!", "Guten Abend.", "Guten Morgen."],
                    ["Geh mit Gott.", "Pass auf dich auf, Junge.", "Bis zum nächsten Mal."]),
    },
    "fr": {
        "Man": (["Bonjour !", "Bien le bonjour.", "Salut, l'ami.", "Bonjour ! Que puis-je pour vous ?",
                 "Ah, bienvenue, bienvenue."], ["Bon voyage.", "Prenez garde à vous.", "Revenez quand vous voulez."]),
        "Young_Man": (["Oh ! Bonjour !", "Salut !", "Salut ! Besoin de quelque chose ?", "Bienvenue !"],
                      ["À plus !", "Prends soin de toi !", "Bonne chance !"]),
        "Woman": (["Bonjour, mon petit.", "Bien le bonjour.", "Oh, bonjour !", "Bienvenue ! Qu'est-ce que je vous sers ?",
                   "Que puis-je faire pour vous ?"], ["Prenez soin de vous.", "Bon voyage.", "Revenez vite !"]),
        "Young_Woman": (["Salut !", "Oh, bonjour !", "Bonjour !", "Entrez, entrez !", "Qu'est-ce que je te sers ?"],
                        ["Au revoir !", "À bientôt !", "Bonne chance !"]),
        "Old_Woman": (["Ah, bonjour, mon petit.", "Bien le bonjour.", "Eh bien, qui voilà ?", "Entre, entre."],
                      ["Allez, file.", "Fais bien attention.", "Couvre-toi bien."]),
        "Deep": (["Oui ?", "Salut à toi.", "Qu'est-ce que ce sera ?", "Salutations.", "Besoin de quelque chose ?"],
                 ["Adieu.", "Bonne chance.", "Bon. Prends soin de toi."]),
        "Guard": (["Halte !", "Citoyen.", "Qu'y a-t-il ?", "Parlez plus fort.", "Pas de grabuge."],
                  ["Circulez.", "Passez votre chemin.", "Pas d'ennuis, hein."]),
        "Noble_Man": (["Ah. Vous pouvez parler.", "Salutations.", "Bienvenue.", "Eh bien ? Qu'y a-t-il ?"],
                      ["Vous pouvez disposer.", "Ce sera tout.", "Adieu."]),
        "Noble_Woman": (["Ah, bienvenue.", "Bonjour.", "Approchez.", "Salutations, voyageur."],
                        ["Ce sera tout.", "Adieu.", "Allez en paix."]),
        "Gruff": (["Qu'est-ce que tu veux ?", "Hmph. Ouais ?", "Hé, toi.", "Alors ? Crache le morceau."],
                  ["Dégage.", "Fiche le camp.", "Fais gaffe à toi."]),
        "Ghost": (["[whispers] Bonjour... ?", "[whispers] Qui vient... ?", "[whispers] Ah... un vivant...",
                   "[whispers] Approche..."], ["[whispers] Va-t'en...", "[whispers] Adieu...", "[whispers] Souviens-toi..."]),
        "Boy": (["Bonjour !", "Salut ! T'es qui ?", "Oh ! Salut !"], ["Au revoir !", "À plus !", "Salut salut !"]),
        "Girl": (["Bonjour !", "Salut ! T'es qui ?", "Oh ! Bonjour !"], ["Au revoir !", "À tout à l'heure !", "Salut salut !"]),
        "Old_Man": (["Bon après-midi.", "Bonjour.", "Bonjour ! Ça fait plaisir de te voir !", "Bonsoir.",
                     "Bien le bonjour."], ["Va en paix.", "Prends soin de toi, petit.", "À la prochaine."]),
    },
    "pt": {
        "Man": (["Olá!", "Bom dia.", "Salve, amigo.", "Bom dia! Em que posso ajudar?", "Ah, seja bem-vindo."],
                ["Boa viagem.", "Vai com cuidado.", "Volte sempre."]),
        "Young_Man": (["Opa! Olá!", "E aí?", "Oi! Precisa de alguma coisa?", "Bem-vindo!"],
                      ["Até mais!", "Se cuida!", "Boa sorte por aí!"]),
        "Woman": (["Olá, querido.", "Bom dia.", "Ah, olá!", "Bem-vindo! O que vai querer?", "Como posso ajudar?"],
                  ["Se cuida.", "Boa viagem.", "Volte logo!"]),
        "Young_Woman": (["Oi!", "Ah, oi!", "Bom dia!", "Entra, entra!", "O que vai ser?"],
                        ["Tchau!", "Até logo!", "Boa sorte!"]),
        "Old_Woman": (["Ah, olá, meu filho.", "Bom dia.", "Ora, quem é você?", "Entra, entra."],
                      ["Vai com Deus.", "Toma cuidado lá fora.", "Se agasalha bem."]),
        "Deep": (["Sim?", "Salve.", "O que vai ser?", "Saudações.", "Precisa de algo?"],
                 ["Passar bem.", "Boa sorte.", "Certo. Se cuida."]),
        "Guard": (["Alto!", "Cidadão.", "O que foi?", "Fale mais alto.", "Mantenha a ordem."],
                  ["Circulando.", "Siga seu caminho.", "Nada de confusão."]),
        "Noble_Man": (["Ah. Pode falar.", "Saudações.", "Seja bem-vindo.", "E então? O que é?"],
                      ["Pode ir.", "Isso é tudo.", "Adeus."]),
        "Noble_Woman": (["Ah, bem-vindo.", "Bom dia.", "Pode se aproximar.", "Saudações, viajante."],
                        ["Isso é tudo.", "Adeus.", "Vá em paz."]),
        "Gruff": (["O que você quer?", "Hmpf. Que é?", "Ei, você.", "E aí? Desembucha."],
                  ["Some daqui.", "Cai fora.", "Fica esperto."]),
        "Ghost": (["[whispers] Olá...?", "[whispers] Quem vem lá...?", "[whispers] Ah... um dos vivos...",
                   "[whispers] Chegue mais perto..."], ["[whispers] Vá...", "[whispers] Adeus...", "[whispers] Lembre-se..."]),
        "Boy": (["Oi!", "Oi! Quem é você?", "Opa! Oi!"], ["Tchau!", "Até mais!", "Tchau tchau!"]),
        "Girl": (["Oi!", "Oi! Quem é você?", "Ah! Olá!"], ["Tchau!", "Até depois!", "Tchau tchau!"]),
        "Old_Man": (["Boa tarde.", "Olá.", "Olá! Que bom te ver!", "Boa noite.", "Bom dia."],
                    ["Vai com Deus.", "Se cuida, rapaz.", "Até a próxima."]),
    },
}


def native(description, lang):
    """A kind's description made one of lang's people: its nation, its accent, and its words in their tongue."""
    L = LANGS[lang]
    d = description.replace("Englishwoman", L["woman"]).replace("Englishman", L["man"])
    d = d.replace("English", L["adj"])
    d = re.sub(r"\b(with|and) an? [^;,.]*?accent", lambda m: m.group(1) + " " + L["accent"], d)
    if L["accent"] not in d:
        d = d.rstrip(".") + ", with " + L["accent"] + "."
    return d + " A native %s speaker." % L["name"]


def jobs():
    """(lang, kind, key in voices.json, its voice, hello, bye) for every voice: English's, then the others'."""
    out = [("en", kind, kind, k, k["hello"], k["bye"]) for kind, k in KINDS.items()]
    for lang in LANGS:
        for kind, (hello, bye) in LINES[lang].items():
            k = KINDS.get(kind, {"voice": OLD_MAN})
            v = dict(voice_id=k["voice_id"], voice=k["voice"] + ", speaking " + LANGS[lang]["name"]) \
                if k.get("voice_id") else dict(voice=native(k["voice"], lang))
            out.append((lang, kind, "%s/%s" % (lang, kind), dict(v, hello=hello, bye=bye), hello, bye))
    return out


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
    import unicodedata
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
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
    os.makedirs(os.path.join(DIR, kind), exist_ok=True)               # (kind: its key, es/Man for another language's)
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
    for lang, kind, key, _, _, _ in jobs():
        mine = [t for t in takes if t["kind"] == kind and t.get("lang", "en") == lang]
        if not mine:
            continue
        v = voices.get(key, {})
        lines += ["## %s" % (kind if lang == "en" else "%s (%s)" % (kind, LANGS[lang]["name"])), "",
                  "Voice designed %s from: *%s* (%s, seed %s)" %
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
    have = {(t.get("lang", "en"), t["kind"], t["said"], t["text"]) for t in takes}
    only = [a for a in argv if a in KINDS or a in LANGS or a == "Old_Man"]
    for lang, kind, key, k, hello, bye in jobs():
        if only and not (kind in only or lang in only):
            continue
        want = [(said, text) for said, texts in (("hello", hello), ("bye", bye)) for text in texts
                if (lang, kind, said, text) not in have]
        if not want:
            continue
        voice_id = design(client, key, k, voices)
        for said, text in want:
            n = sum(1 for t in takes if t["kind"] == kind and t.get("lang", "en") == lang and t["said"] == said) + 1
            name = "%s/%s_%02d_%s.mp3" % (key, said, n, slug(text))
            audio = client.text_to_speech.convert(voice_id, text=text, model_id=MODEL, output_format="mp3_44100_128",
                                                  voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75))
            os.makedirs(os.path.join(DIR, key), exist_ok=True)
            with open(os.path.join(DIR, name), "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            take = {"kind": kind, "said": said, "text": text, "file": name, "voice_id": voice_id, "model": MODEL,
                    "downloaded": now()}
            if lang != "en":
                take["lang"] = lang
            takes.append(take)
            save(TAKES, takes)
            print("  %s %s: %s" % (key, said, text))
        if voices[key].get("own"):
            save(VOICES, voices)
            continue
        try:
            client.voices.delete(voice_id)                        # (a slot free for the next kind)
        except Exception as e:                                    # (a key without voices_write: it stays, and is used
            print("  (%s's voice kept in the account: %s)" % (kind, str(e)[-120:]))   # again for new lines)
            continue
        voices[key]["voice_id"] = ""
        voices[key]["deleted"] = now()
        save(VOICES, voices)
    write_md(takes, voices)
    print("%d lines in all, in dev\\elevenlabs" % len(takes))


if __name__ == "__main__":
    main(sys.argv[1:])
