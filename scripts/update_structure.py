"""Regenerate STRUCTURE.md from the actual repo tree.

Run after adding or removing files:

    python scripts/update_structure.py

The tree is walked from disk rather than hand-maintained, so the document
cannot drift out of sync with reality. Descriptions live in DESCRIPTIONS
below; anything on disk without one is written out as NEEDS DESCRIPTION so
it's visible rather than silently blank.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    "node_modules", ".mypy_cache", "dist", "build", ".idea", ".vscode",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".egg-info"}


def is_ignored(paths: list[Path]) -> set[Path]:
    """Ask git which of these it ignores.

    Anything gitignored is not part of the repo even though it sits on
    disk, so it does not belong in a document describing the repo. Asking
    git beats maintaining a second exclude list here that silently drifts
    out of sync with .gitignore -- and .env, which holds a real API key,
    must never be echoed into a committed file by an oversight in that
    list.

    Returns an empty set outside a git checkout rather than failing.
    """
    if not paths:
        return set()
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            input="\n".join(str(p) for p in paths),
            capture_output=True,
            text=True,
            cwd=REPO,
            check=False,  # exit 1 just means "nothing ignored"
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    # Exit 0 = some ignored, 1 = none ignored, 128 = not a git repo.
    if result.returncode not in (0, 1):
        return set()
    return {Path(line) for line in result.stdout.splitlines() if line}

DESCRIPTIONS: dict[str, str] = {
    # Top level
    "README.md": "Front door: what this is, how to run it, why MCP.",
    "PLAN.md": "Living status doc — what's settled, what's built, what's open.",
    "STRUCTURE.md": "This file. Auto-generated map of the repo.",
    "pyproject.toml": "Package metadata, dependencies, pytest and ruff config.",
    ".gitignore": "Excludes venv, caches, .env, and generated databases.",
    "data/bakeoff_sample60.json": "The full 60-resume corpus as a bake-off sample, for fitting cutoffs on more than 20 points.",
    "data/bakeoff_sample.json": "The fixed, stratified 20 resumes every bake-off arm is scored on. Generated, seeded.",
    "config": "Configuration you edit by hand. Not generated.",
    "config/bakeoff.json": "Bake-off arms: model ids, endpoints, key env vars, prices. Fill in before running.",
    ".env.example": "Template for .env. Names the one key needed; holds no secret.",
    "LICENSE": "MIT.",

    # docs/
    "docs": "Design documents and the target job posting.",
    "docs/job_description.md": "The real posting the rubric is built against. Ground truth for scoring criteria.",
    "docs/corpus_design.md": "Archetypes, labels, and generation method for the synthetic resume corpus.",
    "docs/ARCHITECTURE.md": "Why the system is shaped this way: the cascade, the caching contract, and what each decision cost.",
    "CLAUDE.md": "Guidance for Claude Code in this repo: the hard constraints (no AI attribution in git history, the live key in .env), the load-bearing caching contract, and the ordered next steps.",
    "docs/COST_ANALYSIS.md": "Where the run cost actually goes, the pricing-table bug found 2026-08-27, and why prompt caching is already maxed out here.",
    "docs/LIMITATIONS.md": "Where the numbers stop meaning what they look like, and where this must not be trusted: the fitted cutoffs, the one-directional errors, the escalation blind spot, and the unmeasured bias audit.",

    # research/
    "research": "Background research with citations, gathered before design decisions were made.",
    "research/ats_scoring_criteria.md": "How real ATS and AI screeners score resumes in 2026; gaps in our rubric.",
    "research/cascade_architecture_research.md": "Whether the tiered-cascade design has real support. Honest answer: partial.",
    "research/cost_latency_methodology.md": "How to measure caching savings and latency for real rather than estimating.",
    "research/stonestepper_ablation_review.md": "Review of a prior project's ablation study and the corrections it forced here.",
    "research/synthetic_corpus_sources.md": "Public resume datasets surveyed, and why the corpus is generated instead.",

    # src/
    "src": "Package source.",
    "src/resume_screener": "The installable package.",
    "src/resume_screener/core": "Domain logic. Knows nothing about MCP, HTTP, or the CLI.",
    "src/resume_screener/core/cutoffs.py": "Score-to-verdict cutoffs per model, plus the escalation and human-review margins built on them.",
    "src/resume_screener/core/models.py": "Shared dataclasses: Evidence, ExtractedCandidate, RubricScore, Verdict.",
    "src/resume_screener/core/router.py": "Model provider abstraction. Returns ModelResponse with real token/latency usage.",
    "src/resume_screener/core/ingest.py": "Resume file -> raw text. PDF, DOCX, Markdown, plain text.",
    "src/resume_screener/core/pipeline.py": "The cascade: extract -> panel -> arbitrate on disagreement. Owns the caching contract.",
    "src/resume_screener/core/query.py": "Follow-up questions: sandboxed DuckDB SQL plus a bounded evidence-judgment call.",
    "src/resume_screener/core/enrichment.py": "Documented extension point for consuming external MCP servers. Intentionally unimplemented.",
    "src/resume_screener/core/rubric_gen.py": "Writes the rubric and the three panel personas from any job posting. Validated, not trusted.",
    "src/resume_screener/adapters": "Thin translation layers over core. No scoring logic lives here.",
    "src/resume_screener/adapters/mcp_server.py": "MCP server exposing five tools. The primary interface.",
    "src/resume_screener/adapters/cli.py": "Terminal entry point: rubric, screen, rank. Takes the posting as a file, not a string.",
    "src/resume_screener/adapters/api.py": "FastAPI backend: password gate, screening, reviewer decisions, resume PDFs, run stats.",
    "src/resume_screener/adapters/static": "Static assets for the web adapter.",
    "src/resume_screener/adapters/static/index.html": "The whole UI: login, screening, review queue, results. One file, no build step.",
    "src/resume_screener/prompts": "Prompt text kept out of code so it can be diffed and cached.",
    "src/resume_screener/prompts/rubric.md": "The hand-written rubric for docs/job_description.md. Default when no rubric is generated.",
    "src/resume_screener/prompts/rubric_generator.md": "Meta-prompt: the instructions for writing a rubric from a posting.",

    # tests/
    "tests": "Offline test suite. Never calls a real API.",
    "tests/fakes.py": "Scripted Model implementation so tests are free, deterministic, and key-less.",
    "tests/test_pipeline.py": "Cascade behaviour: escalation, fallbacks, usage accounting, the caching contract.",
    "tests/test_query.py": "SQL safety, aggregate handling, and the two query primitives.",
    "tests/test_mcp_server.py": "Tool registration, session lifecycle, and the preview-to-screen rubric handoff.",
    "tests/test_router.py": "Response text-block extraction (thinking-block bug regression) and Usage accumulation.",
    "tests/test_rubric_gen.py": "Rubric validation: dimension count, identifier names, and failing loud on junk.",
    "tests/test_api.py": "Web adapter: the results and rubric endpoints, and every error surface they show.",
    "tests/test_cli.py": "Terminal adapter, including that the advertised console script still imports.",
    "tests/fixtures": "Static inputs for tests.",
    "tests/fixtures/sample_resume.md": "One well-formed resume used across pipeline tests.",

    # data/
    "data": "Generated corpus, its ground-truth labels, and the latest eval run.",
    "data/synthetic_resumes": "The 60 generated resumes (fictional, no real candidates) -- individually undescribed, see docs/corpus_design.md for the archetypes.",
    "data/resume_pdfs": "Corpus resumes rendered to PDF by scripts/build_resume_pdfs.py, for the web viewer.",
    "data/labels.json": "Ground-truth label + archetype + target dimension levels per resume, written at generation time.",
    "data/eval_run.json": "Raw output of the last scripts/evaluate.py run -- per-candidate predictions, panel detail, usage. Source for CANDIDATE_REPORTS.md.",

    "docs/img": "Screenshots used by the README.",
    "docs/img/candidates.png": "The candidates view, used in the README.",

    # docs/ (eval outputs)
    "docs/EVAL_RESULTS.md": "Headline metrics from the last eval run: macro-F1, per-class P/R/F1, confusion matrix, per-archetype accuracy.",
    "docs/SCORE_SCALE.md": "Why a strong candidate scores 6 not 8, and the measured cost of fixing it.",
    "docs/RESULTS_HISTORY.md": "Every measured run, what changed before it, and why the number moved.",
    "docs/ESCALATION_SWEEP.md": "Output of scripts/sweep_escalation.py: escalation policies compared on cost.",
    "data/UNUSABLE__anthropic-control-60__run2__partial-15of60.json": "Quarantined partial run (15/60). Scored 1.000 on the easy survivors. Kept as a worked example, never as data.",
    "docs/CUTOFF_FIT.md": "Verdict cutoffs refitted per model, with a held-out test that separates real accuracy from overfitting.",
    "docs/METRIC_CHOICE.md": "Why macro-F1 is the headline metric, what was rejected, and what it hides.",
    "docs/VARIANCE.md": "Output of scripts/variance_report.py: how much macro-F1 moves between identical runs.",
    "docs/BAKEOFF.md": "Output of scripts/bakeoff.py: macro-F1, cost, speed and JSON reliability per model.",
    "docs/CUTOFF_SWEEP.md": "Output of scripts/sweep_cutoffs.py: what the advance/hold cutoffs should be.",
    "docs/EVAL_RESULTS__all-haiku-panel-sonnet-arbiter_ANALYSIS.md": "Writeup: why an all-Haiku panel was rejected (JSON-reliability collapse, not accuracy).",
    "docs/CANDIDATE_REPORTS.md": "Full per-candidate report: score, panel breakdown, full reasoning, for all 60. Generated from data/eval_run.json.",

    # scripts/
    "scripts": "Developer utilities. Not part of the installed package.",
    "scripts/update_structure.py": "Regenerates STRUCTURE.md from the real tree.",
    "scripts/archetypes.py": "The 9 archetype specs (label, per-dimension targets, must-include/avoid) that generate_corpus.py writes from.",
    "scripts/generate_corpus.py": "Generates the synthetic resume corpus from archetypes.py. Idempotent, --limit samples across labels.",
    "scripts/check_corpus.py": "Lints generated resumes for leaked or missing signals against their own archetype's constraints.",
    "scripts/evaluate.py": "Scores the pipeline against the labeled corpus. --tag baseline (default) writes the canonical files; any other tag is a comparison run written elsewhere. Model slots overridable per-run.",
    "scripts/build_resume_pdfs.py": "Renders every corpus resume to PDF with reportlab. Deterministic, no model calls.",
    "scripts/sweep_escalation.py": "Compares escalation policies on cost and pointless calls. No API calls.",
    "scripts/sweep_cutoffs.py": "Re-thresholds recorded scores to test the advance/hold cutoffs. No API calls.",
    "scripts/variance_report.py": "Reports run-to-run spread across repeated runs of one config. No API calls.",
    "scripts/fit_cutoffs.py": "Refits the score-to-verdict cutoffs per model and cross-validates them. No API calls.",
    "scripts/bakeoff.py": "Runs the multi-model bake-off from config/bakeoff.json. --check validates without spending.",
    "scripts/make_bakeoff_sample.py": "Picks the fixed, stratified 20-resume sample every bake-off arm scores on. No API calls.",
    "scripts/generate_candidate_report.py": "Builds CANDIDATE_REPORTS.md from the last evaluate.py run.",
}

HEADER = """# Repository structure

Auto-generated by `scripts/update_structure.py` — run it after adding or
removing files rather than editing this by hand.

```
"""

FOOTER = """```

## Notes

- `core/` never imports from `adapters/`. That one-way dependency is what
  lets the MCP server, CLI, and web API stay thin and share behaviour.
- Tests never hit the network. `tests/fakes.py` supplies scripted model
  responses, so the suite is free to run and deterministic.
- Entries marked *(not written yet)* are planned files referenced by
  documentation or the plan but not yet implemented.
"""


def walk(directory: Path, prefix: str = "") -> tuple[list[str], list[str]]:
    lines: list[str] = []
    missing: list[str] = []

    candidates = [
        e for e in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        if e.name not in EXCLUDE_DIRS
        and e.suffix not in EXCLUDE_SUFFIXES
        and not e.name.endswith(".egg-info")
    ]
    ignored = is_ignored(candidates)
    entries = [e for e in candidates if e not in ignored]

    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        connector = "└── " if last else "├── "
        rel = entry.relative_to(REPO).as_posix()
        description = DESCRIPTIONS.get(rel)

        if description is None and entry.name == "__init__.py":
            description = "Package marker."
        elif description is None and re.fullmatch(r"eval_run__.+\.json", entry.name):
            description = "A scripts/evaluate.py comparison run (non-baseline --tag). See docs/RESULTS_HISTORY.md."
        elif description is None and re.fullmatch(r"EVAL_RESULTS__.+\.md", entry.name):
            description = "Human-readable report for a comparison run. See docs/RESULTS_HISTORY.md."
        elif description is None and re.fullmatch(r"bakeoff__.+__run\d+\.json", entry.name):
            description = "One scripts/bakeoff.py run for one model arm. See docs/BAKEOFF.md."
        elif description is None:
            description = "NEEDS DESCRIPTION"
            missing.append(rel)

        name = f"{entry.name}/" if entry.is_dir() else entry.name
        lines.append(f"{prefix}{connector}{name:<28} {description}")

        # Individually undescribed by design (see DESCRIPTIONS) -- 60
        # generated resumes with the same shape don't need 60 tree rows.
        if entry.is_dir() and rel in ("data/synthetic_resumes", "data/resume_pdfs"):
            child_count = len([c for c in entry.iterdir() if c.is_file()])
            noun = "generated resumes" if rel.endswith("synthetic_resumes") else "rendered PDFs"
            sub_prefix = prefix + ("    " if last else "│   ")
            lines.append(f"{sub_prefix}└── ({child_count} {noun}, listed in data/labels.json)")
            continue

        if entry.is_dir():
            sub_lines, sub_missing = walk(entry, prefix + ("    " if last else "│   "))
            lines.extend(sub_lines)
            missing.extend(sub_missing)

    return lines, missing


def main() -> int:
    lines, missing = walk(REPO)
    output = HEADER + "\n".join(lines) + "\n" + FOOTER
    (REPO / "STRUCTURE.md").write_text(output, encoding="utf-8")

    print(f"Wrote STRUCTURE.md ({len(lines)} entries)")
    if missing:
        print(f"\n{len(missing)} entries need a description in DESCRIPTIONS:")
        for path in missing:
            print(f"  {path}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
