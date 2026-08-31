# CLAUDE.md

Guidance for Claude Code working in this repo. Kept deliberately short —
the detail lives in `PLAN.md`, which is the living status doc.

## What this is

An AI resume screener. Reads a stack of resumes against a specific job
posting, ranks them, and says which ones a person should look at first.

**The README has to carry the whole thing on its own** — assume the
reader will not clone anything and may not scroll far. Honesty about what
does not work is a feature, not a liability: the audience is engineers
evaluating judgment.

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

Two stages per resume: extract quoted evidence (Haiku 4.5) → one call
scores all three rubric dimensions (GPT-5.6 Luna) → an arbiter takes a
second look only when the score lands within `ESCALATION_MARGIN` of a
cutoff (Luna). `recommendation_from_score` owns every verdict; the arbiter
returns a score, never a recommendation. `core/` never imports from
`adapters/` — the MCP server, CLI, and web API are thin shells over the
same core.

**The caching contract in `core/pipeline.py` is load-bearing.** The panel
system block is exactly `rubric + job_description`, byte-identical across
every call in a batch. Personas and evidence go in the user turn. Moving
a persona into the system string silently creates one cache entry per
persona. Read that module docstring before touching prompt assembly.

## Where things stand

- **macro-F1 0.88–0.92** on 60 labelled synthetic resumes, measured over
  three runs. **Quote it as a range**, never as a point — identical
  runs span 0.051. Roughly **$0.28** per full run (~0.5c/resume),
  measured, stable to a cent.
- Offline test suite (no network, no key), ruff clean.
- **Escalation and the human-review flag are separate decisions.** The
  arbiter fires when the panel MEAN is within `ESCALATION_MARGIN` (0.5)
  of a cutoff; a human is asked when the FINAL score is within
  `REVIEW_MARGIN_FRACTION` (0.125 of that model's own band -- NOT a flat
  number of points; a flat margin queued 43% of Sonnet's stack and 15% of
  Luna's). Both live in `core/cutoffs.py`. Measured live: escalation 47%
  -> 5% (Sonnet), review queue 53% -> 30%, macro-F1 unchanged.
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

**Done 2026-08-27/31**, kept here because each one changed how a number
is read:

- ~~**Variance estimate.**~~ Band is **macro-F1 0.051** and it is a floor.
  Any comparison turning on less is unresolved. `docs/VARIANCE.md`.
- ~~**Per-model cutoffs.**~~ A fixed threshold is part of the harness, not
  the model. **Any new model must be fitted with
  `scripts/fit_cutoffs.py` before its score means anything** — an
  unlisted model falls back to Sonnet's calibration. `core/cutoffs.py`.
- ~~**Escalation rate.**~~ Escalation and the human-review flag are now
  separate decisions. Queue 53% → 15%, escalation 47% → 23%.
- ~~**Switch to Luna.**~~ Shipped. Same accuracy, half the queue, a third
  of the cost.
- ~~**Single-pass arm.**~~ The headline tie was confounded and the
  decomposition matters: cascade **with** arbiter 0.847, cascade
  **without** 0.788, single-pass 0.821. **The parallel panel earns
  nothing** (it loses 12-6 to one call, paired) **and the arbiter earns
  +0.059**, which clears the noise band. Not switched, but the next
  experiment is obvious: single-pass PLUS an arbiter gated on
  distance-to-cutoff.
- ~~**Bias audit.**~~ Name-swap paired test, largest group gap 0.20 points
  against a ~0.88 noise floor. No detectable name effect — and that rules
  out a LARGE effect only. `docs/BIAS_AUDIT.md`.
- ~~**Output tokens.**~~ `reasoning_effort` is the lever, not rationale
  length (~75% of output is reasoning). `low` adopted: unchanged
  accuracy, 16% faster. The predicted 30-50% cost win did not arrive — it
  moved cost 3.5%.
- ~~**Hosting spend cap.**~~ Built: `adapters/budget.py`, `render.yaml`,
  `docs/HOSTING.md`. **Set the provider-level caps before deploying.**
- ~~**Batch API**~~ and ~~**walkthrough mode**~~ — both dropped. Batch
  saves ~$0.15 on a $0.30 run; walkthrough is README prose now.

**Open, in order:**

1. **Deploy it.** Everything is built. Set the two provider caps, then
   Render → New → Blueprint. `docs/HOSTING.md` is the checklist.
2. **ATS comparison research** (PLAN §8c) — price, accuracy, and above
   all *adaptability*: a keyword ATS is configured against a fixed
   taxonomy, this writes its criteria from the posting you paste. That is
   the axis worth leading with. Requested, not started.
3. **A real corpus.** Every number here is agreement with a generator's
   intended verdict on 60 synthetic resumes. Nothing else on this list
   matters as much, and nothing can be done about it cheaply.
4. **`client_communication` discrimination** — knowingly left alone. Two
   attempts made it worse or moved nothing; `docs/SCORE_SCALE.md`
   explains why, and that is currently the better asset.



## Conventions

- Run the app: `uvicorn resume_screener.adapters.api:app --reload`,
  which prints a generated password to the console. It opens on a
  recorded run and costs nothing until
  you submit a posting.
- `scripts/sweep_cutoffs.py` and `sweep_escalation.py` re-threshold
  recorded scores offline. Free. Use them before spending on a run.
- Anything with `--tag <name>` writes to `data/eval_run__<tag>.json` and
  never overwrites the baseline.
- **Every measured run gets a row in `docs/RESULTS_HISTORY.md`**, with
  what changed before it. A number without that context has misled us
  before.
