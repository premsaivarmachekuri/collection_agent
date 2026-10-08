# Sources and what was actually read

| Source | What happened in this session |
|---|---|
| `fde_case_study.md` | Read in full. Primary requirements. |
| Notion case page `3f309ba4c71e81c785eafc505e32eb26` | Fetch returned a JavaScript wall. Quotes were not re-verified. |
| Rifa Ashby posting | Fetch returned a JavaScript wall. The two sentences in the brief are used as given. |
| UCI Default of Credit Card Clients, id 350 | Dataset card fetched. 30,000 rows, 23 features, CC BY 4.0. Yeh, I-Cheng. Taiwan credit cards, not Indian home loans. DOI 10.24432/C55S3H. |
| RBI Guidelines on Digital Lending, 2 Sep 2022, DOR.CRE.REC.66/21.07.001/2022-23 | Fetched. The circular is marked repealed in favour of the 8 May 2025 Directions. Recovery-agent conduct is cross-referenced, not spelled out as an 8 AM–7 PM clause in the body that was read. |
| RBI (Digital Lending) Directions, 2025, 8 May 2025 | Fetched. Grievance redressal stays with the RE. Repayment goes to the RE account, not an LSP pool. Recovery-agent particulars must be told to the borrower before contact. The 8 AM–7 PM window is the case brief's attribution, not a sentence copied from this Directions text. |
| August 12, 2022 recovery-agent circular | A fetch by notification id returned a different 2022 circular (overseas investment). Clause numbers from that circular are not used. |

## Implication for every figure

- Calling window in this product: [Specified] by the case brief, implemented as 08:00 inclusive to 19:00 exclusive IST.
- 25% first payment, 3 attempts, 0.7 confidence, eval percents: [Specified] by the case brief, not by a regulation this session verified.
- Account balances, names, DOBs, PAN last-4: [Synthetic], derived from UCI where the file downloaded, otherwise from a seeded fallback.
- ROI: [Projected]. See `03-to-be-and-roi.md`.
- Gate metrics in `docs/eval_report.md`: [Measured] on the offline suite after `python scripts/gate.py`.
