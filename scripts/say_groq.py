"""Send one borrower line straight to Groq. Policy still writes the reply.

The key is read from .env or the environment. It is never written into this file.

    copy .env.example .env
    python scripts/say_groq.py "I will pay INR 18400 on 9 October."
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.config  # loads .env before the key is read
from app.models import GroqModel


def main(argv: list[str]) -> int:
    app.config.load_env()
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY is empty. Paste it into .env, copied from .env.example.")
        return 2
    text = " ".join(argv[1:]).strip() or "I am his wife. How much does he owe?"
    result = GroqModel().classify(text, date.today())
    print("said:     ", text)
    print("backend:  ", result.backend)
    print("intent:   ", result.intent)
    print("confidence:", result.confidence)
    print("amount:   ", result.amount)
    print("date:     ", result.date)
    print("draft:    ", result.draft)
    print("note: draft is not sent to the borrower. The policy template is.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
