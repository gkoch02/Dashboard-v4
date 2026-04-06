"""Structured recent-event helpers for the web UI.

This keeps a tiny append-only JSONL event stream in state/web_events.jsonl so the
status page can show meaningful actions/history without forcing users to read raw
logs. Failures are intentionally swallowed after logging so the UI never breaks
because the event file is missing or temporarily unwritable.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_EVENT_FILE = "web_events.jsonl"


def append_event(state_dir: str, kind: str, message: str, **details) -> None:
    path = Path(state_dir) / _EVENT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        "message": message,
        "details": details or {},
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, sort_keys=True) + "\n")
    except Exception as exc:
        logger.debug("Could not append web event: %s", exc)


def read_recent_events(state_dir: str, limit: int = 20) -> list[dict]:
    path = Path(state_dir) / _EVENT_FILE
    if not path.exists():
        return []
    try:
        rows: deque[dict] = deque(maxlen=max(1, limit))
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return list(reversed(rows))
    except Exception as exc:
        logger.debug("Could not read web events: %s", exc)
        return []
