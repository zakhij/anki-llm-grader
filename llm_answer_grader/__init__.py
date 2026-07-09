# LLM Answer Grader — inline Claude grading in the Anki reviewer.
# Injects a text input on cards matched by configured profiles; submissions
# are graded by the Claude API in a background thread and rendered on the card.

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

PYCMD_PREFIX = "llm_grader:"


def _config() -> Dict[str, Any]:
    return mw.addonManager.getConfig(__name__) or {}


def _profile_for(card) -> Optional[Dict[str, Any]]:
    name = card.note().note_type()["name"]
    return grader.match_profile(_config(), name)


def on_card_will_show(text: str, card, kind: str) -> str:
    if kind not in ("reviewQuestion", "reviewAnswer"):
        return text
    if _profile_for(card) is None:
        return text
    cfg = _config()
    prev = None
    if cfg.get("show_previous_attempt", True):
        prev = history.last_entry(card.nid)
    labels = {
        "verdicts": cfg.get("verdict_labels") or {},
        "ratings": cfg.get("rating_labels") or {},
    }
    return text + webui.widget_html(card.id, prev, labels)


def on_js_message(handled, message: str, context) -> Any:
    if not message.startswith(PYCMD_PREFIX):
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
    profile = _profile_for(card)
    if profile is None:
        return
    attempt = (req.get("text") or "").strip()
    if not attempt:
        return

    note = card.note()
    fields = {name: strip_html(note[name]).strip() for name in note.keys()}
    cfg = _config()
    card_id, note_id = card.id, note.id

    def task() -> Dict[str, Any]:
        return grader.grade(cfg, profile, fields, attempt)

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
    rev.web.eval(f"if (window.LLMGrader) LLMGrader.{fn}({payload});")


gui_hooks.card_will_show.append(on_card_will_show)
gui_hooks.webview_did_receive_js_message.append(on_js_message)
