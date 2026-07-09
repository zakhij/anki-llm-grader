### French LLM Grader configuration

- **api_key**: Your Anthropic API key (`sk-ant-...`). Get one at
  console.anthropic.com. If empty, the `ANTHROPIC_API_KEY` environment
  variable is used as a fallback. The key never leaves this machine except
  to call the Anthropic API.
- **model**: Claude model used for grading. Default `claude-opus-4-8`.
- **max_tokens**: Response budget for the grading call.
- **request_timeout_seconds**: How long to wait for the API before giving up.
- **adaptive_thinking**: Let Claude decide how much to reason before grading.
  Slightly slower on hard cards, better feedback. Set `false` for max speed.
- **translate_note_type_prefixes**: Cards whose note type name starts with any
  of these get the grader in *translation* mode (fields `Text`, `Level`).
- **prompt_note_type_prefixes**: Same, but *free-response* mode (fields
  `Level`, `Prompt`, `Constraints`).
- **show_previous_attempt**: Show a "last attempt" summary line on cards you
  have graded before.
- **system_prompt_extra**: Extra instructions appended to the grading prompt,
  e.g. "Ignore missing accents" or "Be extra strict about register".

Changes take effect on the next card shown (no restart needed).
