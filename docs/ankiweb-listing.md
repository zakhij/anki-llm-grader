# AnkiWeb listing — copy-paste kit

Upload page: https://ankiweb.net/shared/addons → **Upload** (requires an
AnkiWeb account). Attach the `.ankiaddon` from the latest GitHub release.

- **Title:** `LLM Answer Grader — type your answer, get graded by AI`
- **Support page:** your GitHub repo issues URL (flip the repo public first),
  or a thread you create in https://forums.ankiweb.net (Add-ons category).
- **Compatibility:** min point version `231000` (23.10). Tested on 25.09.

**Description (HTML is allowed on AnkiWeb):**

```html
<b>Type your answer on the card, get it graded by an LLM — inline, before you rate.</b>

<p>Built for language production practice (translations, free writing), and for any card where "compare my answer" needs judgment instead of exact string matching.</p>

<ul>
<li>A text box appears on cards you choose (matched by note type)</li>
<li>Submit with Ctrl/Cmd+Enter → verdict, 0–100 score, corrected version, specific error feedback, alternative phrasings, and a suggested Again/Hard/Good/Easy rating</li>
<li>Your text and feedback stay on screen when you flip to the answer; you still pick the rating</li>
<li>Attempt history is stored locally; cards show your last attempt's score</li>
</ul>

<p><b>Bring your own model:</b> Claude (default, best grading quality), or any OpenAI-compatible endpoint — OpenAI, OpenRouter, Groq, or a fully local &amp; private Ollama / LM Studio server (no card content ever leaves your machine).</p>

<p><b>Setup:</b> Tools → Add-ons → Config: paste your API key, then point a "profile" at your note types and describe the grading task in plain English. Full reference on the config screen and at the support page.</p>

<p>Desktop only (add-ons don't run on AnkiDroid/AnkiMobile; cards behave normally there). API usage is billed to your own key — typically a fraction of a cent per graded card, or free with a local model. Source: AGPL-3.0.</p>
```

**Pre-upload checklist:**
- [ ] Flip the GitHub repo public (or create a forums.ankiweb.net support thread)
- [ ] Test-install the `.ankiaddon` from the release into a clean profile
- [ ] After upload, note the assigned add-on ID and add it to the README
