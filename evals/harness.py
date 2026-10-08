"""Replay the 80 conversations through the orchestrator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.agent import Orchestrator
from app.store import Store

ROOT = Path(__file__).resolve().parents[1]
CONV_DIR = ROOT / "evals" / "conversations"


@dataclass
class Replay:
    case: dict
    results: list
    violations: list[str] = field(default_factory=list)
    model_ran: bool = False


def load_cases() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(CONV_DIR.glob("*.json"))]


def replay_all(prompt_version: str = "v2") -> list[Replay]:
    replays = []
    for case in load_cases():
        store = Store.load()
        account = store.account(case["account_id"])
        for key, value in case.get("override", {}).items():
            setattr(account, key, value)
        orch = Orchestrator(store, prompt_version=prompt_version)
        session_id = None
        results = []
        violations = []
        model_ran = False
        moment = datetime.fromisoformat(case["now"])
        for turn in case["turns"]:
            result = orch.handle(
                case["account_id"],
                turn["user"],
                now=moment,
                channel=case.get("channel", "inbound_chat"),
                session_id=session_id,
            )
            session_id = result.session_id
            results.append(result)
            violations.extend(result.compliance_violations)
            if result.intent is not None or result.model_draft is not None:
                model_ran = True
            if turn.get("expect_no_amount") and str(account.overdue_inr) in result.visible_text:
                violations.append(f"{case['id']}:amount_shown")
            if turn.get("expect_no_model") and result.model_draft is not None:
                violations.append(f"{case['id']}:model_ran_when_blocked")
        replays.append(Replay(case=case, results=results, violations=violations, model_ran=model_ran))
    return replays


def summarize(replays: list[Replay]) -> dict:
    intent_hit = intent_n = 0
    slot_hit = slot_n = 0
    esc_hit = esc_n = 0
    latencies = []
    misses = []
    for replay in replays:
        case = replay.case
        if case.get("must_escalate"):
            esc_n += 1
            if any(result.escalated for result in replay.results):
                esc_hit += 1
        for turn, result in zip(case["turns"], replay.results):
            latencies.append(result.latency_ms)
            if not turn.get("gold_intent"):
                continue
            intent_n += 1
            if result.intent == turn["gold_intent"]:
                intent_hit += 1
            else:
                misses.append(
                    {
                        "id": case["id"],
                        "text": turn["user"],
                        "gold": turn["gold_intent"],
                        "got": result.intent,
                        "cause": case.get("v1_miss_cause"),
                    }
                )
            if case.get("slot_scored"):
                slot_n += 1
                amount_ok = result.slots.get("amount") == turn.get("gold_amount")
                date_ok = result.slots.get("date") == turn.get("gold_date")
                if amount_ok and date_ok:
                    slot_hit += 1
    latencies.sort()
    p95_index = max(0, int(len(latencies) * 0.95) - 1)
    return {
        "intent_accuracy": intent_hit / intent_n if intent_n else 0,
        "intent_n": intent_n,
        "intent_hit": intent_hit,
        "slot_accuracy": slot_hit / slot_n if slot_n else 0,
        "slot_n": slot_n,
        "slot_hit": slot_hit,
        "escalation_recall": esc_hit / esc_n if esc_n else 0,
        "escalation_n": esc_n,
        "escalation_hit": esc_hit,
        "violations": [item for replay in replays for item in replay.violations],
        "p95_ms": latencies[p95_index] if latencies else 0,
        "n_turns": len(latencies),
        "misses": misses,
    }
