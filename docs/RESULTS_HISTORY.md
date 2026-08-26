# Results history

Every measured run, what changed before it, and why the number moved.
Hand-maintained: add a row whenever an eval run happens.

`docs/EVAL_RESULTS.md` always describes the *latest* run only. This file
is the record of how it got there.

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

**Cost.** $1.796 for 60 resumes, about 3 cents each, and this is the
first figure priced per model rather than billing everything at Haiku
rates. It is not comparable to the "$0.93" in runs 1 and 2, which were
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
