### LLM Answer Grader configuration

**Prefer the visual editor:** Tools → **LLM Answer Grader Settings…** gives
you dropdowns and checkboxes for everything below (note types, fields,
providers). This JSON view is the power-user path; both edit the same config.

**Quick start:** set `api_key`, then edit the example profile so its
`note_type_prefixes` matches your note types, and describe your grading task
in `grading_instructions`. Changes apply on the next card — no restart needed.

#### Provider & connection

- **provider**: `"anthropic"` (default — Claude, best grading quality) or
  `"openai_compatible"` (any /chat/completions server: OpenAI, OpenRouter,
  Groq, Gemini's compatibility endpoint, or local Ollama / LM Studio).
- **api_key**: Your API key for the chosen provider. If empty, the
  `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) environment variable is used.
  Local servers like Ollama need no key — leave it empty. The key never
  leaves your machine except to call your chosen provider.
- **model**: Model name, e.g. `claude-opus-4-8`, `gpt-5`, `llama3.1`.
- **openai_base_url**: Only used with `openai_compatible`. Examples:
  - OpenAI: `https://api.openai.com/v1` (default)
  - OpenRouter: `https://openrouter.ai/api/v1`
  - Ollama (local): `http://localhost:11434/v1`
  - LM Studio (local): `http://localhost:1234/v1`
- **max_tokens**: Response budget for the grading call.
- **request_timeout_seconds**: How long to wait for the API before giving up.
- **adaptive_thinking**: Anthropic only — let Claude decide how much to
  reason before grading. Slightly slower on hard cards, better feedback.

#### Profiles — which cards get the grader, and how they're graded

Each entry in **profiles** targets some of your cards:

- **name**: Just a label for you.
- **note_type_prefixes**: The grader appears on cards whose note type name
  starts with any of these strings (e.g. `["Spanish Translate"]`). Use `"*"`
  to match every note type. Empty list = profile disabled.
- **grading_instructions**: Plain-English description of the task, written for
  the grader. Say what the card shows (mention field names), what the learner
  is supposed to produce, and what matters when grading. Example: *"The card
  shows a German sentence (field 'Front'); the learner translates it into
  English. Judge meaning first; minor article mistakes are acceptable."*
- **card_fields**: Which note fields to send as context (e.g.
  `["Front", "Level"]`). Empty list = all fields.

The **first** matching profile wins, so put more specific prefixes before
catch-alls.

A profile may also override the global connection settings — useful for
grading easy decks with a cheap/local model and hard decks with Claude. Any
of `provider`, `model`, `api_key`, `openai_base_url`, `adaptive_thinking`,
`max_tokens` set inside a profile wins over the global value for that
profile's cards.

#### Grading style

- **system_prompt**: Replaces the built-in grading persona entirely (leave
  empty to keep the sensible default). The response-format contract is always
  preserved.
- **system_prompt_extra**: Appended to the persona — the easy way to tweak
  style, e.g. "Ignore missing accents" or "Feedback in German".
- **show_previous_attempt**: Show a "last attempt" summary line on cards you
  have graded before.
- **rating_labels** / **verdict_labels**: Override the display text of the
  suggested rating and the verdict badge — useful if your Anki UI is not in
  English or you use an add-on that relabels the answer buttons. The
  suggestion itself always maps to Anki's four fixed answer ease values.
  Example: `"rating_labels": {"again": "À revoir", "hard": "Difficile",
  "good": "Correct", "easy": "Facile"}`.

#### Privacy & cost

Card fields of matched cards and your typed answers are sent to your chosen
provider for grading — nothing else, and nothing is sent for cards without a
matching profile. With a local server (Ollama/LM Studio) nothing leaves your
machine at all. Attempt history is stored locally in the add-on's
`user_files/history.json`. Cloud grading typically costs a fraction of a cent
per card.
