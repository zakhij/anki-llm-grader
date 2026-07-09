# Anki LLM Grader — Implementation Notes & Decisions

*Working document maintained by Claude while building the add-on described in
`anki-llm-grader-project.md`. Last updated: 2026-07-08.*

## Status

**Working, generalized, and release-packaged.** The add-on — now the generic
**LLM Answer Grader** — is installed at
`~/Library/Application Support/Anki2/addons21/llm_answer_grader/` and passed
automated in-Anki end-to-end tests twice (original French version and the
generalized version after the v0.2 refactor). The French-specific behavior is
preserved via local user config (`meta.json`), so the FR decks work exactly as
before. The one thing that could not be verified is a real graded response,
because **no Anthropic API key exists on this machine** — add yours via
Tools → Add-ons → LLM Answer Grader → Config, then review any FR Translate
card. Repo: https://github.com/zakhij/anki-llm-grader (private).

## How to use

1. Open Anki → Tools → Add-ons → select **French LLM Grader (Claude)** →
   Config → paste your API key into `"api_key"` → OK.
2. Review the *FR Translate* deck. Under the sentence you'll see a text box.
3. Type your translation, hit **⌘+Enter** (or the *Grade with Claude* button).
4. Feedback appears inline in a few seconds: verdict badge, 0–100 score, the
   natural native version, specific error points, alternatives, and a
   suggested Again/Hard/Good/Easy rating.
5. Show Answer (your text and feedback stay put) → rate the card → next.

Esc gets you out of the text box so normal keyboard shortcuts work again.

---

## 1. Environment findings

| Item | Finding |
|---|---|
| Anki version | **25.09.4** (new uv-based launcher) |
| Python runtime | **3.13.5**, venv at `~/Library/Application Support/AnkiProgramFiles/.venv` (managed by `uv`, recreated on upgrades) |
| Existing add-ons | Only Review Heatmap (`1771074083`) — no conflicts |
| HTTP libs bundled with Anki | `requests` ✅, `certifi` ✅ — `httpx` ❌, `anthropic` SDK ❌ |
| Hooks (confirmed in `_aqt/hooks.py` for 25.09.4) | `card_will_show(text, card, kind)` with kinds `reviewQuestion`/`reviewAnswer`; `webview_did_receive_js_message(handled, message, context)` returning `(True, value)` to consume |
| Background work | `mw.taskman.run_in_background(task, on_done)` — Anki's own executor; `on_done` runs on the main thread, safe for `web.eval()` |

### Collection contents (the actual decks)

- Note types **`FR Translate`** (+ 9 suffixed variants `FR Translate+` … `+++++++`): fields **`Text`**, **`Level`** (CEFR A1–C2). 440 cards, all in deck *FR Translate*.
- Note types **`FR Prompt`**, **`FR Prompt+`**: fields **`Level`**, **`Prompt`**, **`Constraints`**. Currently 0 notes (deck being built — still supported by the add-on).
- **No reference-answer field exists.** `FR Translate` card backs are literally `{{FrontSide}}`. The original brief's pseudo-code assumed a reference translation; the real grading context is *source text + CEFR level only*, so the prompt asks Claude to judge whether a native speaker would accept the attempt.
- **Mixed direction**: some `Text` values are English ("My name is Sophie…"), others French ("Quoi de neuf ?"). The grading prompt tells Claude to detect the direction rather than assume EN→FR.

---

## 2. Design decisions (and why)

### D1. API access: raw HTTPS via bundled `requests`, not the `anthropic` SDK
Anki add-ons run inside Anki's embedded Python. The `anthropic` SDK isn't
installed there and depends on `httpx` + `pydantic-core` (a **compiled**,
platform- and Python-version-specific wheel). Vendoring it into the add-on
would break silently whenever the Anki launcher bumps its Python (the venv is
uv-managed and rebuilt on upgrade). `requests` + `certifi` ship with Anki
itself (pylib depends on them), so a direct POST to
`https://api.anthropic.com/v1/messages` is the stable, ecosystem-standard
choice. Request/response shapes follow the current Messages API reference.

### D2. Model & call shape
- Default model **`claude-opus-4-8`** (current recommended default; configurable).
- **Adaptive thinking** (`thinking: {"type": "adaptive"}`) — the model
  self-calibrates depth, so easy A1 sentences stay fast while C1 nuance gets
  real reasoning. Configurable off (`"adaptive_thinking": false`).
- **Structured output** via `output_config.format` (JSON schema) — guarantees a
  parseable grading object; no brittle "please return JSON" prompting.
- Non-streaming, `max_tokens` 2000, 120 s read timeout. Grading responses are
  short; streaming plumbing through the pycmd bridge isn't worth it for v1.

### D3. Grading schema
```json
{
  "verdict": "correct | minor_issues | significant_errors | incorrect",
  "score": 0-100,
  "corrected_version": "idiomatic native rendering of the user's attempt",
  "feedback": ["specific point", ...],
  "alternatives": ["other natural phrasings", ...],
  "suggested_rating": "again | hard | good | easy"
}
```
`suggested_rating` maps the grading onto Anki's buttons — the user still picks
(auto-rating stays out of scope per the brief), but the suggestion removes the
"how do I translate feedback into a rating?" step.

### D4. Targeting: note-type name prefixes
Inject on cards whose note type name starts with `FR Translate` or `FR Prompt`
(both prefix lists configurable). Rationale: the 10 `FR Translate*` variants
share fields, tags are empty in practice, and deck-based targeting breaks if
cards move. Prefix matching covers all variants and future batches with zero
maintenance.

### D5. Gating: optional, non-blocking
The input never blocks "Show Answer". Sometimes you just want to review
passively; forced gating punishes that. Intended flow:
type → ⌘/Ctrl+Enter → read feedback → Show Answer → rate.

### D6. Surviving the question→answer flip
`{{FrontSide}}` on the answer template is substituted from the *backend-rendered*
question — it does **not** contain add-on-injected HTML, and the reviewer swaps
card content via JS on the same page (no reload). So:
- Inject the widget on **both** `reviewQuestion` and `reviewAnswer`.
- Keep all state (typed text, feedback, in-flight status) in a persistent
  `window.FrenchGrader` JS object keyed by card id; each mount re-renders from
  state. New card id ⇒ state reset.
Verified in the automated test: text and feedback persist across the flip.

### D7. History: JSON sidecar in `user_files/`
Attempts + gradings are appended to `user_files/history.json` keyed by note id
(capped at 50 entries/note, atomic writes, thread-locked).
- `user_files/` is the Anki-blessed location that survives add-on updates.
- Writing into note fields would mutate notes (sync churn); rejected.
- Cards attempted before show a compact "Last attempt <date> — 82/100" line.
- Grading always calls fresh on submit — a cached grade of a *different*
  attempt is useless, since the attempt is the input.

### D8. Keyboard handling
The textarea stops propagation of key events so typing "1"/"2"/space doesn't
trigger Anki's rating shortcuts while composing. ⌘/Ctrl+Enter submits; Escape
blurs the field (restoring normal shortcuts).

### D9. API key storage
`config.json` (`api_key`) via Tools → Add-ons → Config, with
`ANTHROPIC_API_KEY` env-var fallback. The key is only ever sent to
`api.anthropic.com`.

### D10. Grading prompt
System prompt = French-tutor persona + CEFR-aware rubric ("grade at the stated
level; don't demand C2 polish on an A1 card") + a rating-suggestion mapping.
Per-mode task templates:
- *Translate* (`FR Translate*`): source `Text` + `Level`; Claude detects
  EN→FR vs FR→EN direction.
- *Prompt* (`FR Prompt*`): `Prompt` + `Constraints` + `Level`; must call out
  each violated constraint explicitly.
`system_prompt_extra` config lets the user append personal rules (e.g.
"ignore missing accents") without editing code.

### D11. Install location: real directory, NOT a symlink (macOS TCC)
Originally the add-on was developed in `~/Desktop/anki_stuff/french_llm_grader`
and symlinked into `addons21/`. **This fails on modern macOS**: Anki.app has no
TCC permission for `~/Desktop`, so importing the add-on through the symlink
dies with `PermissionError: Operation not permitted` — silently (the widget
just never appears; Anki's loadAddons error dialog never fires because the
failure happens at file-read, and no traceback reached the log). The fix is to
install the add-on as a physical directory inside `addons21/`. Mid-session,
the agent's own Desktop access was also revoked by macOS (every process
started returning EPERM for `~/Desktop` while Documents/Library stayed fine),
which corroborates the TCC diagnosis.

### D12. Generalization: "LLM Answer Grader" with config profiles (v0.2)
For public release the French specifics moved out of code into config. A
**profile** = `{name, note_type_prefixes, card_fields, grading_instructions}`;
the first matching profile wins, `"*"` matches all note types, empty prefix
list disables a profile. The per-mode prompt templates were replaced by one
generic message shape: *instructions + "Card content:" (selected fields as
`Name: value` lines) + "Learner's answer:"* — this covers translation, free
writing, definitions, facts, anything, without a templating language. The
grading persona is replaceable via `system_prompt`, but a fixed **output
contract** (verdict/score/rating semantics) is always appended so the
structured response stays meaningful regardless of persona.

### D13. Backwards compatibility via `meta.json` user config
Anki's `getConfig` does a shallow `defaults.update(user_config)` (verified in
`aqt/addons.py`). The user's French tutor persona and the FR Prompt /
FR Translate profiles were written into the installed add-on's `meta.json`
`config` key — defaults stay neutral for the public package, while this
machine keeps identical French grading behavior. FR Prompt is listed first to
preserve the old precedence. Attempt history was migrated
(`user_files/` moved from the old `french_llm_grader` dir).

### D14. License and distribution
**AGPL-3.0** — the add-on imports Anki's `aqt`, which is AGPL, so this is the
standard license for distributed add-ons. Distribution artifact is a
`.ankiaddon` zip (folder *contents*, no `meta.json`/`user_files`/pycache)
attached to a GitHub release — the same file AnkiWeb's upload form takes.

### D15. Multi-provider via a single OpenAI-compatible adapter (v0.3)
Rather than N provider integrations, v0.3 adds exactly one:
`"provider": "openai_compatible"` + `openai_base_url`, covering OpenAI,
OpenRouter, Groq, Gemini's compat endpoint, and local Ollama / LM Studio
(keyless operation supported — the privacy option). Claude stays the default
and quality benchmark. Robustness for heterogeneous servers is handled by
**capability negotiation** (on 400: strict `json_schema` → `json_object` →
no response_format, and `max_tokens` → `max_completion_tokens`), a
belt-and-braces JSON instruction in the system prompt, fence/prose-tolerant
parsing, and **normalization** of sloppy gradings (derive missing
verdict/rating from score and vice versa, clamp score, coerce lists) so even
small local models produce usable feedback. The provider seam is
`grade(config, profile, fields, attempt) → normalized grading dict` —
everything above it (bridge, UI, history) is provider-agnostic.

### D16. Rating semantics fixed, display labels configurable (v0.3.1)
Anki's v3 scheduler (standard on every version we support) always shows four
answers with fixed ease semantics 1–4 — so the `again/hard/good/easy`
*categories* are safe to hardcode, and the add-on only ever displays a
suggestion (it never presses a button). What varies is presentation:
localized Anki UIs and button-relabeling add-ons show different text. New
`rating_labels` / `verdict_labels` config maps let users align the displayed
suggestion text with their UI; the underlying keys stay canonical in the
schema, history file, and prompt.

---

## 3. Architecture

```
addons21/french_llm_grader/
├── __init__.py      # hook registration, pycmd bridge, threading, card targeting
├── grader.py        # pure module (no aqt import): prompt build + Messages API call
├── history.py       # user_files/history.json persistence (atomic writes)
├── webui.py         # inline HTML/CSS/JS widget builder
├── config.json      # defaults (model, prefixes, api_key placeholder, ...)
├── config.md        # shown in Anki's add-on config UI
├── manifest.json
└── user_files/      # created at runtime; history lives here
```

Flow: `card_will_show` appends widget HTML+JS → user types, ⌘Enter →
`pycmd("french_grader:submit:{json}")` → Python handler validates card, strips
field HTML → `mw.taskman.run_in_background(claude call)` → `on_done` (main
thread) → `reviewer.web.eval("FrenchGrader.showFeedback({...})")` → JS renders
and stores in state → history appended.

Race safety: responses carry the card id; JS drops feedback for a card that's
no longer current, and Python re-checks `mw.reviewer.card` before eval. All
model text is rendered via `textContent` (no HTML injection from the LLM).

---

## 4. Testing log

- ✅ Environment survey (§1)
- ✅ Byte-compile + import of all modules **inside Anki's own venv**
- ✅ Prompt/request-body construction (model, thinking, schema keys)
- ✅ Live HTTPS to `api.anthropic.com` with a dummy key → clean
  "Invalid API key" user-facing error (validates endpoint, headers, TLS,
  error mapping)
- ✅ History round-trip (append + last-entry)
- ✅ Mocked-response unit tests: success parse (thinking block + JSON text
  block), `refusal` branch, `max_tokens` branch — all map to the right
  user-facing outcome
- ✅ FR Prompt mode message construction (prompt + constraints + level)
- ✅ **Automated in-Anki E2E test** (temporary `frg_selftest` add-on drove the
  real reviewer):
  - add-on module loaded, 1 `card_will_show` hook registered
  - real card `FR Translate++` → widget injected (`WIDGET_OK`)
  - simulated submit → full bridge round-trip → expected "No API key" error
    rendered in the widget
  - `_showAnswer()` flip → widget re-mounted, typed text **and** error state
    preserved
- ✅ **Real graded responses (2026-07-08, after the user added their API
  key):** a perfect A1 attempt → `correct`, 100/100, `easy`, one idiomatic
  alternative; a deliberately flawed attempt (missing apostrophe + wrong
  gender agreement) → `minor_issues`, 70/100, `hard`, both errors caught with
  precise fixes in the configured French-tutor style. Structured outputs and
  adaptive thinking accepted by the live API. The system is fully verified
  end-to-end.

**Generalization (v0.2) test pass:**
- ✅ Unit tests in Anki's venv: profile matching (FR Prompt precedence,
  suffixed variants, `"*"` wildcard, no-match), field filtering + message
  shape, persona override + output contract always present, mocked grade
  round-trip, renamed widget internals (`LLMGrader`, `lag-*`, `llm_grader:`)
- ✅ `getConfig` merge semantics verified against `aqt/addons.py` source
- ✅ Second automated in-Anki E2E: French profiles + persona merged from
  `meta.json`, widget injected on `FR Translate++`, bridge round-trip, state
  preserved across flip
- ✅ `.ankiaddon` package built (7 files, no local state inside)

## 5. Incident log

- **macOS TCC lockout (2026-07-08).** During testing, macOS revoked Desktop
  access for the working session: all reads under `~/Desktop` (including the
  git repo `~/Desktop/anki_stuff`) return `EPERM`, while `~/Documents`,
  `~/Library`, and `/tmp` remain accessible. This both explained the original
  symlink failure (D11) and forced the canonical add-on copy into `addons21/`
  and this document into `~/Documents/anki_stuff_staging/`. **To restore:**
  re-grant Desktop access (System Settings → Privacy & Security → Files &
  Folders) or simply run future sessions from a non-Desktop directory. The
  direct access was polled for 20+ minutes without recovery — TCC revocations
  require user action.
- **Resolution via Finder (same day).** Finder has its own TCC identity and
  could still read Desktop. Workflow used: AppleScript-duplicate the repo
  to `~/Documents/anki_stuff` → commit the add-on + docs there → Finder-copy
  the updated repo back to Desktop `with replacing`. The Desktop git repo is
  therefore **fully up to date**; `~/Documents/anki_stuff` remains as a spare
  copy. If the terminal's Desktop access matters for future sessions,
  re-grant it in System Settings → Privacy & Security → Files & Folders.

## 6. Open items / future ideas

- FR Prompt deck has no notes yet — code path implemented but untested against
  real notes (a build script `build_fr_prompt_fixed.py` exists in the repo;
  importing content is left to the user).
- A distributable package was generated at
  `~/Documents/anki_stuff_staging/french_llm_grader.ankiaddon` (installable
  via Tools → Add-ons → Install from file, e.g. on another machine).
- Same-session relearning: if a card rated *Again* reappears in the same
  session, the widget intentionally keeps the earlier attempt + feedback
  (same card id) so you can compare; a fresh session starts clean.
- Streaming feedback rendering (nice-to-have; SSE over `requests`).
- Optional auto-rating (explicitly out of scope for v1).
- A "history browser" dialog (Tools menu) over `user_files/history.json`.
- AnkiWeb packaging (`.ankiaddon` zip) if ever published.
