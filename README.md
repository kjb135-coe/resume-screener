# Resume Screener

A multi-agent resume screening pipeline, exposed as an MCP server, a web UI, and a CLI over one shared core.

Built as a working prototype of the "talent team reviews every resume by hand, no ATS" problem, using a cascade of models -- a cheap tier triages in bulk, escalation to more expensive tiers is triggered by inter-agent disagreement rather than a flat score cutoff.

The design decisions, and the reasoning and tradeoffs behind each one, are in [PLAN.md](PLAN.md) — including what is deliberately unfinished and why.

## Quickstart

Python 3.11+.

```bash
git clone https://github.com/kjb135-coe/resume-screener.git
cd resume-screener
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The test suite is offline — it never calls an API, needs no key, and costs nothing:

```bash
pytest
```

Everything past this point calls the Anthropic API and costs money:

```bash
cp .env.example .env    # then put your key in it
export ANTHROPIC_API_KEY="sk-ant-..."
```

Write a rubric for a posting (one call, a few cents):

```bash
resume-screener rubric docs/job_description.md
```

Score one resume:

```bash
resume-screener screen data/synthetic_resumes/quiet_builder__elena_vasquez.md docs/job_description.md
```

Rank the whole corpus. This is 60 resumes, roughly $0.90 and a few minutes:

```bash
resume-screener rank data/synthetic_resumes docs/job_description.md --top 10
```

Add `-g` to any of `screen`/`rank` to score against a rubric written from the posting instead of the built-in one.

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
  adapters/     # mcp_server.py, api.py, cli.py -- thin, all call the same core functions
  prompts/      # the hand-written rubric, and the meta-prompt that writes new ones
tests/          # offline, never calls an API
data/synthetic_resumes/   # generated corpus, not real resumes
docs/           # the target posting, eval results, per-candidate reports
```

[STRUCTURE.md](STRUCTURE.md) is a generated map of every file with a one-line description.

## Why MCP

The actual end users here — a talent team with no ATS — shouldn't have to adopt a new app. They should be able to ask the AI client they already have. So the MCP server is the primary interface; the web page is a demo instrument for evaluators, not the production design. Full reasoning in [PLAN.md §2](PLAN.md).

Five tools, one per action: `preview_rubric`, `screen_resume`, `rank_pool`, `explain_verdict`, `query_candidates`. None of them takes a real-world action -- they read and report. That boundary keeps a human on every hiring decision, and it means a prompt injection surviving out of a resume still has nothing to actuate.

## Local models

An Ollama-backed provider exists behind the same `Model` interface used for Anthropic (`core/router.py`) and is tested against a mocked endpoint, but is not wired into the default cascade. The reason is hardware, not code — see [PLAN.md §6](PLAN.md). It is the on-prem / data-residency story rather than a live path.

## Results, and what they're worth

Measured on the 60-resume labeled corpus ([full results](docs/EVAL_RESULTS.md), [per-candidate reasoning](docs/CANDIDATE_REPORTS.md)):

| Metric | Value |
|---|---|
| Macro-F1 | 0.601 |
| Accuracy | 0.633 |
| Cost | $0.93 for 60 resumes ($0.015 each) |
| Latency | p50 33.7s, p95 46.0s |
| Escalated to arbiter | 33/60 |

The number that matters more than the headline: **6 of 60 verdicts change between two identical runs.** A single run therefore cannot support a macro-F1 quoted to three decimals, and cannot tell a 0.03 difference from noise. Giving the eval a variance estimate is the next thing worth doing, and it blocks the architecture comparison below from meaning anything.

Where it actually fails: `hold` recall is 0.20. The system separates strong from weak reliably and identifies the middle badly. That is the honest weakness, and it did not move across runs.

Other things named rather than hidden:

- The three-way bake-off in [PLAN.md §8](PLAN.md) is unfinished. Only the panel-plus-arbiter arm has been measured, so "the cascade beats a single call" is asserted, not shown.
- `docs/LIMITATIONS.md` isn't written yet. The known blind spot — disagreement-based escalation cannot catch a panel that is unanimously and confidently wrong — lives in [PLAN.md §4](PLAN.md) meanwhile.
- Roughly 1 panel call in 180 still loses a score to malformed JSON. Those are flagged for human review, never silently scored zero. [PLAN.md §3b](PLAN.md) has the two parsing bugs that only running against the real API uncovered — including one that was fabricating confident zeros and not flagging them.
