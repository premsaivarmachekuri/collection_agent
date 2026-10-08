# Requirements context

Saved 2026-10-08 from the case brief in `fde_case_study.md`.

The Notion page (https://app.notion.com/p/3f309ba4c71e81c785eafc505e32eb26) and the Rifa Ashby page did not return article text in this environment (JavaScript wall). Quotes below are the ones already copied into the local brief, not a fresh scrape of those pages.

## Problem

A collections team works home loans 1 to 30 days overdue for an Indian lender. A caller confirms identity, states the amount due, and logs an outcome. Risky moments today depend on the caller's memory: a plan below the lender minimum, telling a family member about the debt, contact outside allowed hours, or a skipped required line.

## Who decides

| Decision | Owner |
|---|---|
| Contact only between 8 AM and 7 PM IST, at most 3 attempts a day | Rules, before any model call |
| No loan details until identity is checked | Rules |
| Required lines said word for word | Rules on the borrower-facing string. The prompt must also contain them or the gate fails |
| Payment plan only if the first payment is at least 25% of overdue. Never waive charges | Rules. Blocked in code before the borrower sees an offer |
| Eight intents, promised date and amount, draft, confidence | Model |
| Hardship, dispute, already-paid when records disagree, complaint or distress, human request, plan outside limits, identity failed twice, confidence under 0.7 | A person. The router must escalate even if the model does not ask |

Eight intents: `promise_to_pay`, `already_paid`, `hardship`, `dispute`, `wrong_person`, `callback`, `complaint`, `payment_plan`.

## Eval targets (author targets; only the calling window is attributed to RBI)

- Zero compliance violations.
- At least 98% of must-escalate cases reach a person.
- Intent accuracy at least 85%, and at least 10 points above a keyword baseline.
- Promised date and amount captured correctly at least 90% of the time.
- 95% of replies within 2.5 seconds.

## Kill rule

After two rounds of fixes, if any violation remains or fewer than 95% of must-escalate cases reach a person, move those checks into rules and keep the model only for after-call notes.

This repo ships that switch as `AGENT_MODE=notes_only`. It does not auto-flip during `make gate`, because the gate is what the operator reads before flipping it.

## MVP scope

- 200 overdue accounts derived from UCI dataset 350.
- 80 test conversations, including tricky ones.
- 5 tools. Model calls routed through a LiteLLM adapter.
- pytest and DeepEval replay. `make gate` / `python scripts/gate.py` fails if a target is missed.
- A trace of every turn.

## Stretch (not built)

Voice, LangGraph, reviewer corrections as new tests, prompt v1 vs v2 on a traffic slice beyond the offline packs, Postgres, Hinglish beyond the few paraphrase cases, production dialer cutover.

## Demo

- Borrower promises to pay and gets a payment link.
- A request for INR 500 a month goes to a person.
- A family member asks about the debt and gets nothing.
- A prompt change that drops a required line fails the gate. The borrower-facing template still contains the line.

## Source quotes already in the brief

- Rifa: "Automated tests that replay past conversations and check the agent follows the procedure. Nothing ships without passing them." and "guardrails that make out-of-bounds offers impossible rather than just unlikely."
- Dscout: "production replays, or staged rollouts."
- Credgenics, Katonic, Recrew, Holistic AI, and Commure are cited on the Notion page, which was not readable here.
- Brief correction, preserved: Holistic AI's role was posted on 18 Sep, so it is not new. Recrew had over 200 applicants at the time of the brief.
