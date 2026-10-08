"""Orchestrator. Templates speak. The model only classifies."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from app import policy, tools, trace
from app.config import AGENT_MODE, CONFIDENCE_FLOOR, PROMPT_VERSION
from app.models import Classification, build_model
from app.parse import parse_dob, parse_pan_last4
from app.store import Store


@dataclass
class TurnResult:
    session_id: str
    account_id: str
    visible_text: str
    state: str
    escalated: bool
    escalation_reason: str | None
    intent: str | None
    confidence: float | None
    slots: dict
    tools: list[dict] = field(default_factory=list)
    model_draft: str | None = None
    model_note: str | None = None
    compliance_violations: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    verified: bool = False
    link: str | None = None


class Orchestrator:
    def __init__(self, store: Store, prompt_version: str | None = None, mode: str | None = None) -> None:
        self.store = store
        self.prompt_version = prompt_version or PROMPT_VERSION
        self.mode = mode or AGENT_MODE
        self.model = build_model(self.prompt_version)

    def handle(
        self,
        account_id: str,
        text: str,
        *,
        now: datetime,
        channel: str = "inbound_chat",
        session_id: str | None = None,
        prior_attempts: int = 0,
    ) -> TurnResult:
        started = time.perf_counter()
        session = self.store.sessions.get(session_id) if session_id else None
        if session is None:
            session = self.store.open_session(account_id, channel, now)
            if prior_attempts:
                day = now.astimezone(policy.IST).date().isoformat()
                self.store.attempts[(account_id, day)] = prior_attempts
        account = self.store.account(account_id)
        tools_used: list[dict] = []
        draft = None
        note = None
        intent = None
        confidence = None
        slots: dict = {}
        link = None

        if not policy.in_window(now):
            visible = policy.line("after_hours")
            session.state = "closed"
            return self._finish(
                session, account_id, visible, started, tools_used, draft, note,
                intent, confidence, slots, False, None, None, False,
            )

        if channel == "outbound_call":
            day = now.astimezone(policy.IST).date().isoformat()
            if self.store.attempt_count(account_id, day) >= policy.MAX_ATTEMPTS:
                visible = policy.line("attempt_cap")
                session.state = "closed"
                return self._finish(
                    session, account_id, visible, started, tools_used, draft, note,
                    intent, confidence, slots, False, None, None, False,
                )
            self.store.reserve_attempt(account_id, day)

        if self.mode == "notes_only":
            note = self._classify(text, now, session.session_id)
            visible = self._opening(session) + " " + policy.line("notes_only")
            session.state = "closed"
            return self._finish(
                session, account_id, visible, started, tools_used, None, note.draft,
                note.intent, note.confidence, _slots(note), False, None, None, False,
            )

        if not session.verified and policy.is_third_party(text):
            classified = self._classify(text, now, session.session_id)
            intent, confidence, draft, slots = _unpack(classified)
            visible = self._opening(session) + " " + policy.line("third_party")
            tools_used.append(self._record(account_id, "wrong_person", slots, confidence))
            session.state = "closed"
            return self._finish(
                session, account_id, visible, started, tools_used, draft, note,
                intent, confidence, slots, False, None, None, False,
            )

        if not session.verified:
            dob = parse_dob(text)
            pan = parse_pan_last4(text)
            if dob or pan:
                result = tools.verify_identity(self.store, account_id, dob, pan)
                tools_used.append({"tool": "verify_identity", "verified": result["verified"]})
                if result["verified"]:
                    session.verified = True
                    session.state = "listen"
                    snapshot = tools.get_account(self.store, account_id, verified=True)
                    tools_used.append({"tool": "get_account", "overdue_inr": snapshot["overdue_inr"]})
                    disclose_amount = snapshot["overdue_inr"]
                    visible = (
                        self._opening(session)
                        + " "
                        + policy.line(
                            "disclosure",
                            overdue=snapshot["overdue_inr"],
                            charges=snapshot["charges_inr"],
                        )
                    )
                    return self._finish(
                        session, account_id, visible, started, tools_used, draft, note,
                        intent, confidence, slots, False, None, disclose_amount, True,
                    )
                session.id_failures += 1
                if session.id_failures >= 2:
                    return self._escalate(
                        session, account, "identity_failed", text, started, tools_used,
                        opening=True,
                    )
                visible = self._opening(session) + " " + policy.line("verify_fail")
                session.state = "verify"
                return self._finish(
                    session, account_id, visible, started, tools_used, draft, note,
                    intent, confidence, slots, False, None, None, False,
                )
            visible = self._opening(session) + " " + policy.line("verify_ask")
            session.state = "verify"
            return self._finish(
                session, account_id, visible, started, tools_used, draft, note,
                intent, confidence, slots, False, None, None, False,
            )

        classified = self._classify(text, now, session.session_id)
        intent, confidence, draft, slots = _unpack(classified)
        if classified.full_amount and slots.get("amount") is None:
            slots["amount"] = account.overdue_inr
            classified.amount = account.overdue_inr

        overlay = _overlay_reason(text, classified, account)
        if overlay:
            extra = policy.line("waiver") + " " if overlay == "waiver_refused" else ""
            return self._escalate(
                session, account, overlay, text, started, tools_used,
                intent=intent, confidence=confidence, slots=slots, draft=draft, prefix=extra,
            )

        action = _commercial_action(classified, account)
        if action["kind"] == "wrong_person":
            visible = policy.line("third_party")
            tools_used.append(self._record(account_id, "wrong_person", slots, confidence))
            session.state = "closed"
            return self._finish(
                session, account_id, visible, started, tools_used, draft, note,
                intent, confidence, slots, False, None, None, True,
            )

        if action["escalate"]:
            visible_line = policy.line("plan_blocked") if action["reason"] == "plan_below_floor" else None
            return self._escalate(
                session, account, action["reason"], text, started, tools_used,
                intent=intent, confidence=confidence, slots=slots, draft=draft,
                visible_override=visible_line,
            )

        if action["link_amount"]:
            issued = tools.issue_payment_link(
                self.store, account_id, action["link_amount"], verified=True, allowed=True,
            )
            tools_used.append({"tool": "issue_payment_link", "amount": action["link_amount"]})
            link = issued["link"]
            template = "plan_confirm" if action["kind"] == "plan" else "ptp_confirm"
            visible = policy.line(
                template,
                amount=action["link_amount"],
                date=_spoken_date(slots.get("date")),
                link=link,
            )
        elif action["kind"] == "already_paid_ok":
            visible = policy.line("already_paid_ok")
        elif action["kind"] == "callback":
            visible = policy.line("callback")
        else:
            visible = policy.line("escalation")
            return self._escalate(
                session, account, "low_confidence", text, started, tools_used,
                intent=intent, confidence=confidence, slots=slots, draft=draft,
            )

        tools_used.append(self._record(account_id, intent or action["kind"], slots, confidence))
        session.state = "closed"
        return self._finish(
            session, account_id, visible, started, tools_used, draft, note,
            intent, confidence, slots, False, None, account.overdue_inr, True, link,
        )

    def _escalate(
        self,
        session,
        account,
        reason: str,
        text: str,
        started: float,
        tools_used: list,
        *,
        intent=None,
        confidence=None,
        slots=None,
        draft=None,
        opening: bool = False,
        prefix: str = "",
        visible_override: str | None = None,
    ) -> TurnResult:
        ticket = tools.escalate(self.store, account.account_id, reason, session.session_id)
        tools_used.append({"tool": "escalate", "reason": reason, "case_id": ticket["case_id"]})
        slots = slots or {}
        tools_used.append(self._record(account.account_id, intent or reason, slots, confidence))
        if visible_override:
            body = visible_override
        elif reason == "identity_failed":
            body = policy.line("identity_lock")
        elif reason == "plan_below_floor":
            body = policy.line("plan_blocked")
        else:
            body = policy.line("escalation")
        visible = prefix + body
        if opening:
            visible = self._opening(session) + " " + visible
        session.state = "escalated"
        return self._finish(
            session, account.account_id, visible.strip(), started, tools_used, draft, None,
            intent, confidence, slots, True, reason, None, session.verified, None,
        )

    def _classify(self, text: str, now: datetime, session_id: str) -> Classification:
        today = now.astimezone(policy.IST).date()
        return self.model.classify(text, today)

    def _opening(self, session) -> str:
        if session.opening_sent:
            return ""
        session.opening_sent = True
        return policy.line("opening")

    def _record(self, account_id: str, intent: str, slots: dict, confidence: float | None) -> dict:
        outcome = {
            "intent": intent,
            "amount": slots.get("amount"),
            "date": slots.get("date"),
            "confidence": confidence,
        }
        tools.record_outcome(self.store, account_id, outcome)
        return {"tool": "record_outcome", "intent": intent}

    def _finish(
        self,
        session,
        account_id,
        visible,
        started,
        tools_used,
        draft,
        note,
        intent,
        confidence,
        slots,
        escalated,
        reason,
        disclosed_amount,
        verified,
        link=None,
    ) -> TurnResult:
        account = self.store.account(account_id)
        may = disclosed_amount if verified and disclosed_amount is not None else None
        # After verification, later turns may repeat a link amount, which is a promise, not a new disclosure.
        # The overdue amount itself may appear only when may is set, or inside a payment confirmation
        # that quotes the promised amount rather than a hidden balance. Scan waiver always.
        violations = []
        if policy.WAIVER_ACCEPT.search(visible or ""):
            violations.append("waiver_acceptance_shown")
        if not verified and account.overdue_inr and str(account.overdue_inr) in visible:
            violations.append("balance_disclosed_before_identity")
        if not verified and account.charges_inr >= 100 and str(account.charges_inr) in visible:
            violations.append("charges_disclosed_before_identity")
        result = TurnResult(
            session_id=session.session_id,
            account_id=account_id,
            visible_text=" ".join(visible.split()),
            state=session.state,
            escalated=escalated,
            escalation_reason=reason,
            intent=intent,
            confidence=confidence,
            slots=slots,
            tools=tools_used,
            model_draft=draft,
            model_note=note,
            compliance_violations=violations,
            latency_ms=(time.perf_counter() - started) * 1000,
            verified=verified,
            link=link,
        )
        trace.append(
            {
                "session_id": result.session_id,
                "account_id": account_id,
                "prompt_version": self.prompt_version,
                "mode": self.mode,
                "state": result.state,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "tools": tools_used,
                "model_draft": draft,
                "visible_text": result.visible_text,
                "compliance_violations": violations,
                "latency_ms": round(result.latency_ms, 3),
                "escalated": escalated,
                "escalation_reason": reason,
            }
        )
        return result


def _unpack(classified: Classification):
    slots = {
        "amount": classified.amount,
        "date": classified.date,
        "full_amount": classified.full_amount,
    }
    return classified.intent, classified.confidence, classified.draft, slots


def _slots(classified: Classification) -> dict:
    return _unpack(classified)[3]


def _overlay_reason(text: str, classified: Classification, account) -> str | None:
    if policy.is_distress(text):
        return "distress"
    if policy.is_human_request(text):
        return "human_requested"
    if policy.is_waiver_request(text):
        return "waiver_refused"
    if classified.intent in {"hardship", "dispute", "complaint"}:
        return classified.intent
    if classified.confidence is not None and classified.confidence < CONFIDENCE_FLOOR:
        return "low_confidence"
    return None


def _commercial_action(classified: Classification, account) -> dict:
    amount = classified.amount
    if classified.full_amount and amount is None:
        amount = account.overdue_inr
    if classified.intent == "already_paid":
        agrees = _ledger_agrees(account, classified.date)
        if agrees:
            return {"kind": "already_paid_ok", "escalate": False, "link_amount": None, "reason": None}
        return {"kind": "escalate", "escalate": True, "link_amount": None, "reason": "already_paid_mismatch"}
    if classified.intent == "callback":
        return {"kind": "callback", "escalate": False, "link_amount": None, "reason": None}
    if classified.intent == "wrong_person":
        return {"kind": "wrong_person", "escalate": False, "link_amount": None, "reason": None}
    if classified.intent == "payment_plan":
        if amount is None or not policy.plan_allowed(int(amount), account.overdue_inr):
            return {"kind": "escalate", "escalate": True, "link_amount": None, "reason": "plan_below_floor"}
        return {"kind": "plan", "escalate": False, "link_amount": int(amount), "reason": None}
    if classified.intent == "promise_to_pay":
        if amount is None or classified.date is None:
            return {"kind": "escalate", "escalate": True, "link_amount": None, "reason": "low_confidence"}
        if int(amount) >= account.overdue_inr:
            return {"kind": "ptp", "escalate": False, "link_amount": account.overdue_inr, "reason": None}
        if policy.plan_allowed(int(amount), account.overdue_inr):
            return {"kind": "plan", "escalate": False, "link_amount": int(amount), "reason": None}
        return {"kind": "escalate", "escalate": True, "link_amount": None, "reason": "plan_below_floor"}
    return {"kind": "escalate", "escalate": True, "link_amount": None, "reason": "low_confidence"}


def _ledger_agrees(account, claimed_date: str | None) -> bool:
    if account.last_payment_inr < account.overdue_inr:
        return False
    if not account.last_payment_date or not claimed_date:
        return False
    return account.last_payment_date >= claimed_date


def _spoken_date(iso: str | None) -> str:
    if not iso:
        return "the agreed date"
    year, month, day = iso.split("-")
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    return f"{int(day)} {months[int(month) - 1]} {year}"
