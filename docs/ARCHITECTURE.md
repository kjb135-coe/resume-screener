# Architecture

Why this is shaped the way it is. `STRUCTURE.md` says where files live;
this says why they are arranged that way, and what each decision cost.

## The shape

```
JOB POSTING
    │
    └─► [1] RUBRIC AGENT · Opus 5 · ONCE PER BATCH
             │   Writes 3 dimensions + one persona brief each.
             │   ⚠ Skipped when using the built-in rubric — which is
             │     what every eval run does, so this stage is UNTESTED.
             ▼
        RUBRIC + JOB DESCRIPTION
             │   Becomes the cached system block. Byte-identical for
             │   every call below. Written to cache once per batch.
             │
════════════ per resume, from here down ════════════
             │
RESUME ──► [2] EXTRACT AGENT · Haiku 4.5 · 1 call
             │   → {evidence:[{quote, dimension}], confidence}
             │
             ├── no evidence at all? ──► FLAG for human review
             ▼
        EVIDENCE JSON   (replaces the resume downstream)
             │
             ▼      [3] SCORING · GPT-5.6 Luna · ONE call
      ┌──────────────────────────────────┐
      │ production_reality      score 0-10│
      │ technical_integration   score 0-10│
      │ client_communication    score 0-10│
      └──────┬───────────────────────────┘
             │
      any unreadable reply? ──► FLAG for human review
             │
             ▼
      SCORE = mean of the three
             │
      ┌──────┴───────────────────────────────┐
      │ is the mean within 0.5 of a cutoff?  │
      │ (NOT panel disagreement -- one       │
      │  response cannot disagree with itself)│
      └──────┬───────────────────────────────┘
        NO   │         │  YES
             │         ▼
             │   [4] ARBITER · GPT-5.6 Luna · 1 call
             │     Reads the 3 rationales. Never sees the resume.
             │     Returns a SCORE, never a verdict.
             │         │
             └────┬────┘
                  ▼
        recommendation_from_score(score, model's own cutoffs)
                  │
                  ├── within 12.5% of a band from a cutoff?
                  │        └──► FLAG for human review
                  ▼
            ADVANCE / HOLD / REJECT
```

## The decisions, and what each one cost

### Three dimensions, one call — and why it used to be three calls

The system scores three dimensions and shows three rationales. It used to
compute them with **three parallel agents that never saw each other**, on
the premise that independent judgments beat one model judging all three
together.

**That premise was measured and it was wrong.** Three ways:

| | macro-F1 |
|---|---|
| Parallel panel alone | 0.788 |
| One call alone | 0.821 |
| Parallel panel + arbiter | 0.872 |
| **One call + arbiter** | **0.899** |

The panel-only arm *loses* to a single call, paired 12–6 per candidate.
The full cascade ties a single call, because the arbiter's gain cancels
the panel's loss. And one call plus an arbiter beats the cascade at half
the API calls.

So the architecture kept the stage that earned its keep — the second look
at a borderline case — and dropped the one that did not. Nothing
user-facing changed: both paths return three per-dimension scores with a
quoted rationale each.

`screen_one_cascade` is still there, because every recorded result before
2026-08-31 used it and those numbers have to stay reproducible.

**Three is still enforced in code.** `core/rubric_gen.py` rejects any
rubric that is not exactly three dimensions.

### `core/` never imports `adapters/`

The MCP server, CLI and web app are thin shells over the same core. The
claim "swapping providers is a base_url change, not an architecture
change" only holds if nothing in `core/` imports a provider SDK directly.
`core/router.py` is the only place that touches one.

That claim has been cashed: adding OpenAI took one adapter class
(`OpenAICompatibleModel`) and no changes to the cascade.

### The caching contract is load-bearing

The system block on every panel call is exactly `rubric + job_description`
and nothing else. It is byte-identical across all three personas and every
resume in a batch, so one cache write serves the whole run. Personas and
evidence go in the *user* turn.

Moving a persona into the system string would silently create one cache
entry per persona and gut the saving. `core/pipeline.py`'s module
docstring says so, and a test pins it.

### Extraction does not pay for itself

Sending extracted evidence instead of the full resume saves 365 input
tokens per panel call (11.9%), worth ~$0.13 across a 60-resume run.
Extraction itself costs ~$0.24. **Net loss of about $0.11 per run.**

It is kept for grounding — every score cites a verbatim quote — and for
giving all three agents one shared evidence base. It is a quality
decision, not a cost optimisation, and `docs/COST_ANALYSIS.md` says so.
On real multi-page PDFs the saving grows and this may flip.

### One place owns the verdict

`recommendation_from_score` is the only function that turns a score into
`advance`/`hold`/`reject`. The arbiter returns a **score**, never a
recommendation. Before that rule, an escalated 6.5 could be `advance`
because the arbiter said so while an unescalated 6.5 was `hold` — the
same score getting different answers depending on whether the panel
happened to split.

### Cutoffs belong to the model, not the pipeline

`ADVANCE_CUTOFF = 4.0` / `HOLD_CUTOFF = 1.0` were swept against *Sonnet's*
score distribution. Judging another model with them measures whether it
shares Sonnet's calibration, not whether it judges well.

GPT-5.6 Luna scored **0.563** under the global pair and **0.884** under
cutoffs fitted to its own scale — the model untouched. `MODEL_CUTOFFS` in
`core/cutoffs.py` now holds one pair per model, and any unlisted model
falls back to the default, which is honest rather than safe: it is being
judged on someone else's scale until it is fitted.

### Escalation and human review are separate decisions

They used to be one, and it was wrong in both directions.

- **The arbiter only changes a verdict by crossing a cutoff.** It moves a
  score off the panel mean by a median of 0.33 and never more than 1.50,
  so a mean sitting further away is a call it cannot win. 92% of
  escalations returned a different number and the same verdict.
- **Panel disagreement barely predicts a wrong answer.** The old flag
  queued 53% of the stack and caught 36% of errors; a near-cutoff test at
  the same queue size catches 82%.

Now the arbiter fires on the **panel mean** being near a cutoff, and a
human is asked when the **final score** is near one. Different quantities,
separate margins — and the review margin is a *fraction of the model's own
band*, because a flat margin queued 43% of Sonnet's stack and 15% of
Luna's.

### Two providers in production

The panel and arbiter run on GPT-5.6 Luna; extraction stays on Haiku.
**That means a deployment needs both `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY`**, and two spend caps rather than one. The split is
deliberate — it isolates the scoring comparison from extraction quality —
but it is a real operational cost and is not free.

## What is deliberately not here

- **No database of record.** DuckDB is used for sandboxed follow-up
  queries over one session's candidates, not as storage.
- **No vector search or embeddings.** 60 resumes against one posting does
  not need retrieval, and adding it would be resume-driven design.
- **No local model in the default path.** `OllamaModel` exists and is
  tested against a mocked endpoint, but is not wired in — a hardware
  limit, not a code one.
- **`core/enrichment.py` is an intentionally unimplemented extension
  point** for consuming external MCP servers.

## Where to go deeper

`docs/METRIC_CHOICE.md` (why macro-F1) · `docs/VARIANCE.md` (the noise
floor) · `docs/CUTOFF_FIT.md` (per-model calibration) ·
`docs/LIMITATIONS.md` (what none of it proves)
