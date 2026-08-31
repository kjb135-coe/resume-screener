# Verdict cutoffs, fitted and tested per model

The pipeline ships `ADVANCE_CUTOFF = 4.0` / `HOLD_CUTOFF = 1.0`, swept against Sonnet. A model that grades on a different scale loses macro-F1 to the mismatch rather than to its judgment. This refits them per model on recorded scores — offline, no API calls.

| Arm | Mean score | As shipped | Fitted cutoffs | Fitted (upper bound) | **Held-out (honest)** |
|---|---|---|---|---|---|
| `single-pass-arbiter` | 4.22 | 0.899 | 5.4/2.6 | 0.899 | **0.899** |
| `gpt-5.6-luna-60` | 4.03 | 0.847 | 5.4/2.6 | 0.847 | **0.803** |

**Read the held-out column, not the fitted one.** `Fitted` chooses the cutoffs on the same resumes it then scores, which is overfitting by construction — it answers "how good could this model be if perfectly calibrated". `Held-out` chooses cutoffs on 4/5 of the corpus and scores the fold it never saw, averaged over all folds. The gap between the two columns is the overfitting, made visible.

Cutoffs are fitted on every run pooled, not one run, because run-to-run noise is 0.051 macro-F1 (`docs/VARIANCE.md`) and cutoffs fitted to a single run would partly be fitted to that noise.

