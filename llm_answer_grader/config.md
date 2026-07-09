### LLM Answer Grader configuration

**Quick start:** set `api_key`, then edit the example profile so its
`note_type_prefixes` matches your note types, and describe your grading task
in `grading_instructions`. Changes apply on the next card — no restart needed.

#### Connection

- **api_key**: Your Anthropic API key (`sk-ant-...`). Get one at
  console.anthropic.com. If empty, the `ANTHROPIC_API_KEY` environment
  variable is used as a fallback. The key never leaves your machine except to
  call the Anthropic API.
- **model**: Claude model used for grading. Default `claude-opus-4-8`.
- **max_tokens**: Response budget for the grading call.
- **request_timeout_seconds**: How long to wait for the API before giving up.
- **adaptive_thinking**: Let Claude decide how much to reason before grading.
  Slightly slower on hard cards, better feedback. Set `false` for max speed.

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

#### Grading style

- **system_prompt**: Replaces the built-in grading persona entirely (leave
  empty to keep the sensible default). The response-format contract is always
  preserved.
- **system_prompt_extra**: Appended to the persona — the easy way to tweak
  style, e.g. "Ignore missing accents" or "Feedback in German".
- **show_previous_attempt**: Show a "last attempt" summary line on cards you
  have graded before.

#### Privacy & cost

Card fields of matched cards and your typed answers are sent to the Anthropic
API for grading — nothing else, and nothing is sent for cards without a
matching profile. Attempt history is stored locally in the add-on's
`user_files/history.json`. Each grading typically costs a fraction of a cent.
