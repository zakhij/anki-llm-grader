# French LLM Grader — inline Claude grading in the Anki reviewer.
# Injects a text input on FR Translate / FR Prompt cards; submissions are
# graded by the Claude API in a background thread and rendered on the card.

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer

from . import grader, history, webui

try:
    from anki.utils import strip_html
except ImportError:  # older naming
    from anki.utils import stripHTML as strip_html  # type: ignore


def _config() -> Dict[str, Any]:
    return mw.addonManager.getConfig(__name__) or {}


def _mode_for(card) -> Optional[str]:
    cfg = _config()
    name = card.note().note_type()["name"]
    for prefix in cfg.get("prompt_note_type_prefixes") or ["FR Prompt"]:
        if name.startswith(prefix):
            return "prompt"
    for prefix in cfg.get("translate_note_type_prefixes") or ["FR Translate"]:
        if name.startswith(prefix):
            return "translate"
    return None


def on_card_will_show(text: str, card, kind: str) -> str:
    if kind not in ("reviewQuestion", "reviewAnswer"):
        return text
    if _mode_for(card) is None:
        return text
    prev = None
    if _config().get("show_previous_attempt", True):
        prev = history.last_entry(card.nid)
    return text + webui.widget_html(card.id, prev)


def on_js_message(handled, message: str, context) -> Any:
    if not message.startswith("french_grader:"):
        return handled
    if not isinstance(context, Reviewer):
        return handled
    _, action, payload = message.split(":", 2)
    if action == "submit":
        _handle_submit(payload)
        return (True, None)
    return handled


def _handle_submit(payload: str) -> None:
    try:
        req = json.loads(payload)
    except ValueError:
        return
    card = mw.reviewer.card
    if card is None or card.id != req.get("cardId"):
        return
    mode = _mode_for(card)
    if mode is None:
        return
    attempt = (req.get("text") or "").strip()
    if not attempt:
        return

    note = card.note()
    fields = {name: strip_html(note[name]).strip() for name in note.keys()}
    cfg = _config()
    card_id, note_id = card.id, note.id

    def task() -> Dict[str, Any]:
        return grader.grade(cfg, mode, fields, attempt)

    def on_done(fut) -> None:
        try:
            grading = fut.result()
        except grader.GraderError as e:
            _eval_js("showError", {"cardId": card_id, "message": str(e)})
            return
        except Exception as e:  # noqa: BLE001 — never let a bug kill the UI silently
            _eval_js("showError", {"cardId": card_id, "message": f"Unexpected error: {e}"})
            return
        try:
            history.append_entry(note_id, attempt, grading)
        except Exception:
            pass  # history is best-effort; never block feedback on it
        _eval_js("showFeedback", {"cardId": card_id, "grading": grading})

    mw.taskman.run_in_background(task, on_done)


def _eval_js(fn: str, obj: Dict[str, Any]) -> None:
    """Push a result into the reviewer, unless the user already moved on."""
    rev = mw.reviewer
    if rev is None or rev.card is None or rev.card.id != obj["cardId"]:
        return
    payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    rev.web.eval(f"if (window.FrenchGrader) FrenchGrader.{fn}({payload});")


gui_hooks.card_will_show.append(on_card_will_show)
gui_hooks.webview_did_receive_js_message.append(on_js_message)
