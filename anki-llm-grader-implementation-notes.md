# Anki LLM Grader — Implementation Notes & Decisions

*Working document maintained by Claude while building the add-on described in
`anki-llm-grader-project.md`. Last updated: 2026-07-08.*

## Status

**Working.** The add-on is installed at
`~/Library/Application Support/Anki2/addons21/french_llm_grader/` and passed an
automated in-Anki end-to-end test (widget injection → submit → bridge round
trip → feedback rendering → state survives card flip). The one thing that
could not be verified is a real graded response, because **no Anthropic API
key exists on this machine** — add yours via Tools → Add-ons → French LLM
Grader → Config, then review any FR Translate card.

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
- ⬜ Real graded response — requires the user's API key (none on this
  machine). Everything up to and including the HTTP request is verified; the
  request body follows the documented Messages API shape (structured outputs
  + adaptive thinking).

## 5. Incident log

- **macOS TCC lockout (2026-07-08).** During testing, macOS revoked Desktop
  access for the working session: all reads under `~/Desktop` (including the
  git repo `~/Desktop/anki_stuff`) return `EPERM`, while `~/Documents`,
  `~/Library`, and `/tmp` remain accessible. This both explained the original
  symlink failure (D11) and forced the canonical add-on copy into `addons21/`
  and this document into `~/Documents/anki_stuff_staging/`. **To restore:**
  re-grant Desktop access (System Settings → Privacy & Security → Files &
  Folders) or simply run future sessions from a non-Desktop directory. The
  git repo on Desktop has the project brief + deck scripts committed; the
  add-on source and this document still need to be synced into it once access
  is back (copies staged in `~/Documents/anki_stuff_staging/`). Access was
  polled for 20+ minutes without recovery — TCC revocations require user
  action. Run `~/Documents/anki_stuff_staging/sync_to_desktop_repo.sh` after
  re-granting, or ask Claude to do it.

## 6. Open items / future ideas

- Sync staged files back into the Desktop git repo + commit (blocked on TCC).
- FR Prompt deck has no notes yet — code path implemented but untested against
  real notes.
- Streaming feedback rendering (nice-to-have; SSE over `requests`).
- Optional auto-rating (explicitly out of scope for v1).
- A "history browser" dialog (Tools menu) over `user_files/history.json`.
- AnkiWeb packaging (`.ankiaddon` zip) if ever published.
