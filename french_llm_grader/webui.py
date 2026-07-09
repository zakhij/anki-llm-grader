# Builds the HTML/CSS/JS injected into the reviewer. Everything is inlined
# (no web exports needed). State lives in window.FrenchGrader, which persists
# across the question->answer flip because the reviewer swaps card content on
# the same page; each mount re-renders from that state.

from __future__ import annotations

import json
from typing import Any, Dict, Optional

CSS = """
#frg-root { margin-top: 1.4em; text-align: left; font-size: 15px; }
.frg-box { max-width: 620px; margin: 0 auto; padding: 12px 14px; border: 1px solid #d0d0d0;
  border-radius: 10px; background: #fafafa; }
.night_mode .frg-box { background: #2c2c30; border-color: #444; }
.frg-prev { font-size: 12.5px; color: #888; margin-bottom: 8px; }
.frg-textarea { width: 100%; box-sizing: border-box; min-height: 64px; resize: vertical;
  font: inherit; padding: 8px; border: 1px solid #c8c8c8; border-radius: 6px;
  background: #fff; color: inherit; }
.night_mode .frg-textarea { background: #202024; border-color: #555; }
.frg-controls { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.frg-btn { font: inherit; font-size: 14px; padding: 6px 14px; border-radius: 6px;
  border: none; background: #4a68d8; color: #fff; cursor: pointer; }
.frg-btn:disabled { opacity: .55; cursor: default; }
.frg-hint { font-size: 12px; color: #999; }
.frg-status { font-size: 13px; color: #888; }
.frg-error { margin-top: 8px; font-size: 13.5px; color: #c0392b; }
.night_mode .frg-error { color: #e77; }
.frg-feedback { margin-top: 12px; border-top: 1px solid #e0e0e0; padding-top: 10px; }
.night_mode .frg-feedback { border-top-color: #444; }
.frg-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.frg-badge { font-size: 13px; font-weight: 600; padding: 3px 10px; border-radius: 999px; color: #fff; }
.frg-badge.correct { background: #2e9e5b; }
.frg-badge.minor_issues { background: #b9a41f; }
.frg-badge.significant_errors { background: #d87e2e; }
.frg-badge.incorrect { background: #c94040; }
.frg-score { font-size: 13px; color: #777; }
.frg-suggest { font-size: 12.5px; color: #777; border: 1px solid #ccc; border-radius: 999px; padding: 2px 9px; }
.night_mode .frg-suggest { border-color: #555; color: #aaa; }
.frg-corrected { margin: 10px 0 4px; font-size: 16px; line-height: 1.5; }
.frg-corrected .frg-label, .frg-alts .frg-label, .frg-points .frg-label {
  display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
  color: #999; margin-bottom: 3px; }
.frg-points ul, .frg-alts ul { margin: 4px 0 8px; padding-left: 20px; }
.frg-points li, .frg-alts li { margin: 3px 0; line-height: 1.45; }
"""

# The persistent client. Defined once per reviewer page; mount() is called on
# every question/answer render.
JS = r"""
(function () {
  if (window.FrenchGrader) return;
  var VERDICTS = {
    correct: "Correct",
    minor_issues: "Minor issues",
    significant_errors: "Needs work",
    incorrect: "Incorrect"
  };
  var RATINGS = { again: "Again", hard: "Hard", good: "Good", easy: "Easy" };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  window.FrenchGrader = {
    state: null,

    reset: function (cardId) {
      this.state = { cardId: cardId, text: "", status: "idle",
                     feedback: null, error: null, prev: null };
    },

    mount: function (cardId, prev) {
      if (!this.state || this.state.cardId !== cardId) this.reset(cardId);
      this.state.prev = prev;
      this.render();
    },

    submit: function () {
      var s = this.state;
      if (!s) return;
      var text = (s.text || "").trim();
      if (!text || s.status === "grading") return;
      if (typeof pycmd === "undefined") return;
      s.status = "grading";
      s.error = null;
      this.render();
      pycmd("french_grader:submit:" + JSON.stringify({ cardId: s.cardId, text: text }));
    },

    showFeedback: function (data) {
      var s = this.state;
      if (!s || data.cardId !== s.cardId) return;
      s.status = "done";
      s.feedback = data.grading;
      s.error = null;
      this.render();
    },

    showError: function (data) {
      var s = this.state;
      if (!s || data.cardId !== s.cardId) return;
      s.status = "idle";
      s.error = data.message;
      this.render();
    },

    render: function () {
      var root = document.getElementById("frg-root");
      var s = this.state;
      if (!root || !s) return;
      var self = this;
      root.innerHTML = "";
      var box = el("div", "frg-box");

      if (s.prev && !s.feedback) {
        var when = new Date(s.prev.ts * 1000).toLocaleDateString();
        box.appendChild(el("div", "frg-prev",
          "Last attempt " + when + " — " + s.prev.score + "/100 (" +
          (VERDICTS[s.prev.verdict] || s.prev.verdict) + ")"));
      }

      var ta = el("textarea", "frg-textarea");
      ta.placeholder = "Type your French here…";
      ta.value = s.text;
      ta.disabled = s.status === "grading";
      ta.addEventListener("input", function () { s.text = ta.value; });
      ["keydown", "keyup", "keypress"].forEach(function (evt) {
        ta.addEventListener(evt, function (e) {
          // Keep typed keys away from Anki's reviewer shortcuts (1-4, space...)
          e.stopPropagation();
          if (evt === "keydown" && e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            self.submit();
          }
          if (evt === "keydown" && e.key === "Escape") ta.blur();
        });
      });
      box.appendChild(ta);

      var controls = el("div", "frg-controls");
      var btn = el("button", "frg-btn",
        s.status === "grading" ? "Grading…" : "Grade with Claude");
      btn.disabled = s.status === "grading";
      btn.addEventListener("click", function () { self.submit(); });
      controls.appendChild(btn);
      if (s.status === "grading") {
        controls.appendChild(el("span", "frg-status", "asking Claude…"));
      } else {
        controls.appendChild(el("span", "frg-hint", "⌘/Ctrl+Enter to submit"));
      }
      box.appendChild(controls);

      if (s.error) box.appendChild(el("div", "frg-error", s.error));
      if (s.feedback) box.appendChild(this.buildFeedback(s.feedback));

      root.appendChild(box);
    },

    buildFeedback: function (g) {
      var panel = el("div", "frg-feedback");
      var head = el("div", "frg-head");
      head.appendChild(el("span", "frg-badge " + g.verdict,
        VERDICTS[g.verdict] || g.verdict));
      head.appendChild(el("span", "frg-score", g.score + "/100"));
      head.appendChild(el("span", "frg-suggest",
        "Suggested: " + (RATINGS[g.suggested_rating] || g.suggested_rating)));
      panel.appendChild(head);

      if (g.corrected_version) {
        var corr = el("div", "frg-corrected");
        corr.appendChild(el("span", "frg-label", "Natural version"));
        corr.appendChild(document.createTextNode(g.corrected_version));
        panel.appendChild(corr);
      }
      if (g.feedback && g.feedback.length) {
        var pts = el("div", "frg-points");
        pts.appendChild(el("span", "frg-label", "Feedback"));
        var ul = el("ul");
        g.feedback.forEach(function (p) { ul.appendChild(el("li", null, p)); });
        pts.appendChild(ul);
        panel.appendChild(pts);
      }
      if (g.alternatives && g.alternatives.length) {
        var alts = el("div", "frg-alts");
        alts.appendChild(el("span", "frg-label", "Also natural"));
        var ul2 = el("ul");
        g.alternatives.forEach(function (a) { ul2.appendChild(el("li", null, a)); });
        alts.appendChild(ul2);
        panel.appendChild(alts);
      }
      return panel;
    }
  };
})();
"""


def _js_json(obj: Any) -> str:
    # </script>-safe JSON literal for embedding in inline <script>
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def widget_html(card_id: int, prev_entry: Optional[Dict[str, Any]]) -> str:
    prev = None
    if prev_entry:
        prev = {
            "ts": prev_entry.get("ts"),
            "score": prev_entry.get("score"),
            "verdict": prev_entry.get("verdict"),
        }
    return (
        f"<style id='frg-style'>{CSS}</style>"
        "<div id='frg-root'></div>"
        f"<script>{JS}\nFrenchGrader.mount({_js_json(card_id)}, {_js_json(prev)});</script>"
    )
