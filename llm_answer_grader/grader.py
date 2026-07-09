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
            "description": "0-100 quality score for the answer, judged at the expected level.",
        },
        "corrected_version": {
            "type": "string",
            "description": "The best natural version of what the learner tried to produce. Empty string if the answer was already perfect.",
        },
        "feedback": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific, concise points: errors, why they're wrong, style issues. Empty if nothing to say.",
        },
        "alternatives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Other natural/acceptable renderings. At most 2.",
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

# Default grading persona. Users can replace it wholesale via the
# "system_prompt" config key; the output contract below is always appended
# so the structured response stays meaningful either way.
DEFAULT_PERSONA = """You are a precise, encouraging tutor grading a learner's typed answer to a flashcard during an Anki review.

Grading rules:
- Grade against the card's content and the profile's grading instructions. If the card shows a difficulty or level field, judge the answer AT that level — don't demand expert polish on a beginner card.
- Accuracy of meaning first, then correctness (grammar, terminology, facts), then naturalness/style.
- Accept legitimate variants without penalty.
- Be specific: name each error and give the fix. Never pad with generic praise.
- Each feedback item makes exactly one point. Write feedback in English unless the grading instructions say otherwise."""

# Always appended after the persona — keeps the JSON fields meaningful even
# when the user replaces the persona.
OUTPUT_CONTRACT = """

How to fill the response fields:
- verdict: correct = nothing or almost nothing to fix; minor_issues = small slips; significant_errors = substance survives but real mistakes; incorrect = wrong or not produced.
- score: 0-100 quality at the expected level.
- corrected_version: the best natural version of what the learner tried to produce ("" if already perfect).
- alternatives: up to 2 other acceptable renderings.
- suggested_rating maps to Anki's answer buttons: easy = essentially flawless, produced confidently; good = right with only minor slips; hard = real errors worth restudying; again = wrong, garbled, or clearly not known."""

DEFAULT_MODEL = "claude-opus-4-8"


class GraderError(Exception):
    """User-facing grading failure. str(e) is safe to show in the UI."""


def _api_key(config: Dict[str, Any]) -> str:
    key = (config.get("api_key") or "").strip() or os.environ.get(
        "ANTHROPIC_API_KEY", ""
    )
    if not key:
        raise GraderError(
            "No API key configured. Set it in Tools → Add-ons → "
            "LLM Answer Grader → Config."
        )
    return key


def match_profile(
    config: Dict[str, Any], note_type_name: str
) -> Optional[Dict[str, Any]]:
    """First profile whose note_type_prefixes match wins. "*" matches all."""
    for profile in config.get("profiles") or []:
        for prefix in profile.get("note_type_prefixes") or []:
            if prefix == "*" or note_type_name.startswith(prefix):
                return profile
    return None


def build_user_message(
    profile: Dict[str, Any], fields: Dict[str, str], attempt: str
) -> str:
    instructions = (profile.get("grading_instructions") or "").strip() or (
        "Grade the learner's answer against the card content below."
    )
    include = profile.get("card_fields") or list(fields.keys())
    lines = [
        f"{name}: {fields[name]}"
        for name in include
        if name in fields and fields[name].strip()
    ]
    card_block = "\n".join(lines) or "(no card fields)"
    return (
        f"{instructions}\n\n"
        f"Card content:\n{card_block}\n\n"
        f"Learner's answer:\n{attempt}"
    )


def build_request_body(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    system = (config.get("system_prompt") or "").strip() or DEFAULT_PERSONA
    system += OUTPUT_CONTRACT
    extra = (config.get("system_prompt_extra") or "").strip()
    if extra:
        system += "\n\nAdditional instructions from the user:\n" + extra

    body: Dict[str, Any] = {
        "model": config.get("model") or DEFAULT_MODEL,
        "max_tokens": int(config.get("max_tokens") or 2000),
        "system": system,
        "messages": [
            {"role": "user", "content": build_user_message(profile, fields, attempt)}
        ],
        "output_config": {
            "format": {"type": "json_schema", "schema": GRADING_SCHEMA}
        },
    }
    if config.get("adaptive_thinking", True):
        body["thinking"] = {"type": "adaptive"}
    return body


def grade(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    """Blocking Claude API call. Returns the parsed grading dict."""
    key = _api_key(config)
    body = build_request_body(config, profile, fields, attempt)
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
        raise GraderError("Claude declined to grade this answer.")
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
