# Northwind collections agent

An early-bucket collections agent for an Indian home-loan lender. It does not ship unless the replay gate is green.

The model classifies. The policy layer decides what the borrower is allowed to hear. An out-of-bounds offer is blocked in code, not talked out of.

## What this is, and is not

This is the MVP from the case brief: 200 overdue accounts, 80 replayed conversations, five tools, a LiteLLM adapter, pytest, DeepEval, and a trace of every turn.

It is not a replacement for the LMS, the dialer, or the payment gateway. Those stay the systems of record. This service is the untyped middle: identity, the required lines, the offer floor, and the handoff to a person. See `docs/context/` for the as-is, the to-be, and the ROI model. Every money figure there is projected.

UCI dataset 350 supplied the 200 delinquency-shaped rows (`PAY_0 = 1`, one month late). Names, dates of birth, PAN last-4, and rupee amounts are synthetic. The source tag on each account says so.

## Run the gate

```bash
python scripts/gate.py
```

On Windows that is the build gate. `make gate` calls the same script if you have make. It fails if any target is missed:

| Target | Bound |
|---|---|
| Compliance violations | 0 |
| Must-escalate cases that reach a person | >= 98% |
| Intent accuracy | >= 85%, and >= 10 points over the keyword pack |
| Promised date and amount | >= 90% |
| Local reply latency p95 | < 2.5 s |

The default classifier is instruction pack v2. It needs no API key. `MODEL_BACKEND=litellm` and `LITELLM_MODEL` switch the classifier through LiteLLM. `MODEL_BACKEND=groq` calls `https://api.groq.com` directly, with `GROQ_API_KEY` and optional `GROQ_MODEL` (default `qwen/qwen3.8-27b`). `llama-3.1-8b-instant` is not on current Groq accounts and returns 404. The tool router does not change. Hosted latency is not part of `make gate`.

```bash
copy .env.example .env
```

Paste the key into `.env` next to `GROQ_API_KEY`. Set `GROQ_MODEL` on the next line. `.env` is not committed. Leave `MODEL_BACKEND=pack` if you still want `python scripts/gate.py` to stay offline. `scripts/say_groq.py` calls Groq either way.

```bash
python scripts/say_groq.py "I will pay INR 18400 on 9 October."
```

That script prints Groq's classification. The draft is not what the borrower hears.

## Two-minute demo

```bash
python scripts/demo.py promise
python scripts/demo.py plan
python scripts/demo.py family
python scripts/demo.py prompt-break
```

1. A borrower promises to pay INR 18,400 and gets a payment link.
2. INR 500 a month is below the 25% floor. A person gets the case. The amount is not confirmed back.
3. A family member asks what is owed and gets no loan details. `get_account` is not called.
4. `prompt-break` exits 1. The fixture dropped "This is Asha from Northwind Housing Finance. This call is recorded." The borrower-facing template still contains that line. The gate refuses to ship the prompt.

## Kill switch

```bash
set AGENT_MODE=notes_only
```

The live reply stays on templates and rules. The model is called only to attach a note on the trace. The note is not sent. Use this if a second fix round still leaves a violation, or if must-escalate recall drops under 95%. The test suite does not flip this by itself.

## Layout

```
app/            orchestrator, policy, five tools, LiteLLM adapter
policy/         locked scripts and the production prompt
data/           203 accounts (200 UCI-derived + 3 demo)
evals/          80 conversations, pytest gate, DeepEval metric
scripts/        generate, demo, gate, report
traces/         one JSON line per turn
docs/context/   as-is, to-be, ROI, sources
docs/eval_report.md
```

The five tools are `verify_identity`, `get_account`, `issue_payment_link`, `record_outcome`, and `escalate`. Contact window and the attempt cap are not tools. A model cannot forget to call them.

## API

```bash
python -m uvicorn app.main:app --port 8000
```

`GET /health`, `POST /call`, `GET /traces`. Docker is the same process:

```bash
docker compose up --build
```

No model key is baked into the image. The default backend is the offline pack.

## Honesty on the numbers

`docs/eval_report.md` is rewritten by the gate from a fresh replay. Those figures are measured on this suite.

Pack v2 and the 80 paraphrases were written together. 100% intent on that set means the pack covers the set. It does not mean a hosted model will score 100% on live calls. Say that in the room.

ROI in `docs/context/03-to-be-and-roi.md` is projected. Do not present it as measured savings.
