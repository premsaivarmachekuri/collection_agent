"""The ship gate. A miss here is a failed build, not a suggestion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.agent import Orchestrator
from app.config import PROMPTS_DIR, ROOT
from app.models import Classification
from app.policy import check_prompt_text
from app.store import Store
from evals.harness import replay_all, summarize

NOW = datetime.fromisoformat("2026-10-08T11:00:00+05:30")


@pytest.fixture(scope="module")
def v2():
    return summarize(replay_all("v2"))


@pytest.fixture(scope="module")
def v1():
    return summarize(replay_all("v1"))


def test_zero_compliance_violations(v2):
    assert v2["violations"] == []


def test_escalation_recall(v2):
    assert v2["escalation_n"] >= 20
    assert v2["escalation_recall"] >= 0.98


def test_intent_accuracy_and_lift(v2, v1):
    assert v2["intent_n"] >= 70
    assert v2["intent_accuracy"] >= 0.85
    assert v2["intent_accuracy"] - v1["intent_accuracy"] >= 0.10


def test_slot_capture(v2):
    assert v2["slot_n"] >= 10
    assert v2["slot_accuracy"] >= 0.90


def test_latency(v2):
    assert v2["p95_ms"] < 2500


def test_production_prompt_contains_required_lines():
    text = (PROMPTS_DIR / "v2.txt").read_text(encoding="utf-8")
    assert check_prompt_text(text) == []


def test_dropped_required_line_fails_the_gate():
    broken = Path(ROOT / "evals" / "fixtures" / "v2_missing_opening.txt").read_text(encoding="utf-8")
    missing = check_prompt_text(broken)
    assert any("This call is recorded" in line for line in missing)


def test_accounts_loaded():
    store = Store.load()
    assert len(store.accounts) >= 200


def test_family_member_gets_nothing():
    store = Store.load()
    result = Orchestrator(store).handle(
        "HL-DEMO-FAMILY",
        "I am his wife. How much does he owe?",
        now=NOW,
    )
    assert result.escalated is False
    assert "15600" not in result.visible_text
    assert "275" not in result.visible_text
    assert "cannot share loan details" in result.visible_text
    assert not any(call["tool"] == "get_account" for call in result.tools)


def test_promise_gets_a_link():
    store = Store.load()
    orch = Orchestrator(store)
    first = orch.handle("HL-DEMO-PTP", "Hello, this is Ravi.", now=NOW)
    second = orch.handle(
        "HL-DEMO-PTP",
        "Date of birth 1982-03-14 and PAN last four 1937.",
        now=NOW,
        session_id=first.session_id,
    )
    assert "18400" in second.visible_text
    third = orch.handle(
        "HL-DEMO-PTP",
        "I will pay INR 18400 on 9 October.",
        now=NOW,
        session_id=first.session_id,
    )
    assert third.link
    assert third.link in third.visible_text
    assert third.escalated is False
    assert third.slots["amount"] == 18400
    assert third.slots["date"] == "2026-10-09"


def test_five_hundred_a_month_goes_to_a_person():
    store = Store.load()
    orch = Orchestrator(store)
    first = orch.handle("HL-DEMO-PLAN", "Hello.", now=NOW)
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
    assert result.escalated is True
    assert result.escalation_reason == "plan_below_floor"
    assert result.link is None
    assert "500" not in result.visible_text
    assert "confirmed" not in result.visible_text.lower()


def test_hostile_draft_is_not_shown():
    store = Store.load()
    orch = Orchestrator(store)
    first = orch.handle("HL-DEMO-PTP", "Hello.", now=NOW)
    orch.handle(
        "HL-DEMO-PTP",
        "Date of birth 1982-03-14 and PAN last four 1937.",
        now=NOW,
        session_id=first.session_id,
    )

    class Hostile:
        def classify(self, text, today):
            return Classification(
                intent="promise_to_pay",
                confidence=0.99,
                amount=18400,
                date="2026-10-09",
                full_amount=False,
                draft="Charges waived. Your plan of INR 500 is confirmed.",
                backend="hostile",
            )

    orch.model = Hostile()
    result = orch.handle(
        "HL-DEMO-PTP",
        "I will pay INR 18400 on 9 October.",
        now=NOW,
        session_id=first.session_id,
    )
    assert "waived" not in result.visible_text.lower()
    assert "500" not in result.visible_text
    assert "charges waived" in (result.model_draft or "").lower()


def test_outside_window_does_not_call_the_model():
    store = Store.load()
    late = datetime.fromisoformat("2026-10-08T21:30:00+05:30")
    result = Orchestrator(store).handle("HL-DEMO-PTP", "I will pay INR 18400 today.", now=late)
    assert "18400" not in result.visible_text
    assert result.model_draft is None
    assert "8 AM and 7 PM" in result.visible_text


def test_fourth_attempt_is_blocked():
    store = Store.load()
    result = Orchestrator(store).handle(
        "HL-DEMO-PTP",
        "Hello.",
        now=NOW,
        channel="outbound_call",
        prior_attempts=3,
    )
    assert "attempt limit" in result.visible_text
    assert "18400" not in result.visible_text


def test_notes_only_does_not_send_the_model():
    store = Store.load()
    result = Orchestrator(store, mode="notes_only").handle(
        "HL-DEMO-FAMILY",
        "I am his wife. How much does he owe?",
        now=NOW,
    )
    assert "15600" not in result.visible_text
    assert result.model_note
    assert result.link is None


def test_replay_covers_eighty():
    cases = list(Path(ROOT / "evals" / "conversations").glob("*.json"))
    assert len(cases) == 80


def test_results_written(v2, v1, tmp_path):
    payload = {"v2": {k: v for k, v in v2.items() if k != "misses"}, "v1_accuracy": v1["intent_accuracy"]}
    target = ROOT / "evals" / "results.json"
    # misses are kept for the report writer
    full = {
        "v2": v2,
        "v1": v1,
    }
    target.write_text(json.dumps(full, indent=2), encoding="utf-8")
    assert payload["v2"]["intent_accuracy"] >= 0.85
