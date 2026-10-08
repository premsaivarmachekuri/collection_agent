"""Write the 80 replay conversations.

Gold labels are written here, not read back from the classifier. v1_miss marks
paraphrases the keyword pack was not given. Causes are the analyst notes the
eval report may quote only if v1 actually misses.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals" / "conversations"
NOW = "2026-10-08T11:00:00+05:30"
LATE = "2026-10-08T21:30:00+05:30"

# Phrase, gold intent, gold amount or "FULL", gold date, must_escalate, v1_miss, cause
PARAPHRASE = [
    ("Put me down for the full overdue this Friday.", "promise_to_pay", "FULL", "2026-10-09", False, True,
     "v1 only matches 'i will pay' / 'promise to pay'. 'Put me down' is a paraphrase, and v1 does not normalise Friday."),
    ("Main Friday ko bhar dunga.", "promise_to_pay", "FULL", "2026-10-09", False, True,
     "Hinglish promise. No v1 keyword. v2 uses the 'bhar dunga' pattern and Friday normalisation."),
    ("Schedule the entire dues for 15 October.", "promise_to_pay", "FULL", "2026-10-15", False, True,
     "No payment keyword from the v1 list. Date is a named day v1 never parses."),
    ("Kal pay kar dunga, full.", "promise_to_pay", "FULL", "2026-10-09", False, True,
     "Hindi 'kal' plus 'pay kar dunga'. v1 does not treat this as a promise and does not map kal to a date."),
    ("Eighteen thousand four hundred on Friday.", "promise_to_pay", 18400, "2026-10-09", False, True,
     "Spoken amount, no 'INR' token and no v1 promise phrase."),
    ("The money left my account yesterday.", "already_paid", None, "2026-10-07", True, True,
     "Payment claimed without 'already paid'. Ledger does not agree, so a person must take it."),
    ("Transfer ho chuka hai kal.", "already_paid", None, "2026-10-07", True, True,
     "Hinglish already-paid. v1 misses the intent. Ledger disagrees, so the rule escalates anyway."),
    ("Check your ledger, it went through on 7 October.", "already_paid", None, "2026-10-07", True, True,
     "No v1 payment phrase. The date is explicit. Ledger disagrees, so this cannot be closed by the bot."),
    ("Salary stopped last month, I cannot clear this.", "hardship", None, None, True, True,
     "Hardship without the v1 phrase 'lost my job'. Must reach a person."),
    ("Hospital bill ate the EMI.", "hardship", None, None, True, True,
     "Medical hardship. v1 has no 'hospital' keyword."),
    ("This balance is not mine.", "dispute", None, None, True, True,
     "Dispute without the word dispute."),
    ("You added a charge I never agreed to.", "dispute", None, None, True, True,
     "A charge challenge. v1 requires the literal word dispute."),
    ("I am his wife. How much does he owe?", "wrong_person", None, None, False, True,
     "Third party, not the v1 phrase 'wrong number'. The rule must refuse with no balance, even when v1 misses the intent."),
    ("He is not home. What is the due?", "wrong_person", None, None, False, True,
     "A relative asking for the due. Same third-party rule. v1 does not tag it."),
    ("Your caller was abusive yesterday.", "complaint", None, None, True, True,
     "Complaint without the word complaint. Distress-adjacent conduct. A person takes it."),
    ("I am going to the ombudsman.", "complaint", None, None, True, True,
     "Regulator complaint. v1 keyword is only 'complaint'."),
    ("Can we do five hundred rupees a month?", "payment_plan", 500, None, True, True,
     "Monthly plan. v1 looks for 'per month' or 'payment plan', not 'a month'. 500 is below the 25 percent floor."),
    ("Paanch sau rupaye mahine ka.", "payment_plan", 500, None, True, True,
     "Hinglish plan below the floor. No v1 keyword. The amount must not be confirmed back."),
    ("Ring me after six.", "callback", None, None, False, True,
     "Callback without 'call me back'. No escalation required."),
    ("Shaam ko phone karna.", "callback", None, None, False, True,
     "Hinglish callback. v1 misses it. Policy should log it, not disclose anything new."),
]

KEYWORD = [
    ("I will pay INR 12000 on 15 October.", "promise_to_pay", 12000, "2026-10-15", False),
    ("I will pay INR 15000 on 20 October.", "promise_to_pay", 15000, "2026-10-20", False),
    ("I will pay INR 9000 on 12 October.", "promise_to_pay", 9000, "2026-10-12", False),
    ("I will pay INR 11000 on 18 October.", "promise_to_pay", 11000, "2026-10-18", False),
    ("I will pay INR 8000 tomorrow.", "promise_to_pay", 8000, "2026-10-09", False),
    ("I will pay INR 14000 on 28 October.", "promise_to_pay", 14000, "2026-10-28", False),
    ("I will pay INR 10000 on 15 October.", "promise_to_pay", 10000, "2026-10-15", False),
    ("I will pay INR 7000 on 11 October.", "promise_to_pay", 7000, "2026-10-11", False),
    ("I will pay INR 16000 on 22 October.", "promise_to_pay", 16000, "2026-10-22", False),
    ("I will pay INR 13000 on 19 October.", "promise_to_pay", 13000, "2026-10-19", False),
    ("I promise to pay INR 12500 on 16 October.", "promise_to_pay", 12500, "2026-10-16", False),
    ("I'll pay INR 9500 on 21 October.", "promise_to_pay", 9500, "2026-10-21", False),
    ("I will pay INR 18000 on 30 October.", "promise_to_pay", 18000, "2026-10-30", False),
    ("I will pay INR 17500 on 17 October.", "promise_to_pay", 17500, "2026-10-17", False),
    ("I will pay INR 6000 on 13 October.", "promise_to_pay", 6000, "2026-10-13", False),
    ("I can pay INR 1000 on Friday.", "promise_to_pay", 1000, "2026-10-09", True),
    ("I will pay INR 2000 on 15 October.", "promise_to_pay", 2000, "2026-10-15", True),
    ("Can you waive the charges? I will pay INR 10000 on 15 October.", "promise_to_pay", 10000, "2026-10-15", True),
    ("I already paid INR 10000 yesterday.", "already_paid", 10000, "2026-10-07", True),
    ("I already paid yesterday.", "already_paid", None, "2026-10-07", True),
    ("I paid INR 8000 on 6 October.", "already_paid", 8000, "2026-10-06", True),
    ("I already paid the overdue on 7 October.", "already_paid", None, "2026-10-07", True),
    ("I already paid this in full yesterday.", "already_paid", None, "2026-10-07", False),
    ("I paid it yesterday, please check.", "already_paid", None, "2026-10-07", False),
    ("I lost my job and need time.", "hardship", None, None, True),
    ("I lost my job last week.", "hardship", None, None, True),
    ("This is a hardship case. I lost my job.", "hardship", None, None, True),
    ("Hardship. I cannot pay this week.", "hardship", None, None, True),
    ("I lost my job. I cannot go on.", "hardship", None, None, True),
    ("I lost my job and the EMI bounced.", "hardship", None, None, True),
    ("I want to dispute the charge.", "dispute", None, None, True),
    ("I dispute this balance.", "dispute", None, None, True),
    ("Please open a dispute on the penalty.", "dispute", None, None, True),
    ("I dispute the overdue amount.", "dispute", None, None, True),
    ("This is a billing dispute.", "dispute", None, None, True),
    ("I dispute the bounce charge.", "dispute", None, None, True),
    ("You have the wrong number.", "wrong_person", None, None, False),
    ("Wrong number. I do not know that person.", "wrong_person", None, None, False),
    ("This is a wrong number.", "wrong_person", None, None, False),
    ("Sorry, wrong number.", "wrong_person", None, None, False),
    ("You have reached the wrong number.", "wrong_person", None, None, False),
    ("Wrong number, please stop calling.", "wrong_person", None, None, False),
    ("Please call me back tomorrow.", "callback", None, None, False),
    ("Call me back after 5.", "callback", None, None, False),
    ("This is a callback request for tomorrow morning.", "callback", None, None, False),
    ("Please call me back on the registered mobile.", "callback", None, None, False),
    ("Callback tomorrow, I am in a meeting.", "callback", None, None, False),
    ("Can you call me back later today?", "callback", None, None, False),
    ("I want to register a complaint.", "complaint", None, None, True),
    ("This is a complaint about repeated calls.", "complaint", None, None, True),
    ("I am filing a complaint.", "complaint", None, None, True),
    ("Please note my complaint against the caller.", "complaint", None, None, True),
    ("I have a complaint. Someone threatened me.", "complaint", None, None, True),
    ("Take this complaint and stop the calls.", "complaint", None, None, True),
    ("I want a payment plan of INR 500 per month.", "payment_plan", 500, None, True),
    ("INR 500 per month is all I can do.", "payment_plan", 500, None, True),
    ("Can I get a payment plan?", "payment_plan", None, None, True),
    ("I want a payment plan. First instalment INR 5000 on 15 October.", "payment_plan", 5000, "2026-10-15", False),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    cases = []
    for index, item in enumerate(PARAPHRASE, start=1):
        cases.append(_case(f"para_{index:02d}", item[0], item[1], item[2], item[3], item[4], True, item[6], index))
    for offset, item in enumerate(KEYWORD, start=1):
        cases.append(_case(
            f"key_{offset:02d}", item[0], item[1], item[2], item[3], item[4], False, None, 100 + offset,
        ))
    cases.append(_procedural_hours())
    cases.append(_procedural_identity())
    if len(cases) != 80:
        raise SystemExit(f"expected 80 conversations, got {len(cases)}")
    for case in cases:
        (OUT / f"{case['id']}.json").write_text(json.dumps(case, indent=2), encoding="utf-8")
    print(f"wrote {len(cases)} conversations")


def _case(case_id, text, intent, amount, when, escalate, v1_miss, cause, account_n):
    overdue = 20000 if intent == "payment_plan" or (intent == "promise_to_pay" and amount not in (None, "FULL") and amount < 5000) else 10000
    if amount == 18400:
        overdue = 18400
    if amount not in (None, "FULL") and intent == "promise_to_pay" and not escalate:
        overdue = int(amount)
    if amount == "FULL":
        overdue = 18400 if "Eighteen" in text else 15000
        gold_amount = overdue
    else:
        gold_amount = amount
    if intent == "payment_plan" and amount == 5000:
        overdue = 20000
    ledger_agrees = intent == "already_paid" and not escalate
    turns = []
    if intent != "wrong_person":
        turns.append({"user": "Hello, this is the borrower.", "gold_intent": None})
        turns.append({
            "user": "Date of birth 1984-06-15 and PAN last four 4242.",
            "gold_intent": None,
            "expect_verified": True,
            "expect_disclosure": True,
        })
    turns.append({
        "user": text,
        "gold_intent": intent,
        "gold_amount": gold_amount,
        "gold_date": when,
        "expect_escalate": escalate,
        "expect_link": (not escalate) and intent in {"promise_to_pay", "payment_plan"},
        "expect_no_amount": intent == "wrong_person" or escalate,
    })
    return {
        "id": case_id,
        "account_id": f"HL{account_n:06d}",
        "now": NOW,
        "channel": "inbound_chat",
        "gold_intent": intent,
        "must_escalate": escalate,
        "v1_miss": v1_miss,
        "v1_miss_cause": cause,
        "slot_scored": intent in {"promise_to_pay", "payment_plan"} and not escalate and gold_amount is not None and when is not None,
        "override": {
            "dob": "1984-06-15",
            "pan_last4": "4242",
            "overdue_inr": overdue,
            "charges_inr": 250,
            "last_payment_inr": overdue if ledger_agrees else 0,
            "last_payment_date": "2026-10-07" if ledger_agrees else None,
        },
        "turns": turns,
    }


def _procedural_hours() -> dict:
    return {
        "id": "proc_after_hours",
        "account_id": "HL000199",
        "now": LATE,
        "channel": "outbound_call",
        "gold_intent": None,
        "must_escalate": False,
        "v1_miss": False,
        "v1_miss_cause": None,
        "slot_scored": False,
        "override": {"overdue_inr": 15000, "charges_inr": 250},
        "turns": [
            {
                "user": "Hello?",
                "gold_intent": None,
                "expect_no_amount": True,
                "expect_visible_contains": "8 AM and 7 PM",
                "expect_no_model": True,
            }
        ],
    }


def _procedural_identity() -> dict:
    return {
        "id": "proc_identity_twice",
        "account_id": "HL000198",
        "now": NOW,
        "channel": "inbound_chat",
        "gold_intent": None,
        "must_escalate": True,
        "v1_miss": False,
        "v1_miss_cause": None,
        "slot_scored": False,
        "override": {
            "dob": "1984-06-15",
            "pan_last4": "4242",
            "overdue_inr": 15000,
            "charges_inr": 250,
        },
        "turns": [
            {
                "user": "Date of birth 1999-01-01 and PAN last four 0000.",
                "gold_intent": None,
                "expect_escalate": False,
                "expect_no_amount": True,
            },
            {
                "user": "Date of birth 1999-01-01 and PAN last four 0000.",
                "gold_intent": None,
                "expect_escalate": True,
                "expect_no_amount": True,
                "expect_reason": "identity_failed",
            },
        ],
    }


if __name__ == "__main__":
    main()
