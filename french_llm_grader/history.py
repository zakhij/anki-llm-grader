# Attempt/grading history, persisted as JSON in user_files/ (the directory
# Anki preserves across add-on updates). Keyed by note id.

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional

MAX_ENTRIES_PER_NOTE = 50

_lock = threading.Lock()


def _path() -> str:
    base = os.path.join(os.path.dirname(__file__), "user_files")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "history.json")


def _load() -> Dict[str, List[Dict[str, Any]]]:
    try:
        with open(_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(data: Dict[str, List[Dict[str, Any]]]) -> None:
    path = _path()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def append_entry(note_id: int, attempt: str, grading: Dict[str, Any]) -> None:
    entry = {
        "ts": int(time.time()),
        "attempt": attempt,
        "verdict": grading.get("verdict"),
        "score": grading.get("score"),
        "corrected_version": grading.get("corrected_version"),
        "feedback": grading.get("feedback"),
        "suggested_rating": grading.get("suggested_rating"),
    }
    with _lock:
        data = _load()
        entries = data.setdefault(str(note_id), [])
        entries.append(entry)
        del entries[:-MAX_ENTRIES_PER_NOTE]
        _save(data)


def last_entry(note_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        entries = _load().get(str(note_id))
    return entries[-1] if entries else None
