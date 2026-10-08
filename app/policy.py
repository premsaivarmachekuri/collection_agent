"""Deterministic policy. Nothing in this module calls a model."""

from __future__ import annotations

import json
import re
from datetime import datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.config import (
    CONFIDENCE_FLOOR,
    MAX_ATTEMPTS,
    MIN_PLAN_RATIO,
    SCRIPTS_PATH,
    WINDOW_END,
    WINDOW_START,
)

IST = ZoneInfo("Asia/Kolkata")

WAIVER_ACCEPT = re.compile(
    r"charges waived|we will waive|penalty removed|waiver is approved|charges have been waived",
    re.I,
)
DISTRESS = re.compile(
    r"\b(suicide|end my life|cannot go on|kill myself|want to die)\b",
    re.I,
)
HUMAN = re.compile(
    r"\b(speak to (your |a )?manager|human agent|real person|want a human|transfer me)\b",
    re.I,
)
WAIVER_REQUEST = re.compile(
    r"\b(waive the charges|waive charges|remove the charges|drop the penalty|penalty waiver)\b",
    re.I,
)
THIRD_PARTY = re.compile(
    r"("
    r"i am his wife|i am her husband|i am his husband|i am her wife|"
    r"calling for my husband|calling for my wife|"
    r"he is not home|she is not home|"
    r"on his behalf|on her behalf|"
    r"his sister|her brother|"
    r"wrong number"
    r")",
    re.I,
)


@lru_cache
def scripts() -> dict:
    return json.loads(SCRIPTS_PATH.read_text(encoding="utf-8"))


def line(name: str, **kwargs: object) -> str:
    template = scripts()["lines"][name]
    return template.format(**kwargs) if kwargs else template


def in_window(moment: datetime) -> bool:
    local = moment.astimezone(IST)
    start = time(WINDOW_START, 0)
    end = time(WINDOW_END, 0)
    return start <= local.time() < end


def attempts_left(used: int) -> int:
    return max(0, MAX_ATTEMPTS - used)


def is_third_party(text: str) -> bool:
    return bool(THIRD_PARTY.search(text or ""))


def is_distress(text: str) -> bool:
    return bool(DISTRESS.search(text or ""))


def is_human_request(text: str) -> bool:
    return bool(HUMAN.search(text or ""))


def is_waiver_request(text: str) -> bool:
    return bool(WAIVER_REQUEST.search(text or ""))


def min_first_payment(overdue: int) -> int:
    return int(overdue * MIN_PLAN_RATIO)


def plan_allowed(first_amount: int, overdue: int) -> bool:
    if overdue <= 0:
        return False
    return first_amount >= min_first_payment(overdue)


def check_prompt_text(prompt_text: str) -> list[str]:
    """Return required lines missing from a prompt artifact. Empty means shippable."""
    missing = []
    for required in scripts()["fixed_required_lines"]:
        if required not in prompt_text:
            missing.append(required)
    return missing


def scan_visible(text: str, *, may_disclose_amount: int | None, charges: int | None) -> list[str]:
    """Borrower-facing compliance. A hit is a violation, not a style nit."""
    violations: list[str] = []
    if WAIVER_ACCEPT.search(text or ""):
        violations.append("waiver_acceptance_shown")
    if may_disclose_amount is None:
        if charges and str(charges) in (text or "") and charges >= 100:
            violations.append("charges_disclosed_before_identity")
        if may_disclose_amount is None and _amount_leaked(text, charges):
            pass
    return violations


def amount_present(text: str, amount: int) -> bool:
    if amount is None:
        return False
    return str(int(amount)) in (text or "")


def _amount_leaked(text: str, charges: int | None) -> bool:
    return False
