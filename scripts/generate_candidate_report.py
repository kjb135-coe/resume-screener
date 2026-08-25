"""Generate a full per-candidate report from an eval run.

    python scripts/generate_candidate_report.py

Reads data/eval_run.json (written by evaluate.py) and writes
docs/CANDIDATE_REPORTS.md -- one full section per resume: expected vs.
predicted, the final score and rationale, and every panel agent's
individual score and reasoning, untruncated.

Generated from the raw run data rather than hand-written so it can't
drift from what evaluate.py actually produced, and regenerates for free
after every future run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN_JSON = REPO / "data" / "eval_run.json"
OUT = REPO / "docs" / "CANDIDATE_REPORTS.md"


def verdict_line(expected: str, predicted: str) -> str:
    return "correct" if expected == predicted else f"MISMATCH -- expected {expected}"


def main() -> int:
    if not RUN_JSON.exists():
        print(f"{RUN_JSON} not found -- run scripts/evaluate.py first.", file=sys.stderr)
        return 2

    run = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    preds = sorted(run["predictions"], key=lambda p: -p["score"])

    lines: list[str] = []
    add = lines.append

    add(f"# Candidate reports — `{run['tag']}`\n")
    add(
        f"Generated from `data/eval_run.json`. {run['n']} resumes, "
        f"macro-F1 {run['macro_f1']:.3f}, accuracy {run['accuracy']:.3f}. "
        "Do not edit by hand -- rerun `scripts/generate_candidate_report.py` "
        "after any evaluate.py run instead.\n"
    )
    add("Sorted by final score, highest first. `⚠` marks a mismatch against "
        "the archetype's ground-truth label.\n")

    add("## Contents\n")
    for p in preds:
        anchor = p["file"].replace(".", "").replace("_", "-").lower()
        mark = " ⚠" if p["expected"] != p["predicted"] else ""
        add(f"- [{p['file']}](#{anchor}) — {p['expected']} → {p['predicted']}{mark}")
    add("")

    for p in preds:
        mismatch = p["expected"] != p["predicted"]
        add(f"## {p['file']}\n")
        add(f"**Archetype:** {p['archetype']}  ")
        add(f"**Expected:** {p['expected']}  ")
        add(f"**Predicted:** {p['predicted']}{' ⚠ MISMATCH' if mismatch else ''}  ")
        add(f"**Final score:** {p['score']:.1f} / 10  ")
        add(f"**Panel spread:** {p['panel_spread']:.1f}  ")
        add(f"**Escalated to arbiter:** {'yes' if p['escalated'] else 'no'}\n")

        add("**Final rationale:**\n")
        add(f"> {p['rationale']}\n")

        add("**Panel breakdown:**\n")
        add("| Agent | Score | Confidence | Rationale |")
        add("|---|---|---|---|")
        for agent in p["panel"]:
            rationale = agent["rationale"].replace("|", "\\|").replace("\n", " ")
            flag = " (parse failed)" if agent.get("parse_failed") else ""
            add(f"| {agent['agent']} | {agent['score']:.1f} | {agent['confidence']:.2f}{flag} | {rationale} |")

        add("\n---\n")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)} ({len(preds)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
