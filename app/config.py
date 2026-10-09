"""Runtime switches. Defaults keep the gate offline and deterministic."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = ROOT / "policy" / "scripts.json"
PROMPTS_DIR = ROOT / "policy" / "prompts"
TRACES_PATH = ROOT / "traces" / "turns.jsonl"
ACCOUNTS_PATH = ROOT / "data" / "accounts.json"
ENV_PATH = ROOT / ".env"


def load_env(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env. Existing environment variables win."""
    target = path or ENV_PATH
    if not target.exists():
        return
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env()

PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v2")
AGENT_MODE = os.environ.get("AGENT_MODE", "full")  # full | notes_only
MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "pack")  # pack | litellm | groq
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "gpt-4o-mini")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CONFIDENCE_FLOOR = 0.7
MIN_PLAN_RATIO = 0.25
WINDOW_START = 8
WINDOW_END = 19
MAX_ATTEMPTS = 3
