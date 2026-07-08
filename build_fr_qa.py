import genanki

MODEL_ID = 1651073200
DECK_ID = 1651073220

model = genanki.Model(
    MODEL_ID,
    "FR Translate",
    fields=[
        {"name": "Text"},
        {"name": "Level"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": '{{Text}}<br><br><span style="color: #888; font-size: 14px;">[{{Level}}]</span>',
            "afmt": "{{FrontSide}}",
        }
    ],
)

cards = [
    # A1 (20)
    ("Quoi de neuf ?", "A1"),
    ("Tu vas bien ?", "A1"),
    ("Ça donne quoi, ton week-end ?", "A1"),
    ("T'as faim ?", "A1"),
    ("Tu prends quoi ?", "A1"),
    ("T'es libre ce soir ?", "A1"),
    ("T'as un stylo ?", "A1"),
    ("Tu veux que j'apporte quoi ?", "A1"),
    ("Où est-ce qu'on se retrouve ?", "A1"),
    ("T'as l'heure ?", "A1"),
    ("C'est qui ?", "A1"),
    ("T'as compris ?", "A1"),
    ("Tu connais ?", "A1"),
    ("Ça te dit, un café ?", "A1"),
    ("T'as passé une bonne journée ?", "A1"),
    ("T'as bien dormi ?", "A1"),
    ("Tu veux quoi à boire ?", "A1"),
    ("T'as froid ?", "A1"),
    ("C'est où ?", "A1"),
    ("T'es sûr ?", "A1"),

    # A2 (10)
    ("T'as fait quoi de beau ce week-end ?", "A2"),
    ("Comment ça se passe au boulot ?", "A2"),
    ("T'as eu mes messages ?", "A2"),
    ("Ça t'a plu, le film ?", "A2"),
    ("T'es là pour combien de temps ?", "A2"),
    ("T'as essayé le nouveau resto en bas ?", "A2"),
    ("Vous êtes ouverts jusqu'à quelle heure ?", "A2"),
    ("Comment tu connais Marc ?", "A2"),
    ("T'as des plans pour les vacances ?", "A2"),
    ("Ça te dirait de venir avec nous ?", "A2"),

    # B1 (3)
    ("Tu te plais ici, finalement ?", "B1"),
    ("Et sinon, comment ça va, vraiment ?", "B1"),
    ("T'as des nouvelles de Sarah ?", "B1"),

    # B2 (2)
    ("Tu trouves pas qu'on bosse trop, par rapport à avant ?", "B2"),
    ("Si tu devais tout plaquer demain, tu ferais quoi ?", "B2"),

    # C1 (1)
    ("Tu penses qu'on choisit vraiment qui on est, ou c'est juste l'illusion qu'on s'en fait ?", "C1"),
]

level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4}
cards.sort(key=lambda x: level_order[x[1]])

deck = genanki.Deck(DECK_ID, "FR Q&A")
for i, (text, level) in enumerate(cards):
    note = genanki.Note(
        model=model,
        fields=[text, level],
        tags=[f"FR::{level}"],
        due=i,
    )
    deck.add_note(note)

genanki.Package(deck).write_to_file("/Users/zakariahijaouy/Desktop/FR_QA.apkg")

from collections import Counter
dist = Counter(level for _, level in cards)
print(f"Done — {len(cards)} cards written to FR_QA.apkg")
for lvl in sorted(dist, key=lambda x: level_order[x]):
    print(f"  {lvl}: {dist[lvl]}")
