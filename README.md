# Resume Screener

A multi-agent resume screening pipeline, exposed as an MCP server, a web UI, and a CLI over one shared core.

Built as a working prototype of the "talent team reviews every resume by hand, no ATS" problem, using a cascade of models -- a cheap tier triages in bulk, escalation to more expensive tiers is triggered by inter-agent disagreement rather than a flat score cutoff.

## Status

Actively under construction. See `docs/ARCHITECTURE.md` (coming next) for the full design and the reasoning behind each decision.

## The rubric is written, not hardcoded

Give it a job posting and it writes its own scoring standard: three dimensions, each with the criteria the panel scores against and the brief for the agent that owns it. Nothing is pinned to one role.

That matters because the panel is only as good as what it was told to look for. A generic "AI engineer" checklist scores every posting the same way; a rubric derived from the posting can notice that *this* one says "not demos or prototypes" three times and weight production evidence accordingly.

Two rules are enforced rather than left to the model (`core/rubric_gen.py`):

- **Exactly three dimensions.** The escalation threshold is a score spread across a three-agent panel, so a fourth dimension would silently change what disagreement means without changing the threshold.
- **Generation failure raises.** There is no fallback to the built-in rubric — scoring one job's candidates against another job's criteria is worse than a visible error.

Preview it in the browser:

```bash
uvicorn resume_screener.adapters.api:app --reload
```

Paste a posting, read the rubric. That page does not screen resumes; screening a pool is a minutes-long, dollars-scale job that belongs behind the MCP server or `scripts/evaluate.py`.

In Claude Desktop there is nothing to build — the chat *is* the input. Paste the posting, call `preview_rubric`, read the rubric, then hand its `rubric_id` to `rank_pool` so the pool is scored against the rubric you actually approved. Generation isn't deterministic, which is exactly why the id exists.

`scripts/evaluate.py` deliberately keeps using the hand-written rubric in `prompts/rubric.md`, so the published metrics stay comparable across runs.

## Layout

```
src/resume_screener/
  core/         # ingest, the tiered cascade, rubric generation, models, the model-provider router
  adapters/     # mcp_server.py, api.py -- thin, all call the same core functions
  prompts/      # the hand-written rubric, and the meta-prompt that writes new ones
tests/
data/synthetic_resumes/   # generated corpus, not real resumes
```

## Why MCP

See `docs/ARCHITECTURE.md` for the full reasoning. Short version: the actual end users here (a talent team with no ATS) shouldn't have to adopt a new app -- they should be able to ask their existing AI client to do this. The MCP server is the primary interface; the web UI is a demo instrument for evaluators, not the production design.

Five tools, one per action: `preview_rubric`, `screen_resume`, `rank_pool`, `explain_verdict`, `query_candidates`. None of them takes a real-world action -- they read and report. That boundary keeps a human on every hiring decision, and it means a prompt injection surviving out of a resume still has nothing to actuate.

## Local models

An Ollama-backed provider exists behind the same `Model` interface used for Anthropic (`core/router.py`) and is tested against a mocked endpoint, but is not wired into the default cascade. See `docs/ARCHITECTURE.md` for why (hardware, not code).
