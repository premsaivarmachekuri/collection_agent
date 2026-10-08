"""HTTP seam. The demo and a lender channel both call this."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent import Orchestrator
from app.config import TRACES_PATH
from app.store import Store

app = FastAPI(title="Northwind collections agent", version="0.1.0")


class CallIn(BaseModel):
    account_id: str
    text: str
    now: datetime
    channel: str = "inbound_chat"
    session_id: str | None = None


@lru_cache
def get_store() -> Store:
    return Store.load()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "accounts": len(get_store().accounts)}


@app.post("/call")
def call(body: CallIn) -> dict:
    store = get_store()
    if body.account_id not in store.accounts:
        raise HTTPException(status_code=404, detail="unknown account")
    result = Orchestrator(store).handle(
        body.account_id,
        body.text,
        now=body.now,
        channel=body.channel,
        session_id=body.session_id,
    )
    return {
        "session_id": result.session_id,
        "visible_text": result.visible_text,
        "escalated": result.escalated,
        "escalation_reason": result.escalation_reason,
        "intent": result.intent,
        "link": result.link,
        "compliance_violations": result.compliance_violations,
    }


@app.get("/traces")
def traces(limit: int = 20) -> dict:
    if not TRACES_PATH.exists():
        return {"turns": []}
    lines = TRACES_PATH.read_text(encoding="utf-8").splitlines()
    return {"turns": lines[-limit:]}
