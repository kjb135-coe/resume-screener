# Resume Screener

A multi-agent resume screening pipeline, exposed as an MCP server, a web UI, and a CLI over one shared core.

Built as a working prototype of the "talent team reviews every resume by hand, no ATS" problem, using a cascade of models -- a cheap tier triages in bulk, escalation to more expensive tiers is triggered by inter-agent disagreement rather than a flat score cutoff.

## Status

Actively under construction. See `docs/ARCHITECTURE.md` (coming next) for the full design and the reasoning behind each decision.

## Layout

```
src/resume_screener/
  core/         # ingest, the tiered cascade, models, the model-provider router -- no adapter knows about this file's internals
  adapters/     # mcp_server.py, api.py, cli.py -- thin, all call the same core functions
  prompts/      # the shared scoring rubric (cached across every call)
tests/
data/synthetic_resumes/   # generated corpus, not real resumes
```

## Why MCP

See `docs/ARCHITECTURE.md` for the full reasoning. Short version: the actual end users here (a talent team with no ATS) shouldn't have to adopt a new app -- they should be able to ask their existing AI client to do this. The MCP server is the primary interface; the web UI is a demo instrument for evaluators, not the production design.

## Local models

An Ollama-backed provider exists behind the same `Model` interface used for Anthropic (`core/router.py`) and is tested against a mocked endpoint, but is not wired into the default cascade. See `docs/ARCHITECTURE.md` for why (hardware, not code).
