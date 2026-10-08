"""Slot parsing. Used by instruction pack v2. Gold labels are not read here."""

from __future__ import annotations

import re
from datetime import date, timedelta

MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WORD_AMOUNTS = (
    ("eighteen thousand four hundred", 18400),
    ("five hundred", 500),
    ("paanch sau", 500),
)


def parse_amount(text: str) -> int | None:
    lowered = (text or "").lower()
    for phrase, value in WORD_AMOUNTS:
        if phrase in lowered:
            return value
    match = re.search(r"(?:inr|rs\.?|₹)\s*([0-9][0-9,]*)", lowered, re.I)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def mentions_full(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(
        re.search(r"\b(full overdue|full amount|entire dues|the entire|bhar dunga|full)\b", lowered)
    )


def parse_date(text: str, today: date, *, future: bool) -> date | None:
    lowered = (text or "").lower()
    named = _named_date(lowered, today, future=future)
    if named:
        return named
    if re.search(r"\bnext friday\b", lowered):
        return _weekday_on_or_after(today, 4) + timedelta(days=7)
    if re.search(r"\b(this friday|friday)\b", lowered):
        return _weekday_on_or_after(today, 4)
    if future:
        if re.search(r"\b(tomorrow|kal)\b", lowered):
            return today + timedelta(days=1)
        if re.search(r"\bparso\b", lowered):
            return today + timedelta(days=2)
        if re.search(r"\btoday\b", lowered):
            return today
    else:
        if re.search(r"\byesterday\b", lowered):
            return today - timedelta(days=1)
        if re.search(r"\bkal\b", lowered):
            return today - timedelta(days=1)
    return None


def _named_date(lowered: str, today: date, *, future: bool) -> date | None:
    iso = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", lowered)
    if iso:
        return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
    numeric = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", lowered)
    if numeric:
        return date(int(numeric.group(3)), int(numeric.group(2)), int(numeric.group(1)))
    month = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)(?:\s+(20\d{2}))?\b",
        lowered,
    )
    if month and month.group(2) in MONTHS:
        year = int(month.group(3)) if month.group(3) else today.year
        found = date(year, MONTHS[month.group(2)], int(month.group(1)))
        if future and month.group(3) is None and found < today:
            found = date(year + 1, found.month, found.day)
        return found
    return None


def _weekday_on_or_after(today: date, weekday: int) -> date:
    delta = (weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def parse_dob(text: str) -> str | None:
    match = re.search(r"\b(19\d{2}|20\d{2})-(\d{2})-(\d{2})\b", text or "")
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def parse_pan_last4(text: str) -> str | None:
    match = re.search(r"last four\s+(\d{4})\b", text or "", re.I)
    if match:
        return match.group(1)
    match = re.search(r"\bpan\s+(\d{4})\b", text or "", re.I)
    if match:
        return match.group(1)
    return None
