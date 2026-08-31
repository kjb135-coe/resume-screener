# Verdict cutoffs, fitted and tested per model

The pipeline ships `ADVANCE_CUTOFF = 4.0` / `HOLD_CUTOFF = 1.0`, swept against Sonnet. A model that grades on a different scale loses macro-F1 to the mismatch rather than to its judgment. This refits them per model on recorded scores — offline, no API calls.

| Arm | Mean score | Shipped 4.0/1.0 | Fitted cutoffs | Fitted (upper bound) | **Held-out (honest)** |
|---|---|---|---|---|---|
| `anthropic-control-60` | 2.42 | 0.823 | 3.1/0.7 | 0.828 | **0.787** |
| `gpt-5.6-luna-60` | 4.03 | 0.563 | 5.8/2.6 | 0.884 | **0.861** |

**Read the held-out column, not the fitted one.** `Fitted` chooses the cutoffs on the same resumes it then scores, which is overfitting by construction — it answers "how good could this model be if perfectly calibrated". `Held-out` chooses cutoffs on 4/5 of the corpus and scores the fold it never saw, averaged over all folds. The gap between the two columns is the overfitting, made visible.

Cutoffs are fitted on every run pooled, not one run, because run-to-run noise is 0.051 macro-F1 (`docs/VARIANCE.md`) and cutoffs fitted to a single run would partly be fitted to that noise.


## The full-corpus result — and it reverses the 20-resume one

60 resumes, 3 runs per arm, cutoffs fitted per model and tested on folds
they never saw. Folds are split **by resume**, so a resume never appears
in both training and test.

| Fold | Sonnet | Luna | Diff |
|---|---|---|---|
| 1 | 0.972 | 0.972 | +0.000 |
| 2 | 0.799 | 0.836 | +0.037 |
| 3 | 0.855 | 0.944 | +0.089 |
| 4 | 0.635 | 0.749 | +0.114 |
| 5 | 0.674 | 0.804 | +0.130 |
| **mean** | **0.787** | **0.861** | **+0.074** |

**Luna is better in 4 of 5 folds and worse in none.** The gap, 0.074,
exceeds the measured 0.051 noise band. On 20 resumes Sonnet won
(0.896 vs 0.814); on the full 60 the ordering flips.

Alongside cost and reliability:

| | Sonnet 5 | GPT-5.6 Luna |
|---|---|---|
| Held-out macro-F1 | 0.787 | **0.861** |
| Under shipped 4.0/1.0 | **0.823** | 0.563 |
| Cost per resume | $0.0154 | **$0.0053** (2.9x cheaper) |
| p50 latency | **11.6s** | 14.2s |
| Parse failures | 22/540 (4.1%) | **0/540** |
| Escalation rate | **47%** | 70% |

### Why Sonnet's shipped number flatters it

Sonnet scores 0.823 under the shipped cutoffs but only **0.787** held
out. That is not noise — it is the cutoffs. `ADVANCE_CUTOFF = 4.0` and
`HOLD_CUTOFF = 1.0` were swept against *this corpus* using *Sonnet's*
scores, so the shipped configuration carries an advantage that does not
survive being tested on unseen resumes. Luna never had that advantage.
Give both models the same treatment and the ordering changes.

### What this does not license

**Do not swap the panel to Luna on this evidence.** Four reasons:

1. **Luna escalates far more** — 70% against 47%. It sends far more
   candidates to the arbiter, which is a real cost and workload the
   headline hides. The cost figure above already includes it, but a
   deployment would feel it as latency and reviewer load.
2. **Fold spread is wide.** Individual folds range 0.635-0.972 for
   Sonnet, 0.749-0.972 for Luna. Each fold is 12 resumes. The *mean*
   across folds is the number to read; no single fold means anything.
3. **Still one synthetic corpus.** Cutoffs fitted on 60 generated resumes
   and tested on folds of those same 60 is better than fitting and
   scoring on all 60 — but it is not fresh data. See
   `docs/LIMITATIONS.md`.
4. **The dependency stands.** Every arm still needs an Anthropic key,
   because extraction runs on Haiku regardless.

What it does establish: **Luna is a serious candidate, not the also-ran
the shipped-cutoff number made it look like, and the cheapest way to test
that properly is to re-fit the cutoffs before comparing anything.**
