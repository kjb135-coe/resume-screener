# Verdict cutoffs, fitted and tested per model

The pipeline ships `ADVANCE_CUTOFF = 4.0` / `HOLD_CUTOFF = 1.0`, swept against Sonnet. A model that grades on a different scale loses macro-F1 to the mismatch rather than to its judgment. This refits them per model on recorded scores — offline, no API calls.

| Arm | Mean score | Shipped 4.0/1.0 | Fitted cutoffs | Fitted (upper bound) | **Held-out (honest)** |
|---|---|---|---|---|---|
| `anthropic-control` | 2.69 | 0.914 | 3.6/0.7 | 0.914 | **0.896** |
| `gpt-5.6-luna-medium` | 4.60 | 0.517 | 5.7/3.1 | 0.897 | **0.814** |
| `anthropic-control-60` | 2.35 | 0.864 | 3.1/0.4 | 0.900 | **0.898** |

**Read the held-out column, not the fitted one.** `Fitted` chooses the cutoffs on the same resumes it then scores, which is overfitting by construction — it answers "how good could this model be if perfectly calibrated". `Held-out` chooses cutoffs on 4/5 of the corpus and scores the fold it never saw, averaged over all folds. The gap between the two columns is the overfitting, made visible.

Cutoffs are fitted on every run pooled, not one run, because run-to-run noise is 0.051 macro-F1 (`docs/VARIANCE.md`) and cutoffs fitted to a single run would partly be fitted to that noise.


## What is comparable here, and what is not

**The only like-for-like comparison is the 20-resume pair** —
`anthropic-control` and `gpt-5.6-luna-medium`. Same 20 resumes, 3 runs
each, same code. Read those two rows against each other and nothing else.

`anthropic-control-60` is **one** run on the full corpus, not three. It is
included for scale, not for comparison: a single run carries the full
0.051 noise band on its own.

**The Luna 60-resume arm does not exist.** It was launched and died: the
Anthropic credit balance ran out mid-batch, and because evidence
extraction stays on Haiku in *every* arm, the Luna arm failed at the
extraction step despite its own OpenAI key being fine. That dependency is
documented in `scripts/bakeoff.py` and it is the thing to remember before
budgeting a cross-provider run.

To finish the comparison properly:

```
python scripts/bakeoff.py --sample data/bakeoff_sample60.json \
    --arm anthropic-control-60 --arm gpt-5.6-luna-60
```

Roughly $3.80 with credit available.

## The finding that survives regardless

Under the shipped cutoffs Luna scores **0.517**. Held out honestly on
cutoffs fitted to its own scale, it scores **0.814**. The model did not
change. **0.30 of that gap was calibration, not judgment.**

Sonnet still wins the honest comparison (0.896 vs 0.814) — but the
shipped-cutoff number overstated the gap by a factor of four, and Luna
costs roughly a third as much per resume.

**The generalisable lesson:** a fixed score-to-verdict threshold is part
of the harness, not part of the model. Any bake-off that holds it constant
across models is partly measuring which model happens to share the
calibration of whichever model the threshold was tuned on.
