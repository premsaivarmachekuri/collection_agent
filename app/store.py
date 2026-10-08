"""In-memory stand-in for the LMS, CIF, dialer attempt counter, and case queue."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from app.config import ACCOUNTS_PATH


@dataclass
class Account:
    account_id: str
    borrower_name: str
    phone: str
    dob: str
    pan_last4: str
    overdue_inr: int
    charges_inr: int
    dpd: int
    last_payment_inr: int
    last_payment_date: str | None
    language: str
    source: str
    uci_id: int | None = None

    def public_after_verify(self) -> dict:
        return {
            "account_id": self.account_id,
            "overdue_inr": self.overdue_inr,
            "charges_inr": self.charges_inr,
            "dpd": self.dpd,
            "last_payment_inr": self.last_payment_inr,
            "last_payment_date": self.last_payment_date,
        }


@dataclass
class Session:
    session_id: str
    account_id: str
    state: str
    verified: bool = False
    id_failures: int = 0
    opening_sent: bool = False
    channel: str = "inbound_chat"
    created_at: datetime | None = None


@dataclass
class Store:
    accounts: dict[str, Account] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    attempts: dict[tuple[str, str], int] = field(default_factory=dict)
    outcomes: list[dict] = field(default_factory=list)
    tickets: list[dict] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, path=ACCOUNTS_PATH) -> "Store":
        store = cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload:
            account = Account(**row)
            store.accounts[account.account_id] = account
        return store

    def account(self, account_id: str) -> Account:
        if account_id not in self.accounts:
            raise KeyError(account_id)
        return self.accounts[account_id]

    def open_session(self, account_id: str, channel: str, when: datetime) -> Session:
        session = Session(
            session_id=uuid4().hex[:12],
            account_id=account_id,
            state="greet",
            channel=channel,
            created_at=when,
        )
        self.sessions[session.session_id] = session
        return session

    def attempt_count(self, account_id: str, day: str) -> int:
        return self.attempts.get((account_id, day), 0)

    def reserve_attempt(self, account_id: str, day: str) -> int:
        key = (account_id, day)
        self.attempts[key] = self.attempts.get(key, 0) + 1
        return self.attempts[key]
