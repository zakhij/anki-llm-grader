# LLM grading logic. Pure module: no aqt/anki imports, so it can be
# unit-tested outside Anki. Called from a background thread (see __init__.py).
#
# Two providers:
#   "anthropic"          — Claude Messages API (default; structured outputs +
#                          adaptive thinking)
#   "openai_compatible"  — any /chat/completions endpoint (OpenAI, OpenRouter,
#                          Groq, Gemini compat, Ollama, LM Studio, ...)

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "claude-opus-4-8"

VERDICTS = ["correct", "minor_issues", "significant_errors", "incorrect"]
RATINGS = ["again", "hard", "good", "easy"]

# Structured-output schema. Anthropic enforces it via output_config.format;
# OpenAI-compatible servers via response_format (when supported).
GRADING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": VERDICTS},
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
        "suggested_rating": {"type": "string", "enum": RATINGS},
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

# Extra belt-and-braces instruction for OpenAI-compatible backends, some of
# which can't enforce a schema server-side.
JSON_INSTRUCTION = """

Respond with ONLY a JSON object — no markdown fences, no prose — with exactly these keys:
{"verdict": "correct|minor_issues|significant_errors|incorrect", "score": <integer 0-100>, "corrected_version": "<string>", "feedback": ["<string>", ...], "alternatives": ["<string>", ...], "suggested_rating": "again|hard|good|easy"}"""


class GraderError(Exception):
    """User-facing grading failure. str(e) is safe to show in the UI."""


def _provider(config: Dict[str, Any]) -> str:
    p = (config.get("provider") or "anthropic").strip().lower()
    if p not in ("anthropic", "openai_compatible"):
        raise GraderError(f'Unknown provider "{p}" in config.')
    return p


def _resolve_key(config: Dict[str, Any], provider: str) -> str:
    key = (config.get("api_key") or "").strip()
    if key:
        return key
    env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    key = os.environ.get(env_var, "").strip()
    if not key and provider == "anthropic":
        raise GraderError(
            "No API key configured. Set it in Tools → Add-ons → "
            "LLM Answer Grader → Config."
        )
    # openai_compatible tolerates an empty key: local servers (Ollama,
    # LM Studio) don't require one.
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


def _build_system(config: Dict[str, Any], provider: str) -> str:
    system = (config.get("system_prompt") or "").strip() or DEFAULT_PERSONA
    system += OUTPUT_CONTRACT
    if provider == "openai_compatible":
        system += JSON_INSTRUCTION
    extra = (config.get("system_prompt_extra") or "").strip()
    if extra:
        system += "\n\nAdditional instructions from the user:\n" + extra
    return system


def grade(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    """Blocking LLM call. Returns the normalized grading dict."""
    provider = _provider(config)
    if provider == "openai_compatible":
        return _grade_openai_compatible(config, profile, fields, attempt)
    return _grade_anthropic(config, profile, fields, attempt)


# --------------------------------------------------------------------------
# Anthropic (Claude Messages API)
# --------------------------------------------------------------------------

def build_anthropic_request_body(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "model": config.get("model") or DEFAULT_MODEL,
        "max_tokens": int(config.get("max_tokens") or 2000),
        "system": _build_system(config, "anthropic"),
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


def _grade_anthropic(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    key = _resolve_key(config, "anthropic")
    body = build_anthropic_request_body(config, profile, fields, attempt)
    resp = _post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        body=body,
        config=config,
    )
    if resp.status_code != 200:
        raise GraderError(_http_error_message(resp))

    data = resp.json()
    stop = data.get("stop_reason")
    if stop == "refusal":
        raise GraderError("The model declined to grade this answer.")
    if stop == "max_tokens":
        raise GraderError("Response was cut off; raise max_tokens in the config.")

    text = next(
        (b.get("text") for b in data.get("content", []) if b.get("type") == "text"),
        None,
    )
    if not text:
        raise GraderError("The model returned an empty response. Try again.")
    grading = _normalize_grading(_parse_grading_text(text))
    grading["model"] = data.get("model", body["model"])
    return grading


# --------------------------------------------------------------------------
# OpenAI-compatible (/chat/completions)
# --------------------------------------------------------------------------

def _grade_openai_compatible(
    config: Dict[str, Any],
    profile: Dict[str, Any],
    fields: Dict[str, str],
    attempt: str,
) -> Dict[str, Any]:
    key = _resolve_key(config, "openai_compatible")
    base = (config.get("openai_base_url") or DEFAULT_OPENAI_BASE_URL).rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"content-type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    model = config.get("model") or "gpt-5"
    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": int(config.get("max_tokens") or 2000),
        "messages": [
            {"role": "system", "content": _build_system(config, "openai_compatible")},
            {
                "role": "user",
                "content": build_user_message(profile, fields, attempt),
            },
        ],
    }

    # Feature negotiation: some servers reject json_schema (or even
    # json_object) response formats, and some reject max_tokens in favour of
    # max_completion_tokens. Degrade gracefully instead of failing.
    rf_mode = "json_schema"
    for _ in range(4):
        if rf_mode == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "grading",
                    "strict": True,
                    "schema": GRADING_SCHEMA,
                },
            }
        elif rf_mode == "json_object":
            body["response_format"] = {"type": "json_object"}
        else:
            body.pop("response_format", None)

        resp = _post(url, headers=headers, body=body, config=config)

        if resp.status_code == 400:
            err = _error_detail(resp).lower()
            if "max_tokens" in body and "max_completion_tokens" in err:
                body["max_completion_tokens"] = body.pop("max_tokens")
                continue
            if rf_mode == "json_schema" and (
                "response_format" in err or "json_schema" in err or "schema" in err
            ):
                rf_mode = "json_object"
                continue
            if rf_mode == "json_object" and "response_format" in err:
                rf_mode = "none"
                continue
        break

    if resp.status_code != 200:
        raise GraderError(_http_error_message(resp))

    data = resp.json()
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise GraderError("The server returned an unexpected response shape.")
    text = message.get("content") or ""
    if not text.strip():
        raise GraderError("The model returned an empty response. Try again.")
    grading = _normalize_grading(_parse_grading_text(text))
    grading["model"] = data.get("model", model)
    return grading


# --------------------------------------------------------------------------
# Shared plumbing
# --------------------------------------------------------------------------

def _post(url: str, headers: Dict[str, str], body: Dict[str, Any], config: Dict[str, Any]):
    timeout = (10, int(config.get("request_timeout_seconds") or 120))
    try:
        return requests.post(url, headers=headers, json=body, timeout=timeout)
    except requests.exceptions.Timeout:
        raise GraderError("Request timed out. Try again.")
    except requests.exceptions.ConnectionError:
        raise GraderError(
            f"Could not reach {url.split('/chat/')[0].split('/v1/')[0]}. "
            "Check your connection (and that the server is running, if local)."
        )


def _parse_grading_text(text: str) -> Dict[str, Any]:
    """Parse model output into a dict, tolerating markdown fences and prose."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except ValueError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            raise GraderError("Could not parse the grading response. Try again.")
        try:
            parsed = json.loads(m.group(0))
        except ValueError:
            raise GraderError("Could not parse the grading response. Try again.")
    if not isinstance(parsed, dict):
        raise GraderError("Could not parse the grading response. Try again.")
    return parsed


def _normalize_grading(g: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce a possibly-sloppy grading (weak local models) into our shape."""
    score = g.get("score")
    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = None

    verdict = g.get("verdict")
    if verdict not in VERDICTS:
        if score is None:
            raise GraderError("The model's grading was missing verdict and score.")
        verdict = (
            "correct" if score >= 90
            else "minor_issues" if score >= 70
            else "significant_errors" if score >= 40
            else "incorrect"
        )
    if score is None:
        score = {"correct": 95, "minor_issues": 80,
                 "significant_errors": 55, "incorrect": 25}[verdict]

    rating = g.get("suggested_rating")
    if rating not in RATINGS:
        rating = {"correct": "easy", "minor_issues": "good",
                  "significant_errors": "hard", "incorrect": "again"}[verdict]

    def _str_list(v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        if isinstance(v, str) and v.strip():
            return [v]
        return []

    return {
        "verdict": verdict,
        "score": score,
        "corrected_version": str(g.get("corrected_version") or ""),
        "feedback": _str_list(g.get("feedback")),
        "alternatives": _str_list(g.get("alternatives")),
        "suggested_rating": rating,
    }


def _error_detail(resp) -> str:
    try:
        err = resp.json().get("error", {})
        if isinstance(err, dict):
            return err.get("message", "") or json.dumps(err)
        return str(err)
    except ValueError:
        return resp.text[:300] if hasattr(resp, "text") else ""


def _http_error_message(resp) -> str:
    detail = _error_detail(resp)
    if resp.status_code == 401:
        return "Invalid API key. Check it in the add-on config."
    if resp.status_code == 404:
        return f"Endpoint or model not found: {detail or 'check model and base URL in the config.'}"
    if resp.status_code == 429:
        return "Rate limited by the API. Wait a moment and resubmit."
    if resp.status_code >= 500:
        return f"API server error ({resp.status_code}). Try again shortly."
    return f"API error {resp.status_code}: {detail or 'unknown error'}"
