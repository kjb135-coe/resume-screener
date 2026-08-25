# Measuring cost and latency for real, not asserting it

## Prompt caching — the actual mechanics and numbers (2026 pricing)

- **Cache read**: 0.1x base input token price — a 90% discount.
- **Cache write**: 1.25x base price for a 5-minute TTL, 2x base price
  for a 1-hour TTL.
- **Breakeven**: the 1-hour cache is only worth the extra write cost if
  you get more than 5-7 reads out of it before it would've expired anyway.
- Worked example at $3/M input tokens (Sonnet-class): write once, read
  10 times within a 5-minute window -> effective cost
  `(3.75 + 9 x 0.30) / 10 = $0.645` per million tokens — a 78.5% reduction
  from the $3 base rate for that batch.

For us: the rubric + job description is the shared prefix, re-read on
every Tier 1 panel call and every Tier 2 arbiter call. A `rank_pool` run
over N resumes writes the cache once and reads it `3N` times (3 panel
agents per resume) plus once per escalation. That's exactly the
many-reads-per-write shape caching is built for.

## How to measure it for real, not estimate it

Don't trust a theoretical percentage — the Anthropic API returns exact
token accounting on every response (`usage.input_tokens`,
`usage.cache_creation_input_tokens`, `usage.cache_read_input_tokens`).
The methodology:

1. Run the same batch of N resumes twice against the same job
   description: once with `cache_control` on the rubric prefix, once
   without.
2. Sum the actual `usage` fields from every response in both runs.
3. Compute real $ cost from the summed tokens at each tier's real
   per-token price, not an assumed batch-average.
4. Report the measured delta as a table in the README, not a claimed
   percentage — this is the "exactly how much you're able to save"
   number, and it should come from a logged run over the synthetic
   corpus, not a calculation done in the abstract.

This needs `core/pipeline.py` to log every `usage` object per call
(not implemented yet) before it can produce a real number — flagging
as a needed addition, not done.

## Latency methodology

- Wall-clock per resume, per tier, and end-to-end for a full `rank_pool`
  batch — captured with a timer around each `model.complete()` call, not
  inferred from token counts.
- Report p50/p95 across the batch, not just an average — a batch's tail
  latency (the slowest few resumes) is what a recruiter actually
  perceives as "is this fast," not the mean.
- Compare against the same batch run with no cascade at all (every
  resume forced through all 3 tiers) to isolate exactly how much the
  disagreement-based escalation saves versus a flat pipeline.

## What the actual test needs (not built yet)

A run script that: takes the labeled synthetic corpus + one job
description, runs it under N configurations (see
`cascade_architecture_research.md` for the candidate list), logs
`usage` and wall-clock per call, and outputs one comparison table:
accuracy against ground-truth labels, cost per resume, p50/p95 latency,
per configuration. This is the actual deliverable that turns "we
optimized cost and latency" from a claim into a result.
