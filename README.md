# Resume Screener

An agent that reads a stack of resumes against a specific job posting, ranks them, and says which ones a person should look at first.

Built for a team screening by hand with no ATS. It is not a filter that rejects people quietly: every verdict carries the evidence behind it, and anything borderline goes back to a human instead of being decided.

## TL;DR

- **What it does.** Writes scoring criteria *from your job posting*, scores each resume against them with a quoted rationale per dimension, and asks a second model for another look when the call is close.
- **How well.** macro-F1 **0.88–0.92** on 60 labelled resumes, **~$0.28 per 60** (~0.5¢ each), p50 **8.4s**, **16%** sent to a human. → [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md)
- **Why a range, not a number.** Four identical runs — same code, same corpus — span **0.051** macro-F1. Any smaller difference is unresolved. → [VARIANCE.md](docs/VARIANCE.md)
- **It replaced its own architecture.** It ran as three parallel agents plus an arbiter. Measured, the parallel panel scored *worse* than a single call (0.788 vs 0.821) at twice the API calls; the arbiter was the part earning its keep. → [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md)
- **What it does not prove.** The corpus is synthetic, the cutoffs were fitted on it, and about half the errors ship unreviewed. → [LIMITATIONS.md](docs/LIMITATIONS.md)
- **Run it:** `uvicorn resume_screener.adapters.api:app --reload`, password `screener`. Opens on a recorded run and costs nothing until you submit a posting.

## How it works

Two stages per resume, plus a third on about a quarter of them.

```
  Job posting ──▶ writes 3 scoring dimensions          once per batch
                            │
  Resume ──▶ Extract        pulls out quoted evidence
                            │
             Score          ONE call, all three dimensions
                            │   8.0      9.0      6.0
                            ▼
             Is the mean near a verdict cutoff?
                │                          │
                no                        yes
                │                          ▼
                │              Arbiter re-reads the rationales
                │                          │
                └────────────┬─────────────┘
                             ▼
                   advance · hold · reject
```

**Every score cites a verbatim quote.** The extraction step pulls real lines out of the file, and the scoring call is given only those quotes — so a rationale cannot be based on an impression the resume never supported.

**The arbiter is gated on distance to a cutoff, not disagreement.** It moves a score by 0.33 on average and never more than 1.5, so a score further out than that is one it cannot change. Under the old disagreement trigger, 92% of arbiter calls changed nothing. → [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md)

**Cutoffs belong to the model, not the pipeline.** Models grade on different scales. Judging one model with another's thresholds measures calibration, not judgment — it made a good model look 0.26 worse than it was. → [CUTOFF_FIT.md](docs/CUTOFF_FIT.md)

## Results

Measured on 60 labelled synthetic resumes, 3 runs. Full working in [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md); raw run files in [`data/`](data).

| Metric | Value | Evidence |
|---|---|---|
| Macro-F1 | **0.88–0.92** | [why this metric](docs/METRIC_CHOICE.md) |
| Accuracy | 0.88–0.92 | [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md) |
| Cost | ~$0.28 per 60 (~0.5¢ each) | [COST_ANALYSIS.md](docs/COST_ANALYSIS.md) |
| Latency | p50 8.4s | [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md) |
| Sent to a human | 9 / 60 | [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md) |
| Offline tests | 338, no network, no key | `pytest` |

**Does the name change the score?** Swapping only the candidate's name — heading, email, LinkedIn handle, nothing else — moved group means by at most **0.20 points** against a ~0.88 noise floor. No detectable name effect, which rules out a *large* one and not a small one. → [BIAS_AUDIT.md](docs/BIAS_AUDIT.md)

### Where it fails

- **About half the errors ship unreviewed.** The system is wrong on ~10% of candidates and a human sees 16%. Reviewing a sixth of a stack cannot catch most of the mistakes in it — arithmetic, not a tuning failure.
- **The corpus is synthetic and its labels come from the generator.** Every number is agreement with an intended verdict, not with a hiring manager.
- **The cutoffs were fitted on the corpus they are scored against.** Cross-validation makes them honest; it does not make them held-out.
- **A confidently wrong answer is invisible.** The review flag fires on scores near a boundary. A resume everyone reads the same wrong way lands far from one.

All of it, with numbers: [LIMITATIONS.md](docs/LIMITATIONS.md).

## Quickstart

Python 3.11+.

```bash
git clone https://github.com/kjb135-coe/resume-screener.git
cd resume-screener
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The test suite is offline — no API calls, no key, no cost:

```bash
pytest
```

Open the recorded run in a browser. Still no key needed; it reads from disk:

```bash
uvicorn resume_screener.adapters.api:app --reload
```

Everything past here calls a paid API:

```bash
cp .env.example .env    # then fill in the two keys
```

```bash
resume-screener rank data/synthetic_resumes docs/job_description.md --top 10
```

`rubric <posting>` writes criteria for any posting; `screen <resume> <posting>` scores one. Add `-g` to score against a generated rubric instead of the built-in one.

## Interfaces

The same core runs behind three shells, none of which contain scoring logic:

- **MCP server** — 5 tools, so an assistant can screen and then ask follow-up questions about the batch
- **CLI** — `rubric`, `screen`, `rank`
- **Web app** — [`adapters/api.py`](src/resume_screener/adapters/api.py) plus one HTML file, no build step

## Where to read next

| If you want | Read |
|---|---|
| What the numbers are worth | [LIMITATIONS.md](docs/LIMITATIONS.md) |
| How the system is built, and why | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Every measured run, and what changed before it | [RESULTS_HISTORY.md](docs/RESULTS_HISTORY.md) |
| How noisy it is | [VARIANCE.md](docs/VARIANCE.md) |
| Why macro-F1 | [METRIC_CHOICE.md](docs/METRIC_CHOICE.md) |
| Per-model calibration | [CUTOFF_FIT.md](docs/CUTOFF_FIT.md) · [BAKEOFF.md](docs/BAKEOFF.md) |
| Whether the name changes the score | [BIAS_AUDIT.md](docs/BIAS_AUDIT.md) |
| Where the money goes | [COST_ANALYSIS.md](docs/COST_ANALYSIS.md) |
| Longer design reasoning | [DESIGN_NOTES.md](docs/DESIGN_NOTES.md) |
| Deploying it without an unbounded bill | [HOSTING.md](docs/HOSTING.md) |
| A single page with the headline results | [overview](docs/overview/index.html) |
