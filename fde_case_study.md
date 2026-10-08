Today's case study is a **collections agent that can't ship until it passes a test gate**, built for an Indian home loan lender. I picked that sector from the post's fintech slide. The requirements come from this week's postings, mainly Rifa, Credgenics and Dscout. The full version, with 29 quotes taken word for word from the postings, is on the [Case Study 2026-10-08 Notion page](https://app.notion.com/p/3f309ba4c71e81c785eafc505e32eb26).

**The problem.** A collections team works loans that are 1 to 30 days overdue. Today a caller confirms the borrower's identity, states the amount due, and logs the outcome: promise to pay, already paid, hardship, dispute, wrong person, callback, or complaint. The risky moments depend on the caller's memory: offering a plan below the lender's minimum, telling a family member about the debt, calling outside allowed hours, or skipping a required line.

**Who decides what:**
- **Rules:** contact only between 8 AM and 7 PM, per the RBI's 2022 guidance, and at most 3 attempts a day. No loan details are shared until identity is checked. Required lines are said word for word. A payment plan is offered only if the first payment is at least 25% of what's overdue, and the agent never waives charges. Any offer outside these limits is blocked in code before the borrower sees it.
- **The model:** works out what the borrower means (8 categories), picks out the promised date and amount, calls the tools, and drafts replies within the rules. It also gives a confidence score.
- **A person:** takes over for hardship, disputes, "already paid" when the records disagree, complaints or distress, a request for a human, a plan outside the limits, identity that fails twice, or confidence under 0.7.

**MVP in 1–2 hours.** Take 200 overdue accounts from the public [UCI credit default dataset](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) and write 80 test conversations, including tricky ones. Build 5 tools and route model calls through LiteLLM, which LiteLLM's own posting names. Use pytest and DeepEval to replay every conversation, so that `make gate` fails the build when any target is missed. Log a trace of every turn.
**Stretch over 1–2 days.** Add voice, use LangGraph to run the call as fixed steps, and turn a reviewer's corrections into new test conversations. Then compare prompt version 1 against version 2 on a simulated slice of traffic, and add Postgres, Docker and Hinglish conversations.

**Eval targets** (these are my targets; only the calling window comes from the RBI):
- Zero compliance violations.
- At least 98% of the cases that must reach a person actually reach one.
- Intent accuracy of at least 85%, and at least 10 points above a simple keyword baseline.
- Promised date and amount captured correctly at least 90% of the time.
- 95% of replies within 2.5 seconds.

**Kill rule.** If, after two rounds of fixes, any violation remains or fewer than 95% of must-escalate cases reach a person, move those checks into rules and keep the model only for after-call notes.

**What to ship.** A README, a 2-minute demo, an eval report with 10 failures and their causes, the traces, and a write-up with every figure marked [Measured] or [Projected]. In the demo:
- A borrower promises to pay and gets a payment link.
- A request for ₹500 a month goes to a person.
- A family member asks about the debt and gets nothing.
- A prompt change drops a required line and fails the gate.

**Where the requirements come from:**
- [Rifa](https://jobs.ashbyhq.com/rifa/bd6366c8-893a-49fd-9b9a-31cb75a397d0): "Automated tests that replay past conversations and check the agent follows the procedure. Nothing ships without passing them." and "guardrails that make out-of-bounds offers impossible rather than just unlikely"
- [Dscout](https://job-boards.greenhouse.io/dscout/jobs/4370258009): "production replays, or staged rollouts"
- Credgenics, Katonic, Recrew, Holistic AI and Commure are also quoted on the Notion page.

One correction to Tuesday's digest: Holistic AI's role was actually posted on 18 Sep, so it isn't new. Recrew now has over 200 applicants.

as  aprifessional architect and fde with ecased of years of experincee let's plan the abvoe product and dpleyable
