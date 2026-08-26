# Resume Screener — Project Plan

Living status doc. Three honest buckets: **settled** (decided, with the
actual reasoning), **built** (code that exists — separate from whether
it's been run), and **open** (still needs a real decision or a missing
piece before we can move on).

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
  wrong for a shared/correlated reason. Documented fix is a governance
  practice (audit a sample of confident unanimous rejects too) —
  belongs in `LIMITATIONS.md`, which **does not exist yet.**

## 5. Cost/latency measurement — methodology settled, nothing implemented

- Real pricing (verified, not assumed): cache reads are a 90% discount,
  writes cost 1.25x (5-min TTL) or 2x (1-hour TTL) base price —
  caching has a real breakeven, isn't automatically a win.
- Methodology: run the same batch cached and uncached, sum the actual
  `usage.cache_read_input_tokens`/`cache_creation_input_tokens` the API
  returns, report the measured delta. Latency as p50/p95, not mean,
  compared against a flat "everything hits all three tiers" run.
- **Partly implemented.** `Usage` accumulates through the cascade and
  `scripts/evaluate.py` reports real totals — the last run measured
  $0.890981 for 60 resumes (p50 31.3s, p95 44.0s, 425K cache-read
  tokens). What is still missing is the *comparison*: no uncached run
  has been done, so the caching saving is recorded but not yet
  quantified against its own baseline.

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
- `adapters/api.py` + `adapters/static/index.html` — the rubric-preview
  page. Deliberately scoped to previewing a rubric; it does not screen.
- `prompts/rubric.md`, `prompts/rubric_generator.md`.
- `adapters/cli.py` — `rubric`, `screen`, `rank`. The `resume-screener`
  console script in pyproject.toml now resolves; it previously pointed at
  a module that did not exist, so the documented command raised
  ImportError on a fresh install.
- **143 offline tests**, none of which touch the network.
- The 60-resume synthetic corpus, its labels, and a real eval run:
  macro-F1 0.601, accuracy 0.633, $0.93 for 60 resumes. Written up in
  `docs/EVAL_RESULTS.md` and `docs/CANDIDATE_REPORTS.md`. Read §3c before
  quoting that number — run-to-run drift is larger than it looks.
- The live path has actually been exercised end to end: rubrics
  generated from both the target posting and an unrelated non-technical
  one (a charge-nurse req, which produced nursing dimensions with no
  leakage from the AI rubric), plus 8 resumes screened against a
  generated rubric, 6 of 8 matching ground truth. Both misses were
  hold→reject, consistent with `hold` recall being the known weak class
  (0.2 in the recorded run) rather than a regression.

**Still does not exist:**
- `adapters/cli.py` — zero code. The `resume-screener` console script in
  pyproject.toml points at it and would fail today.
- `docs/ARCHITECTURE.md`, `docs/LIMITATIONS.md` — referenced by the
  README, still missing. LIMITATIONS is the more urgent of the two: §4's
  known blind spot is documented nowhere a reader would find it.
- The embedding pre-filter, and the pydantic validation of `_parse_json`.
- The 3-way architecture bake-off from §8 — only the panel+arbiter arm
  has been measured. Single-pass and flat-ensemble are unrun, so the
  "does the cascade earn its complexity" question is still open.
- Any demo recording, any deployment.

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

- The CLI adapter (`adapters/cli.py`), still referenced by the
  `resume-screener` console script in pyproject.toml.
- `ARCHITECTURE.md`, `LIMITATIONS.md`.
- The single-pass and flat-ensemble arms of the §8 bake-off.
- An uncached eval run to quantify the caching saving (§5).
- Demo recordings (MCP-in-Claude-Desktop clip, web UI walkthrough).
- Deployment of the web UI anywhere reachable.
- Exact timeline — mentioned once as "right now," then explicitly
  paused for deeper planning; never re-confirmed.

## 10. Immediate next decision needed

The corpus, the eval, and generated rubrics (§3a) are all done. In order:

1. **Give the eval a variance estimate.** §3c found 10% verdict drift
   between two identical runs. Until each configuration is run several
   times and reported as a spread, the §8 bake-off cannot resolve the
   differences it exists to measure, and no macro-F1 here should be read
   to three decimals. This now blocks item 4.
2. **`LIMITATIONS.md`.** §4 names a real blind spot — disagreement-based
   escalation cannot catch a panel that is unanimously and confidently
   wrong — and it is currently written down only here, in a planning
   doc. For a tool that advises on hiring, that belongs somewhere a
   reader will actually find it. §3b's residual failure mode (an
   unescaped quote still costs a score, ~4% of calls) belongs there too.
3. **Structured output for the panel.** §3b's repairs are patches over
   free-text JSON. Tool-use or a JSON schema would remove the failure
   class rather than mitigate it.
4. **The rest of the §8 bake-off.** Only panel+arbiter has been
   measured, so the claim that the cascade beats a single call is
   currently asserted rather than shown — the honest possibility is that
   a single-pass baseline matches it for less money.
