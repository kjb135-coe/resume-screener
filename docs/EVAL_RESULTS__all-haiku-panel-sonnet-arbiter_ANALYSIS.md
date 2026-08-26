# Comparison run — all-Haiku panel, Sonnet arbiter

Requested as a cost experiment: what if `triage` and `panel` both ran on
Haiku, keeping only the arbiter on Sonnet? Run with:

```
python scripts/evaluate.py \
  --triage-model claude-haiku-4-5-20251001 \
  --panel-model claude-haiku-4-5-20251001 \
  --arbiter-model claude-sonnet-5 \
  --tag all-haiku-panel-sonnet-arbiter
```

Full metrics in [EVAL_RESULTS__all-haiku-panel-sonnet-arbiter.md](EVAL_RESULTS__all-haiku-panel-sonnet-arbiter.md)
and [../data/eval_run__all-haiku-panel-sonnet-arbiter.json](../data/eval_run__all-haiku-panel-sonnet-arbiter.json).
Does not touch the baseline files — see the header comment in
`scripts/evaluate.py` for why a non-`baseline` tag writes elsewhere.

## Headline

| | Baseline (Sonnet panel) | All-Haiku panel |
|---|---|---|
| macro-F1 | **0.847** | 0.516 |
| accuracy | 0.850 | 0.533 |
| cost | $1.796 | $1.286 (28% cheaper) |
| escalation rate | 47% | 38% |

Cheaper, and not close to worth it.

## The actual cause, not just the number

**88 of 180 Haiku panel calls (49%) returned text that was not parseable
JSON at all** — not a missing field, not a truncated brace the repair
logic could recover, just prose that didn't match the requested shape.
Sonnet's rate on the same prompt is 4/180 (2.2%).

Every one of those 88 defaults to a flagged 0.0, per the parse-failure
contract in `pipeline.py`. A representative case:

```
academic_researcher__devon_whitaker.md
  production_reality       score=0.0  parse_failed=True
  technical_integration    score=0.0  parse_failed=True
  client_communication     score=2.0  parse_failed=False
```

Two of three judgments on this candidate are fabricated zeros, not
opinions. The final score is an average that is two-thirds noise.

This is not "Haiku is a worse judge." It never got the chance to judge on
half its calls — it did not reliably produce the JSON the pipeline asked
for. That is an instruction-following gap, not a reasoning gap, and it is
the entire explanation for the collapse. `hold` recall falling to 0.25 and
`advance` recall to 0.60 both follow mechanically from roughly half the
inputs to the average being garbage.

## The safety net worked, and that is also the bad news

`_review_reason` flags a verdict when any panel call parse-failed,
independent of escalation. On this run that catches **59 of 60
candidates**. Nothing here reached a decision without a review flag.

But 59/60 flagged is not a working automation pipeline — it is manual
review with extra steps. The entire cost argument for this system is that
a human should only need to look at the disputed cases. An all-Haiku
panel makes every case a disputed case, at which point the 28% API
saving is irrelevant next to the labor cost of a human re-reading every
resume anyway.

## Conclusion

**Not adopting this.** Haiku is not a viable panel model for this task at
the current prompt. If a cheaper panel is worth revisiting later, the
JSON-reliability gap would need to be closed first — likely structured
output / tool-use enforcement rather than a "respond as JSON" instruction
in prose, which is the same durable fix already on the list for the
parsing issues in `PLAN.md` section 3b.
