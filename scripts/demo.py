"""Four demo beats from the brief. prompt-break exits 1 on purpose."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent import Orchestrator
from app.policy import check_prompt_text
from app.store import Store

NOW = datetime.fromisoformat("2026-10-08T11:00:00+05:30")


def main(argv: list[str]) -> int:
    which = argv[1] if len(argv) > 1 else "all"
    if which in {"all", "promise"}:
        _promise()
    if which in {"all", "plan"}:
        _plan()
    if which in {"all", "family"}:
        _family()
    if which == "prompt-break":
        return _prompt_break()
    if which == "all":
        _prompt_break()
        print("prompt-break alone exits 1. The suite above is the demo.")
    return 0


def _promise() -> None:
    store = Store.load()
    orch = Orchestrator(store)
    first = orch.handle("HL-DEMO-PTP", "Hello, this is Ravi.", now=NOW)
    print("BORROWER: Hello, this is Ravi.")
    print("AGENT:   ", first.visible_text)
    second = orch.handle(
        "HL-DEMO-PTP",
        "Date of birth 1982-03-14 and PAN last four 1937.",
        now=NOW,
        session_id=first.session_id,
    )
    print("BORROWER: Date of birth 1982-03-14 and PAN last four 1937.")
    print("AGENT:   ", second.visible_text)
    third = orch.handle(
        "HL-DEMO-PTP",
        "I will pay INR 18400 on 9 October.",
        now=NOW,
        session_id=first.session_id,
    )
    print("BORROWER: I will pay INR 18400 on 9 October.")
    print("AGENT:   ", third.visible_text)
    print()


def _plan() -> None:
    store = Store.load()
    orch = Orchestrator(store)
    first = orch.handle("HL-DEMO-PLAN", "Hello, this is Meera.", now=NOW)
    orch.handle(
        "HL-DEMO-PLAN",
        "Date of birth 1990-07-02 and PAN last four 4410.",
        now=NOW,
        session_id=first.session_id,
    )
    result = orch.handle(
        "HL-DEMO-PLAN",
        "I can only do INR 500 a month.",
        now=NOW,
        session_id=first.session_id,
    )
    print("BORROWER: I can only do INR 500 a month.")
    print("AGENT:   ", result.visible_text)
    print("CASE:    ", result.escalation_reason)
    print()


def _family() -> None:
    store = Store.load()
    result = Orchestrator(store).handle(
        "HL-DEMO-FAMILY",
        "I am his wife. How much does he owe?",
        now=NOW,
    )
    print("CALLER:   I am his wife. How much does he owe?")
    print("AGENT:   ", result.visible_text)
    print("TOOLS:   ", [call["tool"] for call in result.tools])
    print()


def _prompt_break() -> int:
    broken = (ROOT / "evals" / "fixtures" / "v2_missing_opening.txt").read_text(encoding="utf-8")
    missing = check_prompt_text(broken)
    print("Broken prompt is missing:")
    for line in missing:
        print(" -", line)
    print("Gate refuses to ship. Borrower-facing templates still contain the line.")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
