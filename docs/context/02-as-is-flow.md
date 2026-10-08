# As-is flow

This is the operating as-is of an Indian home-loan early-bucket desk. It is not a system found in this repository. The repo had no lender integration when this note was written. Figures for handle time and QA sample rate are industry texture, not a measured book. Tag: [Industry as-is].

## What already exists

The lender is not missing a system of record. The gap is the untyped middle between screen pop and the disposition click.

| System | Owns | Does not enforce |
|---|---|---|
| LMS (FinnOne, Nucleus, Finacle, or equivalent) | EMI, overdue, bounce charges, DPD, last credit | Who is on the phone |
| NACH / eNACH / UPI Autopay | Presentment and the bounce file | A conversation |
| Night batch | Who enters the 1–30 book | Contact rules |
| Allocator | Whose list the account is on | What may be said |
| Dialer | Campaign window, its own attempt count, recording | A personal mobile or a WhatsApp after logout |
| Collections screen | Name, phone, overdue visible before connect, disposition dropdown | Identity before disclosure |
| SMS / WhatsApp / IVR | Approved templates | A negotiated plan |
| Payment gateway | A link into the lender's account | That the amount matches what was just promised |
| QA | A small sample of recordings, next day | The moment the sentence is said |
| Supervisor workbook | Next-morning PTP chase, roll to 31+ | The call itself |

RBI's digital lending directions (2 Sep 2022, consolidated 8 May 2025) keep grievance redressal and recovery conduct with the regulated entity, and require repayment to land in the RE's account rather than a pass-through. The 8 AM–7 PM window is the case brief's reading of RBI 2022 guidance. In the as-is it usually lives in the dialer campaign and the handbook, not as a hard stop on every channel. The August 12, 2022 recovery-agent circular was not re-fetched cleanly in this session; do not cite a clause number that was not read.

## The day

1. Due date: NACH is presented.
2. Bounce file returns. Night batch posts the charge and puts the account on the 1–30 queue.
3. Allocator drops it on a caller list.
4. Dialer screen pop shows name, phone, and amount before anyone has confirmed identity.
5. Caller dials inside the shift. If a spouse answers, the balance is often still said. Policy PDF forbids it. Nothing in the screen prevents it.
6. Caller asks for a date. "Next Friday" is typed as free text. A INR 500 plan or a charge waiver can be agreed out loud. The LMS cannot book the waiver without a credit memo, but the borrower has already heard the yes.
7. Disposition is one code: PTP, paid, callback, no contact, wrong number, dispute. Hardship and complaints go to whoever is standing. If the lead is busy, it is a note.
8. Payment link is copied from a portal. Wrong amount is a paste error.
9. Recording is stored. QA listens to a sample tomorrow.
10. Next morning the workbook chases broken PTPs. "Already paid" is an argument with a ledger that may not have posted yet.

After the call the lender can usually produce a recording, a disposition code, and a credit if one arrived. They cannot produce, for every turn, who was verified, which required sentence was said, what amount was offered, or why a person was not pulled in.

## The four risks, and the system that fails them

| Risk | Where it lives today |
|---|---|
| Plan below the floor, or a waived charge | A sentence. Not a field the LMS rejects before it is spoken |
| Balance told to a family member | Screen pop has the balance before identity. Dialer does not know who picked up |
| Contact after 7 PM, or a 4th attempt | Campaign schedule only. Side channels are invisible |
| Skipped required line | Absent from the disposition. Present only on a recording nobody sampled |

The agent in this repo does not replace the LMS, the dialer, or the gateway. It replaces that untyped middle.
