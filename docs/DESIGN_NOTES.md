# Design notes

Longer-form background moved out of the README to keep the front door
short. Each section is the reasoning behind one decision.

## Why MCP

A talent team with no ATS shouldn't have to adopt a new app. They should be able to ask the AI client they already have.

So this is an MCP server first. In Claude Desktop there is nothing to install and no UI to learn: paste the posting into the chat, ask it to rank a folder. The web page exists to look at results, not as the product.

Five tools, one per action: `preview_rubric`, `screen_resume`, `rank_pool`, `explain_verdict`, `query_candidates`.

**None of them takes a real-world action.** They read and report. Nothing can reject a candidate, send mail, or write to a system of record. That keeps a human on every hiring decision, and it means a prompt injection that survives out of a resume still has nothing to actuate.

`preview_rubric` returns a `rubric_id` that `rank_pool` accepts, so the rubric a person reads and approves is the one that scores the pool. Generation isn't deterministic, which is exactly why that id exists.


### What keeps the demo honest

A run against any posting other than the bundled one **reports no accuracy figure at all**. The labels in `data/labels.json` describe exactly one job. Screening these same resumes against a payments or nursing posting produces perfectly correct verdicts that those labels say nothing about, and grading them against the wrong answer key would publish a made-up number as if it meant something.

Expect most candidates to score near zero there. The corpus is 60 AI-engineer resumes, and rejecting them for a payments role is the system working, not failing.

A live run is capped at 24 resumes. That is a spending limit, not a technical one.


### The cutoffs were the bug

`scripts/sweep_cutoffs.py` re-thresholds recorded scores — no API calls, free ([output](CUTOFF_SWEEP.md)). It found the score-to-verdict mapping was discarding most of the signal.

| Label | lowest score | median | highest |
|---|---|---|---|
| advance | **4.0** | 6.5 | 8.0 |
| hold | 0.0 | 2.5 | **4.5** |
| reject | 0.0 | 0.3 | **1.0** |

Every `advance` scored ≥ 4.0. Every `reject` scored ≤ 1.0. The panel was ranking candidates correctly the whole time; the hand-picked 7.0/5.0 bar was rejecting most of the people it was meant to advance.

Moving to **4.0/1.0** took macro-F1 from 0.601 to **0.847**, with `hold` recall going 0.20 → 0.65. The sweep predicted 0.846; the run measured 0.847.

**Escalation and human review were later unwelded** — that turned out to matter more than either. Escalating used to auto-flag a candidate for a human, so ~half the stack landed in a queue. But panel disagreement barely predicts a wrong answer: the old flag queued 53% of candidates and caught 36% of errors, while a *near-cutoff* flag at the same queue size catches 82%. And the arbiter itself was mostly ceremony — it moves a score by 0.33 on average, so **92% of escalations returned a different number and the same verdict**. Now the arbiter fires only when the panel mean sits within 0.5 of a cutoff, and a human is asked only when the *final* score sits near one. Measured live: escalation fell **47% → 5%**, the human queue **53% → 30%**, macro-F1 unchanged. The review margin is a fraction of each model's own score band, not a fixed number of points — a flat margin queued 43% of Sonnet's stack and 15% of Luna's, because they grade on different scales. [docs/RESULTS_HISTORY.md](RESULTS_HISTORY.md)

Two things landed with it. The arbiter now returns a **score only** — previously an escalated 6.5 could be `advance` because the arbiter said so while an unescalated 6.5 was `hold`, the same score getting different answers depending on a coin flip. And escalation now requires the agents to disagree on the *verdict*, not merely to vary: a 9.0/7.0/6.0 panel has a wide spread but nothing an arbiter returns changes the outcome.

Caveat worth keeping: those cutoffs were fitted on the same 60 resumes they are scored against. The plateau is narrow on the advance side, so treat 4.0/1.0 as informed rather than validated until the corpus grows.

Other things named rather than hidden:

- The three-way architecture bake-off has since been run, and the cascade lost. The parallel panel scored 0.788 against a single call's 0.821; only the arbiter earned its keep. The architecture changed to match. See [ARCHITECTURE.md](ARCHITECTURE.md).
- **A third of the stack still reaches a human, and half the errors still get through.** The system is wrong on ~13% of candidates and a reviewer sees ~30%; reviewing a third of a stack cannot catch most of the mistakes in it. That is arithmetic, not a tuning failure — raising the review margin trades queue size for recall roughly linearly, and cannot reach high recall at any tolerable queue size.
- Disagreement-based escalation can't catch a panel that is unanimously and confidently wrong, because there is no disagreement to detect. That and the rest of the failure modes are in [docs/LIMITATIONS.md](LIMITATIONS.md).
- Roughly 1 panel call in 180 still loses its score to malformed JSON. Those get flagged for review, never silently scored zero. [RESULTS_HISTORY.md](RESULTS_HISTORY.md) has the two parsing bugs that only appeared once this ran against the real API, including one that was fabricating confident zeros and not flagging them.

Every measured run, what changed before it, and why the number moved is tracked in [docs/RESULTS_HISTORY.md](RESULTS_HISTORY.md).


### Why scores run low: one agent, and a decision that was tested

Of the three panel agents, `client_communication` scores a mean of **1.00**, versus 7.55 and 6.39 for the other two on candidates the corpus labels `advance`. It rarely exceeds 4.0 for anyone. The reason: most resumes never document client-facing work, and this persona reads that silence close to disqualifying rather than neutral — so it drags nearly every composite down about two points. That is why a 7.0 cutoff was far too high, why the arbiter kept overriding it upward, and why all remaining errors run the same direction.

**This was fixed and measured, then reverted.** A version telling the agent that silence scores mid-scale, not near-zero, was built and run against the full corpus. It worked on the agent's own terms — mean 1.00 → 3.34, 35 zeros → zero — but corpus accuracy fell, each version at its *own* best cutoffs: **0.880 → 0.796 macro-F1**. Kept the stricter version for accuracy.

The honest caveat: the synthetic archetypes were generated with an intended `client_communication` level, so a harsh reading of silence correlates with the answer key on *this* corpus specifically. On a real applicant, the fairer version is probably the better judge — this comparison only says which one matches synthetic labels better. Full numbers in [docs/SCORE_SCALE.md](SCORE_SCALE.md).

The design decisions and their tradeoffs are in [RESULTS_HISTORY.md](RESULTS_HISTORY.md), including what's deliberately unfinished and why.


## Local models

`core/router.py` is provider-agnostic, and that is demonstrated rather than asserted: adding OpenAI took one adapter class and no change to the cascade, and the panel now runs on it. A local provider would be the same shape. It is not built — the reason is hardware, not code (the results history) — so treat on-prem as a plausible next step, not a feature.

## Layout

```
src/resume_screener/
  core/         # ingest, the cascade, rubric generation, models, the provider router
  adapters/     # mcp_server.py, api.py, cli.py -- thin, all call the same core
  prompts/      # the hand-written rubric, and the meta-prompt that writes new ones
tests/          # offline, never calls an API
data/synthetic_resumes/   # generated corpus, no real candidates
docs/           # the target posting, eval results, per-candidate reports
```

`core/` never imports from `adapters/`. That one-way dependency is what lets the MCP server, the CLI, and the web API stay thin and share behaviour. maps every file with a one-line description.

The 60 resumes are generated, not real. [docs/corpus_design.md](corpus_design.md) covers the archetypes and how ground-truth labels were assigned.


### Why three dimensions

The count came from the posting, not from an experiment. This job description has three distinct requirement clusters:

| Dimension | What it judges |
|---|---|
| `production_reality` | Shipped and running, or a demo that stopped at the prototype? The posting says "not demos or prototypes" three separate times. |
| `technical_integration` | Real agentic work with memory, tools, and orchestration, or a skills list? |
| `client_communication` | Evidence of explaining technical work to non-technical people. |

`core/rubric_gen.py` rejects any rubric that isn't exactly three.

**Honest caveat:** the count was never tested. Two versus three versus five is still open in the results history.


## The rubric is written from the posting, not hardcoded

Hand a job posting in and the system writes its own scoring standard first: three dimensions, each with the criteria the panel scores against and the brief for the agent that owns it.

This matters because a panel is only as good as what it was told to look for. A generic "AI engineer" checklist scores every posting identically. A rubric derived from *this* posting notices what this posting actually repeats.

To check it wasn't just pattern-matching to engineering roles, I ran it against a charge-nurse posting for a hospital emergency department. It produced dimensions on ACLS/PALS/TNCC certification, charge authority on an unsupervised night shift, and Joint Commission documentation compliance. Nothing leaked through from the engineering version. It also picked up the posting's "we are not looking for" section and treated outpatient-only experience as a negative signal rather than a neutral one.

Two rules are enforced in code rather than trusted to the model:

- **Exactly three dimensions**, for the reason above.
- **Generation failure raises.** There is no silent fallback to the built-in rubric. Scoring one job's candidates against a different job's criteria is a wrong answer that looks like a right one.

