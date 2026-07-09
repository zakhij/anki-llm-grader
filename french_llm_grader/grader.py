# Claude API grading logic. Pure module: no aqt/anki imports, so it can be
# unit-tested outside Anki. Called from a background thread (see __init__.py).

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Structured-output schema: the API guarantees the response text is valid JSON
# matching this shape, so rendering never has to guess.
GRADING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["correct", "minor_issues", "significant_errors", "incorrect"],
        },
        "score": {
            "type": "integer",
            "description": "0-100 quality score for the attempt, judged at the card's CEFR level.",
        },
        "corrected_version": {
            "type": "string",
            "description": "The most natural native rendering of what the learner tried to say. Empty string if the attempt was already perfect.",
        },
        "feedback": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific, concise points: errors, why they're wrong, register issues. Empty if nothing to say.",
        },
        "alternatives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Other natural ways a native speaker might phrase it. At most 2.",
        },
        "suggested_rating": {
            "type": "string",
            "enum": ["again", "hard", "good", "easy"],
        },
    },
    "required": [
        "verdict",
        "score",
        "corrected_version",
        "feedback",
        "alternatives",
        "suggested_rating",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a precise, encouraging French tutor grading a learner's written attempt during an Anki review. The learner is studying French; cards are tagged with a CEFR level (A1-C2).

Grading rules:
- Judge the attempt AT THE CARD'S CEFR LEVEL. An A1 card needs correct basic grammar and vocabulary, not literary polish. A C1 card may be marked down for unidiomatic register.
- Accuracy of meaning first, then grammar (conjugation, agreement, articles, prepositions), then naturalness/register.
- Accept legitimate variants (tu/vous where either fits, contractions, regional usage) without penalty.
- Ignore missing accents ONLY if explicitly told to; otherwise treat them as minor errors worth mentioning.
- Be specific: name the error and give the fix ("« je suis allé au magasin » — 'allée' if the speaker is female"). Never pad with generic praise.
- feedback items must each make one point, in English, quoting French in « guillemets ».

Rating suggestion mapping:
- easy: essentially flawless for the level, produced confidently
- good: meaning right, only minor slips
- hard: meaning conveyed but with real errors worth restudying
- again: meaning wrong, garbled, or the learner clearly couldn't produce it

Verdict mapping: correct = nothing or almost nothing to fix; minor_issues = small grammar/naturalness slips; significant_errors = meaning survives but grammar/vocab is substantially wrong; incorrect = meaning lost or wrong."""

TRANSLATE_TASK = """The card asks the learner to translate a sentence into the other language.
- If the source sentence is in English, the learner translates into French.
- If the source sentence is in French, the learner translates into English.
Detect the direction from the source. Grade the translation for meaning, grammar and naturalness at the stated level. There is no single reference answer; judge whether the attempt is something a native speaker would accept.

Source sentence: {text}
CEFR level: {level}

Learner's attempt:
{attempt}"""

PROMPT_TASK = """The card gives the learner a free-writing prompt with constraints. Grade the learner's French response: does it answer the prompt, does it satisfy every constraint, and is the French correct and natural at the stated level? Explicitly mention any constraint that was violated.

Prompt: {prompt}
Constraints: {constraints}
CEFR level: {level}

Learner's response:
{attempt}"""


class GraderError(Exception):
    """User-facing grading failure. str(e) is safe to show in the UI."""


def _api_key(config: Dict[str, Any]) -> str:
    key = (config.get("api_key") or "").strip() or os.environ.get(
        "ANTHROPIC_API_KEY", ""
    )
    if not key:
        raise GraderError(
            "No API key configured. Set it in Tools → Add-ons → "
            "French LLM Grader → Config."
        )
    return key


def build_user_message(mode: str, fields: Dict[str, str], attempt: str) -> str:
    if mode == "prompt":
        return PROMPT_TASK.format(
            prompt=fields.get("Prompt", ""),
            constraints=fields.get("Constraints", "(none)") or "(none)",
            level=fields.get("Level", "unknown"),
            attempt=attempt,
        )
    return TRANSLATE_TASK.format(
        text=fields.get("Text", ""),
        level=fields.get("Level", "unknown"),
        attempt=attempt,
    )


def build_request_body(
    config: Dict[str, Any], mode: str, fields: Dict[str, str], attempt: str
) -> Dict[str, Any]:
    system = SYSTEM_PROMPT
    extra = (config.get("system_prompt_extra") or "").strip()
    if extra:
        system += "\n\nAdditional instructions from the learner:\n" + extra

    body: Dict[str, Any] = {
        "model": config.get("model") or "claude-opus-4-8",
        "max_tokens": int(config.get("max_tokens") or 2000),
        "system": system,
        "messages": [
            {"role": "user", "content": build_user_message(mode, fields, attempt)}
        ],
        "output_config": {
            "format": {"type": "json_schema", "schema": GRADING_SCHEMA}
        },
    }
    if config.get("adaptive_thinking", True):
        body["thinking"] = {"type": "adaptive"}
    return body


def grade(
    config: Dict[str, Any], mode: str, fields: Dict[str, str], attempt: str
) -> Dict[str, Any]:
    """Blocking Claude API call. Returns the parsed grading dict."""
    key = _api_key(config)
    body = build_request_body(config, mode, fields, attempt)
    timeout = (10, int(config.get("request_timeout_seconds") or 120))

    try:
        resp = requests.post(
            API_URL,
            headers={
                "x-api-key": key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json=body,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise GraderError("Request timed out. Try again.")
    except requests.exceptions.ConnectionError:
        raise GraderError("Could not reach the Claude API. Check your connection.")

    if resp.status_code != 200:
        raise GraderError(_http_error_message(resp))

    data = resp.json()
    stop = data.get("stop_reason")
    if stop == "refusal":
        raise GraderError("Claude declined to grade this attempt.")
    if stop == "max_tokens":
        raise GraderError("Response was cut off; raise max_tokens in the config.")

    text = next(
        (b.get("text") for b in data.get("content", []) if b.get("type") == "text"),
        None,
    )
    if not text:
        raise GraderError("Claude returned an empty response. Try again.")
    try:
        grading = json.loads(text)
    except ValueError:
        raise GraderError("Could not parse the grading response. Try again.")

    grading["model"] = data.get("model", body["model"])
    return grading


def _http_error_message(resp: requests.Response) -> str:
    detail = ""
    try:
        detail = resp.json().get("error", {}).get("message", "")
    except ValueError:
        pass
    if resp.status_code == 401:
        return "Invalid API key. Check it in the add-on config."
    if resp.status_code == 429:
        return "Rate limited by the API. Wait a moment and resubmit."
    if resp.status_code >= 500:
        return f"Claude API server error ({resp.status_code}). Try again shortly."
    return f"API error {resp.status_code}: {detail or 'unknown error'}"
