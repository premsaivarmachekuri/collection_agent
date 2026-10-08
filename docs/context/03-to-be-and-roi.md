# To-be flow, integration, and the number for the company

Design choices are marked [Design]. Brief targets are marked [Specified]. Money figures are [Projected] unless a later eval report marks them [Measured]. Nothing here is a measured lender P&L.

## To-be

The night batch still decides who is overdue. This service never computes DPD, never posts a charge, and never moves money. It may speak only after a precheck. The borrower hears a template the policy layer released, not the model draft.

```
LMS night batch -> read extract
  -> precheck (08:00-19:00 IST, attempts, DND, open complaint)
  -> registered channel only
  -> identity against CIF (pass/fail; expected DOB never enters the prompt)
  -> read balance
  -> model: intent, date, amount, confidence, draft
  -> policy gate
       reject: third party, hardship, dispute, complaint, distress,
               human request, below-floor plan, ledger disagree,
               identity failed twice, confidence < 0.7
       allow: full promise, or a plan whose first payment is >= 25%
  -> payment link from the existing gateway, amount set here
  -> structured disposition back to the collections module
  -> trace of every turn
```

Side channel close [Design]: on accounts this workflow owns, the collector screen does not show the phone number or the balance. Otherwise the personal-mobile hole stays open and the attempt cap is theatre.

Fail closed [Design]:

- LMS down or stale: do not quote a balance.
- Attempt count stale: do not contact.
- Gateway down: record the promise, send no link, do not invent a VPA.
- Escalation write returns no case id: the account stays open. It does not fall back to the bot.

## Integration contract

| System | Direction | Contract |
|---|---|---|
| LMS | Read only | Account, overdue, charges, DPD, last credit, NACH status. After identity |
| CIF / KYC | Read only | Compare DOB and PAN last-4. Model sees pass or fail |
| Dialer | Read and write | Attempt count is the source of the 3-a-day cap. Reserve before contact. Transfer on the same session |
| Payment gateway | Write request, read webhook | Link for an amount this service computed. Idempotency key is account plus due cycle. Status returns through the LMS posting |
| Collections module | Write | Intent, ISO date, amount in paise, reason code, case id. Free text stops being the system of record |
| SMS / WhatsApp BSP | Template id only | Existing registered template plus variables |
| Human queue | Write | `escalate` must return a case id |
| QA / audit | Append | Every turn |

Not in the first integration: bureau, field app, legal, GL.

This MVP does not call a real LMS. `app/tools.py` is the seam. A lender adapter implements the same five functions. The demo store is the stand-in.

## Five tools

1. `verify_identity` — returns verified or failed, and attempts remaining. Never returns the expected DOB.
2. `get_account` — refused by the router unless the session is verified.
3. `issue_payment_link` — only for a full overdue promise or an already-accepted plan. Amount checked again here.
4. `record_outcome` — disposition. A promise missing date or amount is incomplete, not a kept PTP.
5. `escalate` — reason code enum, returns a case id.

There is no `propose_plan` tool. Plan math sits inside the gate and `issue_payment_link`, so there is no path that offers a plan without also being able to block it. Contact window and attempt count are not tools.

## ROI the company should be shown

Do not present a credit-loss saving as the base case. This product escalates hardship. It does not squeeze it. The accounts a CFO would count as loss avoided are the ones a person still handles. Booking an NPA rupee in the base case is how the pitch gets thrown out.

Base case is capacity released on the scripted slice. Conduct is a gate, not a rupee line.

Per 10,000 accounts entering the 1–30 queue in a month. Replace every input with the lender's MIS before the meeting. [Projected]

| Input | Illustrative | Source |
|---|---|---|
| Right-party contact | 50% | Their dialer, not measured here |
| Routine share (promise, pay now, callback, wrong party) | 55% | Last 90 days of dispositions |
| Containment of that routine share | 70% | A projection from a green gate, not a production result |
| Conversations a collector finishes in a month | 500 | Their dialer |
| Fully loaded collector cost | INR 40,000 / month | Their HR |
| Conversations removed | 1,925 | 10000 x 0.50 x 0.55 x 0.70 |
| Capacity released | about 4 collectors, INR 1.5 lakh / month, INR 18 lakh / year | Arithmetic on the rows above |

Print INR 18 lakh only as "per 10,000 accounts a month, if your mix matches these inputs." A book at 3,000 accounts a month does not have an opex case. A book at 40,000 does: about INR 6 lakh a month of capacity, about INR 70 lakh a year. Ask for the queue size before stating a payback.

Year-1 build to read an LMS extract, reserve dialer attempts, issue links, and write dispositions: INR 40–70 lakh [Projected]. At 10,000 accounts a month, opex payback is about three years and the project is not justified on headcount. At 40,000, opex payback is inside a year. Model cost on the messaging path is a few rupees a contained conversation. Voice is a later line.

Upside, as a scenario, not as the ask [Projected]: operational leakage. Borrowers who already said yes and slipped because the date was free text, the link was wrong, or nobody called back. If their MIS shows that leakage, the value is those accounts times the EMI, counted as roll avoided. Illustrative: 20% leakage on the routine slice is 550 accounts; recovering half is about INR 70 lakh of EMI staying in the month at INR 25,000 average due. Most of that is timing, not income. The funding benefit of one month at 9% is under INR 1 lakh. The collections head is measured on the roll, so it belongs on that slide, not in the P&L bridge.

Conduct is not an ROI line. One third-party disclosure is a complaint path the lender already owns. The board slide is binary: this path cannot offer below the floor, cannot disclose before identity, and cannot contact outside the window, because those checks are code. If the gate is red, it does not ship.

## The ask

Not a bot in production. Ninety days read-only on the 1–30 extract and the dialer dispositions, so the 55% and the leakage become their numbers. Write access to the gateway and the collections module comes after the gate is green. If two fix rounds still miss the escalation floor, the live path goes to `notes_only` and the model is kept for after-call notes.

## Staged rollout [Specified by the Dscout line in the brief]

1. Cassette / synthetic accounts. This repo.
2. Shadow: live model, replies discarded, traces compared with the human collector.
3. A small slice of 1–30 accounts, window only, human queue staffed. Nothing promotes itself.
