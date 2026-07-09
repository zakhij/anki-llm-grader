# LLM Answer Grader — Anki add-on

Type your answer on a flashcard, get it graded by Claude, right inside the
Anki reviewer. Built for language production practice (translations, free
writing), but works for anything where "compare my answer to the card" needs
judgment instead of string matching.

```
┌──────────────────────────────────────────┐
│  It is cold today. I want a hot coffee.  │
│                 [A1]                     │
│  ┌────────────────────────────────────┐  │
│  │ Il fait froid aujourd'hui. Je veux │  │
│  │ boire un café chaud.               │  │
│  └────────────────────────────────────┘  │
│  [Grade with Claude]  ⌘/Ctrl+Enter       │
│  ────────────────────────────────────    │
│  ● Correct   96/100   Suggested: Easy    │
│  BETTER VERSION                          │
│  Il fait froid aujourd'hui. J'ai envie   │
│  d'un café bien chaud.                   │
│  FEEDBACK                                │
│  • « je veux boire » is fine at A1;      │
│    « j'ai envie de » is more natural.    │
└──────────────────────────────────────────┘
```

## Why

The usual loop — see card, write your answer somewhere, paste it into a
chatbot with "grade my translation", read the feedback, switch back to Anki,
rate the card — works, but the context switching is brutal. This add-on
collapses it: input field on the card, one keystroke, feedback inline, rate
and move on. You still choose the rating; the grader just tells you what it
thinks (verdict, 0–100 score, corrected version, specific errors, and a
suggested Again/Hard/Good/Easy).

## Install

**From file:** download `llm_answer_grader.ankiaddon` from the
[latest release](https://github.com/zakhij/anki-llm-grader/releases), then in
Anki: Tools → Add-ons → Install from file.

Requires Anki 23.10+ on desktop (developed and tested on 25.09). Add-ons
don't run on AnkiDroid/AnkiMobile; cards behave normally there.

## Setup

1. Tools → Add-ons → **LLM Answer Grader** → Config.
2. Set `api_key` to your Anthropic API key
   ([console.anthropic.com](https://console.anthropic.com)).
3. Edit the example **profile** to target your cards:

```jsonc
"profiles": [
  {
    "name": "ES Translate",
    "note_type_prefixes": ["Spanish Translate"],   // matches note type names
    "card_fields": ["Front", "Level"],             // context sent to the grader ([] = all)
    "grading_instructions": "The card shows an English sentence (field 'Front') that the learner translates into Spanish. Grade meaning, grammar and naturalness at the level in the 'Level' field."
  }
]
```

The input box appears only on cards matching a profile. First matching
profile wins; `"*"` matches every note type. Grading style is tunable via
`system_prompt_extra` (e.g. `"Ignore missing accents"`) — see the config
screen for the full reference.

## How it works

Card JS can't call external APIs (the webview blocks cross-origin requests),
so the add-on bridges through Python:

1. A `card_will_show` hook appends the input widget to matching cards.
2. On submit, the widget calls `pycmd(...)` → the add-on's Python handler
   collects your answer + the card's fields.
3. A background thread (Anki's `taskman`) POSTs to the Claude Messages API —
   structured outputs guarantee a parseable grading JSON; adaptive thinking
   lets the model reason harder on hard answers. The UI never blocks.
4. The result is pushed back with `web.eval(...)` and rendered. Widget state
   lives in a persistent JS object, so your text and feedback survive the
   question→answer flip.

Attempts are archived locally (`user_files/history.json`, capped per note);
previously-attempted cards show a "last attempt" line. Nothing is written to
your notes and the API key is only ever sent to Anthropic.

Uses Anki's bundled `requests` — no vendored SDK, nothing to break when
Anki's launcher swaps its Python.

## Development

```
llm_answer_grader/
├── __init__.py   # hooks, pycmd bridge, threading
├── grader.py     # pure: profile matching, prompt build, API call (testable outside Anki)
├── history.py    # local attempt history
├── webui.py      # inline HTML/CSS/JS widget
├── config.json   # defaults
└── config.md     # config reference (shown in Anki)
```

To hack on it: copy `llm_answer_grader/` into your Anki `addons21/` directory
(real copy — on macOS, symlinks into TCC-protected folders like Desktop fail
silently) and restart Anki. `grader.py` and `history.py` import cleanly
outside Anki for unit testing.

This repo also contains the original project brief, working notes
(`anki-llm-grader-implementation-notes.md`), and the deck-generation scripts
it was built alongside.

## License

[AGPL-3.0](LICENSE) — same license family as Anki itself (`aqt`, which this
add-on imports, is AGPL).
