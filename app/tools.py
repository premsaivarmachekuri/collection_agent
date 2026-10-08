"""Five tools. The router calls these. The model cannot call them directly."""

from __future__ import annotations

import hashlib

from app.store import Store

REASONS = {
    "hardship",
    "dispute",
    "complaint",
    "distress",
    "human_requested",
    "plan_below_floor",
    "already_paid_mismatch",
    "identity_failed",
    "low_confidence",
    "waiver_refused",
}


class ToolError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def verify_identity(store: Store, account_id: str, dob: str | None, pan_last4: str | None) -> dict:
    account = store.account(account_id)
    matched = bool(dob) and bool(pan_last4) and dob == account.dob and pan_last4 == account.pan_last4
    return {"verified": matched, "attempts_remaining_hint": None if matched else "check session"}


def get_account(store: Store, account_id: str, *, verified: bool) -> dict:
    if not verified:
        raise ToolError("identity_required")
    return store.account(account_id).public_after_verify()


def issue_payment_link(store: Store, account_id: str, amount: int, *, verified: bool, allowed: bool) -> dict:
    if not verified:
        raise ToolError("identity_required")
    if not allowed or amount <= 0:
        raise ToolError("offer_blocked")
    token = hashlib.sha256(f"{account_id}:{amount}".encode()).hexdigest()[:16]
    link = f"https://pay.northwind.example/p/{token}"
    record = {"account_id": account_id, "amount": amount, "link": link}
    store.links.append(record)
    return record


def record_outcome(store: Store, account_id: str, outcome: dict) -> dict:
    row = {"account_id": account_id, **outcome}
    store.outcomes.append(row)
    return {"recorded": True, "outcome": outcome.get("intent")}


def escalate(store: Store, account_id: str, reason: str, transcript_ref: str) -> dict:
    if reason not in REASONS:
        raise ToolError("unknown_reason")
    case_id = f"CASE-{len(store.tickets) + 1:05d}"
    ticket = {
        "case_id": case_id,
        "account_id": account_id,
        "reason": reason,
        "transcript_ref": transcript_ref,
    }
    store.tickets.append(ticket)
    return ticket
