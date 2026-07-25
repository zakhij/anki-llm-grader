import genanki

# NOTE: every build script must use a UNIQUE model id AND model name.
# All four scripts originally shared id 1651073200; each import then
# name-clashed with an existing note type and Anki minted a renamed
# "FR Translate+" copy — hence the +…+++++++ ladder in the collection.
# This id is kept because the collection's main note type (the 234-card
# "FR Translate+++++++") was created by this script's import.
MODEL_ID = 1651073200
DECK_ID = 1651073210

# Match the styling of the hand-fixed note types; without a css= argument
# genanki ships an unstyled model (left-aligned, browser-default font).
CARD_CSS = ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; padding: 20px; }"

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
    css=CARD_CSS,
)

cards = [
    # =================== A1 (60) ===================

    # Original 25
    ("I'm tired of waiting.", "A1"),
    ("— Are you coming? — In a minute.", "A1"),
    ("The bread smells very good.", "A1"),
    ("I'm a little nervous about tomorrow.", "A1"),
    ("I'm freezing!", "A1"),
    ("He's my brother, but we are very different.", "A1"),
    ("I miss my old apartment.", "A1"),
    ("My cat thinks he's the boss of the house.", "A1"),
    ("Be careful, the soup is very hot!", "A1"),
    ("— Whose phone is this? — Mine, sorry.", "A1"),
    ("I don't know yet.", "A1"),
    ("I'm happy to see you again.", "A1"),
    ("She doesn't want to talk to me. I don't know why.", "A1"),
    ("I add salt. I mix everything in the pan.", "A1"),
    ("My bed is so warm. I don't want to get up.", "A1"),
    ("One day, I want to live near the sea.", "A1"),
    ("It's not my fault!", "A1"),
    ("I was at the store. I saw my teacher. I said hello.", "A1"),
    ("I'm bored. There's nothing to do.", "A1"),
    ("I run every Monday morning.", "A1"),
    ("Don't be angry. I'm sorry.", "A1"),
    ("When I was little, I had a red bike.", "A1"),
    ("It's dark in this room. I can't see anything.", "A1"),
    ("I don't agree.", "A1"),
    ("— Where are my keys? — On the table.", "A1"),

    # Spatial 10
    ("The cat is sleeping under the table.", "A1"),
    ("— Excuse me, where is the post office? — Turn left at the corner.", "A1"),
    ("We walk along the beach every morning.", "A1"),
    ("My phone is on the chair, next to my bag.", "A1"),
    ("The kitchen is between the living room and the bedroom.", "A1"),
    ("The bakery is far from here. The supermarket is closer.", "A1"),
    ("I climb the stairs to the third floor.", "A1"),
    ("There is a big tree behind the house. The children play under it.", "A1"),
    ("The shop is across from the church. You can't miss it.", "A1"),
    ("— Where do we go now? — Straight ahead, then right.", "A1"),

    # New A1 25
    ("I'm so proud of you.", "A1"),
    ("He's afraid of dogs.", "A1"),
    ("I lived here ten years ago.", "A1"),
    ("We met at school.", "A1"),
    ("Good luck for the test!", "A1"),
    ("Don't worry, it's okay.", "A1"),
    ("My sister is angry with me.", "A1"),
    ("We don't agree, but it's fine.", "A1"),
    ("This coffee is too strong for me.", "A1"),
    ("Your perfume smells nice.", "A1"),
    ("My head hurts. I want to rest.", "A1"),
    ("This jacket is too small for me.", "A1"),
    ("I have a math test tomorrow.", "A1"),
    ("My boss is nice. I like my job.", "A1"),
    ("I'm looking for a gift for my mother.", "A1"),
    ("— Are you tired? — Yes, very.", "A1"),
    ("— Do you want some coffee? — No, thanks. I prefer tea.", "A1"),
    ("— Is this seat free? — Yes, sit down.", "A1"),
    ("I called him three times. He never answered.", "A1"),
    ("We waited an hour. The doctor was late.", "A1"),
    ("Maybe tomorrow. We'll see.", "A1"),
    ("My dog hates the rain. He doesn't want to go out.", "A1"),
    ("Don't forget your keys!", "A1"),
    ("I'll be right back.", "A1"),
    ("He's my best friend. I trust him.", "A1"),

    # =================== A2 (30) ===================

    # Original 20
    ("Last night, I couldn't sleep. I heard a strange noise outside. In the end, it was just the wind.", "A2"),
    ("— You said you'd call me. — I know, I'm sorry, I forgot.", "A2"),
    ("I'm going crazy with all this noise.", "A2"),
    ("I don't know what to think. He says one thing and does another.", "A2"),
    ("The market smells of fish and fresh bread. I love walking there in the morning.", "A2"),
    ("If you could have a superpower, which one would you choose?", "A2"),
    ("I played guitar when I was a teenager. I haven't played in years, but I still remember a few chords.", "A2"),
    ("My grandfather tells the same stories at every dinner. We pretend to be surprised.", "A2"),
    ("I used to be afraid of the dark. Now I sleep with the window open.", "A2"),
    ("It's so quiet you can hear the rain on the roof.", "A2"),
    ("Did you hear about Marie? She quit her job last week.", "A2"),
    ("— I can't come tonight. — Again? You always say that.", "A2"),
    ("I want to be happy for her, but I'm a little jealous too.", "A2"),
    ("I was running late. I forgot my umbrella. Of course, it started raining.", "A2"),
    ("First, fry the onions until they're golden. Then add the tomatoes. Let it cook for ten minutes.", "A2"),
    ("He always shows up at the worst moment.", "A2"),
    ("I think I need a break. I haven't stopped in weeks.", "A2"),
    ("We hadn't spoken in years. When I saw him, I didn't know what to say.", "A2"),
    ("Easier said than done.", "A2"),
    ("Her perfume reminded me of my grandmother. I almost cried.", "A2"),

    # Spatial 8
    ("The clock above the fireplace is very old. It belonged to my grandmother.", "A2"),
    ("We walked along the river for an hour. It was very peaceful.", "A2"),
    ("There are little cafés all around the square. We can sit at any one.", "A2"),
    ("She crossed the street without looking. A car nearly hit her.", "A2"),
    ("To get to the museum, you have to go through the old part of the city.", "A2"),
    ("Walk straight ahead until you see the church, then turn right.", "A2"),
    ("His apartment is right above the bakery, so it always smells of fresh bread.", "A2"),
    ("We took a small road that wound up into the mountains. The view was incredible.", "A2"),

    # New A2 2
    ("He invited me to dinner, but I had already eaten. I went anyway.", "A2"),
    ("My computer is too slow. I think I need a new one.", "A2"),

    # =================== B1 (12) ===================

    ("I was about to leave when she called my name. She wanted to apologize, which I wasn't expecting at all. We ended up talking for over an hour.", "B1"),
    ("— So you finally decided to come. — Don't start. — I'm just saying.", "B1"),
    ("Sometimes I wonder what would have happened if I'd stayed. But it's pointless to think like that.", "B1"),
    ("He claims he speaks four languages, but he can barely manage to order coffee.", "B1"),
    ("Even though I'd promised myself I would say something, when the moment came I just stayed silent, like always.", "B1"),
    ("The meeting was supposed to last thirty minutes. Three hours later, we still hadn't reached a decision.", "B1"),
    ("He drives me crazy with his attitude.", "B1"),
    ("If I could redo my twenties, I think I would worry less about what other people thought of me.", "B1"),
    ("We don't talk about it anymore. After what happened, it's better that way.", "B1"),
    ("There was something about the way she looked at me that made me uncomfortable, though I couldn't have said exactly what.", "B1"),
    ("Every Sunday, my father makes the same recipe. He doesn't write anything down. He learned it from his mother, who learned it from hers.", "B1"),
    ("I told him the truth. He preferred the lie.", "B1"),

    # =================== B2 (6) ===================

    ("There's a particular kind of loneliness that hits you in a crowded room — when you realize that none of the people around you actually know who you are.", "B2"),
    ("She walked into the café as if she'd been there a hundred times. The waiter brought her usual order without asking. I had never seen her before in my life.", "B2"),
    ("We argued about money, about the children, about the apartment — but the real fight was always something else, something neither of us was willing to say out loud.", "B2"),
    ("The doctor explained that the results were inconclusive, but that further tests would only be necessary if symptoms persisted.", "B2"),
    ("What we call common sense is often nothing more than a collection of prejudices acquired before the age of eighteen.", "B2"),
    ("Had I known then what I know now, I wouldn't have wasted so much time trying to convince people who had already made up their minds.", "B2"),

    # =================== C1 (3) ===================

    ("There's a quiet violence in the way certain people listen — not to understand, but to wait for their turn to speak, as though conversation itself were a competition they had every intention of winning.", "C1"),
    ("Memory has a way of polishing certain images while letting others fade into nothing — and one rarely gets to choose which is which.", "C1"),
    ("What struck me most was not what she said, but the casual cruelty with which she said it, as though dismissing me had cost her absolutely nothing.", "C1"),
]

# Sort by level so positions are A1 first
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

genanki.Package(deck).write_to_file("/Users/zakariahijaouy/Desktop/FR_Translate_Batch3.apkg")

from collections import Counter
dist = Counter(level for _, level in cards)
print(f"Done — {len(cards)} cards written to FR_Translate_Batch3.apkg")
for lvl in sorted(dist, key=lambda x: level_order[x]):
    print(f"  {lvl}: {dist[lvl]}")
