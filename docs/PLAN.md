# Build plan

Status: this is the plan the implementation follows. Scope is the MVP in the brief, plus the deployable seam (Dockerfile, fail-closed tools, `notes_only`). Stretch items are named and not built.

## Decisions

1. Borrower-facing text comes from locked templates in `policy/scripts.json`. The model draft is traced and never concatenated onto the reply. Out-of-bounds offers are impossible, not unlikely.
2. The gate still fails if the production prompt drops a required line. Protection of the borrower and permission to ship are separate checks.
3. `make gate` is deterministic and does not need an API key. Live LiteLLM is an adapter behind `MODEL_BACKEND=litellm`. Latency under 2.5s is measured on the local path and reported as [Measured] there. A hosted-model latency number is [Projected] until `make gate-live` is run with a key.
4. Intent v1 is a narrow keyword pack. Intent v2 is a paraphrase pack. Both sit behind the same policy wrapper, so a weak classifier still cannot disclose or offer below the floor. That is the point of the architecture, and the eval report should show it.
5. UCI 350 is a source of overdue-shaped numbers only. Every derived Indian field is synthetic. The adapter records `source` on each account.
6. DeepEval runs a deterministic metric over the same replays. It is not an LLM judge. Compliance is never delegated to a judge model.
7. The kill rule is an operator switch, not something the test suite flips on itself.

## Build order

1. Save research under `docs/context/`.
2. Policy, scripts, prompt artifact check.
3. Account store, five tools, trace log.
4. Orchestrator and both instruction packs.
5. Generate 200 accounts and 80 conversations.
6. pytest gate, DeepEval metric, demo commands, eval report written from the run.
7. Dockerfile and README.

## Out of scope

Voice, LangGraph, Postgres, a real dialer, a real payment gateway, Hinglish coverage beyond the paraphrase cases in the 80, production PII, auto-promotion between rollout stages.
