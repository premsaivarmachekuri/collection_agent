"""Runtime switches. Defaults keep the gate offline and deterministic."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = ROOT / "policy" / "scripts.json"
PROMPTS_DIR = ROOT / "policy" / "prompts"
TRACES_PATH = ROOT / "traces" / "turns.jsonl"
ACCOUNTS_PATH = ROOT / "data" / "accounts.json"

PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v2")
AGENT_MODE = os.environ.get("AGENT_MODE", "full")  # full | notes_only
MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "pack")  # pack | litellm
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "gpt-4o-mini")
CONFIDENCE_FLOOR = 0.7
MIN_PLAN_RATIO = 0.25
WINDOW_START = 8
WINDOW_END = 19
MAX_ATTEMPTS = 3
