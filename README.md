# Resume Screener

An agent that reads a stack of resumes against a specific job posting, ranks them, and tells you which ones a human should look at first.

Built for the problem of a talent team reading every resume by hand with no ATS. It is not a filter that rejects people quietly. Every verdict comes with the evidence behind it, and anything the system isn't confident about gets handed back to a person rather than decided.

![Submit a posting, see the criteria it wrote, then the ranked results](docs/img/candidates.png)

Submit a posting, and the whole flow runs top to bottom:

1. **Paste a job posting.** Any posting, not just this one.
2. **It writes three scoring criteria from that posting**, each with the brief for the agent that owns it.
3. **Resumes get screened against those criteria**, ranked, with the reasoning behind every score.

The screenshot shows 60 test resumes screened for **$0.93 total**, about a cent and a half each. 14 advance, 10 hold, 36 reject, and **33 flagged for a human**.

```bash
uvicorn resume_screener.adapters.api:app --reload
```

The page opens on the bundled posting and a run that already happened, so there is something real to look at before spending anything. Submit a different posting and it does a live run over a 12-resume sample, about $0.19 and under a minute, with a progress bar. Identical postings are served from cache rather than re-billed, and **Criteria only** writes the criteria without screening, for a few cents.

### Reasoning you can check

Each agent's verdict shows as **two bullets, no more**, and every quote it relied on is traced back to the section of the resume it came from. The section chips are clickable: they open that candidate's resume and highlight the exact line.

The first question anyone asks about AI-written feedback is whether it actually read this resume or is producing plausible boilerplate. A citation that resolves to `§ Experience` and jumps to the sentence answers that in one click. A quote the system cannot find verbatim in the resume gets **no citation at all**, rather than a confident-looking label — an unlocatable quote means the model paraphrased, and dressing that up would defeat the point. Across the recorded run that leaves 100% of candidates with at least one grounded citation and about 6 highlighted lines each.

## How it works

Each resume goes through three stages, and the expensive stage usually doesn't run.

```
  Resume
    │
    ▼
  Extract        cheap model pulls out quoted evidence
    │
    ▼
  Panel          3 agents score in parallel, one per dimension
    │            8.0        9.0        6.0
    │
    ▼
  Do they agree?
    │
    ├── yes ──▶  average the scores            (45% of candidates)
    │
    └── no  ──▶  arbiter reads all three       (55% of candidates)
                 rationales and rules
                          │
                          ▼
              ≥7 advance · ≥5 hold · else reject
```

Escalation is triggered by the panel disagreeing with each other, not by a score being near a cutoff. A candidate everyone agrees is strong costs three cheap calls. A candidate the panel splits on gets the expensive model, and gets flagged for a person.

### Why three agents

The count came from the posting, not from an experiment. This job description has three distinct requirement clusters, so there's one agent per cluster:

| Agent | What it judges |
|---|---|
| `production_reality` | Shipped and running, or a demo that stopped at the prototype? The posting says "not demos or prototypes" three separate times. |
| `technical_integration` | Real agentic work with memory, tools, and orchestration, or a skills list? |
| `client_communication` | Evidence of explaining technical work to non-technical people. |

Three also happens to be the smallest number that makes disagreement *readable*. With one agent there's no disagreement signal at all. With two you learn they differ but not which one is the outlier. With three you get a spread and a majority, so "two agreed, one dissented" is something you can act on. Each agent is another API call per resume, so cost scales with the count.

It's now load-bearing: the escalation threshold is a spread across three scores, and more agents would widen that spread by chance alone and silently escalate more often. `core/rubric_gen.py` rejects any rubric that isn't exactly three.

**Honest caveat:** the count was never tested. Two versus three versus five is still an open question in [PLAN.md §8](PLAN.md), and the "be skeptical of unbacked claims" instinct was folded into all three agents rather than made a fourth agent specifically to avoid prejudging it.

## The rubric is written from the posting, not hardcoded

Hand a job posting in and the system writes its own scoring standard first: three dimensions, each with the criteria the panel scores against and the brief for the agent that owns it.

This matters because a panel is only as good as what it was told to look for. A generic "AI engineer" checklist scores every posting identically. A rubric derived from *this* posting notices what this posting actually repeats.

To check it wasn't just pattern-matching to engineering roles, I ran it against a charge-nurse posting for a hospital emergency department. It produced dimensions on ACLS/PALS/TNCC certification, charge authority on an unsupervised night shift, and Joint Commission documentation compliance. Nothing leaked through from the engineering version. It also picked up the posting's "we are not looking for" section and treated outpatient-only experience as a negative signal rather than a neutral one.

Two rules are enforced in code rather than trusted to the model:

- **Exactly three dimensions**, for the reason above.
- **Generation failure raises.** There is no silent fallback to the built-in rubric. Scoring one job's candidates against a different job's criteria is a wrong answer that looks like a right one.

### What keeps the demo honest

A run against any posting other than the bundled one **reports no accuracy figure at all**. The labels in `data/labels.json` describe exactly one job. Screening these same resumes against a payments or nursing posting produces perfectly correct verdicts that those labels say nothing about, and grading them against the wrong answer key would publish a made-up number as if it meant something.

Expect most candidates to score near zero there. The corpus is 60 AI-engineer resumes, and rejecting them for a payments role is the system working, not failing.

A live run is capped at 24 resumes. That is a spending limit, not a technical one.

## Why MCP

A talent team with no ATS shouldn't have to adopt a new app. They should be able to ask the AI client they already have.

So this is an MCP server first. In Claude Desktop there is nothing to install and no UI to learn: paste the posting into the chat, ask it to rank a folder. The web page exists to look at results, not as the product.

Five tools, one per action: `preview_rubric`, `screen_resume`, `rank_pool`, `explain_verdict`, `query_candidates`.

**None of them takes a real-world action.** They read and report. Nothing can reject a candidate, send mail, or write to a system of record. That keeps a human on every hiring decision, and it means a prompt injection that survives out of a resume still has nothing to actuate.

`preview_rubric` returns a `rubric_id` that `rank_pool` accepts, so the rubric a person reads and approves is the one that scores the pool. Generation isn't deterministic, which is exactly why that id exists.

## Results, and what they're worth

Measured on 60 labeled synthetic resumes ([full results](docs/EVAL_RESULTS.md), [every candidate's reasoning](docs/CANDIDATE_REPORTS.md)):

| Metric | Value |
|---|---|
| Macro-F1 | 0.601 |
| Accuracy | 0.633 |
| Cost | $0.93 for 60 ($0.015 each) |
| Latency | p50 33.7s, p95 46.0s |
| Flagged for a human | 33 / 60 |

**The number that matters more than the headline: 6 of 60 verdicts change between two identical runs.** A single run can't support a macro-F1 quoted to three decimals, and can't tell a 0.03 difference from noise. Giving the eval a variance estimate is the next thing worth doing, and until it exists the architecture comparison below can't mean much.

**Where it actually fails:** `hold` recall is 0.20. It separates strong from weak reliably and identifies the middle badly. That did not move across runs, so it's real rather than noise.

### The failure has a shape

The 60 resumes are generated from nine **archetypes** — candidate types with a target verdict and a target level on each dimension, assigned at generation time. That is where the ground-truth labels come from, and it is what makes the failure legible:

| Archetype | Label | Correct |
|---|---|---|
| `production_generalist` · `academic_researcher` · `keyword_stuffer` · `wrong_domain` | advance / reject | **100%** |
| `adjacent_shipper` | advance | 67% |
| `demo_specialist` · `quiet_builder` | hold / advance | 43% |
| `early_career` | hold | 17% |
| `production_light_ai` | hold | **0%** (0 of 7) |

Perfect on every unambiguous archetype, and progressively worse the more a candidate sits in the middle. `production_light_ai` — a real production engineer whose AI work is shallow — is rejected every single time.

Two facts point at the same cause: **all 22 mismatches run in one direction**, the model scoring below the label, and the archetype it fails hardest on is the one strong on production but light on AI depth. The panel over-weights AI depth, and the 7.0/5.0 cutoffs are too harsh. That is a calibration problem with a known fix ([PLAN.md §8](PLAN.md) items 5 and 6, both unrun), not a mystery.

Having nine archetypes rather than one generic "bad resume" template is what makes that diagnosis possible. All three reject types fail for different reasons — shipped nothing, evidenced nothing, wrong field — so a screener cannot pass by pattern-matching. [docs/corpus_design.md](docs/corpus_design.md) has the full specs.

Other things named rather than hidden:

- The three-way architecture bake-off in [PLAN.md §8](PLAN.md) is unfinished. Only this design has been measured, so "the cascade beats one big call" is asserted, not shown.
- `docs/LIMITATIONS.md` isn't written yet. The known blind spot, that disagreement-based escalation can't catch a panel which is unanimously and confidently wrong, is in [PLAN.md §4](PLAN.md) meanwhile.
- Roughly 1 panel call in 180 still loses its score to malformed JSON. Those get flagged for review, never silently scored zero. [PLAN.md §3b](PLAN.md) has the two parsing bugs that only appeared once this ran against the real API, including one that was fabricating confident zeros and not flagging them.

The design decisions and their tradeoffs are in [PLAN.md](PLAN.md), including what's deliberately unfinished and why.

## Quickstart

Python 3.11+.

```bash
git clone https://github.com/kjb135-coe/resume-screener.git
cd resume-screener
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The test suite is offline. It never calls an API, needs no key, and costs nothing:

```bash
pytest
```

Look at the recorded run in a browser. No API key needed, since it reads results from disk:

```bash
uvicorn resume_screener.adapters.api:app --reload
```

Everything past this point calls the Anthropic API and costs money:

```bash
cp .env.example .env    # then put your key in it
```

Write a rubric for any posting (one call, a few cents):

```bash
resume-screener rubric docs/job_description.md
```

Score one resume:

```bash
resume-screener screen data/synthetic_resumes/quiet_builder__elena_vasquez.md docs/job_description.md
```

Rank the whole corpus. 60 resumes, roughly $0.93 and a few minutes:

```bash
resume-screener rank data/synthetic_resumes docs/job_description.md --top 10
```

Add `-g` to `screen` or `rank` to score against a rubric written from the posting instead of the built-in one.

## Layout

```
src/resume_screener/
  core/         # ingest, the cascade, rubric generation, models, the provider router
  adapters/     # mcp_server.py, api.py, cli.py -- thin, all call the same core
  prompts/      # the hand-written rubric, and the meta-prompt that writes new ones
tests/          # offline, never calls an API
data/synthetic_resumes/   # generated corpus, no real candidates
docs/           # the target posting, eval results, per-candidate reports
```

`core/` never imports from `adapters/`. That one-way dependency is what lets the MCP server, the CLI, and the web API stay thin and share behaviour. [STRUCTURE.md](STRUCTURE.md) maps every file with a one-line description.

The 60 resumes are generated, not real. [docs/corpus_design.md](docs/corpus_design.md) covers the archetypes and how ground-truth labels were assigned.

## Local models

An Ollama provider sits behind the same `Model` interface as Anthropic (`core/router.py`) and is tested against a mocked endpoint, but is not wired into the default path. The reason is hardware, not code ([PLAN.md §6](PLAN.md)). It's the on-prem and data-residency story rather than something running today.
