# AnkiWeb listing — copy-paste kit

**Published:** https://ankiweb.net/shared/info/365951175 — add-on ID
`365951175`, first published 2026-07-09.

**To update:** open the listing while signed in → **Update** (bottom of the
page) → in the upload form, choose the `.ankiaddon` from the latest GitHub
release — **as-is; it's already a zip, don't re-zip it** — then Save. Same
listing, same ID; never create a second listing.

- **Title:** `LLM Answer Grader — type your answer, get graded by AI`
- **Support page:** your GitHub repo issues URL (flip the repo public first),
  or a thread you create in https://forums.ankiweb.net (Add-ons category).
- **Branches:** one branch, **min `23.10` to max `25.09.4`** (dotted Anki
  version strings — the integer point-version format like `231000` is
  rejected with BadRequest; that format is only for `manifest.json`). Don't
  minus-prefix the max: a plain max is informational and newer Anki versions
  can still install. Bump the max as you test newer releases.
- **Updates:** re-upload the new `.ankiaddon` into the *same* listing (edit
  it from your account) — never create a second listing, or you'll mint a
  new add-on ID and strand existing users.

**Description (HTML is allowed on AnkiWeb; screenshots are hotlinked from
this repo's `docs/screenshots/`, so re-pushing updated images under the same
names updates the listing automatically):**

```html
<b>Type your answer on the card, get it graded by an LLM — inline, before you rate.</b>

<p>Built for language production practice (translations, free writing), and for any card where "compare my answer" needs judgment instead of exact string matching.</p>

<img src="https://raw.githubusercontent.com/zakhij/anki-llm-grader/main/docs/screenshots/03-graded.png">

<ul>
<li>A text box appears on cards you choose (matched by note type)</li>
<li>Submit with Ctrl/Cmd+Enter → verdict, 0–100 score, corrected version, specific error feedback, alternative phrasings, and a suggested Again/Hard/Good/Easy rating</li>
<li><b>Ask follow-up questions</b> about any grading ("why is that wrong?") — answered in the context of your attempt</li>
<li>Optional <b>accent keyboard</b> per profile (French: à â æ ç é è …) for typing accents on a bare QWERTY</li>
<li>Your text and feedback stay on screen when you flip to the answer; you still pick the rating</li>
<li>Attempt history is stored locally; cards show your last attempt's score</li>
</ul>

<p>Ask a follow-up about any grading and get a grounded answer before you rate:</p>

<img src="https://raw.githubusercontent.com/zakhij/anki-llm-grader/main/docs/screenshots/05-followup-answer.png">

<p><b>Easy setup:</b> a visual settings dialog (Tools → LLM Answer Grader Settings) with note-type and field pickers — no JSON editing required (raw config remains available for power users).</p>

<img src="https://raw.githubusercontent.com/zakhij/anki-llm-grader/main/docs/screenshots/01-settings.png">

<p><b>Bring your own model:</b> Claude (default, best grading quality), or any OpenAI-compatible endpoint — OpenAI, OpenRouter, Groq, or a fully local &amp; private Ollama / LM Studio server (no card content ever leaves your machine). Different decks can use different models: e.g. a free local model for easy cards, Claude for hard ones.</p>

<p>Desktop only (add-ons don't run on AnkiDroid/AnkiMobile; cards behave normally there). API usage is billed to your own key — typically a fraction of a cent per graded card, or free with a local model. Source: AGPL-3.0.</p>
```

**Per-update checklist:**
- [ ] Test-install the `.ankiaddon` from the release into a clean profile
- [ ] Bump the branch max version if a newer Anki was tested
- [ ] Update the listing description if the release added user-visible features
