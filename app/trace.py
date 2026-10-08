"""Append-only turn trace. One JSON object per line."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import TRACES_PATH


def append(event: dict, path: Path | None = None) -> None:
    target = path or TRACES_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")
