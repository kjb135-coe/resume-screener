# Run-to-run variance

4 runs of one unchanged configuration: `var1`, `var2`, `var3`, `var4`.

Every difference below is noise, not a change. **Only pass runs that share the same code.** This script cannot check that for you, and comparing runs across a code change is the exact error that made the original 10% drift figure soft.

**Partial runs present:** `var2` (52/60), `var4` (59/60).

## Headline spread

All figures are recomputed over the **51 candidates every run scored**, not read from the stored per-run totals. That keeps a partial run comparable instead of throwing it away.

| Metric | Mean | Range | Spread | Stdev |
|---|---|---|---|---|
| Macro-F1 | 0.824 | 0.788–0.838 | 0.051 | 0.024 |
| Accuracy | 0.833 | 0.804–0.843 | 0.039 | 0.020 |
| Escalation rate | 0.529 | 0.510–0.549 | 0.039 | 0.016 |
| Cost (USD) | 0.951 | 0.946–0.956 | 0.010 | 0.007 |

Cost and wall clock cover each run's whole batch, so they are only comparable between runs that scored the same number of resumes. They sit in the per-run table below rather than in this spread.

**The noise band on macro-F1 is 0.051.** Any future change that moves macro-F1 by less than this has not been measured — it has been observed once.

## Run health

Check this before reading anything above. A run that dropped candidates to network errors keeps the easy ones, which makes the noise look smaller than it is.

| Run | Scored | Escalated (own batch) | Max panel spread | Median spread |
|---|---|---|---|---|
| `var1` | 60/60 | 28/60 (47%) | 9.0 | 2.0 |
| `var2` | 52/60 | 27/52 (52%) | 9.0 | 4.0 |
| `var3` | 60/60 | 27/60 (45%) | 9.0 | 2.0 |
| `var4` | 59/60 | 29/59 (49%) | 9.0 | 3.0 |

## Per-class F1

The narrow middle class carries the most instability. It has a boundary on both sides, so jitter can push a candidate out either way.

| Class | Mean | Range | Spread | Stdev |
|---|---|---|---|---|
| `advance` | 0.961 | 0.923–0.974 | 0.051 | 0.025 |
| `hold` | 0.750 | 0.722–0.765 | 0.042 | 0.020 |
| `reject` | 0.761 | 0.667–0.828 | 0.161 | 0.068 |

## Verdict churn

- Candidates scored in all 4 runs: **51**
- Candidates that changed verdict at least once: **9** (18%)
- Candidates correct and stable in every run: **37**

Every candidate that moved:

| Candidate | Label | Verdicts | Scores | Score range | Nearest cutoff |
|---|---|---|---|---|---|
| `early_career__vera_klimenko.md` | hold | hold → advance → advance → hold | 3.5, 5.0, 4.5, 3.0 | 2.0 | 0.5 |
| `quiet_builder__ewan_brackenridge.md` | advance | advance → advance → hold → advance | 4.3, 5.0, 3.0, 4.5 | 2.0 | 0.3 |
| `adjacent_shipper__keiko_yamashita.md` | advance | advance → advance → advance → hold | 4.0, 4.5, 4.0, 3.3 | 1.2 | 0.0 |
| `early_career__ingrid_solberg.md` | hold | advance → hold → advance → hold | 4.0, 3.0, 4.0, 3.5 | 1.0 | 0.0 |
| `keyword_stuffer__rosalind_pike.md` | reject | hold → reject → reject → reject | 1.0, 0.0, 0.3, 0.0 | 1.0 | 0.0 |
| `production_light_ai__larissa_petrov.md` | hold | hold → reject → hold → reject | 1.3, 0.7, 1.3, 0.3 | 1.0 | 0.3 |
| `academic_researcher__freya_ashcombe.md` | reject | hold → reject → reject → reject | 1.0, 0.3, 0.3, 0.7 | 0.7 | 0.0 |
| `keyword_stuffer__aleksandr_volkov.md` | reject | hold → reject → reject → reject | 1.0, 0.3, 0.7, 0.7 | 0.7 | 0.0 |
| `production_light_ai__signe_aalborg.md` | hold | reject → reject → hold → reject | 0.7, 0.7, 1.0, 0.3 | 0.7 | 0.0 |

**9 of 9** unstable candidates sat within 1.0 of a cutoff (`1.0` or `4.0`). That is the mechanism: scores bunch near the thresholds, so small jitter crosses a line.

## Score movement

Verdict churn undercounts the noise. A score can swing and still land in the same bucket.

- Mean score range across runs: **0.88** points
- Largest single-candidate swing: **2.5** points
- Candidates whose score never moved: **1** of 51

## Parse failures

A failed parse scores 0.0, which is indistinguishable from a confident reject in the final verdict. This is noise with a mechanical cause, not a judgment the model made.

| Run | Failed panel calls | Of total | Rate |
|---|---|---|---|
| `var1` | 4 | 180 | 2.2% |
| `var2` | 3 | 156 | 1.9% |
| `var3` | 7 | 180 | 3.9% |
| `var4` | 6 | 177 | 3.4% |

Rate across runs: 1.9%–3.9%.

## Per-run detail

`Macro-F1` is on the shared 51. `Stored` is what the run itself reported over whatever it scored — shown only so the two are not confused.

| Run | n | Macro-F1 | Stored | Accuracy | Escalated | Cost | Wall clock |
|---|---|---|---|---|---|---|---|
| `var1` | 60 | **0.788** | 0.814 | 0.804 | 53% | $0.956 | 99s |
| `var2` | 52 | **0.833** | 0.837 | 0.843 | 53% | $0.838 | 93s |
| `var3` | 60 | **0.838** | 0.844 | 0.843 | 51% | $0.946 | 101s |
| `var4` | 59 | **0.837** | 0.861 | 0.843 | 55% | $0.957 | 104s |

## How to use this

Quote macro-F1 as a range, not a point. Treat any difference under 0.051 as unresolved. With 4 runs this is a rough band and not a confidence interval — it is a floor on the noise, and more runs would likely widen it rather than narrow it.

