# Results history

Every measured run, what changed before it, and why the number moved.
Hand-maintained: add a row whenever an eval run happens.

`docs/EVAL_RESULTS.md` always describes the *latest* run only. This file
is the record of how it got there.

> **Every cost in this file is overstated.** The pricing table in
> `scripts/evaluate.py` carried Sonnet 4.6 rates for Sonnet 5 and Opus
> 4.1 rates for Opus 5 until 2026-08-27. The dollar figures below are
> left as they were reported, because this file is a record of what each
> run said at the time. Run 3's $1.796 is really about **$1.20**. Token
> counts, macro-F1, and every other number here are unaffected. See
> `docs/COST_ANALYSIS.md`.

## Runs

| # | Date | macro-F1 | Accuracy | Reported cost | What changed before this run |
|---|---|---|---|---|---|
| 1 | 2026-08-25 | 0.630 | 0.667 | $0.891 | First full run of the 60-resume corpus. Hand-written rubric, 7.0/5.0 cutoffs, spread > 2.0 escalation, Opus arbiter. |
| 2 | 2026-08-26 | **0.601** | 0.633 | $0.925 | Two parsing fixes (PLAN §3b): a missing score no longer becomes a silent, unflagged 0.0; and an unterminated JSON response is now repaired instead of discarded. |
| — | 2026-08-26 | *(void)* | — | — | Died 45/60 on an exhausted credit balance. Discarded, not recorded: the failures clustered in two archetypes, so the surviving class balance was skewed and its metrics were not comparable. `evaluate.py` now refuses to report quietly on a partial run. |
| 3 | 2026-08-26 | **0.847** | **0.850** | $1.796 | Cutoffs 7.0/5.0 → **4.0/1.0** (swept). Arbiter returns a **score only**; `recommendation_from_score` owns every verdict. Arbiter model Opus → Sonnet. Escalation now also requires the agents to disagree on the verdict bucket. Cost priced per model for the first time. |

### Why run 2 went *down*

It did not, in any way that can be shown. Traced candidate by candidate:

- **6 of 60 verdicts changed** between the two runs.
- **Only 1 of those 6** was a candidate that had suffered a parse failure.
  That one moved `hold → advance` against a label of `advance` — the fix
  working exactly as intended.
- The other 5 parsed cleanly in both runs. They moved because the model is
  nondeterministic.

The parsing fix did what it was for: lost panel calls fell from **5/180 to
1/180**. The headline moved by noise, in the unlucky direction.

That is the more important result. **10% of verdicts drift between two
identical runs**, which is larger than most of the differences anyone
would want to compare. Until each configuration is run 3-5 times and
reported as a spread, no single run supports a macro-F1 quoted to three
decimals.

## Run 3 — what actually moved

The prediction from the offline sweep was macro-F1 ≈ 0.846-0.862. Measured:
**0.847**. That is close enough to count as the sweep being validated,
with the caveat that the cutoffs were fitted on this same corpus.

| | Run 2 | Run 3 |
|---|---|---|
| macro-F1 | 0.601 | **0.847** |
| accuracy | 0.633 | **0.850** |
| `advance` recall | 0.70 | 0.90 |
| **`hold` recall** | **0.20** | **0.65** |
| `reject` recall | 1.00 | 1.00 |
| errors | 22 | **9** |
| escalation rate | 55% | 47% |
| parse failures | 1/180 | 4/180 |
| archetypes at 100% | 4 of 9 | **6 of 9** |

`hold` recall was the whole problem and it more than tripled. That is
what the headline change actually is: the cutoffs were never the
weakness of a class, they were the weakness of the *mapping*, and `hold`
is the class a bad mapping destroys first because it is the one with a
boundary on both sides.

**What did not change:** all 9 remaining errors still run in the same
direction — the model scoring below the label, never above. The bias is
much smaller but it has not reversed or become symmetric.

`production_light_ai` improved from 0/7 to 1/7. It is now the only
archetype still failing badly, and with `adjacent_shipper` at 4/6 it
accounts for 8 of the 9 remaining errors. Strong production history with
shallow AI depth is the profile this rubric still cannot place.

**Cost.** $1.796 for 60 resumes as reported, about 3 cents each, and this
is the first figure priced per model rather than billing everything at
Haiku rates. (Corrected for the bad rate table, it is roughly $1.20, or
2 cents each — see the note at the top of this file.) It is not comparable to the "$0.93" in runs 1 and 2, which were
wrong rather than cheaper. Against a corrected estimate of run 2 at
roughly $4, moving the arbiter to Sonnet did close to halve real spend.

## Comparison runs — not the baseline

These use `--tag` other than `baseline`, so they write to
`eval_run__<tag>.json` / `EVAL_RESULTS__<tag>.md` and never touch the
files everything else in the repo reads.

### All-Haiku panel, Sonnet arbiter — 2026-08-26

Requested experiment: `triage` and `panel` both on Haiku, arbiter kept on
Sonnet. Full writeup in
[EVAL_RESULTS__all-haiku-panel-sonnet-arbiter_ANALYSIS.md](EVAL_RESULTS__all-haiku-panel-sonnet-arbiter_ANALYSIS.md).

| | Baseline | All-Haiku panel |
|---|---|---|
| macro-F1 | 0.847 | 0.516 |
| accuracy | 0.850 | 0.533 |
| cost | $1.796 | $1.286 |

28% cheaper, and not close to worth it. **88 of 180 Haiku panel calls
(49%) returned unparseable text**, against 2.2% for Sonnet on the
identical prompt — an instruction-following gap, not a reasoning gap.
Every failure defaults to a flagged 0.0, so roughly half the panel's
inputs to the final average were noise rather than judgments.

The review-flag safety net (§4) caught 59 of 60 candidates as a result,
which is the honest finding: nothing reached an unreviewed decision, but
"59 of 60 need a human" is not automation with a discount, it's manual
review with extra steps. **Not adopted.**

### Recalibrated scale — 2026-08-26, not adopted

Tested whether the 0-10 scale could be made to mean what a reader
expects, with 7+ as the advance line. Full reasoning in
[SCORE_SCALE.md](SCORE_SCALE.md).

Added explicit score anchors to the rubric and told
`client_communication` that silence is a 3-4 rather than a 0.

It worked on its own terms: that agent went from mean 0.60 / max 4.0 /
35 zeros to mean 3.34 / max 7.0 / **zero** zeros, and `advance`
composites rose 5.51 → 6.37.

| Scoring | Best cutoffs | macro-F1 |
|---|---|---|
| Original | 3.7 / 0.9 | **0.880** |
| Recalibrated | 6.1 / 3.1 | 0.796 |
| Recalibrated, drop `client_comm` | 5.6 / 3.1 | 0.756 |

Each at its own best cutoffs, so this is not a cutoff artifact.
**Reverted.** And 7+ as the advance line is not reachable regardless:
even after recalibration the best line the sweep finds is 5.6-6.2.

The caveat worth keeping: the archetypes were generated with an intended
`client_communication` level, so an agent that punishes silence harshly
correlates with the answer key. The fairer agent is probably better on
real applicants and measurably worse on this corpus, and the corpus is
the only evidence there is.

## Offline sweeps — analysis, not runs

Neither of these called an API. Both re-derive decisions from scores
already in `data/eval_run.json`, so they are cheap and repeatable, and
neither is a measured result.

### Cutoffs (`docs/CUTOFF_SWEEP.md`)

| Policy | At 7.0/5.0 | Best | At |
|---|---|---|---|
| respect-arbiter | 0.601 | 0.646 | 7.0 / 1.0 |
| uniform | 0.342 | **0.862** | 4.0 / 1.0 |

Score distribution by true label explains it: every `advance` scored
≥ 4.0, every `reject` scored ≤ 1.0. The panel ranks correctly and the
7.0/5.0 mapping was discarding that.

**Not applied.** The cutoffs were fitted on the same 60 resumes they were
scored against, and run-to-run drift is 10%. 0.862 is an upper bound that
justifies a re-run, not a result.

### Escalation (`docs/ESCALATION_SWEEP.md`)

At corrected cutoffs 4.0/1.0, *not escalating at all* scored 0.784 — as
high as any escalation policy tested. At the current 7.0/5.0 cutoffs, not
escalating scores 0.254.

Read together: **the arbiter has been compensating for miscalibrated
cutoffs**, not adding independent judgment. That is consistent with it
overriding the cutoffs more generously on 17 of 33 escalations, and with
every one of the 22 errors running in the same direction.

Caveat: escalated candidates reuse the recorded arbiter verdict, which was
produced under the old cutoffs. The comparison is directionally clear and
not clean enough to act on alone.

## `client_communication` — a correction

An earlier version of this file called this agent "the root cause" and
implied re-weighting it was the fix. **Half of that was wrong**, and the
correction is worth keeping.

What is still true — it scores far lower than the other two and barely
discriminates:

| Archetype target | production_reality | technical_integration | client_communication |
|---|---|---|---|
| high | 5.63 | 6.33 | **2.29** |
| medium | 1.92 | 2.28 | **0.55** |
| low | 0.85 | 0.24 | **0.39** |

It never exceeded 6.0 for anyone and cannot tell `medium` from `low`.
Because the final score is a mean of three, that pulled every candidate
down roughly two points.

**What was wrong:** the conclusion that re-weighting it would fix the
accuracy. Tested offline across five aggregation schemes, each with
cutoffs re-fitted:

| Aggregation | Best macro-F1 |
|---|---|
| equal (1,1,1), i.e. today | 0.846 |
| weighted (2,2,1) | 0.846 |
| weighted (3,3,1) | 0.861 |
| drop it entirely | 0.843 |
| treat it as a bonus | 0.861 |

A 0.018 spread across every option, well inside the 10% run-to-run drift.
**Re-weighting buys nothing once the cutoffs are right.** The depressed
scores were never the problem in themselves; they only meant the cutoffs
had to sit lower than someone eyeballing a 0-10 scale would guess.

So the fix was the mapping, not the aggregation — and run 3 confirmed it
at 0.847 with the aggregation left alone.

The agent's poor discrimination is still a real defect worth fixing on
its own merits: a dimension that cannot separate `high` from `medium`
is not measuring anything. But that is a prompt problem, and it is worth
much less than it looked.

## Variance runs — 2026-08-27

**What changed before these runs: nothing.** That is the point. `var1`
through `var4` re-ran one configuration four times with no edit of any
kind between them.

**`baseline` is deliberately excluded.** Three commits touched
`core/pipeline.py` after `data/eval_run.json` was recorded — `7380abc`,
`198a49a` (which fixed a real scoring bug), and `c39bb03`. Comparing
`baseline` against a run made today would repeat the flaw in the original
§3c drift figure, where a parse fix sat between the two runs being called
identical.

Metrics are recomputed over the **51 candidates all four runs scored**,
not read from stored per-run totals, so a run that dropped a few resumes
still contributes.

| Run | n | Macro-F1 (shared 51) | Accuracy | Escalated | Cost |
|---|---|---|---|---|---|
| `var1` | 60 | 0.788 | 0.804 | 53% | $0.956 |
| `var2` | 52 | 0.833 | 0.843 | 53% | $0.838 |
| `var3` | 60 | 0.838 | 0.843 | 51% | $0.946 |
| `var4` | 59 | 0.837 | 0.843 | 55% | $0.957 |

**Macro-F1 spans 0.788–0.838 with nothing changed. The band is 0.051.
9 of 51 candidates (18%) changed verdict at least once.**

The band grew as runs were added — 0.042 at two runs, 0.051 at four.
That is the expected direction. **More runs will widen it, not narrow
it.** Treat 0.051 as a floor on the noise, not a confidence interval.

**Treat any difference under 0.051 as unresolved.** That is larger than
most gaps this repo has compared. The aggregation sweep spanned 0.018 and
is now firmly inside the noise. §8a's all-Haiku collapse (0.847 → 0.516)
survives easily; little else does.

### What the README should say

Quoted on whole runs, the four runs gave 0.814, 0.844 and 0.861 (`var2`
was partial). The published **0.847 sits inside that range**, so it is
not wrong — but it is one draw from a wide distribution. **Quote
macro-F1 as roughly 0.81–0.86, not 0.847.**

### The mechanism, confirmed

**All 9 unstable candidates sat within 1.0 of a cutoff.** With
`ADVANCE_CUTOFF` at 4.0 and `HOLD_CUTOFF` at 1.0, and 44 of 60 scores
inside 1.0 of a cutoff, scores bunch against the thresholds and small
jitter crosses a line. Score movement is near-universal: the mean score
range across runs is 0.88 points, and **only 1 of 51 candidates scored
identically in all four runs.**

Three further findings:

- **`reject` is the least stable class, not `hold`.** Per-class F1
  spread: `advance` 0.051, `hold` 0.042, `reject` **0.161**. The
  `hold`-recall story in §3c pointed at the wrong place.
- **Routing is roughly stable.** Escalation ran 51–55%. The noise lives
  in the scores far more than in the decision to escalate.
- **Cost is stable and lower than estimated.** Three full runs cost
  $0.946, $0.956 and $0.957 — a spread of one cent. `COST_ANALYSIS.md`
  re-derived $1.20 and bracketed it at $1.15–$1.24. **The measured figure
  is ~$0.95, below that bracket.** That doc needs updating.

Parse failures ran 1.9%–3.9% (4/180, 3/156, 7/180, 6/177), wider than the
2.2% §8a measured for Sonnet. A failed parse scores 0.0, which is
indistinguishable from a confident reject, so this is noise with a
mechanical cause and a plausible fix.

### A methodology note worth keeping

The first `var3` attempt scored 29 of 60 and had to be thrown away.
31 candidates died on connection errors, and **the survivors were not a
random subset**: zero escalations, and panel spread capped at 5.0 against
9.0 in every other run. An escalating candidate makes an extra arbiter
call, so it is more exposed to a dropped connection — and it is also the
hard candidate carrying the disagreement. The run kept only the easy
cases, which would have understated the very thing it was measuring.
`scripts/variance_report.py` now has a **Run health** section that flags
this automatically.

Full detail: `docs/VARIANCE.md`.

## Multi-provider bake-off — 2026-08-27

First cross-provider comparison. Panel + arbiter swapped; extraction
stays on Haiku in every arm. 20 resumes (`data/bakeoff_sample.json`,
stratified 7/7/6 across all 9 archetypes), 3 runs per arm.

| Arm | Macro-F1 (3 runs) | Cost/resume | p50 latency | Parse failures |
|---|---|---|---|---|
| `anthropic-control` (Sonnet 5) | 0.867 (0.802–0.949) | $0.0164 | 12.8s | 2/180 (1.1%) |
| `gpt-5.6-luna` (medium) | 0.517 (0.456–0.579) | **$0.0053** | 16.6s | **0/180** |

**Gemini 3.7 Flash did not run.** The key is on the free tier, capped at
**20 requests per day per model**. One 20-resume run needs 60+ (20 x 3
panel agents). The model id `gemini-3.7-flash` is confirmed valid — the
quota error names it, so it resolved. This arm needs billing enabled on
the Google Cloud project, nothing else.

### The headline number is misleading, and the reason is the interesting part

Read alone, Luna looks far worse: 0.517 against 0.867, a gap of 0.35 that
is way outside the ~0.098 noise band for a 20-resume sample. That reading
is wrong.

**Luna grades on a different scale.** Its mean score is 4.60 against the
control's 2.65, and its errors run entirely the opposite direction:

| Arm | Errors above the label | Errors below the label |
|---|---|---|
| `anthropic-control` | 1 | 7 |
| `gpt-5.6-luna` | **27** | **0** |

Every single Luna error is a candidate scored too generously. The
cutoffs it is being judged against (`ADVANCE_CUTOFF = 4.0`,
`HOLD_CUTOFF = 1.0`) were swept against *Sonnet's* distribution in
`docs/CUTOFF_SWEEP.md`. Applying them to a model that grades two points
higher is the same mistake that held macro-F1 at 0.601 until the cutoffs
were fixed.

Re-thresholding each arm's recorded scores offline (free):

| Arm | As shipped (4.0/1.0) | Own best cutoffs | Best macro-F1 |
|---|---|---|---|
| `anthropic-control` | 0.867 | 3.7/0.7 | 0.881 |
| `gpt-5.6-luna` | 0.517 | 5.7/3.1 | **0.896** |

**With cutoffs fitted to itself, Luna edges the control — at a third of
the cost.** That is not a licence to switch: those cutoffs are fitted on
the same 20 resumes they are scored against, which is worse overfitting
than the 60-resume version `docs/LIMITATIONS.md` already flags. It means
the arm is live, not that it wins.

**The methodological finding is the durable one.** As designed, this
bake-off measured *"which model shares Sonnet's calibration"* rather than
*"which model judges better"*. Any future arm must be re-thresholded
before its accuracy is quoted, so `scripts/bakeoff.py` now prints a
Calibration section above the ranking, and `--report-only` rebuilds it
from recorded runs at no cost.

### Two smaller results

- **Luna is not a JSON-reliability problem.** 0 parse failures in 180
  panel calls, against Sonnet's 2/180. This is the opposite of §8a, where
  an all-Haiku panel was rejected on 49% unparseable output. Cheaper did
  not mean sloppier here.
- **Cheaper is slower.** Luna costs 3.1x less per resume but its p50 is
  16.6s against 12.8s — reasoning tokens at medium effort. Cost and
  latency do not move together.

### The variance prediction held

Before running this, the 20-resume noise band was predicted at ~0.098
median (2000 resamples of the four variance runs, 90th percentile 0.163).
The control arm's observed band across 3 runs was **0.147**, and Luna's
**0.123**. Both sit inside the predicted distribution. `docs/VARIANCE.md`
is doing its job.

Full detail: `docs/BAKEOFF.md`.

## Haiku panel, re-tested properly — 2026-08-27

An all-Haiku panel was already tried and rejected in PLAN.md §8a, on the
stated grounds that **49% of its responses were "unparseable JSON"**.
That diagnosis was wrong, and the re-test replaces it.

Three Haiku arms on the same 20 resumes, 3 runs each:

| Arm | Macro-F1 | Parse failures | What changed |
|---|---|---|---|
| `anthropic-control` (Sonnet) | 0.933 (0.901–0.949) | 8/180 (4.4%) | — |
| `haiku-panel-bare` | 0.433 (0.404–0.447) | 78/180 (43.3%) | reproduces §8a |
| `haiku-panel-prefill` | 0.390 (0.364–0.442) | 70/180 (38.9%) | assistant turn prefilled with `{` |
| `haiku-panel-unwrapped` | 0.402 (0.318–0.447) | 60/180 (33.3%) | parser now unwraps envelopes |

**Haiku is rejected again, but for the right reason this time.**

### The JSON was never unparseable

Reading the failures rather than the count: Haiku's output is valid JSON.
It is the wrong *shape*.

    {"production_reality": {"score": 9, "confidence": 0.95, ...}}

The parser found no top-level `score` and discarded a score the model had
already produced. 60 of 78 failures in the bare run were this envelope.

Two hypotheses were tested, in order of cheapness:

1. **Structured output (prefill).** §8a's own note guessed this was a
   formatting problem. Prefilling the assistant turn with `{` makes the
   preamble impossible. **Refuted:** failures moved 43.3% → 38.9% and
   macro-F1 did not improve. The arm is kept as evidence.
2. **Parser unwrapping.** `_unwrap_panel_score` now recovers an envelope
   keyed by the agent's own name, and refuses one keyed by a sibling
   agent. **Partly worked:** failures 43.3% → 33.3%. Accuracy unmoved.

### The real cause, and why no fix rescues it

Of the 45 remaining failures, **29 are Haiku answering for a different
dimension than the one it was asked to judge.** The agent is told "your
specific lens: production_reality" and returns a score for
`client_communication`. The parser correctly refuses those — accepting
one would award an agent a number another agent wrote.

That is not a formatting problem and no output constraint fixes it. It is
an instruction-following failure: **Haiku cannot reliably hold a single-
dimension persona in this three-agent design.** It explains why macro-F1
sits near 0.40 across all three arms regardless of what is repaired
downstream, and why even its own best cutoffs only reach 0.633–0.662
against the control's 0.933.

### What was kept

`_unwrap_panel_score` stays. It recovers real work from a real failure
mode, it is conservative about attribution, and it benefits any model
that wraps its answer — 9 tests cover it, including the case where it
must refuse a sibling's score. It simply does not make Haiku viable.

The pre-fix control runs are preserved as
`data/bakeoff__anthropic-control-prefix__run*.json` so the parser change
can be evaluated against them later. The control's own numbers moved
0.867 → 0.933 across the two rounds, which is inside the 20-resume noise
band (~0.098) and should not be read as an effect of the fix.

Full detail: `docs/BAKEOFF.md`.

## Panel confidence removed — 2026-08-27

Each panel agent used to return `{score, confidence, rationale}`. The
confidence is gone. Measured on the same 20 resumes, 3 runs each:

| | Macro-F1 | Output tokens | Cost |
|---|---|---|---|
| With confidence | 0.933 (0.901–0.949) | 24,311 | $0.332 |
| **Without** | 0.914 (0.897–0.949) | 23,452 | $0.317 |

**No measurable accuracy cost.** The 0.019 difference is far inside the
20-resume noise band (~0.098) and the ranges overlap almost completely.
Output tokens fell 3.5% and cost 4.5%, free.

### Why it was removed

**It was never used for anything.** Panel confidence never touched the
score, the escalation decision, or the verdict. It was printed in the CLI
and the web UI and nowhere else.

**And it was actively misleading.** Across 537 recorded panel scores:

| Measure | Value |
|---|---|
| Mean | 0.824, never below 0.50, clustered 0.85–0.95 |
| Mean when the verdict was **correct** | 0.816 |
| Mean when the verdict was **wrong** | **0.867** |

It is *higher when the system is wrong*. A reviewer using it to decide
what to check would be steered toward the cases the system got right.

Per agent, the pattern is worse:

| Agent | Mean confidence |
|---|---|
| `production_reality` | 0.798 |
| `technical_integration` | 0.810 |
| **`client_communication`** | **0.864** |

`client_communication` barely discriminates and scores nearly everyone
low (`docs/SCORE_SCALE.md`). It was the most confident of the three.

**Extraction confidence is kept** — different field, and load-bearing: it
gates a human-review flag at `< 0.4`.

### A related finding: that flag has never fired

Across `var1`, `var3` and `var4` (180 resume-screenings), every verdict
flagged for review is explained by escalation or a parse failure. **Zero**
came from extraction confidence below 0.4. The branch is live code that
has never once triggered on this corpus. Either the threshold is too low
or Haiku never reports low confidence on clean synthetic input — worth
knowing before that flag is trusted on real, messier resumes.

## Cutoffs refitted per model, and held out — 2026-08-27

The verdict cutoffs (`ADVANCE_CUTOFF = 4.0`, `HOLD_CUTOFF = 1.0`) were
swept against Sonnet's score distribution, then used to judge every other
model. `scripts/fit_cutoffs.py` refits them per model on recorded scores
— offline, free — and, critically, **tests them on resumes they were not
fitted on.**

| Arm | Mean score | Shipped 4.0/1.0 | Own cutoffs | Fitted (upper bound) | **Held-out (honest)** |
|---|---|---|---|---|---|
| `anthropic-control` (20, 3 runs) | 2.69 | 0.914 | 3.6/0.7 | 0.914 | **0.896** |
| `gpt-5.6-luna-medium` (20, 3 runs) | 4.60 | 0.517 | 5.7/3.1 | 0.897 | **0.814** |
| `anthropic-control-60` (60, 1 run) | 2.35 | 0.864 | 3.1/0.4 | 0.900 | **0.898** |

**0.30 of Luna's apparent deficit was calibration, not judgment.** It goes
0.517 → 0.814 with the model untouched. Sonnet still wins honestly
(0.896 vs 0.814), but the shipped-cutoff number overstated the gap
roughly fourfold — and Luna costs about a third as much per resume.

### Why "held-out" is the column that counts

Sweeping every cutoff pair and keeping the winner fits the cutoffs to the
same resumes they are then scored on. `docs/LIMITATIONS.md` has always
flagged this for the shipped values; the fitted column has the same flaw
by construction. The held-out column chooses cutoffs on 4/5 of the corpus
and scores the fold it never saw, averaged over 5 folds. **The gap
between the two columns is the overfitting, made visible** — and for a
single run it is large: `var1` alone fits to 0.843 but holds out at
0.729.

That is also why cutoffs are fitted on runs *pooled*, never one run. With
a 0.051 noise band, cutoffs fitted to a single run are partly fitted to
that run's noise.

### The 60-resume comparison is unfinished

Only one of six planned runs completed. The Anthropic credit balance ran
out mid-batch, and **the Luna arm died with it** — because evidence
extraction stays on Haiku in every arm, an arm with a perfectly good
OpenAI key still fails at the extraction step. That dependency is real
and worth remembering before budgeting a cross-provider run.

One partial run (15 of 60) scored macro-F1 **1.000** and has been
quarantined as `data/UNUSABLE__anthropic-control-60__run2__partial-15of60.json`
rather than deleted. It is a textbook example of why partial runs are
excluded: the survivors are the easy candidates, and the number looks
perfect.

To finish, with credit available (~$3.80):

    python scripts/bakeoff.py --sample data/bakeoff_sample60.json \
        --arm anthropic-control-60 --arm gpt-5.6-luna-60

### The generalisable lesson

A fixed score-to-verdict threshold is part of the **harness**, not part of
the model. Any bake-off that holds it constant across models is partly
measuring which model happens to share the calibration of whichever model
the threshold was tuned on. Full detail: `docs/CUTOFF_FIT.md`.

## The 60-resume bake-off, finished — 2026-08-27

Both arms, 3 runs each, all 60 resumes, no failures. This completes the
run that credit exhaustion cut short earlier.

| | Sonnet 5 (control) | GPT-5.6 Luna |
|---|---|---|
| Under shipped cutoffs (4.0/1.0) | **0.823** (0.797–0.843) | 0.563 (0.548–0.587) |
| **Held-out, own cutoffs** | 0.787 | **0.861** |
| Cost per resume | $0.0154 | **$0.0053** (2.9x cheaper) |
| p50 latency | **11.6s** | 14.2s |
| Parse failures | 22/540 (4.1%) | **0/540** |
| Escalation rate | **47%** | 70% |

**The ordering reverses once both models are calibrated fairly.** Paired
by fold:

| Fold | Sonnet | Luna | Diff |
|---|---|---|---|
| 1 | 0.972 | 0.972 | +0.000 |
| 2 | 0.799 | 0.836 | +0.037 |
| 3 | 0.855 | 0.944 | +0.089 |
| 4 | 0.635 | 0.749 | +0.114 |
| 5 | 0.674 | 0.804 | +0.130 |
| **mean** | **0.787** | **0.861** | **+0.074** |

Luna wins 4 of 5 folds and loses none. The 0.074 gap exceeds the 0.051
noise band. **On 20 resumes Sonnet won, 0.896 to 0.814; on 60 the result
flips.** That is a warning about the 20-resume sample, not a contradiction
— the noise band there is ~0.098, wider than either gap.

### Sonnet's shipped number flatters it

Sonnet scores 0.823 under the shipped cutoffs and **0.787** held out. The
difference is not noise, it is the cutoffs: 4.0/1.0 were swept against
*this corpus* using *Sonnet's* scores, so the shipped configuration
carries a home-field advantage that does not survive unseen resumes. Luna
never had it.

### A flaw found and fixed in our own method

The first version of the cross-validation split **prediction rows**. With
3 runs pooled, the same resume then appeared in both training and test
folds, so a cutoff was chosen partly from that resume's own typical
score. That is leakage. `stratified_folds` now groups every row for a
resume into one fold.

The corrected numbers were identical to three decimals — fitting two
scalar thresholds is not sensitive enough for the leak to bite — but the
method was wrong and is now right.

### What this does NOT license

**Do not swap the panel to Luna on this evidence.**

- **Luna escalates 70% of candidates against Sonnet's 47%.** It sends far
  more work to the arbiter. Cost above already includes that; a real
  deployment would feel it as latency and reviewer load.
- **Fold spread is wide** — 0.635–0.972 for Sonnet, 0.749–0.972 for Luna,
  at 12 resumes per fold. Read the mean, never a fold.
- **Still one synthetic corpus.** Better than fitting and scoring on all
  60, but not fresh data.
- **Every arm still needs an Anthropic key**, because extraction stays on
  Haiku.

What it establishes: **Luna is a serious candidate, not the also-ran the
shipped-cutoff number implied — and no model comparison here is valid
until the cutoffs are re-fitted per model.** Full detail:
`docs/CUTOFF_FIT.md`.

## Cutoffs are now per-model — shipped 2026-08-27

`recommendation_from_score` now takes the cutoffs belonging to whichever
model scored the panel, instead of one global pair.

```python
MODEL_CUTOFFS = {
    "claude-sonnet-5": Cutoffs(3.1, 0.7),
    "gpt-5.6-luna":    Cutoffs(5.8, 2.6),
}
```

Re-scoring the recorded 60-resume runs through the shipped code:

| Arm | Cutoffs | Before | After |
|---|---|---|---|
| `anthropic-control-60` | 3.1/0.7 | 0.823 | 0.828 (+0.005) |
| `gpt-5.6-luna-60` | 5.8/2.6 | 0.563 | **0.884 (+0.321)** |

Sonnet barely moves, which is the expected result — the old global pair
*was* Sonnet's calibration. Luna gains 0.321 with no change to the model,
the prompt, or the evidence.

A model absent from the table falls back to the historical 4.0/1.0. That
fallback is honest rather than safe: it means an unfitted model is being
judged on Sonnet's scale, which is exactly the trap this change exists to
close. Fit it with `scripts/fit_cutoffs.py` before trusting its score.

`recommendation_from_score(score)` with no cutoffs argument behaves
exactly as before, so every recorded run and every existing caller is
unaffected. 7 tests cover the new behaviour, including that the same 5.0
is an `advance` on Sonnet's scale and a `hold` on Luna's.

### Corrections to the previous entry

Two claims in the write-up above were wrong or overstated:

- **"Luna is faster" is false.** Luna's p50 is **14.2s** against Sonnet's
  **11.6s** — about 22% slower. It is cheaper and, held out, more
  accurate. It is not faster.
- **The Anthropic-key dependency was listed as a reason not to adopt
  Luna. It is not one.** Extraction runs on Haiku in every arm; that is a
  fact about the architecture, not a mark against any panel model.

The objections that stand are the escalation rate (70% vs 47%, being
addressed next), the wide fold spread, and the fact that this is one
synthetic corpus.

## Escalation and human review, unwelded — 2026-08-27

The reviewer queue was the problem: escalating auto-flagged a candidate
for human review, so at a 47% escalation rate (70% for Luna) most of the
stack landed in a person's queue. That defeats the point of the product.

Two faults, welded into one decision. Both measured over 179 recorded
screenings (`var1`, `var3`, `var4`).

### Fault 1: the arbiter was called when it could not help

The arbiter changes a verdict only by moving the score across a cutoff.
Measured over 84 escalations, it moves the score off the panel mean by:

| median | p75 | p90 | p95 | max |
|---|---|---|---|---|
| 0.33 | 0.50 | 0.93 | 1.00 | 1.50 |

So a panel mean sitting further from a cutoff than that is a call the
arbiter cannot win. **92% of escalations (77/84) returned a different
number and the same verdict.** Every one of the 7 that did change a
verdict had a mean within **0.33** of a cutoff.

`ESCALATION_MARGIN = 0.5` adds a third condition: the mean must be close
enough that the arbiter could realistically cross a line. It is twice the
largest distance at which an escalation has ever mattered, and equal to
the arbiter's p75 movement.

### Fault 2: `escalated` was a bad proxy for "a human should look"

Panel disagreement does not predict a wrong answer. The old flag was
dominated on both axes:

| Flag rule | Queue | Errors caught |
|---|---|---|
| **Old** (parse failure OR escalated) | **53%** | **36%** |
| Near-cutoff 0.75 | 54% | **82%** |

At the *same* queue size, a near-cutoff test catches more than twice the
errors. `REVIEW_MARGIN = 0.4` now drives the flag, off the **final**
score. Escalation keys off the **panel mean**, before the arbiter runs —
different quantities, so they get separate margins.

### The review margin had to become band-relative

The first version used a flat 0.4 points. Run live, that produced very
different queues per model, because the models grade on different scales
— **the same mistake the single global cutoff pair made**:

| Flat 0.4 margin | Queue |
|---|---|
| Sonnet (band 0.7–3.1, width 2.4) | **43%** |
| Luna (band 2.6–5.8, width 3.2) | 15% |

Sonnet's scores cluster tightly inside a narrower band, so a fixed gap
catches far more of them. `REVIEW_MARGIN_FRACTION = 0.125` is a fraction
of each model's own hold band — 0.30 points for Sonnet, 0.40 for Luna.

The escalation margin stays **absolute** at 0.5. Its justification is the
arbiter's measured movement (84 recorded escalations), and movement does
*not* scale cleanly with band width: as a fraction of band, Sonnet's max
move is 0.139 and Luna's 0.521. Each margin is expressed in the unit its
own evidence supports.

### Measured result, live

One run per arm on all 60 resumes:

| | Sonnet | Luna |
|---|---|---|
| Escalation rate | **5%** (was 47%) | **23%** (was ~70%) |
| Review queue | **30%** (was 53%) | **15%** |
| macro-F1 | 0.857 | 0.853 |
| Cost | $0.841 | $0.309 |

Both arms sit inside the 0.051 noise band of where they were. **Escalation
fell by roughly 90% for Sonnet and two-thirds for Luna, the queue nearly
halved, and accuracy did not move.**

### What this does not fix

**57% of errors still ship unreviewed.** The system is wrong on 16% of
candidates and a human now sees 32% of them. Reviewing a third of a stack
cannot catch most errors in it — that is arithmetic, not a tuning
failure. Raising `REVIEW_MARGIN` trades queue size for recall roughly
linearly up to ~0.75; it cannot reach high recall at any tolerable queue
size.

**The margin rests on 7 events.** All 7 useful escalations sat within
0.33 and the margin is 0.5. The principled retreat, if it proves too
tight, is 1.0 — the arbiter's p95 movement — which still cuts calls 39%.
Do not tune below 0.33.

### A correction to the earlier "never escalate" figures

`docs/ESCALATION_SWEEP.md` reports never-escalating at **0.797**; an
earlier entry in this file says **0.784**. Measured over var1/var3/var4
the answer is **0.813 mean (0.784–0.830)** — the 0.784 was one run, not
the figure. Either way the arbiter's whole contribution is 0.027
macro-F1, *inside* the 0.051 noise band, which is the honest frame: it
was never carrying the system.


## Panel switched to GPT-5.6 Luna — 2026-08-31

`DEFAULT_MODEL_IDS` now uses `gpt-5.6-luna` for the panel and arbiter.
Extraction stays on Haiku. Measured on the full 60, each model given
cutoffs fitted to its own scale:

| | Sonnet 5 | **GPT-5.6 Luna** |
|---|---|---|
| macro-F1 | 0.857 | 0.853 |
| Review queue | 30% | **15%** |
| Escalation | **5%** | 23% |
| Parse failures | 5/180 | **0/180** |
| Cost per 60 | $0.84 | **$0.31** |
| p50 latency | **11s** | 13s |

Same accuracy inside the 0.051 noise band, half the human queue, a third
of the cost. Sonnet keeps latency and a lower escalation rate.

**The arbiter moved with the panel.** It adjudicates between panel
rationales, so it has to read them on the scale they were written on — a
Sonnet arbiter ruling on Luna's 4.6-mean distribution would be applying
2.4-mean instincts.

**Operational cost of this change: production now needs two API keys.**
`OPENAI_API_KEY` for the panel and arbiter, `ANTHROPIC_API_KEY` for
extraction, and two spend caps rather than one. `MODEL_PROVIDERS` in
`core/pipeline.py` holds the non-Anthropic wiring; it is deliberately
separate from `config/bakeoff.json`, which exists to make experiments
cheap. A model only reaches production wiring after a bake-off earns it.

## The extraction-confidence review flag, replaced — 2026-08-31

`candidate.confidence < 0.4` was removed. Across 180 recorded screenings
it fired **zero** times — every flagged verdict was explained by a parse
failure or a near-cutoff score, with no residual. A magic threshold that
has never triggered is not a safety net.

It was **not** deleted outright, because a test proved the underlying
failure is reachable: extraction can return nothing at all, and the panel
then scores an empty evidence list and produces a confident-looking number
about nothing. The replacement condition is objective rather than tuned —
**no evidence extracted** — and the test pins that it fires.

## The cascade vs one call — 2026-08-31

The cascade's entire justification is that four-to-five calls per resume
beat asking one model once. That was asserted for the life of this
project and never tested. `screen_one_single_pass` is the control: same
model, same cached system block, same extraction step, same personas
verbatim, same cutoffs — the **only** difference is whether the three
dimensions are judged independently or together.

3 runs each, all 60 resumes:

| | Cascade | Single-pass |
|---|---|---|
| macro-F1 | 0.847 (0.804–0.884) | 0.821 (0.789–0.845) |
| Cost per 60 | $0.310 | **$0.277** (−11%) |
| p50 latency | 13.5s | **8.4s** (−38%) |
| Output tokens | 74,617 | **57,629** (−23%) |
| Parse failures | 0/540 | 0/540 |

**The 0.026 gap is inside the 0.051 noise band**, and the ranges overlap
heavily. So the means do not separate them.

### The paired test is decisive, and it is a tie

Comparing means wastes the fact that both arms scored the *same 60
resumes*. Per candidate, across 3 runs each:

| | Count |
|---|---|
| Cascade more often correct | **10** |
| Single-pass more often correct | **10** |
| Both always correct | 37 |
| Tied otherwise | 3 |

**Exactly 10–10.** Of the 20 candidates where the two architectures
disagree, the cascade wins half. This is the sensitive test — it holds
candidate difficulty constant — and it finds nothing.

### What this means

**On accuracy, the cascade is unproven.** It is not measurably better
than one call, while costing 11% more and taking 38% longer. After
today, that is measured rather than assumed.

**The burden has moved.** The remaining arguments for the cascade are not
about accuracy:

- **Explainability.** Three independent agents produce three rationales
  that did not see each other. A single call produces three rationales
  that anchored on one another. For a tool whose pitch is "every verdict
  shows its evidence", that is a real product difference — but it is a
  judgment call, not a measurement.
- **The disagreement signal.** Single-pass structurally cannot produce
  one: a single response cannot disagree with itself, so `panel_spread`
  is always 0.0 and it can never escalate. The cascade's spread is the
  only signal of genuine uncertainty the system has. Worth noting that
  escalation itself contributes only 0.027 macro-F1 — also inside the
  noise band — so this argument is weaker than it first appears.

**Not switched.** A 10–10 tie means "no difference detected", not
"single-pass is better", and the explainability story is the product. But
the cost and latency case for the cascade is now negative, and the
accuracy case is absent. That is written here rather than buried.

**Caveats.** Single-pass still runs the extraction step, so this is 2
calls against 4-5, not 1 against 5. And it is 60 synthetic resumes.


## Cutting output tokens — analysed, run blocked — 2026-08-31

Output is ~69% of the bill, so it is the biggest remaining cost lever.
The obvious move was to shorten the rationale. **Measurement says that is
the wrong lever.**

| | Per panel call |
|---|---|
| Visible rationale | 271 chars ≈ **68 tokens** |
| Total output | ≈ **290 tokens** |

So roughly **75% of output tokens are Luna's reasoning, not text anyone
reads.** Shortening a one-sentence rationale cannot touch that. The
prompt already caps it at one sentence and the UI renders a single
bullet, so there was never much to reclaim there.

The lever is `reasoning_effort`. A `luna-effort-low` arm is configured
in `config/bakeoff.json` and ready to run.

**The run is blocked, and not on anything about the experiment.** The
Anthropic credit balance ran out mid-batch. Evidence extraction runs on
Haiku in *every* arm, so an arm that is otherwise entirely OpenAI still
dies at the extraction step. That is the third time this dependency has
stopped a run; it is documented in `scripts/bakeoff.py` and
`docs/HOSTING.md`, and it is the strongest practical argument for
eventually moving extraction onto the same provider as the panel.

One partial run (8 of 60) is quarantined as
`data/UNUSABLE__luna-effort-low__run1.json`. Its macro-F1 of 0.667 on 8
survivors and accuracy of 1.000 are exactly the artefact partial runs
produce, and it is kept as an example rather than deleted.

To finish, with Anthropic credit available (~$1):

    python scripts/bakeoff.py --sample data/bakeoff_sample60.json --runs 3

**Accept/reject:** macro-F1 must hold within 0.051 of 0.847. Expected
saving is roughly 30-50% of output tokens, so ~$0.31 → ~$0.20 per run.
