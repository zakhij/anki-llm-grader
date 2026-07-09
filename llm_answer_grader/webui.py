# Builds the HTML/CSS/JS injected into the reviewer. Everything is inlined
# (no web exports needed). State lives in window.LLMGrader, which persists
# across the question->answer flip because the reviewer swaps card content on
# the same page; each mount re-renders from that state.

from __future__ import annotations

import json
from typing import Any, Dict, Optional

CSS = """
#lag-root { margin-top: 1.4em; text-align: left; font-size: 15px; }
.lag-box { max-width: 620px; margin: 0 auto; padding: 12px 14px; border: 1px solid #d0d0d0;
  border-radius: 10px; background: #fafafa; }
.night_mode .lag-box { background: #2c2c30; border-color: #444; }
.lag-prev { font-size: 12.5px; color: #888; margin-bottom: 8px; }
.lag-textarea { width: 100%; box-sizing: border-box; min-height: 64px; resize: vertical;
  font: inherit; padding: 8px; border: 1px solid #c8c8c8; border-radius: 6px;
  background: #fff; color: inherit; }
.night_mode .lag-textarea { background: #202024; border-color: #555; }
.lag-controls { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.lag-btn { font: inherit; font-size: 14px; padding: 6px 14px; border-radius: 6px;
  border: none; background: #4a68d8; color: #fff; cursor: pointer; }
.lag-btn:disabled { opacity: .55; cursor: default; }
.lag-hint { font-size: 12px; color: #999; }
.lag-status { font-size: 13px; color: #888; }
.lag-error { margin-top: 8px; font-size: 13.5px; color: #c0392b; }
.night_mode .lag-error { color: #e77; }
.lag-feedback { margin-top: 12px; border-top: 1px solid #e0e0e0; padding-top: 10px; }
.night_mode .lag-feedback { border-top-color: #444; }
.lag-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.lag-badge { font-size: 13px; font-weight: 600; padding: 3px 10px; border-radius: 999px; color: #fff; }
.lag-badge.correct { background: #2e9e5b; }
.lag-badge.minor_issues { background: #b9a41f; }
.lag-badge.significant_errors { background: #d87e2e; }
.lag-badge.incorrect { background: #c94040; }
.lag-score { font-size: 13px; color: #777; }
.lag-suggest { font-size: 12.5px; color: #777; border: 1px solid #ccc; border-radius: 999px; padding: 2px 9px; }
.night_mode .lag-suggest { border-color: #555; color: #aaa; }
.lag-corrected { margin: 10px 0 4px; font-size: 16px; line-height: 1.5; }
.lag-corrected .lag-label, .lag-alts .lag-label, .lag-points .lag-label,
.lag-fu-answer .lag-label {
  display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
  color: #999; margin-bottom: 3px; }
.lag-points ul, .lag-alts ul { margin: 4px 0 8px; padding-left: 20px; }
.lag-points li, .lag-alts li { margin: 3px 0; line-height: 1.45; }
.lag-fu { margin-top: 10px; }
.lag-fu-row { display: flex; gap: 8px; }
.lag-fu-input { flex: 1; font: inherit; font-size: 13.5px; padding: 6px 8px;
  border: 1px solid #c8c8c8; border-radius: 6px; background: #fff; color: inherit; }
.night_mode .lag-fu-input { background: #202024; border-color: #555; }
.lag-fu-btn { padding: 6px 12px; }
.lag-fu-answer { margin-bottom: 8px; font-size: 14px; line-height: 1.5; }
"""

# The persistent client. Defined once per reviewer page; mount() is called on
# every question/answer render.
JS = r"""
(function () {
  if (window.LLMGrader) return;
  // Default display labels; overridable per-mount via config
  // ("verdict_labels" / "rating_labels") for other languages or relabeled
  // answer buttons. The four rating keys mirror Anki's fixed ease values 1-4.
  var VERDICTS = {
    correct: "Correct",
    minor_issues: "Minor issues",
    significant_errors: "Needs work",
    incorrect: "Incorrect"
  };
  var RATINGS = { again: "Again", hard: "Hard", good: "Good", easy: "Easy" };

  function label(table, overrides, key) {
    return (overrides && overrides[key]) || table[key] || key;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  window.LLMGrader = {
    state: null,

    reset: function (cardId) {
      this.state = { cardId: cardId, text: "", status: "idle",
                     feedback: null, error: null, prev: null,
                     fuQuestion: "", fuAnswer: null, fuError: null,
                     fuStatus: "idle" };
    },

    mount: function (cardId, prev, labels) {
      if (!this.state || this.state.cardId !== cardId) this.reset(cardId);
      this.state.prev = prev;
      this.labels = labels || {};
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
      pycmd("llm_grader:submit:" + JSON.stringify({ cardId: s.cardId, text: text }));
    },

    showFeedback: function (data) {
      var s = this.state;
      if (!s || data.cardId !== s.cardId) return;
      s.status = "done";
      s.feedback = data.grading;
      s.error = null;
      this.render();
      this.unfocus();  // free the keyboard for Anki's rating shortcuts
    },

    showError: function (data) {
      var s = this.state;
      if (!s || data.cardId !== s.cardId) return;
      s.status = "idle";
      s.error = data.message;
      this.render();
      this.unfocus();
    },

    askFollowUp: function () {
      var s = this.state;
      if (!s || !s.feedback) return;
      var q = (s.fuQuestion || "").trim();
      if (!q || s.fuStatus === "asking") return;
      if (typeof pycmd === "undefined") return;
      s.fuStatus = "asking";
      s.fuAnswer = null;
      s.fuError = null;
      this.render();
      pycmd("llm_grader:followup:" + JSON.stringify({ cardId: s.cardId, question: q }));
    },

    showFollowUp: function (data) {
      var s = this.state;
      if (!s || data.cardId !== s.cardId) return;
      s.fuStatus = "idle";
      if (data.error) { s.fuError = data.error; }
      else { s.fuAnswer = data.answer; s.fuQuestion = ""; }
      this.render();
    },

    unfocus: function () {
      var root = document.getElementById("lag-root");
      var active = document.activeElement;
      if (root && active && root.contains(active)) active.blur();
    },

    render: function () {
      var root = document.getElementById("lag-root");
      var s = this.state;
      if (!root || !s) return;
      var self = this;
      root.innerHTML = "";
      var box = el("div", "lag-box");

      if (s.prev && !s.feedback) {
        var when = new Date(s.prev.ts * 1000).toLocaleDateString();
        box.appendChild(el("div", "lag-prev",
          "Last attempt " + when + " — " + s.prev.score + "/100 (" +
          label(VERDICTS, this.labels.verdicts, s.prev.verdict) + ")"));
      }

      var ta = el("textarea", "lag-textarea");
      ta.placeholder = "Type your answer…";
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

      var controls = el("div", "lag-controls");
      var btn = el("button", "lag-btn",
        s.status === "grading" ? "Grading…" : "Grade with Claude");
      btn.disabled = s.status === "grading";
      btn.addEventListener("click", function () { self.submit(); });
      controls.appendChild(btn);
      if (s.status === "grading") {
        controls.appendChild(el("span", "lag-status", "asking Claude…"));
      } else {
        controls.appendChild(el("span", "lag-hint", "⌘/Ctrl+Enter to submit"));
      }
      box.appendChild(controls);

      if (s.error) box.appendChild(el("div", "lag-error", s.error));
      if (s.feedback) {
        box.appendChild(this.buildFeedback(s.feedback));
        box.appendChild(this.buildFollowUp());
      }

      root.appendChild(box);
    },

    buildFollowUp: function () {
      var s = this.state;
      var self = this;
      var wrap = el("div", "lag-fu");

      if (s.fuAnswer) {
        var ans = el("div", "lag-fu-answer");
        ans.appendChild(el("span", "lag-label", "Answer"));
        ans.appendChild(document.createTextNode(s.fuAnswer));
        wrap.appendChild(ans);
      }
      if (s.fuError) wrap.appendChild(el("div", "lag-error", s.fuError));

      var row = el("div", "lag-fu-row");
      var input = el("input", "lag-fu-input");
      input.type = "text";
      input.placeholder = "Ask about this grading… (e.g. why is that wrong?)";
      input.value = s.fuQuestion;
      input.disabled = s.fuStatus === "asking";
      input.addEventListener("input", function () { s.fuQuestion = input.value; });
      ["keydown", "keyup", "keypress"].forEach(function (evt) {
        input.addEventListener(evt, function (e) {
          e.stopPropagation();
          if (evt === "keydown" && e.key === "Enter") {
            e.preventDefault();
            self.askFollowUp();
          }
          if (evt === "keydown" && e.key === "Escape") input.blur();
        });
      });
      row.appendChild(input);
      var btn = el("button", "lag-btn lag-fu-btn",
        s.fuStatus === "asking" ? "…" : "Ask");
      btn.disabled = s.fuStatus === "asking";
      btn.addEventListener("click", function () { self.askFollowUp(); });
      row.appendChild(btn);
      wrap.appendChild(row);
      return wrap;
    },

    buildFeedback: function (g) {
      var panel = el("div", "lag-feedback");
      var head = el("div", "lag-head");
      head.appendChild(el("span", "lag-badge " + g.verdict,
        label(VERDICTS, this.labels.verdicts, g.verdict)));
      head.appendChild(el("span", "lag-score", g.score + "/100"));
      head.appendChild(el("span", "lag-suggest",
        (this.labels.suggested_prefix || "Suggested: ") +
        label(RATINGS, this.labels.ratings, g.suggested_rating)));
      panel.appendChild(head);

      if (g.corrected_version) {
        var corr = el("div", "lag-corrected");
        corr.appendChild(el("span", "lag-label", "Better version"));
        corr.appendChild(document.createTextNode(g.corrected_version));
        panel.appendChild(corr);
      }
      if (g.feedback && g.feedback.length) {
        var pts = el("div", "lag-points");
        pts.appendChild(el("span", "lag-label", "Feedback"));
        var ul = el("ul");
        g.feedback.forEach(function (p) { ul.appendChild(el("li", null, p)); });
        pts.appendChild(ul);
        panel.appendChild(pts);
      }
      if (g.alternatives && g.alternatives.length) {
        var alts = el("div", "lag-alts");
        alts.appendChild(el("span", "lag-label", "Also acceptable"));
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


def widget_html(
    card_id: int,
    prev_entry: Optional[Dict[str, Any]],
    labels: Optional[Dict[str, Any]] = None,
) -> str:
    prev = None
    if prev_entry:
        prev = {
            "ts": prev_entry.get("ts"),
            "score": prev_entry.get("score"),
            "verdict": prev_entry.get("verdict"),
        }
    return (
        f"<style id='lag-style'>{CSS}</style>"
        "<div id='lag-root'></div>"
        f"<script>{JS}\nLLMGrader.mount({_js_json(card_id)}, {_js_json(prev)}, "
        f"{_js_json(labels or {})});</script>"
    )
