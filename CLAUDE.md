# CLAUDE.md

Guidance for Claude Code working in this repo. Kept deliberately short —
the detail lives in `PLAN.md`, which is the living status doc.

## What this is

An AI resume screener, built as a **portfolio piece** for a remote AI
Solutions Engineer role at Marco Technologies, sent as a follow-up after
a second-round interview. The email is already out and links here, so
**the README has to carry the entire pitch on its own** — assume the
reader will not clone anything and may not scroll far.

That framing drives most decisions: honesty about what does not work is
a feature, not a liability. The audience is engineers evaluating
judgment, not a customer being sold to.

## Hard constraints

- **No Claude/Anthropic attribution anywhere in git history.** No
  `Co-Authored-By` trailer, no mention in commit messages. Commits are
  authored `kjb135-coe <keeganborig@gmail.com>` (set in repo-local git
  config).
- **`.env` holds a live `ANTHROPIC_API_KEY`.** chmod 600, gitignored.
  Never commit it, never echo it into a file, never print it.
- The test suite is **offline** and must stay that way — 249 tests, no
  network, no key, no cost.

## Architecture in one paragraph

Three stages per resume: extract quoted evidence (Haiku 4.5) → three
agents score one rubric dimension each in parallel (Sonnet 5) → an
arbiter runs only when the panel disagrees on the *verdict bucket*
(Sonnet 5). `recommendation_from_score` owns every verdict; the arbiter
returns a score, never a recommendation. `core/` never imports from
`adapters/` — the MCP server, CLI, and web API are thin shells over the
same core.

**The caching contract in `core/pipeline.py` is load-bearing.** The panel
system block is exactly `rubric + job_description`, byte-identical across
every call in a batch. Personas and evidence go in the user turn. Moving
a persona into the system string silently creates one cache entry per
persona. Read that module docstring before touching prompt assembly.

## Where things stand

- **macro-F1 0.81–0.86** on 60 labelled synthetic resumes, measured over
  four runs. **Quote it as a range**, never as a point — four identical
  runs span 0.051. Roughly **$0.95** per full run (~1.6c/resume),
  measured, stable to a cent.
- 290 offline tests, ruff clean.
- **Panel agents no longer emit a confidence score.** It was never used in
  any logic and was anti-correlated with correctness (0.867 mean when the
  verdict was wrong, 0.816 when right). Extraction confidence is kept —
  it gates the review flag — though that flag has never once fired.
- Working: the cascade, rubrics generated from any posting, MCP server
  (5 tools), CLI (3 commands), web app with reviewer workflow and
  password gate, PDF/Word upload.

`docs/METRIC_CHOICE.md` explains why macro-F1 is the headline, and what
it hides. **"Parse failure" throughout these docs means our code could
not read the model's JSON reply — not that a resume failed to parse.**

**Read `docs/LIMITATIONS.md` before making any accuracy claim.** The
short version: the noise band is 0.051 so any smaller difference is
unresolved, the cutoffs were fitted on the same 60 resumes they are
scored against, the errors run below the label, and no bias audit exists.

**Before comparing two runs, check they share the same code.** Run
`scripts/variance_report.py`, and read its **Run health** table first — a
run that lost candidates to network errors keeps the easy ones and
understates the noise.

## What's next — in order

1. ~~**Variance estimate.**~~ **Done 2026-08-27.** Four runs. The band is
   **macro-F1 0.051**, and it is a floor — it grew from 0.042 at two
   runs. See `docs/VARIANCE.md`. **Any comparison turning on less than
   0.051 is unresolved.**
2. **Re-fit the cutoffs per model before any model comparison.** Measured
   2026-08-27: on 60 resumes, held out, GPT-5.6 Luna scores **0.861** vs
   Sonnet's **0.787** at a third of the cost — after scoring 0.563 vs
   0.823 under the shipped 4.0/1.0. The threshold is part of the harness,
   not the model. Luna escalates 70% vs 47% though, so this is not yet a
   switch recommendation. `docs/CUTOFF_FIT.md`.
3. **Single-pass arm of the bake-off** (PLAN §8). The cascade's entire
   justification is that it beats one big call. That is asserted, never
   measured. **No single-pass code path exists** — this is implementation
   plus a run, not just a run. It must beat the cascade by more than
   0.051 to count, which likely means several runs per arm.
3. **Batch API** — roughly 50% off input and output, and the eval is
   exactly the offline fixed-corpus job Batch exists for. Biggest
   available cost win; changes latency only. See `docs/COST_ANALYSIS.md`.
4. **Cut output tokens** — 69% of the bill. Try `effort: "low"|"medium"`
   on panel calls, and stop generating reasoning the UI truncates to two
   bullets anyway. Needs an eval run to confirm accuracy holds.
5. **Walkthrough mode** (PLAN §11) — fully specified, zero code. Only
   matters if the app gets hosted.
6. **Hosting spend cap.** Option 2 was chosen (shared password + hard
   daily cap). The password gate is built; the cap and the deploy are
   not. Do not deploy with a live key until the cap exists.

`docs/ARCHITECTURE.md` is referenced but unwritten, and is lower priority
than it looks — the README's "How it works" and `STRUCTURE.md` already
cover most of it.

## Conventions

- Run the app: `uvicorn resume_screener.adapters.api:app --reload`,
  password `marco1`. It opens on a recorded run and costs nothing until
  you submit a posting.
- After adding or removing a file, run `scripts/update_structure.py` —
  `STRUCTURE.md` is generated, and the file descriptions live in that
  script, not in the doc.
- `scripts/sweep_cutoffs.py` and `sweep_escalation.py` re-threshold
  recorded scores offline. Free. Use them before spending on a run.
- Anything with `--tag <name>` writes to `data/eval_run__<tag>.json` and
  never overwrites the baseline.
- **Every measured run gets a row in `docs/RESULTS_HISTORY.md`**, with
  what changed before it. A number without that context has misled us
  before.
