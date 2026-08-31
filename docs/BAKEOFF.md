# Model bake-off

2 arms, 3 runs each, on the same 60 resumes (`data/bakeoff_sample.json`, seed 20260827). Swapped slots: `panel`, `arbiter`. Extraction stays on Haiku in every arm.

**Read this before ranking anything by accuracy.** The macro-F1 noise band on a stratified 20 is roughly **0.098** (median of 2000 resamples of four identical runs; see `docs/VARIANCE.md`). Treat any accuracy gap smaller than the per-arm spread below as unresolved. Cost, latency and parse-failure rate are far more stable and can be read directly.

## Summary

| Arm | Macro-F1 (range) | Accuracy | Cost/resume | Latency p50 | Parse failures |
|---|---|---|---|---|---|
| `anthropic-control-60` | 0.823 (0.797–0.843) | 0.828 | $0.0154 | 11.6s | 22/540 (4.1%) |
| `gpt-5.6-luna-60` | 0.563 (0.548–0.587) | 0.583 | $0.0053 | 14.2s | 0/540 (0.0%) |

## Per-run detail

| Arm | Run | n | Macro-F1 | Accuracy | Cost | p50 | Parse failures |
|---|---|---|---|---|---|---|---|
| `anthropic-control-60` | 1 | 60 | 0.797 | 0.800 | $0.956 | 11.8s | 10/180 |
| `anthropic-control-60` | 2 | 60 | 0.830 | 0.833 | $0.905 | 11.6s | 4/180 |
| `anthropic-control-60` | 3 | 60 | 0.843 | 0.850 | $0.913 | 11.5s | 8/180 |
| `gpt-5.6-luna-60` | 1 | 60 | 0.587 | 0.617 | $0.314 | 13.6s | 0/180 |
| `gpt-5.6-luna-60` | 2 | 60 | 0.554 | 0.567 | $0.320 | 14.9s | 0/180 |
| `gpt-5.6-luna-60` | 3 | 60 | 0.548 | 0.567 | $0.319 | 14.1s | 0/180 |

## Calibration — read this before the ranking above

The verdict cutoffs in `core/pipeline.py` (`ADVANCE_CUTOFF = 4.0`, `HOLD_CUTOFF = 1.0`) were swept against **Sonnet's** score distribution. A model that grades on a different scale loses macro-F1 to the mismatch, not to bad judgment. The right-hand columns re-threshold each arm's own recorded scores offline — free, no new calls — and show what it would reach with cutoffs fitted to itself.

| Arm | Mean score | As shipped (4.0/1.0) | Own best cutoffs | Best macro-F1 |
|---|---|---|---|---|
| `anthropic-control-60` | 2.42 | 0.823 | 3.1/0.7 | 0.828 |
| `gpt-5.6-luna-60` | 4.03 | 0.563 | 5.8/2.6 | 0.884 **(+0.321)** |

**These fitted cutoffs are an upper bound, not a result.** They are chosen on the same resumes they are scored against, on a sample of 20 — a smaller corpus than the 60 that `docs/LIMITATIONS.md` already calls overfitted. Read the right-hand column as *"this model is not out of the running"*, never as its accuracy. A model that needs its own cutoffs also needs them re-fitted on a corpus it has not seen before any of it counts.

## How to read this

0. **Calibration before anything else.** See the section above. The cutoffs in `core/pipeline.py` were fitted to one model's score distribution; a model that grades on a different scale is penalised for the scale, not for its judgment.
1. **Parse failures first.** A model that cannot reliably emit JSON is disqualified regardless of its scores — a failed parse scores 0.0, which is indistinguishable from a confident reject. This is what decided the previous bake-off (PLAN.md section 8a).
2. **Then cost and latency.** These are stable across runs and can be compared directly.
3. **Accuracy last, and only against the spread.** If two arms' macro-F1 ranges overlap, the bake-off has not separated them. Say so rather than picking the higher mean.

