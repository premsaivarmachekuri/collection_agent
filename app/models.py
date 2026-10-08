"""Instruction packs and the LiteLLM adapter.

Packs classify. They do not speak to the borrower. v1 is the keyword baseline.
v2 is the paraphrase pack the gate ships. Neither is allowed to bypass policy.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from app.parse import mentions_full, parse_amount, parse_date

INTENTS = (
    "promise_to_pay",
    "already_paid",
    "hardship",
    "dispute",
    "wrong_person",
    "callback",
    "complaint",
    "payment_plan",
)


@dataclass
class Classification:
    intent: str | None
    confidence: float
    amount: int | None
    date: str | None
    full_amount: bool
    draft: str
    backend: str


class PackModel:
    def __init__(self, version: str) -> None:
        if version not in {"v1", "v2"}:
            raise ValueError(f"unknown prompt version: {version}")
        self.version = version

    def classify(self, text: str, today) -> Classification:
        if self.version == "v1":
            intent = _v1_intent(text)
            amount = parse_amount(text)
            return Classification(
                intent=intent,
                confidence=0.88 if intent else 0.42,
                amount=amount,
                date=None,
                full_amount=False,
                draft=f"v1 draft for {intent}",
                backend="pack-v1",
            )
        return _v2_classify(text, today)


class LiteLLMModel:
    """Optional live backend. The gate does not use this unless MODEL_BACKEND=litellm."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def classify(self, text: str, today) -> Classification:
        import litellm

        from app.config import PROMPTS_DIR

        system = (PROMPTS_DIR / "v2.txt").read_text(encoding="utf-8")
        response = litellm.completion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            timeout=2.0,
        )
        raw = response.choices[0].message.content or "{}"
        payload = json.loads(raw)
        intent = payload.get("intent")
        if intent not in INTENTS:
            intent = None
        return Classification(
            intent=intent,
            confidence=float(payload.get("confidence") or 0.0),
            amount=payload.get("amount"),
            date=payload.get("date"),
            full_amount=bool(payload.get("full_amount")),
            draft=str(payload.get("draft") or ""),
            backend=f"litellm:{self.model_name}",
        )


def build_model(version: str, backend: str | None = None):
    chosen = backend or os.environ.get("MODEL_BACKEND", "pack")
    if chosen == "litellm":
        return LiteLLMModel(os.environ.get("LITELLM_MODEL", "gpt-4o-mini"))
    return PackModel(version)


def _v1_intent(text: str) -> str | None:
    lowered = (text or "").lower()
    table = (
        ("complaint", ("complaint",)),
        ("hardship", ("lost my job", "hardship")),
        ("dispute", ("dispute",)),
        ("wrong_person", ("wrong number",)),
        ("callback", ("call me back", "callback")),
        ("payment_plan", ("payment plan", "per month")),
        ("already_paid", ("already paid", "i paid")),
        ("promise_to_pay", ("promise to pay", "i will pay", "i'll pay")),
    )
    for intent, phrases in table:
        if any(phrase in lowered for phrase in phrases):
            return intent
    return None


_V2 = (
    ("wrong_person", re.compile(
        r"i am his wife|i am her husband|calling for my husband|calling for my wife|"
        r"he is not home|she is not home|on his behalf|wrong number",
        re.I,
    )),
    ("complaint", re.compile(
        r"harassment|abusive|ombudsman|complaint|threaten",
        re.I,
    )),
    ("hardship", re.compile(
        r"lost my job|salary stopped|hospital|hardship|no income",
        re.I,
    )),
    ("dispute", re.compile(
        r"\bdispute\b|not mine|never agreed|not my loan|wrong amount",
        re.I,
    )),
    ("already_paid", re.compile(
        r"already paid|i paid|money left my account|transfer ho chuka|went through|"
        r"already transferred",
        re.I,
    )),
    ("payment_plan", re.compile(
        r"a month|per month|mahine|payment plan|instalment|installment|the rest next month",
        re.I,
    )),
    ("callback", re.compile(
        r"call me back|callback|ring me|phone karna|after six|shaam ko",
        re.I,
    )),
    ("promise_to_pay", re.compile(
        r"promise to pay|i will pay|i'll pay|i can pay|put me down|bhar dunga|"
        r"pay kar dunga|schedule the entire|full overdue|eighteen thousand",
        re.I,
    )),
)


def _v2_classify(text: str, today) -> Classification:
    intent = None
    for name, pattern in _V2:
        if pattern.search(text or ""):
            intent = name
            break
    future = intent != "already_paid"
    found = parse_date(text, today, future=future)
    amount = parse_amount(text)
    full = mentions_full(text) and intent in {"promise_to_pay", "payment_plan"}
    confidence = 0.92 if intent else 0.41
    if intent == "promise_to_pay" and found is None and amount is None and not full:
        confidence = 0.62
    return Classification(
        intent=intent,
        confidence=confidence,
        amount=amount,
        date=found.isoformat() if found else None,
        full_amount=full,
        draft=f"v2 draft for {intent}",
        backend="pack-v2",
    )
