import genanki

MODEL_ID = 1651073200
DECK_ID = 1651073230

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
    # ===== A1 (28) =====
    ("There is a small bird in the tree. It is singing.", "A1"),
    ("My uncle has chickens and a goat on his farm.", "A1"),
    ("I'm afraid of snakes.", "A1"),
    ("The fish in the aquarium are orange and white.", "A1"),
    ("There are mosquitoes everywhere tonight!", "A1"),
    ("I broke my arm last year.", "A1"),
    ("She has very small hands.", "A1"),
    ("My back hurts. I need to rest.", "A1"),
    ("He is wearing white pants and black shoes.", "A1"),
    ("It's cold. Take a scarf and gloves.", "A1"),
    ("The chair is made of wood.", "A1"),
    ("The bag is plastic. It is very light.", "A1"),
    ("The bread costs three euros.", "A1"),
    ("Do you have cash, or just a card?", "A1"),
    ("The pharmacy is closed on Sundays.", "A1"),
    ("I need to go to the bank this morning.", "A1"),
    ("We're taking the plane to Spain.", "A1"),
    ("Call a taxi, please. It's late.", "A1"),
    ("— Where is the train station? — Over there.", "A1"),
    ("There is a forest behind my house.", "A1"),
    ("I swim in the lake every summer.", "A1"),
    ("The soup tastes very good.", "A1"),
    ("We can leave now if you want.", "A1"),
    ("I have to call my mother tonight.", "A1"),
    ("In France, we eat dinner at eight.", "A1"),
    ("Look at me, not at him!", "A1"),
    ("I love this song!", "A1"),
    ("There are too many people in this bus.", "A1"),

    # ===== A2 (14) =====
    ("I have a cold. I need to take medicine.", "A2"),
    ("We celebrated her birthday at a Lebanese restaurant.", "A2"),
    ("My mother makes a delicious tagine with chicken and preserved lemons.", "A2"),
    ("He plays the piano beautifully. He's been learning since he was six.", "A2"),
    ("When I heard the news, I felt a huge wave of relief.", "A2"),
    ("— Which jacket do you want? — I prefer the blue one.", "A2"),
    ("— Are you going to the market? — Yes, I'm going there now.", "A2"),
    ("— Do you want some bread? — No thanks, I already have some.", "A2"),
    ("The book that I lent you last week — have you finished it?", "A2"),
    ("I have never been to Italy, but I'd love to go one day.", "A2"),
    ("He explained everything calmly and clearly.", "A2"),
    ("It was raining hard, so we decided to stay home.", "A2"),
    ("I'll call you as soon as I arrive at the hotel.", "A2"),
    ("There's nothing in the fridge. We have to go shopping.", "A2"),

    # ===== B1 (5) =====
    ("By the time we got to the restaurant, they had already closed the kitchen.", "B1"),
    ("The man whose dog you petted yesterday is my new neighbor.", "B1"),
    ("Even though it was pouring rain, we went out anyway.", "B1"),
    ("I don't think it's a good idea, honestly.", "B1"),
    ("She walked into the room slowly, as if she were afraid of what she'd find.", "B1"),

    # ===== B2 (2) =====
    ("Had I known you were coming, I would have prepared something to eat.", "B2"),
    ("It's about time we sat down and talked about this seriously.", "B2"),

    # ===== C1 (1) =====
    ("Whatever the outcome of the meeting, I refuse to compromise on this point.", "C1"),
]

level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4}
cards.sort(key=lambda x: level_order[x[1]])

deck = genanki.Deck(DECK_ID, "FR Translate")
for i, (text, level) in enumerate(cards):
    note = genanki.Note(
        model=model,
        fields=[text, level],
        tags=[f"FR::{level}"],
        due=i,
    )
    deck.add_note(note)

genanki.Package(deck).write_to_file("/Users/zakariahijaouy/Desktop/FR_Translate_GapFill.apkg")

from collections import Counter
dist = Counter(level for _, level in cards)
print(f"Done — {len(cards)} cards written to FR_Translate_GapFill.apkg")
for lvl in sorted(dist, key=lambda x: level_order[x]):
    print(f"  {lvl}: {dist[lvl]}")
