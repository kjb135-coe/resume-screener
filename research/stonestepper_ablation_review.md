# Review of the StoneStepper ablation study, and what it should change here

Source: `stonestepper/docs/experiment-ablation-sensitivity.md` and its
`experiments/sensitivity_ablation/` implementation (a 3-class email
sensitivity classifier: normal/personal/confidential). Different domain,
directly transferable methodology. This is more rigorous than what we'd
sketched — several things below are corrections, not just additions.

## What it actually does

One variable changes per run against a fixed baseline (Sonnet, temp 0,
single call, direct prompt, no embedding). 19 runs total, each scored
against the same held-out 50 labeled examples, ranked by macro F1. It
separately tests: model choice, temperature, self-consistency (call the
same prompt N times, check if it agrees with itself), logprob-based
confidence, embedding k-NN classification against a labeled exemplar
library, three prompt phrasings (direct / chain-of-thought / structured
rules), and confidence-threshold sweeps that decide when to **defer**
an example to a human instead of forcing a label.

## Directly adopt, no disagreement

- **Coverage and accuracy reported separately, not blended.** Every run
  reports macro F1 *on the classified subset* plus a separate coverage
  and deferral rate. This is the exact instrumentation our human-review
  question needed and didn't have: report accuracy on auto-scored
  candidates, and deferral rate (= our `needs_human_review` rate),
  as two different numbers, not one blended figure.
- **A trivial baseline as the floor.** `run_00` is a keyword-only,
  non-LLM classifier, kept explicitly as a lower bound with an honest
  caveat that it's not a perfectly fair comparison. We should have the
  equivalent: a pure keyword/skills-match screener with no LLM at all,
  so the cascade has to earn its complexity against something, not just
  against itself.
- **`delta_vs_baseline` as a column, not generated prose.** Their
  report.py explicitly avoids "fragile string generation" — every run's
  row just shows its macro F1 delta from the baseline run. Adopting this
  directly for our own eventual report.
- **Run order: cheap and high-expected-impact first.** Prompt variants
  before model swaps before temperature before self-consistency before
  embedding sweeps before threshold sweeps. Cheaper to test first, and
  answers the highest-leverage question earliest. Better sequencing
  logic than what we had; adopting it over our own draft ordering.
- **A cost estimate table before running anything.** 19 runs x 50
  examples costed out to ~$1.05 up front. We should do the same before
  committing to a run plan — see open question below on scope.

## Corrections to what we'd already decided

**1. Our panel doesn't test what we implied it tests.** StoneStepper
cleanly separates two different sources of disagreement that we'd
conflated: *self-consistency* (same prompt, called twice, does it agree
with itself — measures model noise) versus *prompt/persona variation*
(different framings of the same question — measures perspective
difference). Our 3-persona panel only measures the second. We've been
treating cross-persona disagreement as if it were pure signal about
genuine ambiguity, but if a single persona wouldn't even agree with
itself at temp 0 across repeated calls, some of what we're attributing
to "the panel disagreed" could just be sampling noise, not real
judgment conflict. **Action:** before trusting the disagreement
threshold at all, run a self-consistency check — call one persona twice
at temp 0 on the same candidate — as a control. If that ever disagrees
with itself, the panel's disagreement signal is partly confounded by
noise, not perspective, and needs a fix before we calibrate anything
against it.

**2. We never set temperature at all.** `core/router.py`'s
`AnthropicModel.complete()` doesn't pass a `temperature` parameter,
meaning every call rides the API's default rather than a deliberate
choice. StoneStepper's baseline is temp 0 specifically because
classification tasks want determinism, not creative sampling — a
resume score should be reproducible, not a matter of what the sampler
rolled. This is a real gap, not a style preference; fixing it now.

**3. Our recommendation thresholds are exactly as arbitrary as the
disagreement threshold we already flagged.** `_recommendation_from_score`
hard-codes score >= 7 as advance and >= 5 as hold. That's the same kind
of hand-picked constant we already called out `DISAGREEMENT_THRESHOLD
= 2.0` for. Once the labeled corpus exists, both cutoffs should be
calibrated against it the same way, not treated differently just
because one was flagged first.

**4. Embedding model choice — reconciling with the earlier decision.**
Two turns ago I recommended `nomic-embed-text` for the pre-filter.
StoneStepper already uses and presumably validated `all-MiniLM-L6-v2`
(sentence-transformers, ~80MB) for exactly this kind of semantic
similarity task. Matching an already-proven choice from a sibling
project has real value — same library, same tooling already understood
— over introducing a second embedding model with no track record here.
**Changing the recommendation to `all-MiniLM-L6-v2`.**

**5. A genuinely new idea worth adding as a 6th architecture candidate:
embedding k-NN as a standalone scorer, not just a pre-filter.**
StoneStepper's embedding runs aren't a pre-filter — they classify
directly via k-nearest-neighbor vote against a labeled exemplar
library, with library size (10/25/50/100) as its own swept variable.
We're already building a labeled synthetic corpus with ground-truth
recommendations. That corpus can double as an exemplar library: embed
each new resume, find its k nearest labeled examples, vote. If that
alone gets close to the LLM cascade's accuracy at near-zero cost, it
changes the whole cost conversation. This wasn't on the original list
of five alternatives — adding it now.

**6. Our JSON parsing is fragile in a way StoneStepper's isn't.**
`classifier.py` retries once on parse failure and falls back to an
explicit `deferred` state. Our `_parse_json` in `pipeline.py` just does
`json.loads` and direct key access (`data["score"]`) — a missing key
throws, uncaught. Given `pydantic` is already a dependency, LLM JSON
outputs should be validated against a schema with a defined fallback,
not accessed raw. Flagging as a needed fix, not yet made.

**7. Prompt variant as its own testable axis.** We only wrote one
prompt style (direct instructions). StoneStepper tests direct vs.
chain-of-thought vs. structured deterministic rules as a first-class
variable, and prioritizes it as one of the cheapest, highest-expected-
impact tests to run early. We should do the same for the rubric prompt,
not just for the architecture choice.

## What this changes about our testing plan, concretely

Updated axis list (was 5 candidate architectures; now expanded):

1. Self-consistency control (new, run first — a correctness check, not
   a competing architecture)
2. Keyword-only floor baseline (new, matches `run_00`'s role)
3. Prompt variant: direct vs. chain-of-thought vs. structured rules
   (new axis, cheap to test)
4. Temperature (need to actually pick one deliberately — defaulting to
   0 and treating anything else as a swept variable, not an oversight)
5. The five original architecture candidates, now six: single-pass,
   flat ensemble, embedding pre-filter, whole-batch long-context,
   panel+arbiter, and embedding k-NN-as-scorer (new, from item 5 above)
6. Disagreement/escalation trigger design (simple threshold vs. the
   three-signal design), calibrated against the corpus once it exists
7. Score-to-recommendation cutoffs, calibrated the same way as (6)
   rather than treated as separately fixed

Not deciding the final combination here — flagging that the honest
scope grew from the last conversation, and a cost estimate for the
full run plan (StoneStepper-style) should happen before committing to
running all of it.
