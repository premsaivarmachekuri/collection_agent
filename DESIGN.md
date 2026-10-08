# Design

## Runtime

```
Inbound turn
  -> precheck (window, attempts)     # no model
  -> if unverified and third party   # rules, safe template, stop
  -> if unverified                    # extract DOB / PAN last-4, verify_identity
  -> if verified                      # model classifies, policy chooses the tool
  -> template reply                   # draft is not shown
  -> trace append
```

States: `greet`, `verify`, `listen`, `escalated`, `closed`.

`AGENT_MODE=notes_only` still runs the rule path for the live reply. The model is called only to attach a note on the trace. The note is not sent.

## Who may see the balance

`get_account` checks `session.verified`. The disclosure template is the only borrower-facing string that contains the overdue amount, and it is emitted only on the turn that verification succeeds, or afterwards. Third-party, after-hours, attempt-cap, and failed-identity replies do not contain it.

## Offer rule

Let D be overdue in INR.

- One-time promise with amount >= D: `issue_payment_link` for D (or the promised amount if it equals D).
- A monthly plan, or a one-time amount below D: allowed only if the first amount >= 0.25D. Otherwise `escalate(plan_below_floor)` and the blocked template. The borrower's number is not repeated back.
- Any waiver request: `escalate(waiver_refused)` plus the no-waiver line. The draft is not shown, so a model "yes" cannot land.

## Escalation enum

`hardship`, `dispute`, `complaint`, `distress`, `human_requested`, `plan_below_floor`, `already_paid_mismatch`, `identity_failed`, `low_confidence`, `waiver_refused`.

`wrong_person` is logged and not escalated. The demo is a refusal, not a transfer. `callback` is logged and not escalated.

Already-paid agrees only when the ledger last credit is on or after the claimed date and at least the overdue amount. Otherwise a person.

## Prompt gate

`policy/prompts/v2.txt` must contain every fixed required line in `policy/scripts.json`. `evals/fixtures/v2_missing_opening.txt` is the broken prompt. `python scripts/demo.py prompt-break` exits 1. pytest fails if the production prompt fails the same check.

## Traces

One JSON object per turn in `traces/turns.jsonl`: session, account, state, model version, intent, confidence, slots, tool calls, draft, visible text, violations, latency. Visible text is what the borrower was allowed to see. Violations must stay empty for the gate to pass.

## Eval

`evals/harness.py` replays the 80 conversations. Intent is scored only on turns with `gold_intent` where the model ran. Precheck blocks are in the 80 and are not called intent errors. Slot score is exact date and exact INR on `promise_to_pay` and accepted `payment_plan` turns. Escalation recall is must-escalate cases that reached `escalate`. Compliance is a scan of visible text plus illegal tool calls.

The keyword baseline is instruction pack v1, not a second product path. The gate compares v2 accuracy to v1 accuracy on the same 80.

## Deploy

One process. `uvicorn app.main:app`. Demo defaults to pack v2 and needs no key. `MODEL_BACKEND=litellm` and `LITELLM_MODEL` switch the classifier. Tools stay local until a lender adapter replaces `app/tools.py`.
