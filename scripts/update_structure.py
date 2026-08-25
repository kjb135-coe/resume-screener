"""Regenerate STRUCTURE.md from the actual repo tree.

Run after adding or removing files:

    python scripts/update_structure.py

The tree is walked from disk rather than hand-maintained, so the document
cannot drift out of sync with reality. Descriptions live in DESCRIPTIONS
below; anything on disk without one is written out as NEEDS DESCRIPTION so
it's visible rather than silently blank.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    "node_modules", ".mypy_cache", "dist", "build", ".idea", ".vscode",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".egg-info"}

DESCRIPTIONS: dict[str, str] = {
    # Top level
    "README.md": "Front door: what this is, how to run it, why MCP.",
    "PLAN.md": "Living status doc — what's settled, what's built, what's open.",
    "STRUCTURE.md": "This file. Auto-generated map of the repo.",
    "pyproject.toml": "Package metadata, dependencies, pytest and ruff config.",
    ".gitignore": "Excludes venv, caches, .env, and generated databases.",

    # docs/
    "docs": "Design documents and the target job posting.",
    "docs/job_description.md": "The real posting the rubric is built against. Ground truth for scoring criteria.",
    "docs/corpus_design.md": "Archetypes, labels, and generation method for the synthetic resume corpus.",
    "docs/ARCHITECTURE.md": "Design decisions and their reasoning. (not written yet)",
    "docs/LIMITATIONS.md": "What this tool does not catch — bias, injection, human-review boundaries. (not written yet)",

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
    "src/resume_screener/core/models.py": "Shared dataclasses: Evidence, ExtractedCandidate, RubricScore, Verdict.",
    "src/resume_screener/core/router.py": "Model provider abstraction. Returns ModelResponse with real token/latency usage.",
    "src/resume_screener/core/ingest.py": "Resume file -> raw text. PDF, DOCX, Markdown, plain text.",
    "src/resume_screener/core/pipeline.py": "The cascade: extract -> panel -> arbitrate on disagreement. Owns the caching contract.",
    "src/resume_screener/core/query.py": "Follow-up questions: sandboxed DuckDB SQL plus a bounded evidence-judgment call.",
    "src/resume_screener/core/enrichment.py": "Documented extension point for consuming external MCP servers. Intentionally unimplemented.",
    "src/resume_screener/adapters": "Thin translation layers over core. No scoring logic lives here.",
    "src/resume_screener/adapters/mcp_server.py": "MCP server exposing four tools. The primary interface.",
    "src/resume_screener/adapters/cli.py": "Terminal entry point. Not written yet.",
    "src/resume_screener/adapters/api.py": "FastAPI backend for the web demo. Not written yet.",
    "src/resume_screener/prompts": "Prompt text kept out of code so it can be diffed and cached.",
    "src/resume_screener/prompts/rubric.md": "The scoring rubric. Forms the cacheable prefix shared by every panel call.",

    # tests/
    "tests": "Offline test suite. Never calls a real API.",
    "tests/fakes.py": "Scripted Model implementation so tests are free, deterministic, and key-less.",
    "tests/test_pipeline.py": "Cascade behaviour: escalation, fallbacks, usage accounting, the caching contract.",
    "tests/test_query.py": "SQL safety, aggregate handling, and the two query primitives.",
    "tests/test_mcp_server.py": "Tool registration and session lifecycle.",
    "tests/test_router.py": "Response text-block extraction (thinking-block bug regression) and Usage accumulation.",
    "tests/fixtures": "Static inputs for tests.",
    "tests/fixtures/sample_resume.md": "One well-formed resume used across pipeline tests.",

    # data/
    "data": "Generated corpus, its ground-truth labels, and the latest eval run.",
    "data/synthetic_resumes": "The 60 generated resumes (fictional, no real candidates) -- individually undescribed, see docs/corpus_design.md for the archetypes.",
    "data/labels.json": "Ground-truth label + archetype + target dimension levels per resume, written at generation time.",
    "data/eval_run.json": "Raw output of the last scripts/evaluate.py run -- per-candidate predictions, panel detail, usage. Source for CANDIDATE_REPORTS.md.",

    # docs/ (eval outputs)
    "docs/EVAL_RESULTS.md": "Headline metrics from the last eval run: macro-F1, per-class P/R/F1, confusion matrix, per-archetype accuracy.",
    "docs/CANDIDATE_REPORTS.md": "Full per-candidate report: score, panel breakdown, full reasoning, for all 60. Generated from data/eval_run.json.",

    # scripts/
    "scripts": "Developer utilities. Not part of the installed package.",
    "scripts/update_structure.py": "Regenerates STRUCTURE.md from the real tree.",
    "scripts/archetypes.py": "The 9 archetype specs (label, per-dimension targets, must-include/avoid) that generate_corpus.py writes from.",
    "scripts/generate_corpus.py": "Generates the synthetic resume corpus from archetypes.py. Idempotent, --limit samples across labels.",
    "scripts/check_corpus.py": "Lints generated resumes for leaked or missing signals against their own archetype's constraints.",
    "scripts/evaluate.py": "Scores the pipeline against the labeled corpus. Writes EVAL_RESULTS.md and eval_run.json.",
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

    entries = [
        e for e in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        if e.name not in EXCLUDE_DIRS and e.suffix not in EXCLUDE_SUFFIXES
        and not e.name.endswith(".egg-info")
    ]

    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        connector = "└── " if last else "├── "
        rel = entry.relative_to(REPO).as_posix()
        description = DESCRIPTIONS.get(rel)

        if description is None and entry.name == "__init__.py":
            description = "Package marker."
        elif description is None:
            description = "NEEDS DESCRIPTION"
            missing.append(rel)

        name = f"{entry.name}/" if entry.is_dir() else entry.name
        lines.append(f"{prefix}{connector}{name:<28} {description}")

        # Individually undescribed by design (see DESCRIPTIONS) -- 60
        # generated resumes with the same shape don't need 60 tree rows.
        if entry.is_dir() and rel == "data/synthetic_resumes":
            child_count = len(list(entry.iterdir()))
            sub_prefix = prefix + ("    " if last else "│   ")
            lines.append(f"{sub_prefix}└── ({child_count} generated resumes, listed in data/labels.json)")
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
