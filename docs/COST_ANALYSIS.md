# Cost and caching analysis

Measured 2026-08-27, against the recorded 60-resume run in
`data/eval_run.json`. Rates verified the same day against
[the published pricing page](https://platform.claude.com/docs/en/about-claude/pricing).

## The headline: two of three prices were wrong

`scripts/evaluate.py` priced every run from a hardcoded table. Two rows
carried rates from older models:

| Model | Table had | Actual | Error |
|---|---|---|---|
| `claude-sonnet-5` | $3 / $15 / $0.30 | **$2 / $10 / $0.20** | Sonnet 4.6's rates, 50% high |
| `claude-opus-5` | $15 / $75 / $1.50 | **$5 / $25 / $0.50** | Opus 4.1's rates, 3x high |
| `claude-haiku-4-5` | $1 / $5 / $0.10 | $1 / $5 / $0.10 | correct |

Sonnet runs the panel and the arbiter, so it carries most of the spend.
The recorded run reported **$1.796**; the same measured token counts at
correct rates come to roughly **$1.20**, about **2 cents per resume**
rather than 3.

**That $1.20 is re-derived, not measured.** The run predates
`cost_by_model`, so its per-model token split was never saved. The
estimate splits Sonnet from Haiku output by measuring the stored
rationale text, which brackets the answer at $1.15-$1.24. The next full
run will report the exact figure directly. Treat $1.20 as "about right,
pending a re-run" and do not quote it to the cent.

## Where the money actually goes

Priced at the correct rates:

| Line | Tokens | Share of cost |
|---|---|---|
| **Output** | 104,090 | **~69%** |
| Uncached input | 196,805 | ~25% |
| **Cache reads** | 420,992 | **~6%** |

Output dominates, by a lot. This is the number that matters for any
future optimization work, and it is the one caching cannot touch.

## Prompt caching: already working, and nearly maxed out

Measured directly against the live API with the real panel prefix:

```
panel prefix: 6239 chars
cold call:  input=13  cache_create=2024  cache_read=0
warm call:  input=13  cache_create=0     cache_read=2024
```

The caching contract documented in `core/pipeline.py` does what it
claims. The cacheable prefix is **2,024 tokens**, comfortably over
Sonnet 5's 1,024-token minimum.

But 2,024 tokens is a small prefix, and cache reads bill at 0.1x. The
entire caching mechanism is worth about **6% of the run**. Perfect
caching from here saves single-digit cents. **Caching is not where the
remaining savings are** — it is already solved, and it was never the
big lever for this workload.

### `cache_write: 0` is not a bug

`eval_run.json` records 420,992 cache reads against zero cache writes,
which looks impossible. It isn't: **cache reads refresh the TTL**. A
continuous run with six resumes in flight writes the prefix once and
then refreshes it indefinitely. That run inherited a warm cache from an
earlier process, so every write fell outside the measured window.

The practical consequence: the recorded cost slightly *understates* the
write side, and heavily *overstates* the rate side. Net, it is still too
high.

### Do not switch to the 1-hour TTL

A 1-hour TTL costs 2x base on write instead of 1.25x. It pays for itself
only across gaps in bursty traffic. This workload is a continuous batch
whose own reads keep the 5-minute window alive, so the longer TTL would
double the write cost and buy nothing.

### Extraction caching is a no-op

`extract_candidate` passes `cache_system=True`, but Haiku 4.5's minimum
cacheable prefix is **4,096 tokens** and the extraction system prompt is
far shorter. The marker is silently ignored — no error, no write, no
saving. Harmless, but it is decorative rather than load-bearing, and
worth knowing before anyone "optimizes" it.

## What would actually reduce cost

In order of size, none of it built:

1. **Batch API — roughly 50% off, and the natural fit.** Batch rates are
   half of standard on both input and output (Sonnet 5: $1/$5 instead of
   $2/$10), and caching multipliers still stack. The eval is an offline
   job over a fixed corpus with no latency requirement, which is exactly
   the case Batch exists for. This is the single largest available win
   and it changes no behaviour, only latency.
2. **Cut output tokens — 69% of the bill.** Two routes: set
   `output_config: {effort: "low"|"medium"}` on the panel calls, since
   scoring one dimension against a stated rubric is a bounded judgment
   rather than deep reasoning; and stop asking for reasoning the UI then
   truncates to two bullets anyway. Both need an eval run to confirm
   they do not cost accuracy.
3. **Leave caching alone.** It works, it is 6% of cost, and the contract
   is already documented and protected by the module docstring.

Combining 1 and 2 would plausibly take a 60-resume run from ~$1.20 to
~$0.50. Further caching work would save perhaps five cents.
