# LLM Answer Grader — inline LLM grading in the Anki reviewer.
# Injects a text input on cards matched by configured profiles; submissions
# are graded via the configured provider in a background thread and rendered
# on the card.

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Dict, Optional

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.utils import tooltip

from . import grader, history, webui

try:
    from anki.utils import strip_html
except ImportError:  # older naming
    from anki.utils import stripHTML as strip_html  # type: ignore

PYCMD_PREFIX = "llm_grader:"

# Grading context of recently shown cards, so follow-up questions stay
# grounded in what was actually graded. {card_id: {...}}
_contexts: Dict[int, Dict[str, Any]] = {}
_MAX_CONTEXTS = 10

_config_error_notified = False


def _config() -> Dict[str, Any]:
    return mw.addonManager.getConfig(__name__) or {}


def _profile_for(card) -> Optional[Dict[str, Any]]:
    name = card.note().note_type()["name"]
    return grader.match_profile(_config(), name)


def _note_config_error() -> None:
    """Log the traceback; nag at most once per session."""
    global _config_error_notified
    traceback.print_exc()
    if not _config_error_notified:
        _config_error_notified = True
        tooltip(
            "LLM Answer Grader hit an error (likely a config problem) and "
            "stayed out of the way. See Tools → LLM Answer Grader Settings.",
            period=5000,
        )


def on_card_will_show(text: str, card, kind: str) -> str:
    # Fail open, always: a broken config must never break card display.
    try:
        if kind not in ("reviewQuestion", "reviewAnswer"):
            return text
        cfg = _config()
        if grader.match_profile(cfg, card.note().note_type()["name"]) is None:
            return text
        prev = None
        if cfg.get("show_previous_attempt", True):
            prev = history.last_entry(card.nid)
        labels = {
            "verdicts": cfg.get("verdict_labels") or {},
            "ratings": cfg.get("rating_labels") or {},
        }
        return text + webui.widget_html(card.id, prev, labels)
    except Exception:
        _note_config_error()
        return text


def on_js_message(handled, message: str, context) -> Any:
    if not message.startswith(PYCMD_PREFIX):
        return handled
    if not isinstance(context, Reviewer):
        return handled
    try:
        _, action, payload = message.split(":", 2)
        if action == "submit":
            _handle_submit(payload)
            return (True, None)
        if action == "followup":
            _handle_followup(payload)
            return (True, None)
    except Exception:
        _note_config_error()
        return (True, None)
    return handled


def _remember_context(card_id: int, ctx: Dict[str, Any]) -> None:
    _contexts[card_id] = ctx
    while len(_contexts) > _MAX_CONTEXTS:
        _contexts.pop(next(iter(_contexts)))


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
    template = None
    try:
        if len(note.note_type()["tmpls"]) > 1:
            template = card.template().get("name")
    except Exception:
        pass
    cfg = _config()
    card_id, note_id = card.id, note.id

    def task() -> Dict[str, Any]:
        return grader.grade(cfg, profile, fields, attempt, template)

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
        _remember_context(card_id, {
            "profile": profile, "fields": fields, "attempt": attempt,
            "grading": grading,
        })
        _eval_js("showFeedback", {"cardId": card_id, "grading": grading})

    mw.taskman.run_in_background(task, on_done)


def _handle_followup(payload: str) -> None:
    try:
        req = json.loads(payload)
    except ValueError:
        return
    card_id = req.get("cardId")
    question = (req.get("question") or "").strip()
    ctx = _contexts.get(card_id)
    if not question or ctx is None:
        return
    cfg = _config()

    def task() -> str:
        return grader.follow_up(
            cfg, ctx["profile"], ctx["fields"], ctx["attempt"],
            ctx["grading"], question,
        )

    def on_done(fut) -> None:
        try:
            answer = fut.result()
        except grader.GraderError as e:
            _eval_js("showFollowUp", {"cardId": card_id, "error": str(e)})
            return
        except Exception as e:  # noqa: BLE001
            _eval_js("showFollowUp", {"cardId": card_id, "error": f"Unexpected error: {e}"})
            return
        _eval_js("showFollowUp", {"cardId": card_id, "answer": answer})

    mw.taskman.run_in_background(task, on_done)


def _eval_js(fn: str, obj: Dict[str, Any]) -> None:
    """Push a result into the reviewer, unless the user already moved on."""
    rev = mw.reviewer
    if rev is None or rev.card is None or rev.card.id != obj["cardId"]:
        return
    payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    rev.web.eval(f"if (window.LLMGrader) LLMGrader.{fn}({payload});")


# --- Settings & first run ---------------------------------------------------

def _open_settings() -> None:
    try:
        from . import settings

        settings.open_dialog()
    except Exception:
        traceback.print_exc()
        tooltip("Could not open settings; use Tools → Add-ons → Config instead.")


def _first_run_marker() -> str:
    base = os.path.join(os.path.dirname(__file__), "user_files")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "first_run_done")


def _maybe_show_first_run() -> None:
    try:
        cfg = _config()
        configured = bool(
            (cfg.get("api_key") or "").strip()
            or any(p.get("note_type_prefixes") for p in cfg.get("profiles") or [])
        )
        if configured or os.path.exists(_first_run_marker()):
            return
        with open(_first_run_marker(), "w", encoding="utf-8") as f:
            f.write("shown")
        from aqt.qt import QMessageBox

        box = QMessageBox(mw)
        box.setWindowTitle("LLM Answer Grader")
        box.setText(
            "LLM Answer Grader is installed.\n\n"
            "To get started, add your API key and point a grading profile "
            "at your note types."
        )
        open_btn = box.addButton("Open Settings…", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            _open_settings()
    except Exception:
        traceback.print_exc()


def _setup_menu() -> None:
    try:
        from aqt.qt import QAction

        action = QAction("LLM Answer Grader Settings…", mw)
        action.triggered.connect(_open_settings)
        mw.form.menuTools.addAction(action)
        # Make the add-on screen's "Config" button open the dialog too.
        mw.addonManager.setConfigAction(__name__, _open_settings)
    except Exception:
        traceback.print_exc()


gui_hooks.card_will_show.append(on_card_will_show)
gui_hooks.webview_did_receive_js_message.append(on_js_message)
gui_hooks.profile_did_open.append(_maybe_show_first_run)
if mw is not None:  # None when imported outside a running Anki (e.g. tests)
    _setup_menu()
