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

## Changes made since run 2, not yet measured

These are in the code now. **No eval run has been done against them**, so
their effect is predicted, not measured. The next run is what settles it.

| Change | Why | Expected effect |
|---|---|---|
| Cost priced per model (PLAN §3g) | `Usage.__add__` kept only the first model id, so every Verdict was labelled Haiku and the whole run was priced at Haiku rates. Reported cost was understated several-fold. | Reported cost rises sharply. Actual spend unchanged — it was always this. |
| Arbiter Opus → Sonnet | The arbiter was ~57% of real spend while adjudicating between three rationales already written for it. | Cost roughly halves. Accuracy effect unknown; this is the one to watch. |
| Escalation guard: spread > threshold **and** the agents disagree on bucket | Spread measures variance, not decision uncertainty. 9.0/7.0/6.0 clears the threshold but every score means the same verdict. | Escalations 33 → 26 at current cutoffs. No verdict can change, so accuracy should be flat. |

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

## The known root cause

`client_communication` is broken, and it is dragging everything else.

| Agent | mean | median | zeros |
|---|---|---|---|
| production_reality | 3.23 | 1.0 | 14/60 |
| technical_integration | 2.98 | 2.0 | 22/60 |
| **client_communication** | **0.67** | **0.0** | **33/60** |

It never scores above 6.0 for anyone, and it barely separates the classes
it is supposed to:

| Archetype target | production_reality | technical_integration | client_communication |
|---|---|---|---|
| high | 5.63 | 6.33 | **2.29** |
| medium | 1.92 | 2.28 | **0.55** |
| low | 0.85 | 0.24 | **0.39** |

The other two discriminate cleanly. This one compresses everything toward
zero and cannot tell `medium` from `low`.

Because the final score is a mean of three, an agent that scores near zero
for almost everyone pulls **every** candidate down by roughly two points.
That is why the 7.0 cutoff was far too high, why the arbiter kept
overriding it upward, and why all errors ran one direction. One broken
dimension explains the whole chain.

The rubric tells this agent that absence "is not automatically
disqualifying" — but scoring 0.0 into a mean *is* a penalty. The dimension
needs to either abstain, be weighted, or be scored on presence rather than
on a 0-10 scale. Not yet decided, and it should be settled before chasing
cutoffs, because fixing it moves the score distribution the cutoffs are
being fitted to.
