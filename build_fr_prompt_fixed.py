import genanki

MODEL_ID = 1651073200
DECK_ID = 1651073202

model = genanki.Model(
    MODEL_ID,
    "FR Prompt",
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

def card(level, prompt, constraints):
    """Combine prompt + constraints into one text block."""
    text = f"{prompt}<br><br>{constraints}"
    return (text, level)

cards = [
    # ============ BATCH 1 ============

    # A1 (5)
    card("A1", "Describe your family.",
         "3-4 simple sentences. Use <b>avoir</b> and <b>être</b>, possessive adjectives (<i>mon, ma, mes</i>), basic adjectives."),
    card("A1", "What do you eat for breakfast?",
         "3-4 sentences. Use <b>je mange</b>, <b>je bois</b>, partitive articles (<i>du, de la, des</i>)."),
    card("A1", "Describe your best friend.",
         "3-4 sentences. Use physical and personality adjectives, <b>il/elle est</b>, <b>il/elle a</b>."),
    card("A1", "What's the weather like today?",
         "3-4 sentences. Use <b>il fait</b>, <b>il y a</b>, weather vocabulary, one sentence about what you do because of the weather."),
    card("A1", "What do you do after work?",
         "3-4 sentences. Use <b>je + verb</b> in present tense, at least one time word (<i>après, le soir, ensuite</i>)."),

    # A2 (5)
    card("A2", "Tell me about your last vacation.",
         "4-5 sentences. Use passé composé, at least one time expression (<i>l'été dernier, pendant une semaine</i>), location prepositions (<i>à, en, au</i>)."),
    card("A2", "What's your favorite holiday or celebration, and why?",
         "4-5 sentences. Use <b>parce que</b> / <b>car</b>, present tense, vocabulary for food/family/traditions."),
    card("A2", "Describe your daily routine.",
         "5-6 sentences. Use reflexive verbs (<i>se lever, se coucher, se préparer</i>), time expressions, logical sequencing."),
    card("A2", "What do you like to cook?",
         "4-5 sentences. Use <b>aimer</b> + infinitive, ingredient vocabulary, <b>d'abord</b> / <b>puis</b> / <b>enfin</b> for steps."),
    card("A2", "Describe your neighborhood.",
         "4-5 sentences. Use <b>il y a</b>, <b>près de</b> / <b>loin de</b> / <b>en face de</b>, adjectives to describe places."),

    # B1 (5)
    card("B1", "Convince a friend to try your favorite hobby.",
         "5-7 sentences. Use imperative (<i>essaie, viens</i>), conditional for suggestions (<i>tu pourrais, ça te plairait</i>), <b>si + present → future</b>."),
    card("B1", "You missed a friend's birthday. Apologize and explain.",
         "5-7 sentences. Use passé composé for narrating what happened, expressions of apology (<i>je suis vraiment désolé, pardonne-moi</i>), cause/explanation (<i>comme, à cause de</i>)."),
    card("B1", "What are the advantages of learning a foreign language?",
         "5-7 sentences. Use <b>permettre de</b> + infinitive, comparative structures, at least two linking words (<i>de plus, en effet, par exemple</i>)."),
    card("B1", "Describe a memorable meal you had.",
         "5-7 sentences. Use imparfait for setting the scene + passé composé for events, sensory vocabulary (<i>le goût, l'odeur, délicieux</i>), relative pronouns (<i>qui, que</i>)."),
    card("B1", "If you could live anywhere in the world, where would you go and why?",
         "5-7 sentences. Use conditional (<i>j'aimerais, je vivrais, ce serait</i>), <b>si + imparfait → conditionnel</b>, at least one comparison."),

    # B2 (5)
    card("B2", "Should voting be mandatory? Argue your position.",
         "8-10 sentences. Use subjunctive after <i>il est essentiel que</i> / <i>bien que</i>, concession (<i>certes… mais</i>), structured argumentation with connectors (<i>en premier lieu, en revanche, par conséquent</i>)."),
    card("B2", "Is it better to travel alone or with others? Discuss.",
         "8-10 sentences. Use opposition structures (<i>tandis que, alors que, contrairement à</i>), subjunctive after opinion verbs (<i>je ne pense pas que ce soit</i>), balanced argument with personal conclusion."),
    card("B2", "A local park is being replaced by a shopping mall. Write a response for the local paper.",
         "8-10 sentences. Use formal register, passive voice (<i>être + past participle</i>), conditional for suggestions (<i>il conviendrait de, ne serait-il pas préférable de</i>), rhetorical questions."),
    card("B2", "Do you think remote work will become the norm? Discuss.",
         "8-10 sentences. Use future and conditional tenses, nuanced expressions (<i>il est probable que, on peut s'attendre à ce que</i>), cause-consequence links (<i>étant donné que, c'est pourquoi</i>)."),
    card("B2", "Should financial literacy be taught in schools? Argue.",
         "8-10 sentences. Use impersonal structures (<i>il est indéniable que, il paraît souhaitable que</i> + subj.), exemplification (<i>à titre d'exemple, notamment</i>), logical connectors (<i>dès lors, ainsi</i>)."),

    # C1 (5)
    card("C1", "\"Art that doesn't disturb isn't art.\" Discuss.",
         "2 developed paragraphs. Use subjunctive in at least 2 contexts, nominalization (<i>la provocation, le dérangement</i>), concessive/nuancing structures (<i>quand bien même, il n'en demeure pas moins que</i>), register soutenu."),
    card("C1", "To what extent should governments regulate artificial intelligence?",
         "2 developed paragraphs. Use passive constructions, hypothetical reasoning (<i>dans l'hypothèse où, à supposer que</i> + subj.), abstract vocabulary, balanced argumentation with a stated position."),
    card("C1", "Is nostalgia a helpful or harmful emotion? Analyze.",
         "2 developed paragraphs. Use at least 2 subjunctive clauses, abstract/psychological vocabulary, citation or reference to support argument, nuanced conclusion."),
    card("C1", "\"Travel broadens the mind\" — is this always true?",
         "2 developed paragraphs. Use restrictive structures (<i>ne… que, à condition que</i> + subj.), exemplification from concrete/cultural contexts, subjunctive, critical analysis."),
    card("C1", "Can true objectivity exist in journalism? Discuss.",
         "2 developed paragraphs. Use impersonal constructions (<i>force est d'admettre, il serait illusoire de</i>), passive voice, conditional for hypothetical reasoning, philosophical/media vocabulary."),

    # ============ BATCH 2 ============

    # A1 (20)
    card("A1", "What is your name and where are you from?",
         "2-3 sentences. Use <b>je m'appelle</b>, <b>je suis de</b> / <b>je viens de</b>, <b>j'habite à</b>."),
    card("A1", "What are you wearing today?",
         "3-4 sentences. Use <b>je porte</b>, clothing vocabulary, colors as adjectives."),
    card("A1", "What is in your bag?",
         "3-4 sentences. Use <b>il y a</b>, <b>dans mon sac</b>, indefinite articles (<i>un, une, des</i>)."),
    card("A1", "Do you have any pets?",
         "3-4 sentences. Use <b>j'ai</b> / <b>je n'ai pas de</b>, animal vocabulary, one adjective per animal."),
    card("A1", "What time do you wake up?",
         "3-4 sentences. Use <b>je me réveille à…</b>, time expressions (<i>tôt, tard</i>), <b>parce que</b>."),
    card("A1", "What sports do you like?",
         "3-4 sentences. Use <b>j'aime</b> / <b>je n'aime pas</b>, <b>jouer à</b> / <b>faire du</b>, one reason."),
    card("A1", "Describe your house or apartment.",
         "3-4 sentences. Use <b>il y a</b>, room vocabulary (<i>chambre, cuisine, salon</i>), basic adjectives (<i>grand, petit</i>)."),
    card("A1", "What is your favorite food?",
         "3-4 sentences. Use <b>mon plat préféré, c'est…</b>, <b>j'adore</b> / <b>je déteste</b>, one taste adjective (<i>sucré, salé, épicé</i>)."),
    card("A1", "How do you get to work or school?",
         "3-4 sentences. Use <b>je prends</b> + transport, <b>je vais à pied</b>, duration (<i>ça prend… minutes</i>)."),
    card("A1", "What days of the week do you prefer, and why?",
         "3-4 sentences. Use days of the week, <b>je préfère</b>, <b>parce que</b>, one activity per day."),
    card("A1", "Describe what you see from your window.",
         "3-4 sentences. Use <b>je vois</b>, <b>il y a</b>, basic nouns and colors."),
    card("A1", "What do you do on Sunday?",
         "3-4 sentences. Use present tense verbs, <b>le dimanche</b>, one connector (<i>et, mais, aussi</i>)."),
    card("A1", "What is your favorite color and why?",
         "2-3 sentences. Use <b>ma couleur préférée, c'est…</b>, <b>parce que</b>, one associated object."),
    card("A1", "Do you like your job or school? Say why.",
         "3-4 sentences. Use <b>j'aime</b> / <b>je n'aime pas</b>, <b>parce que</b>, one adjective to describe it."),
    card("A1", "Name three things you do every morning.",
         "3 sentences. Each sentence: <b>je + verb</b> in present tense, one time word (<i>d'abord, puis, ensuite</i>)."),
    card("A1", "What music do you listen to?",
         "3-4 sentences. Use <b>j'écoute</b>, <b>j'aime bien</b>, genre vocabulary, <b>quand</b> + situation."),
    card("A1", "What did you eat yesterday?",
         "3-4 sentences. Use passé composé with <b>avoir</b> (<i>j'ai mangé, j'ai bu</i>), meal vocabulary (<i>le déjeuner, le dîner</i>)."),
    card("A1", "Introduce a member of your family.",
         "3-4 sentences. Use <b>il/elle s'appelle</b>, <b>il/elle a … ans</b>, <b>il/elle est</b> + adjective, one thing they like."),
    card("A1", "Do you prefer summer or winter? Why?",
         "3-4 sentences. Use <b>je préfère</b>, weather words (<i>il fait chaud, il fait froid</i>), one activity per season."),
    card("A1", "What do you want to do this weekend?",
         "3-4 sentences. Use <b>je veux</b> + infinitive, <b>avec</b> + person, one place."),

    # A2 (15)
    card("A2", "Tell me about a film you watched recently.",
         "4-5 sentences. Use passé composé, opinion adjectives (<i>intéressant, ennuyeux, émouvant</i>), <b>parce que</b> / <b>car</b>."),
    card("A2", "Describe a typical Saturday for you.",
         "5-6 sentences. Use present tense, time sequencing (<i>le matin, l'après-midi, le soir</i>), reflexive verbs."),
    card("A2", "What kind of music or artist do you like, and what do they make you feel?",
         "4-5 sentences. Use <b>quand j'écoute…</b>, emotion vocabulary (<i>heureux, triste, calme, énergique</i>), <b>parce que</b>."),
    card("A2", "You are sick and need to cancel plans with a friend. Write them a message.",
         "4-5 sentences. Use <b>je suis désolé</b>, <b>je ne peux pas</b> + infinitive, propose a new date with <b>on pourrait</b>."),
    card("A2", "Describe the last gift you gave someone.",
         "4-5 sentences. Use passé composé, <b>pour</b> + occasion, <b>il/elle a aimé</b> / <b>il/elle était content(e)</b>."),
    card("A2", "What is your city or town known for?",
         "4-5 sentences. Use <b>il y a</b>, <b>on peut</b> + infinitive, <b>connu pour</b>, one superlative (<i>le plus grand, le meilleur</i>)."),
    card("A2", "Describe your favorite place to relax.",
         "4-5 sentences. Use location prepositions, sensory details (<i>calme, bruyant, joli</i>), <b>j'aime y aller parce que</b>."),
    card("A2", "What did you do for your last birthday?",
         "5-6 sentences. Use passé composé, <b>avec</b> + people, time expressions, one emotion."),
    card("A2", "You're at a restaurant. Order a meal and explain your choices.",
         "4-5 sentences. Use <b>je voudrais</b>, <b>pour moi</b>, <b>parce que</b>, food vocabulary, polite expressions."),
    card("A2", "Describe a person you admire (not from your family).",
         "4-5 sentences. Use <b>il/elle est</b> + character traits, <b>il/elle travaille comme</b>, <b>je l'admire parce que</b>."),
    card("A2", "What is your favorite season and what do you do during it?",
         "5-6 sentences. Use present tense, weather vocabulary, <b>pendant</b> + season, at least 3 activities."),
    card("A2", "Tell me about a time you were lost.",
         "4-5 sentences. Use passé composé + imparfait for background, <b>j'étais</b>, direction vocabulary (<i>à gauche, tout droit</i>)."),
    card("A2", "Compare two people you know (a friend and a family member).",
         "4-5 sentences. Use comparatives (<i>plus… que, moins… que, aussi… que</i>), physical and personality adjectives."),
    card("A2", "What do you usually do when it rains?",
         "4-5 sentences. Use <b>quand il pleut</b>, <b>d'habitude</b>, indoor activity vocabulary, <b>avec</b> + person or <b>seul(e)</b>."),
    card("A2", "Describe a photo on your phone — what's happening in it?",
         "4-5 sentences. Use present continuous (<b>être en train de</b>), <b>il y a</b>, location, describe people and actions."),

    # B1 (10)
    card("B1", "A friend wants to quit their job to travel. What advice would you give?",
         "5-7 sentences. Use conditional for advice (<i>je te conseillerais de, à ta place je…</i>), <b>si + imparfait → conditionnel</b>, pros and cons."),
    card("B1", "Describe a tradition from your culture that you think is important to preserve.",
         "5-7 sentences. Use <b>il est important de</b>, time markers (<i>depuis, autrefois, de nos jours</i>), relative clauses (<i>qui, que, où</i>)."),
    card("B1", "Tell me about a skill you learned on your own (not in school).",
         "5-7 sentences. Use passé composé + imparfait, <b>grâce à</b>, <b>au début… puis… finalement</b>, describe difficulty and progress."),
    card("B1", "What would you change about your city if you could?",
         "5-7 sentences. Use conditional, <b>si + imparfait → conditionnel</b>, <b>il faudrait que</b> + subjunctive, at least one comparison with another city."),
    card("B1", "Do you prefer to read books or watch films? Explain.",
         "5-7 sentences. Use comparative structures, <b>tandis que</b> / <b>alors que</b>, give specific examples, state a clear preference with reasoning."),
    card("B1", "Describe a misunderstanding you had with someone and how it was resolved.",
         "5-7 sentences. Use passé composé for events + imparfait for context, direct/indirect speech (<i>il m'a dit que…</i>), emotional vocabulary."),
    card("B1", "What do you think is the most useful invention of the last 50 years?",
         "5-7 sentences. Use <b>je pense que</b>, <b>grâce à</b>, <b>avant… maintenant</b>, explain impact with concrete examples."),
    card("B1", "You're hosting a dinner for friends from different countries. Describe your plan.",
         "5-7 sentences. Use future tense (<i>je préparerai, on mangera</i>), food vocabulary, <b>d'abord… ensuite… pour finir</b>, explain choices."),
    card("B1", "Tell me about a place you visited that surprised you (positively or negatively).",
         "5-7 sentences. Use passé composé + imparfait, <b>je m'attendais à… mais</b>, comparative (<i>plus… que je pensais</i>), sensory details."),
    card("B1", "Is it better to live in a big city or the countryside? Give your opinion.",
         "5-7 sentences. Use <b>d'un côté… de l'autre</b>, conditional, comparatives, state and justify a personal position."),

    # B2 (5)
    card("B2", "\"Privacy is the price we pay for technology.\" Do you agree?",
         "8-10 sentences. Use subjunctive after <i>bien que, il est douteux que</i>, concession (<i>certes… néanmoins</i>), concrete examples (social media, surveillance), logical connectors (<i>dès lors, force est de constater</i>)."),
    card("B2", "Should universities be free for everyone? Argue your position.",
         "8-10 sentences. Use impersonal structures (<i>il convient de, il est légitime de se demander si</i>), subjunctive, cause-consequence (<i>dans la mesure où, c'est la raison pour laquelle</i>), address a counterargument."),
    card("B2", "A friend says \"learning languages is pointless because AI will translate everything.\" Respond.",
         "8-10 sentences. Use concession (<i>s'il est vrai que… il n'en reste pas moins que</i>), subjunctive, nuanced vocabulary about culture/cognition/identity, personal examples."),
    card("B2", "Is it ethical to keep animals in zoos? Discuss both sides.",
         "8-10 sentences. Use opposition structures (<i>d'une part… d'autre part</i>), passive voice, subjunctive after <i>il est contestable que</i>, conclude with a nuanced personal stance."),
    card("B2", "Describe a societal change you've witnessed in your lifetime and analyze its impact.",
         "8-10 sentences. Use past tenses for narration, present for analysis, abstract vocabulary (<i>bouleversement, mutation, répercussions</i>), temporal connectors (<i>jadis, désormais, à l'heure actuelle</i>)."),

    # C1 (2)
    card("C1", "\"The more connected we become, the more isolated we feel.\" Analyze this paradox.",
         "2 developed paragraphs. Use subjunctive in at least 2 contexts, nominalization (<i>l'hyperconnexion, l'isolement</i>), concessive structures (<i>aussi… que, si… que + subj.</i>), reference to sociological or philosophical ideas."),
    card("C1", "Is it possible to separate an artist from their work? Should we?",
         "2 developed paragraphs. Use impersonal constructions (<i>il serait réducteur de, force est de reconnaître</i>), conditional for hypotheticals, abstract moral/aesthetic vocabulary, address both questions distinctly."),
]

deck = genanki.Deck(DECK_ID, "FR Prompt")

# Assign due positions ordered by level
level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4}

# Tag and sort
tagged_cards = []
for text, level in cards:
    tagged_cards.append((text, level))

# Sort by level
tagged_cards.sort(key=lambda x: level_order.get(x[1], 99))

for i, (text, level) in enumerate(tagged_cards):
    note = genanki.Note(
        model=model,
        fields=[text, level],
        tags=[f"FR::{level}"],
        due=i,
    )
    deck.add_note(note)

genanki.Package(deck).write_to_file("/Users/zakariahijaouy/Desktop/FR_Prompt_Fixed.apkg")
print(f"Done — {len(cards)} cards written to FR_Prompt_Fixed.apkg")

# Count by level
from collections import Counter
dist = Counter(level for _, level in cards)
for lvl in sorted(dist, key=lambda x: level_order[x]):
    print(f"  {lvl}: {dist[lvl]}")
PYEOF