# Anki LLM Grader — Project Brief

## Problem statement

Current French study flow with Anki:

1. Card front shows a sentence (FR Translate) or prompt+constraints (FR Prompt).
2. User writes a translation/response by hand or in a separate app.
3. User copies attempt + reference into Claude (or another LLM) with a prompt like *"grade my translation"*.
4. User reads the LLM feedback.
5. User returns to Anki and rates the card Easy / Good / Hard / Again based on the feedback.

Steps 3–4 are friction-heavy: context-switching, re-pasting, losing the LLM thread, no record of past attempts. The goal is to **collapse the entire loop into the Anki reviewer itself**.

## Target experience

While reviewing a card:
- A text input field appears below the prompt.
- User types their attempt.
- Hits submit → Claude grades it inline.
- Feedback renders directly on the card.
- User rates the card and moves on.

## Scope

### In scope
- Anki **Desktop** (macOS, the user's platform).
- FR Translate and FR Prompt decks (filtered by tag or note type).
- Calls to the Claude API (Anthropic SDK).
- Configurable grading prompt + model selection.
- Local API key storage via Anki's standard `config.json`.

### Out of scope (initial version)
- AnkiDroid / AnkiMobile / iOS — add-ons don't run on mobile, and the JS bridge doesn't exist there. Mobile reviews fall back to the existing manual flow.
- AnkiWeb sync of feedback history.
- Multi-LLM provider abstraction (Claude only for v1).
- Auto-rating the card based on grading (user still picks Easy/Good/Hard/Again).

### Open design questions
- **Targeting:** Inject the input on all cards in FR decks? On any card with a `FR::*` tag? Based on note type name?
- **Gating:** Must submit before "Show Answer" unlocks, or optional?
- **Grading prompt:** What system prompt does Claude get? Includes user attempt + reference text + DELF-style rubric?
- **Caching:** Re-show prior grading on subsequent reviews of the same card, or always call fresh?
- **History:** Store past attempts in a sidecar file or note field?

---

## Architectural research

### Anki extensibility (desktop)
- Add-ons are Python packages in `~/Library/Application Support/Anki2/addons21/<name>/`.
- The reviewer is a Chromium webview (Qt WebEngine) — full HTML/CSS/JS support.
- **Critical constraint:** JS inside card templates cannot make HTTP requests. CORS blocks calls to external APIs from the webview's local origin. Confirmed by Anki forum moderators.
- **Solution:** A Python add-on acts as a bridge. JS in the card calls `pycmd(...)`; Python catches it, calls Claude API, pushes result back via `webview.eval(...)`.

### Hooks to use
| Hook | Purpose |
|------|---------|
| `gui_hooks.card_will_show(html, card, context)` | Inject `<input>` + submit button into card HTML before rendering. Returns modified HTML. |
| `gui_hooks.webview_did_receive_js_message(handled, message, context)` | Catch `pycmd("grader:submit:<text>")` calls from JS. |
| `gui_hooks.webview_will_set_content(web_content, context)` | Inject CSS/JS asset files into the webview. |
| `mw.reviewer.web.eval(js_string)` | Push the grading result back into the DOM after the API call returns. |

### `pycmd` bridge convention
- JS: `pycmd("french_grader:submit:<user_text>", function(result) { ... })`
- Python handler returns `(True, return_value)`; result is JSON-serialized back to the JS callback.
- For async (LLM call takes 1–5 seconds), pattern is: JS sends pycmd → Python kicks off background thread → background thread does the API call → on completion, pushes result back via `web.eval(f"showFeedback({json.dumps(data)})")`.

### Mobile compatibility
| Platform | Status |
|----------|--------|
| Anki Desktop (macOS/Win/Linux) | Full support — Python add-ons + `pycmd` available |
| AnkiDroid (Android) | Java/Kotlin codebase — no Python add-ons. JS in templates runs but can't call out. |
| AnkiMobile (iOS) | Swift/ObjC codebase — same story as AnkiDroid. |

Result: feature degrades gracefully on mobile. Card template detects `pycmd` availability and hides the input field if absent.

---

## Prior art (existing add-ons)

| Add-on | Relevance |
|--------|-----------|
| **SmartReviewPad** ([github.com/Dor-sketch/anki-interactive-addon](https://github.com/Dor-sketch/anki-interactive-addon)) | **Closest reference.** Adds an interactive input field to the reviewer, auto-checks answers, plays sound feedback, tracks streaks. Uses exactly the hook pattern we'll use — local string matching instead of LLM grading. Replace the matching logic with a Claude API call. |
| **Anki Terminator V2** (AnkiWeb ID: 1468920185) | Opens a ChatGPT/Gemini sidebar during review. Proves "LLM during review" is a solved problem. Different UX though (sidebar vs. inline). |
| **AnkiBrain / AnkiChatGPT** (AnkiWeb ID: 1915225457) | GPT integration focused on card *creation*, not review-time grading. |
| **Anki AI** (AnkiWeb ID: 643253121) | Card enhancement at authoring time. |
| **AnkiAIUtils** ([github.com/thiswillbeyourgithub/AnkiAIUtils](https://github.com/thiswillbeyourgithub/AnkiAIUtils)) | CLI scripts that enhance cards with LLM-generated explanations. Demonstrates calling LLMs from Python in the Anki ecosystem. |
| **Anki MCP** ([ankimcp.ai](https://ankimcp.ai)) | MCP server connecting Claude to Anki for card creation. External tool, but proves Claude+Anki integration. |

**No existing add-on does this exact flow** (inline input → LLM grading → feedback before rating). All the building blocks are proven individually, just not combined.

---

## Reference docs

### Anki add-on development
- [Writing Anki Add-ons (official)](https://addon-docs.ankiweb.net/)
- [Hooks and Filters](https://addon-docs.ankiweb.net/hooks-and-filters.html)
- [Reviewer JavaScript](https://addon-docs.ankiweb.net/reviewer-javascript.html)
- [Add-on Folders](https://addon-docs.ankiweb.net/addon-folders.html)
- [Add-on Config](https://addon-docs.ankiweb.net/addon-config.html)

### Anki templating + JS
- [Templates: Styling & HTML / JavaScript](https://docs.ankiweb.net/templates/styling.html)
- [Field Replacements (incl. type-answer)](https://docs.ankiweb.net/templates/fields.html)

### External API access
- [Forum thread: accessing external URLs from JS — confirms it's blocked, must use add-on](https://forums.ankiweb.net/t/accessing-external-programs-or-urls-with-javascript/66121)
- [Forum thread: pycmd conventions](https://forums.ankiweb.net/t/convention-for-messages-sent-with-pycmd/47349)
- [Forum thread: bidirectional pycmd / async results](https://forums.ankiweb.net/t/how-to-ask-for-a-value-from-my-add-ons-python-code-from-js/26249)

### AnkiConnect (alternative integration path)
- [AnkiConnect repo (SourceHut)](https://git.sr.ht/~foosoft/anki-connect)
- [AnkiConnect API reference](https://deepwiki.com/amikey/anki-connect/2.2-api-reference)
- *Verdict:* useful if we ever want an external dashboard, but native add-on is the right fit for the inline review experience.

### Mobile constraints
- [AnkiDroid JavaScript API wiki](https://github.com/ankidroid/Anki-Android/wiki/AnkiDroid-Javascript-API)
- [AnkiDroid issue: JS add-ons feature request](https://github.com/ankidroid/Anki-Android/issues/7959)
- [Forum: AnkiMobile JS compatibility](https://forums.ankiweb.net/t/javascript-code-compatibility-issue-with-ankimobile-on-ios/57299)

### Anthropic SDK
- [Anthropic Python SDK on PyPI](https://pypi.org/project/anthropic/) — `pip install anthropic`
- Standard usage: `anthropic.Anthropic(api_key=...).messages.create(model=..., messages=...)`

---

## Implementation outline (planned, not yet started)

```
addons21/french_llm_grader/
├── __init__.py          # main entry — registers hooks
├── config.json          # default config (model, API key placeholder, prompt template)
├── config.md            # rendered in Anki's add-on config UI
├── grader.py            # Claude API call logic, runs in background thread
├── injector.py          # builds the HTML to inject (input field + submit btn + feedback div)
└── web/
    ├── grader.js        # client-side: capture submit, call pycmd, render feedback
    └── grader.css       # styling for input field + feedback panel
```

**Core flow (pseudo-code):**

```python
# __init__.py
from aqt import mw
from aqt.gui_hooks import card_will_show, webview_did_receive_js_message
from .grader import grade_async
from .injector import build_input_html

def on_card_will_show(html, card, context):
    if context != "reviewQuestion":
        return html
    if not should_inject(card):  # tag/note-type filter
        return html
    return html + build_input_html()

def on_js_message(handled, message, context):
    if not message.startswith("french_grader:"):
        return handled
    _, action, payload = message.split(":", 2)
    if action == "submit":
        card = mw.reviewer.card
        grade_async(
            user_text=payload,
            reference=card.note().fields[0],
            on_done=lambda fb: mw.reviewer.web.eval(
                f"window.showFeedback({json.dumps(fb)})"
            ),
        )
        return (True, None)
    return handled

card_will_show.append(on_card_will_show)
webview_did_receive_js_message.append(on_js_message)
```

### Estimated work
- Skeleton + injection: ~30 min
- Claude API integration with threading: ~1 hr
- UI styling + feedback rendering: ~1 hr
- Config UI + API key handling: ~30 min
- Polish + edge cases (empty input, API errors, slow response): ~1–2 hr

**Total: roughly an afternoon for a working v1.**

### Known gotchas
- Background thread for API call to avoid freezing Anki UI.
- Recent Anki versions (25.02+) added webview security restrictions — may need to whitelist the AnkiWebViewKind.
- Add-on must guard against being invoked on non-FR cards.
- Card template JS must `typeof pycmd === 'undefined'` check to hide input on mobile.
