# Resume Screener — Project Plan

Living status doc. Three honest buckets: **settled** (decided, with the
actual reasoning), **built** (code that exists — separate from whether
it's been run), and **open** (still needs a real decision or a missing
piece before we can move on).

## Start here — updated 2026-08-27

**State:** macro-F1 0.847, accuracy 0.850, ~$1.20 per 60-resume run,
249 offline tests, everything committed and pushed. Nothing is
half-finished in the working tree.

**Next, in order** (full reasoning in §10):

1. **Variance estimate** — 3–5 runs, reported as a spread, ~$2. Two
   identical runs disagree on ~10% of verdicts. Until this exists, no
   comparison in this document can be trusted, including §8a.
2. **Single-pass arm of the bake-off** (§8) — the cascade's entire
   justification, still unmeasured. Blocked on item 1.
3. **Batch API** — ~50% off, natural fit, see `docs/COST_ANALYSIS.md`.
4. **Cut output tokens** — 69% of spend; try lower effort on the panel.
5. **Walkthrough mode** (§11) and the **hosting spend cap** — both
   specified, neither built.

**Read before quoting any number:** `docs/LIMITATIONS.md` (fitted
cutoffs, one-directional errors, no bias audit) and
`docs/COST_ANALYSIS.md` (the pricing table was wrong until 2026-08-27;
older cost figures in this repo are inflated).

---

## 1. Goal and hard constraints — settled

- Public GitHub repo + a demo link/video, sent as a follow-up after a
  second-round interview for a remote AI solutions engineering role.
- Standalone repo, not a folder inside the private nanobot monorepo —
  **done**, live at https://github.com/kjb135-coe/resume-screener,
  public, single commit, author `kjb135-coe` only, no Claude/Anthropic
  attribution anywhere in git history.
- Rubric and scoring are built against this specific posting
  (`docs/job_description.md`), not a generic AI-engineer template.
- Microsoft and ADP integration: deprioritized per explicit instruction
  — documented as a mapping (Copilot/VS Code MCP support, Claude models
  GA in Microsoft Foundry, ADP as an undone extension point), not a
  build focus right now.

## 2. Architecture — settled shape, specific config still open (see §8)

- One shared core library (`core/`), with CLI, web UI, and MCP server
  as thin adapters over it. No adapter contains scoring logic.
- MCP is the primary interface — the recruiter talks to an AI client
  they already have, rather than adopting a new app. Web UI is a demo
  instrument for the three evaluators, not the production design.
- Five MCP tools, one per action: `preview_rubric`, `screen_resume`,
  `rank_pool`, `explain_verdict`, `query_candidates`. (`preview_rubric`
  was added with generated rubrics — see §3a.)
- MCP scope: **server-only** for the demo. `core/enrichment.py`
  documents the client-consuming extension point (e.g. verifying a
  candidate's GitHub profile via an external MCP server) without a
  live third-party dependency in the demo path.
- Transport: stdio for local/dev, Streamable HTTP for the real hosted,
  multi-client deployment. Only stdio is wired up in code today.
- The tiered cascade concept — cheap extraction, a panel of judgment
  agents, an arbiter that only runs on disagreement — is settled as a
  *shape*. Whether it actually beats a simpler design is an open,
  three-way bake-off, see §8.
- `query_candidates` composes two general primitives per question:
  a sandboxed structured-query engine (DuckDB, generated SQL, never
  `eval`/`exec`) and an evidence-judgment LLM call, capped to a bounded
  answer. This split does double duty as a real defense against resume
  prompt injection, not just a cost optimization.

## 3. Rubric — settled

Three JD-anchored personas replaced the earlier generic depth/
trajectory/skeptic panel:

| Persona | What it checks | Why |
|---|---|---|
| `production_reality` | Shipped/production evidence vs. demo-stage work | JD explicitly repeats "not demos or prototypes, but systems used in production" |
| `technical_integration` | Agentic systems (memory, tools, orchestration) + real API/business-system integration | JD's own phrase, used verbatim |
| `client_communication` | Cross-functional/client-facing evidence | JD names this explicitly as a required skill; rare in resumes, treated as a differentiator not a requirement |

The old "skeptic" instinct (don't credit unbacked claims) is a shared
instruction across all three personas, not a fourth persona — kept
deliberately to avoid preempting the still-open agent-count question.

### 3a. Generated rubrics — settled and built (2026-08-25)

The table above is now the *default*, not the only option. `core/
rubric_gen.py` writes an equivalent rubric — three dimensions, each with
scoring criteria and its agent's brief — from any posting handed to it.
`prompts/rubric_generator.md` holds the meta-prompt.

Why this was worth building: the hardcoded rubric made the demo's central
claim ("scored against *this* posting, not a generic template") true for
exactly one posting. A reviewer pasting their own req would have gotten
scores computed against someone else's job.

Decisions inside it, each load-bearing:

- **Resolved once per batch, never per resume.** The panel's cached
  prefix is `rubric + job_description`. A rubric regenerated per resume
  would differ slightly every time and turn every cache read into a
  cache write. `rank_all` takes the rubric as a parameter for this
  reason; it does not generate one internally.
- **Exactly three dimensions, enforced in code.** `DISAGREEMENT_
  THRESHOLD` is a spread across a three-agent panel. A four-dimension
  rubric changes what that spread means without changing the number, so
  the count is validated rather than trusted to the model.
- **Failure raises, no silent fallback.** Falling back to
  `prompts/rubric.md` would score one job's candidates against another
  job's criteria — a wrong answer that looks like a right one.
- **The agent brief stays out of the shared prefix.** Each dimension's
  `lens` travels in the user turn, like the hand-written personas do.
  In the system block it would both break caching and tell all three
  agents how the other two were briefed.
- **Written by the most expensive model in the cascade** (`rubric` slot,
  Opus). It runs once per batch and sets the standard every later score
  is judged against — the cheapest place to buy quality.
- **`scripts/evaluate.py` keeps using the hand-written rubric.** The
  published metrics were measured against it; auto-generating there
  would make consecutive eval runs incomparable.

Human-in-the-loop: `preview_rubric` returns a `rubric_id`, and
`rank_pool` accepts one, so the rubric a person read is the rubric that
scores the pool. Generation is not deterministic — without the id,
re-generating at screening time would quietly score against a rubric
nobody approved.

### 3b. Panel response parsing — two real bugs, found by running it (2026-08-25)

Both were found only once the pipeline ran against the live API. Neither
was visible offline, and one of them was silently corrupting scores.

**Bug 1 — a missing score became a confident 0.0.** Asked to score its
one assigned dimension, the panel model sometimes answered for *all
three at once*, keyed by dimension name. That is valid JSON with no
top-level `score`, so `_parse_json` succeeded, `parse_failed` stayed
`False`, and `_coerce_float(None, 0.0)` produced a 0.0 that no agent had
assigned. Because the parse "succeeded", `review_reason` stayed `None` —
so a candidate could be rejected on a fabricated zero **and not be
flagged for human review**. Silent and wrong, the worst combination.

Two fixes: the generated rubric no longer says "score each of the three
dimensions" (that instruction fought the single-lens user turn and
caused the behaviour), and a missing or non-numeric score is now a parse
failure rather than a zero. A genuine 0.0 is still a genuine 0.0 — the
tests pin both halves.

**Bug 2 — usable scores were being thrown away.** Intermittently the
model ends its turn (`stop_reason="end_turn"`, ~324 of 4000 tokens used)
having closed its final string but never emitted the closing brace.
`_parse_json` located the JSON with `rfind("}")`, found nothing, and
discarded a complete score. **5 of 180 panel calls in the recorded eval
run were lost this way**, each becoming a spurious 0.0 that dragged its
candidate's average down.

`_parse_json` now falls back to closing an unfinished fragment: it
tracks string state and bracket depth, drops a partial `\uXXXX` escape
at the cut, and parses with `strict=False` so a raw newline in a long
rationale doesn't reject the whole response. Mismatched brackets are
still refused — the repair is for *unfinished* output, not wrong output.

Measured effect on a live 24-call sample: parse failures fell from 4 to
1. The remaining case is an unescaped `"` inside a rationale, which
cannot be repaired without guessing where the string ends — it is
correctly flagged for review instead.

**Worth doing next:** the durable fix for all of this is structured
output (tool-use / JSON schema) rather than parsing free text. That
would make every repair above unnecessary. Not done yet.

### 3c. Re-run after the fixes, and what it exposed (2026-08-25)

Re-ran the full corpus on the fixed code. The mechanical goal was met:
**parse failures fell from 5/180 to 1/180.**

Headline metrics moved *down*, and the honest reading is that this is
noise rather than a regression:

| | Before | After |
|---|---|---|
| Macro-F1 | 0.630 | **0.601** |
| Accuracy | 0.667 | 0.633 |
| Lost panel calls | 5/180 | **1/180** |
| Cost | $0.891 | $0.925 |

Tracing it candidate by candidate: **6 of 60 verdicts changed between
the two runs, and only 1 of those 6 was a candidate that had suffered a
parse failure.** That one moved `hold -> advance` against a ground-truth
label of `advance` — the fix working exactly as designed, recovering a
score that had been a spurious 0.0. The other 5 flips involved
candidates whose calls parsed cleanly both times. They moved because the
model is nondeterministic, not because anything changed in the code.

**The real finding is methodological.** A 10% verdict drift between
identical runs means a single run cannot support a macro-F1 quoted to
three decimals, and cannot distinguish a 0.03 change from noise. Every
comparison in §8 — the whole three-way bake-off, the +5-point bar for
keeping the cascade — is built on single runs, so none of it can
currently resolve differences smaller than its own variance.

Before the bake-off means anything, the eval needs to report variance:
run each arm 3-5 times and report a spread, not a point estimate. That
is now the blocking item for §8, ahead of building the other two arms.

`hold` recall is unchanged and remains the genuine weakness (0.20 in
both runs). The system reliably separates strong from weak, and
reliably fails to identify the middle.

### 3c-i. The errors are systematic, not random (2026-08-26)

Reading all 60 scores together turns the weakness above into something
specific and fixable.

**Every one of the 22 mismatches runs the same direction: the model
scored *below* the label.** Not once did it grade a candidate more
generously than ground truth. Random error does not do that.

Per-archetype accuracy says where:

| Archetype | Correct |
|---|---|
| `production_generalist`, `academic_researcher`, `keyword_stuffer`, `wrong_domain` | 100% |
| `adjacent_shipper` | 4/6 |
| `demo_specialist`, `quiet_builder` | 3/7 |
| `early_career` | 1/6 |
| `production_light_ai` | **0/7** |

Perfect on every unambiguous archetype, and worse the closer a candidate
sits to the middle. `production_light_ai` — strong production history,
shallow AI work — is rejected every single time despite being labelled
`hold`.

Those two facts point at one cause: the panel over-weights AI depth
relative to production evidence, and the hand-picked 7.0/5.0 cutoffs sit
too high. Both already have planned fixes that have never been run —
§8 item 5 (sweep the disagreement threshold) and item 6 (sweep the
cutoffs against the corpus rather than trusting 7/5). Item 6 in
particular is cheap: it re-scores nothing, it only re-thresholds scores
already in `data/eval_run.json`.

This is worth doing before the §8 bake-off. Comparing architectures
while the shared cutoffs are miscalibrated measures the cutoffs, not the
architectures.

### 3d. Grounded reasoning in the UI — built 2026-08-26

The page shows each agent's verdict as **two bullets maximum**, and every
quote inside them is traced to the resume section it came from. The
section chips are clickable and highlight the exact line.

The reason is narrow and worth stating: the first question anyone asks
about AI-written hiring feedback is whether it read *this* resume or
produced plausible boilerplate. Prose alone cannot answer that. A
citation that resolves to a real heading and jumps to the sentence can.

Decisions worth keeping:

- **A quote that cannot be found verbatim in the resume gets no
  citation.** Not a guessed section, not a "probably Experience" — the
  chip simply does not appear. An unlocatable quote means the model
  paraphrased, and labelling a paraphrase as a citation would defeat the
  entire purpose. `_locate` returning None is a feature.
- **Done at the display layer, not by changing the panel's response
  schema.** The recorded run and every future live run render identically
  with no re-scoring, and the eval numbers stay comparable. Had this gone
  into the prompt as a structured `points` field, every past run would
  have become undisplayable.
- **The bullet keeps the model's sentence verbatim.** Stripping quotes
  out to build a tidier claim turned a two-citation sentence into
  "… and … matching the posting". The prose is the model's; only the
  citations are ours.
- **All four quote styles are matched** — straight, curly, and single.
  Agents on the same candidate use different marks, and matching only
  double quotes silently dropped one agent's citations entirely. Single
  quotes risk catching an apostrophe pair, which is harmless precisely
  because of the first rule above.
- **Sentence splitting is quote-aware.** A regex on `[.!?]\s+` cuts
  `..., e.g. "Shipped a system. It handles 12K docs."` into fragments,
  one opening mid-quotation. Both the abbreviation guard and the
  in-quotation guard exist because that happened to real output.

Coverage on the recorded run: 100% of candidates carry at least one
grounded citation, ~5.8 highlighted lines each, 64% of bullets cite
something. The 36% that don't are mostly negative findings ("no evidence
mentions client engagement"), which have nothing to point at by nature.

### 3e. Cutoff sweep — run 2026-08-26, and it changes the picture

`scripts/sweep_cutoffs.py` re-thresholds the scores already in
`data/eval_run.json`. No API calls, instant, free. Full output in
`docs/CUTOFF_SWEEP.md`.

**The subtlety that makes this non-trivial.** `screen_one` does not
derive the recommendation from the cutoffs for every candidate. When the
panel disagrees, the arbiter returns its own recommendation and *that* is
what the pipeline uses — 33 of 60 candidates, and on 17 of them the
arbiter's verdict differs from what the cutoffs would say, always more
generously. So a sweep that just applies cutoffs to all 60 scores is
measuring a different pipeline. Both policies are reported separately.

| Policy | Current 7.0/5.0 | Best | Best cutoffs |
|---|---|---|---|
| respect-arbiter (what editing the constants does today) | 0.601 | **0.646** | 7.0 / 1.0 |
| uniform (arbiter returns only a score) | 0.342 | **0.862** | 4.0 / 1.0 |

The second row is the finding. Score distributions by true label:

| Label | min | median | max |
|---|---|---|---|
| advance | **4.0** | 6.5 | 8.0 |
| hold | 0.0 | 2.5 | **4.5** |
| reject | 0.0 | 0.3 | **1.0** |

Every `advance` scored at or above 4.0. Every `reject` scored at or below
1.0. **The panel's scores were always good — the 7.0/5.0 mapping was
discarding the signal.** That is structural separation, not a knife-edge
fit, which is why this is more believable than a typical same-data
optimisation.

Confusion at uniform 4.0/1.0: advance 20/20, hold 13/20, reject 19/20.

**What this implies, stated carefully.** Two changes are on the table and
they are not the same size:

1. Move `ADVANCE_CUTOFF`/`HOLD_CUTOFF` to 7.0/1.0. Small, safe, +0.045.
2. Stop having the arbiter return its own recommendation, and re-threshold
   at 4.0/1.0. Large, and a real design change — the arbiter would resolve
   the *score* and the cutoffs would own the verdict. Worth ~+0.26 over
   today if it holds up.

Neither has been applied. Both need a fresh eval run to confirm, because
the cutoffs were chosen on the same 60 resumes they are scored against
and §3c measured 10% verdict drift between identical runs. **Do not quote
0.862 as a result.** It is an upper bound that says "this is worth
testing", not a measurement.

Reading this next to §3c-i: the arbiter has been quietly compensating for
miscalibrated cutoffs. That explains why the errors all run one direction,
and why `production_light_ai` fails 0/7 — those candidates score in the
1.3–4.5 band that 5.0 wrongly calls reject.

### 3f. Resume upload — built 2026-08-26

`POST /api/screen-upload` takes a PDF, Word, Markdown or text file plus a
posting, screens that one resume, and drops it into the ranked list beside
the corpus. `core/ingest.py` already handled all four formats; this is the
web path to it. Verified end to end against a real PDF and a real .docx.

Deliberate choices:

- **Nothing is persisted.** The file goes to a temp directory, is read,
  and the directory is removed in a `finally`. It is somebody's actual
  resume; keeping a copy on a demo server is not ours to decide. A test
  asserts the temp directory is gone afterwards.
- **No ground truth is invented.** An uploaded resume has no label, so
  `expected` and `matches_ground_truth` are null rather than guessed.
  Scoring a real person against the synthetic answer key would report a
  fictional accuracy.
- **One rubric per posting, cached by fingerprint.** Five uploads against
  one posting must be judged by *identical* criteria. Regenerating per
  upload would score each candidate by a slightly different standard,
  which is precisely the unfairness this project exists to avoid.
- **The bundled posting keeps the hand-written rubric**, so an uploaded
  resume stays comparable to the recorded 60.
- **Refusals are specific**: unsupported type (415), empty (400), over
  2 MB (413), and — the useful one — a file that extracts to under 40
  words (422), which catches scanned or image-only PDFs. Scoring those
  would produce a confident zero about a resume nobody could read.

**Security note.** An uploaded resume is untrusted input and could contain
text aimed at the model. It cannot make anything happen: no tool here
takes an action, so the worst an injected instruction can do is argue for
its own score, and every verdict is advisory with a human in the loop.
Worth stating rather than assuming.

### 3g. Cost accounting, arbiter tier, escalation guard — 2026-08-26

**The cost figures were wrong.** `Usage.__add__` kept `self.model_id or
other.model_id`, and in `screen_one` usage starts from the Haiku
extraction call. So every Verdict was labelled Haiku, and
`estimate_cost` priced Sonnet panel calls and Opus arbiter calls at Haiku
rates. Opus output is 15x Haiku output; the reported ~$0.93 per run was
understating several-fold. `Usage.by_model` now splits tokens by the
model that spent them, and evaluate.py prices each separately.

This surfaced because real spend was visibly outrunning the documented
figure. Worth noting how it hid: the number looked plausible, was derived
from genuine API usage fields, and was wrong anyway.

**Arbiter moved Opus → Sonnet.** By the corrected accounting it was ~57%
of run cost while running on 55% of candidates. The job is adjudicating
between three rationales already written for it — reading and choosing,
not fresh analysis. Opus stays on the `rubric` slot, which runs once per
batch and sets the standard everything else is judged against.

**Escalation now requires decision uncertainty, not just variance.**
Escalating on spread alone pays to resolve disagreements that cannot
change the answer: 9.0/7.0/6.0 has spread 3.0 and clears the threshold,
but under sane cutoffs all three mean `advance`. `_verdict_is_in_doubt`
adds the second condition — the agents must disagree on which *bucket*
the candidate falls in. 7 of 33 escalations on the recorded run were
provably pointless by this test.

Honest limit, pinned by a test: at the current 7.0/5.0 cutoffs a 6.0 is
`hold`, so the two candidates that motivated this (9/7/6 and 8/9/6) still
escalate. The guard removes 7 of 33; the rest needs the cutoff correction
in §3e. The two changes are entangled and should land together.

### 3h. The root cause: `client_communication` is broken

| Agent | mean | median | zeros |
|---|---|---|---|
| production_reality | 3.23 | 1.0 | 14/60 |
| technical_integration | 2.98 | 2.0 | 22/60 |
| **client_communication** | **0.67** | **0.0** | **33/60** |

It never exceeds 6.0 for anyone, and it does not separate the levels it
exists to separate — candidates whose archetype targets `high` average
2.29, `medium` 0.55, `low` 0.39. The other two dimensions discriminate
cleanly (high 5.63/6.33 vs low 0.85/0.24).

The final score is a mean of three. An agent scoring near zero for almost
everyone drags **every** candidate down about two points. That single
fact explains the entire chain in §3c-i, §3e and §3f: why 7.0 was far too
high a cutoff, why the arbiter kept overriding it upward, why every error
ran one direction, and why `production_light_ai` failed 0/7.

The rubric tells this agent absence "is not automatically disqualifying",
but contributing 0.0 to a mean *is* a penalty — the instruction and the
arithmetic contradict each other. Options: let the dimension abstain and
average over the agents that scored, weight it below the other two, or
score presence rather than a 0-10 level.

**Not decided, and it should be settled before the cutoffs.** Fixing it
moves the score distribution the cutoffs would be fitted to, so tuning
cutoffs first means tuning them twice.

### 3i. Run 3 — the cutoffs were the bug, and it is measured (2026-08-26)

macro-F1 **0.601 → 0.847**, accuracy **0.633 → 0.850**, on the full 60.
The offline sweep predicted 0.846; the run measured 0.847.

Changes in this run, all landing together because they interact:

- **Cutoffs 7.0/5.0 → 4.0/1.0**, swept rather than guessed (§3e).
- **The arbiter returns a score only.** `recommendation_from_score` now
  owns every verdict. Previously an escalated 6.5 could be `advance`
  because the arbiter said so while an unescalated 6.5 was `hold` — the
  same score getting a different answer depending on whether the panel
  happened to split. One score, one mapping, one place.
- **Arbiter Opus → Sonnet** (§3g).
- **Escalation requires bucket disagreement**, not just spread (§3g).

| | Run 2 | Run 3 |
|---|---|---|
| macro-F1 | 0.601 | **0.847** |
| `hold` recall | **0.20** | **0.65** |
| errors | 22 | 9 |
| escalation | 55% | 47% |
| archetypes at 100% | 4/9 | 6/9 |

`hold` recall tripling is the real story. A miscalibrated mapping
destroys the middle class first, because it is the only one with a
boundary on both sides.

**Still open.** All 9 remaining errors run the same direction, and
`production_light_ai` (1/7) plus `adjacent_shipper` (4/6) account for 8
of them — the same profile both times: real production history, shallow
AI depth.

**Correction to §3h.** That section called `client_communication` the
root cause and implied re-weighting it was the fix. Half wrong. Tested
across five aggregation schemes with cutoffs re-fitted each time, the
spread was 0.843-0.861 — nothing, relative to run-to-run drift.
Re-weighting buys nothing once the cutoffs are right. The low scores
were never the problem in themselves; they only meant the cutoffs had to
sit lower than a human eyeballing a 0-10 scale would guess. The agent's
inability to separate `high` from `medium` is still a genuine defect,
but a prompt-level one worth far less than it appeared.

**A partial run was discarded.** An earlier attempt died 45/60 on an
exhausted credit balance and scored 0.850 — a number that looked fine
and was not comparable, because the failures clustered in two archetypes
and skewed the class balance. `evaluate.py` now refuses to report
quietly on a partial run and exits non-zero when nothing scored.

### 3j. Reviewer workflow, PDFs, and an access gate — 2026-08-26

**A parse failure was being scored as a zero.** `screen_one` averaged
every panel score including the placeholder 0.0 left by an unreadable
response. Caught on a real PDF upload: one agent failed, and the fake 0.0
dragged a 7.0/2.0 panel to a 4.5 composite, manufactured a 7.0 "spread",
and bought an arbiter call to resolve a disagreement with a value that
was never an opinion. Failed agents are now excluded from the mean and
the spread, still shown in the panel, and still flagged. If *every* agent
fails the score is 0.0 and flagged, rather than pretending to average
nothing.

To be clear about the original cause: the PDF was fine. Three repeat runs
of the same file parsed cleanly. This is the known intermittent Sonnet
JSON failure (~2.2% per call, so ~6.5% odds across three agents), and the
fix is about not letting one bad call fabricate a judgment.

**Output length.** The arbiter now gets two sentences, panel agents one,
and generated criteria are capped at 40 words with 25-word briefs. The
old generated rubric ran ~150 words per dimension, which is more than
anyone reads when there are three of them side by side. Verified live:
the same nursing-adjacent posting now produces 30-37 word criteria and
17-19 word briefs, and still catches the posting's exclusions.

**The UI leads with the average, not the spread.** Each verdict says how
it was reached — the mean of the agents that answered, and the cutoffs
that mapped it. Spread is no longer surfaced as a headline number: it
gates whether the arbiter runs and nothing a reader can act on, and
leading with it made a wide spread look like a problem in itself. Review
reasons name the actual scores ("the panel disagreed (9.0, 9.0, 2.0)")
rather than an abstract spread figure.

**Resume PDFs.** `scripts/build_resume_pdfs.py` renders all 60 with
reportlab. **No model is involved** — it is a deterministic
Markdown-to-PDF pass, so it costs nothing and reruns identically.
reportlab is an optional `[pdf]` extra since only this script needs it.

**Review queue.** Flagged candidates get their own tab: the panel notes,
the resume as text and as PDF, and approve/reject with a note. Decisions
are stored in `data/reviewer_decisions.json`, gitignored, and attached at
read time rather than written over the model's output — the disagreement
between human and model is the most useful data this produces, and
overwriting the score would erase it.

**Access gate.** A shared password (`APP_PASSWORD`, default `marco1`),
implemented as middleware rather than per-route dependencies so a new
endpoint is closed by default. Not authentication: there are no accounts,
and it exists so a hosted link is not an open invoice, since every live
screening call spends real money (PLAN 11, option 2). Compared with
`hmac.compare_digest`, and a test asserts each new endpoint 401s
anonymously.

## 4. Human-in-the-loop and security — settled as design, partially built

- No MCP tool can take a real-world action — all four only ever return
  information. That boundary defends against prompt injection *and*
  keeps a human in the loop on hiring decisions; same design choice,
  two motivations.
- `Verdict.escalated` is surfaced as `needs_human_review` +
  `review_reason` in every tool's output, and `rank_pool` reports a
  `needs_human_review_count`. **Built.**
- Known blind spot, not yet mitigated in code: disagreement-based
  escalation can't catch a panel that's unanimously and confidently
  wrong for a shared/correlated reason. The fix is a governance practice
  (audit a sample of confident unanimous rejects too) rather than a code
  change. Written up, with the rest of the failure modes, in
  `docs/LIMITATIONS.md`.

## 5. Cost/latency measurement — methodology settled, nothing implemented

- Real pricing (verified, not assumed): cache reads are a 90% discount,
  writes cost 1.25x (5-min TTL) or 2x (1-hour TTL) base price —
  caching has a real breakeven, isn't automatically a win.
- Methodology: run the same batch cached and uncached, sum the actual
  `usage.cache_read_input_tokens`/`cache_creation_input_tokens` the API
  returns, report the measured delta. Latency as p50/p95, not mean,
  compared against a flat "everything hits all three tiers" run.
- **Partly implemented.** `Usage` accumulates through the cascade and
  `scripts/evaluate.py` reports real totals. The latest recorded run
  (run 3, `data/eval_run.json`) measured p50 19.4s, p95 32.9s, and 421K
  cache-read tokens against 197K input and 104K output. It *reported*
  $1.796, but two of the three rates in the pricing table were wrong --
  at correct rates the same tokens come to roughly **$1.20** (~2c per
  resume). See `docs/COST_ANALYSIS.md`; the exact figure needs a re-run.
- Cost is now attributed **per model** (`Usage.by_model`), which was the
  fix for a real accounting bug: `Usage.__add__` kept the first
  `model_id` it saw, and extraction leads the cascade, so an entire run
  was being priced at Haiku rates. Documented spend was roughly half of
  actual spend until this was corrected — the reason the earlier
  $0.89 figure looked so good.
- Run 3 costs about twice run 1 despite dropping the arbiter from Opus
  to Sonnet. That is not a regression: run 1 was mispriced by the bug
  above. Comparing the two headline costs directly is meaningless.
- What is still missing is the *comparison*: no uncached run has been
  done, so the caching saving is recorded but not yet quantified
  against its own baseline.

## 6. Local and embedding models — settled

- Full generative models (Ollama): implemented behind the same
  `Model` interface as Anthropic (`core/router.py`), explicitly kept
  off the demo path — your GTX 970 (Maxwell, 4GB) genuinely can't do
  this workload justice. Documented as the on-prem/PII-residency story
  instead.
- Embeddings are a different, much lighter workload and a genuinely
  good local fit even on this hardware: `sentence-transformers` with
  `all-MiniLM-L6-v2`, matching the already-validated choice from your
  StoneStepper project rather than the `nomic-embed-text` I first
  suggested. No persistent vector store needed at this scale — computed
  fresh per `rank_pool` call, discarded after. **Not built yet.**

## 7. What's actually built vs. designed-only (read this before assuming progress)

Rewritten 2026-08-25. The previous version of this section was badly
stale — it still claimed `tests/` was empty and no API call had ever
run, both untrue for a while by then.

**Exists as real code, and has been run:**
- `core/models.py`, `core/router.py` (Anthropic + Ollama), `core/
  ingest.py`, `core/pipeline.py` (Tier 0/1/2), `core/query.py`,
  `core/enrichment.py` (documented stub), `core/rubric_gen.py` (§3a).
- `adapters/mcp_server.py` — all 5 tools.
- `adapters/api.py` + `adapters/static/index.html` — the full flow, not
  just a rubric preview: submit a posting, get generated criteria, screen
  a sample or read the recorded run, open a candidate, follow every
  citation back to the resume line it came from. Three tabs (Screen /
  Review queue / Results), a reviewer approve-reject workflow whose
  decisions are stored separately from model output so human-vs-model
  disagreement survives, PDF/Word/Markdown/text upload that persists
  nothing, and a default-closed password gate implemented as middleware.
- `prompts/rubric.md`, `prompts/rubric_generator.md`.
- `adapters/cli.py` — `rubric`, `screen`, `rank`. The `resume-screener`
  console script in pyproject.toml now resolves; it previously pointed at
  a module that did not exist, so the documented command raised
  ImportError on a fresh install.
- `scripts/sweep_cutoffs.py`, `scripts/sweep_escalation.py` — offline
  re-thresholding of recorded scores, zero API cost.
  `scripts/build_resume_pdfs.py` renders the corpus to PDF
  deterministically via reportlab, with no model calls.
- **249 offline tests**, none of which touch the network.
- The 60-resume synthetic corpus, its labels, and three recorded eval
  runs. The current one: macro-F1 **0.847**, accuracy 0.850, roughly
  $1.20 for 60 resumes. Written up in `docs/EVAL_RESULTS.md` and
  `docs/CANDIDATE_REPORTS.md`, with the full history in
  `docs/RESULTS_HISTORY.md`. Read §3c before quoting any of these to
  three decimals — run-to-run drift is larger than it looks.
- The live path has actually been exercised end to end: rubrics
  generated from both the target posting and an unrelated non-technical
  one (a charge-nurse req, which produced nursing dimensions with no
  leakage from the AI rubric), plus 8 resumes screened against a
  generated rubric, 6 of 8 matching ground truth. Both misses were
  hold→reject, consistent with `hold` recall being the known weak class
  (0.2 in the recorded run) rather than a regression.

**Still does not exist:**
- `docs/ARCHITECTURE.md` — referenced by the README, still missing.
  Lower priority than it looks: the README's "How it works" section and
  `STRUCTURE.md` between them already cover most of what it would say.
- The embedding pre-filter, and the pydantic validation of `_parse_json`.
- The 3-way architecture bake-off from §8 — only the panel+arbiter arm
  has been measured. Single-pass and flat-ensemble are unrun, so the
  "does the cascade earn its complexity" question is still open.
- A variance estimate. Every number in this document comes from a single
  run of each configuration, and §3c measured 10% verdict drift between
  two identical runs.
- Walkthrough mode (§11), any demo recording, any deployment.

## 8. Testing and evaluation — ironed out 2026-08-25

Some of this borrows structure from a prior project's ablation study
(`research/stonestepper_ablation_review.md` has the full detail) but
this is now our own list, scoped to what's actually worth testing here
— not a re-run of that methodology for its own sake.

### Corpus size — settled

**60 synthetic resumes**, balanced ~20 each across advance/hold/reject,
with 2-3 distinct archetype flavors inside each class (e.g. "reject"
covers keyword-stuffed, wrong-domain, and genuinely underqualified
separately, not one generic "bad resume" template) so the rubric gets
stress-tested on *why* something fails, not just that it does. No
mandatory train/test split — nothing here trains a model. The one
exception is noted below under the k-NN candidate.

### The list

1. **Self-consistency check — cut.**

2. **Keyword-only floor baseline — cut**, per instruction. Single-pass
   (item 4 below) replaces it as the floor — a better one, since a
   pure keyword match was never going to be a fair comparison for a
   judgment this nuanced (production-vs-prototype isn't a keyword you
   can grep for).

### 8a. Model-tier bake-off — first data point (2026-08-26)

The panel/arbiter model choice is itself an axis worth sweeping, not
just the architecture shape. First data point, via
`scripts/evaluate.py --panel-model ... --triage-model ... --tag <name>`
(writes to tag-suffixed files, never the baseline):

**All-Haiku panel, Sonnet arbiter:** macro-F1 0.847 → 0.516, cost $1.796
→ $1.286. Rejected. The cause is decisive rather than marginal: 88 of 180
Haiku panel calls (49%) returned unparseable JSON, against 2.2% for
Sonnet on the identical prompt. Full analysis in
`docs/EVAL_RESULTS__all-haiku-panel-sonnet-arbiter_ANALYSIS.md`.

Worth noting for later: this reads as a structured-output problem, not a
capability problem. A "respond as JSON" instruction in prose is exactly
the failure mode `_close_unterminated` (§3b) already exists to patch
around, and Haiku just hits it far more often. If a cheaper panel is
revisited, enforcing the schema via tool-use rather than prose is the
prerequisite, not a bigger model.

3. **Prompt variant (direct vs. chain-of-thought vs. structured rules)
   — cut**, and I agree with cutting it. Our rubric prompts are already
   closer to StoneStepper's "structured criteria" variant than its bare
   baseline — each persona already gets explicit, named criteria, not
   a loose "classify this." The axis that mattered for their simpler
   3-class email problem has less headroom left for us to gain from.
   Worth stating plainly as a deliberate scope cut in the eventual
   limitations doc, not silently dropped — a reviewer could reasonably
   ask "did you test your prompt phrasing," and the honest answer is no.

4. **The architecture candidates — restructured, not just trimmed.**
   Talking through each on its own merits:

   - **Single-pass (one call, all three dimensions)** — keep, as the
     floor. Cheapest possible, and the number the more complex design
     has to actually beat to justify existing.
   - **Flat ensemble (always run all three personas, never escalate)**
     — keep. This is the one that actually tests our core cost claim:
     does disagreement-gating save money without losing accuracy, or
     were we just adding complexity for a savings that isn't real here?
   - **Our panel + arbiter-on-disagreement** — keep, it's the leading
     design and already built.
   - **Embedding pre-filter** — reclassifying this. It isn't really a
     competing *architecture* — it's orthogonal to all three of the
     above and can sit underneath whichever one wins. Build it once as
     an always-on cheap layer, not as a fourth arm of the bake-off.
   - **Whole-batch long-context ranking — cutting entirely**, not just
     deprioritizing. It structurally conflicts with the per-candidate
     design already built (the session store, `explain_verdict`, the
     human-review flag all assume one `Verdict` per candidate) — giving
     it a fair test would mean building a second, parallel pipeline
     just for the experiment, which isn't worth it for a design we're
     unlikely to adopt anyway.
   - **Embedding k-NN as a standalone scorer — conditional, likely
     cut.** Its whole value depends on having enough labeled examples
     per class for nearest-neighbor voting to mean anything. At 20
     resumes per class, that's thin for a fair train/exemplar-library
     split — I'd lean toward dropping this one too unless the corpus
     size above gets bumped up specifically to support it.

   Net result: **a real 3-way bake-off** (single-pass, flat ensemble,
   panel+arbiter), one always-on layer (embedding pre-filter) that
   applies to all three, and one conditional/likely-cut candidate
   (k-NN) rather than the original six competing designs.

5. **Escalation trigger — kept, confirmed as pure calibration, not a
   design debate.** Right, this needs the numbers played with, not
   decided in the abstract: sweep a handful of disagreement-threshold
   values against the labeled corpus (e.g. 1.0/1.5/2.0/2.5/3.0) and
   look at the tradeoff curve between macro-F1 and how often it
   escalates to a human. Start with the simple score-range version;
   only reach for the fancier three-signal design if the simple one
   demonstrably fails on real cases the corpus surfaces.

6. **Score-to-recommendation cutoffs (currently hardcoded 7/5) — kept,
   same treatment as #5.** Sweep candidate cutoff sets against the
   labeled corpus, pick whichever maximizes macro-F1, rather than
   trusting the hand-picked 7/5 split.

7. **Cost estimate for the whole run plan — kept.** Doing this once
   the scope above is actually locked, not before — pricing out a list
   that's still shifting isn't useful. Coming once corpus generation
   and the 3-way bake-off scope above are final.

### How this gets evaluated

- **Primary metric**: macro-F1 across advance/hold/reject against the
  corpus's ground-truth labels, computed on the auto-scored subset —
  reported *separately* from coverage/escalation-rate, never blended
  into one number.
- **Secondary**: real measured cost per resume (from actual API
  `usage` fields, not estimates) and p50/p95 latency, for the 3-way
  architecture bake-off specifically.
- **Bar for keeping the more complex design over the single-pass
  floor**: the winner needs to beat single-pass's macro-F1 by a real
  margin (proposing +5 macro-F1 points as the bar, open to adjusting)
  — or match it at a materially lower cost. If neither happens, the
  honest conclusion is that the cascade's complexity isn't earning its
  keep, and that's a legitimate result to report, not a failure to hide.

All of this is blocked on the synthetic corpus existing — nothing above
can be measured until those 60 resumes and their labels exist.

## 9. Not started at all

- `ARCHITECTURE.md`. `LIMITATIONS.md` was the urgent one and now exists
  at `docs/LIMITATIONS.md`.
- A variance estimate: 3-5 runs per configuration, reported as a spread.
  This blocks the bake-off below from meaning anything.
- The single-pass and flat-ensemble arms of the §8 bake-off.
- An uncached eval run to quantify the caching saving (§5).
- **Walkthrough mode** (§11) — planned below, not built.
- **Hosting.** Nothing is deployed. Option 2 (shared password + hard
  daily spend cap) is chosen; the password gate is built, the spend cap
  and the deployment are not. See §11.
- Demo recordings.

## 10. Where this actually stands — 2026-08-26

**Working and verified end to end:** the cascade, generated rubrics, the
MCP server (5 tools), the CLI (3 commands), the web app (submit a posting
→ criteria → screened results → grounded reasoning → reviewer decision),
resume upload for PDF/Word/Markdown/text, a password gate, and a
60-resume labelled eval. 249 offline tests.

**The honest headline:** macro-F1 **0.847**, accuracy 0.850, ~2 cents per
resume. `hold` recall is 0.65 against 0.90 for `advance` and 1.00 for
`reject` — the middle class is still the weak one, but it is no longer
broken. It was 0.20 before the cutoffs were swept.

**The caveat that outranks the headline:** every number here is one run,
and §3c measured 10% verdict drift between two identical runs. Several
comparisons in this document are smaller than that.

**The best-supported next move, in order:**

1. **Give the eval a variance estimate.** 3-5 runs of the current
   configuration, reported as a spread rather than a point. Roughly $2,
   and until it exists nothing below can be concluded — including
   whether the model-tier bake-off in §8a found anything real.
2. **The single-pass arm of the §8 bake-off.** The cascade's whole
   justification is that it beats one big call. That is currently
   asserted, not measured. Needs item 1 first, or the comparison is
   noise against noise.
3. **Grow the corpus, or accept the cutoffs as fitted.** 4.0/1.0 was
   swept on the same 60 resumes it is scored against, and the plateau on
   the `advance` side is narrow. This is the single largest threat to
   the headline number being real.

Items 1 and 2 are entangled and cost roughly $4 of eval runs together.
Item 3 is the honest one and is more work than either.

## 11. Walkthrough mode and hosting — planned, not built

### What it is for

The repo currently assumes a reader who will clone it. A hosted link
assumes the opposite: someone clicks, has ninety seconds, and will not
read a README first. Walkthrough mode is a guided path through the app
for that person.

### Proposed shape

A dismissible overlay driven by a small step list, each step pointing at
an element already on the page and explaining what it is. No new
screens — it narrates the real UI rather than duplicating it, so it
cannot drift out of sync with the product.

| Step | Anchors on | The point being made |
|---|---|---|
| 1 | The posting box | Any posting works. Nothing is hardcoded to one role. |
| 2 | The three criteria cards | The agent wrote these from *your* posting. Show the nursing example as proof. |
| 3 | The stats row | 60 resumes, ranked, 33 flagged for a human. |
| 4 | A candidate row | Click through to one verdict. |
| 5 | The panel bullets | Two bullets per agent, every quote traced to a resume section. Click a chip and watch it highlight. |
| 6 | The review flag | Disagreement escalates to a human. Nothing here is auto-rejected. |
| 7 | The upload button | Try your own resume. Nothing is stored. |
| 8 | The honest slide | macro-F1 0.601, `hold` recall 0.20, and what is being done about it. |

Step 8 is not decoration. A walkthrough that ends on a win reads like a
pitch; one that ends on a known weakness reads like engineering, and that
is the actual differentiator for this audience.

### Open questions before building

- **Auto-play or click-through?** Auto-play demos well unattended;
  click-through respects someone who wants to poke at it. Probably
  click-through with an obvious "next".
- **Does it replay a recorded run or make live calls?** Recorded, almost
  certainly — a walkthrough that costs money per visitor is a walkthrough
  that gets turned off.
- **Where does it live?** A `?tour=1` query param keeps it out of the way
  for anyone who does not want it, and gives a link that starts the tour.

### Hosting — the real blocker is the key, not the host

Deploying this is easy. Deploying it *safely* is the question, and it has
nothing to do with which platform:

- **The API key would sit on a public server**, and every "Screen
  resumes" or "Upload" click spends real money. An unauthenticated public
  page with a live key on it is an open invoice.
- **Uploads become a data question.** Nothing is persisted today (§3f),
  which is the right default and should stay true in any hosted build.

Options, cheapest to most work:

1. **Recorded-only build.** Ship the app with live calls disabled: the
   recorded run, the criteria, the reasoning, the walkthrough, all
   working. No key on the server, no spend, nothing to abuse. Loses live
   posting submission and upload.
2. **Keep live calls, add a gate.** A shared password or a link token,
   plus a hard per-day spend cap. Preserves the whole demo for a handful
   of known viewers.
3. **Live and open with rate limits.** Most work, most risk. Not worth it
   for an audience of three interviewers.

**Recommendation: option 2**, with option 1 as the fallback if a spend
cap turns out to be awkward. The two features worth protecting are
exactly the two that cost money, and the audience is small enough that a
gate costs them nothing.

**Decided: option 2.** The password gate is built — `APP_PASSWORD`,
a session cookie, and a default-closed middleware that gates every route
except the login page and the health check (see §3j). What is still
missing is the other half of option 2, the hard per-day spend cap, and
the deployment itself. Until the cap exists, a hosted build with a live
key is still an open invoice to anyone who gets the password.
