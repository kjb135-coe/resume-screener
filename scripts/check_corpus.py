"""Lint the generated corpus for leaked signals.

    python scripts/check_corpus.py

A generated resume is only useful as test data if it actually carries the
signal levels its archetype claims. A demo-stage resume that mentions
on-call, or a "no client contact" resume that mentions stakeholders, makes
its ground-truth label wrong -- and a wrong label silently corrupts every
accuracy number computed against it.

This checks the mechanical constraints only. It cannot judge whether a
resume is *convincing*; that still needs a human read of a sample.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "synthetic_resumes"
LABELS = REPO / "data" / "labels.json"

# Signals that must not appear, per archetype. Each entry is
# (regex, human explanation of why it invalidates this archetype).
_DEMO_LABELS = (
    r"\b(prototype|proof[- ]of[- ]concept|POC|hackathon|side project|pilot project)\b"
)
_CLIENT_SIGNAL = (
    r"\b(stakeholder|client|customer-facing|presented to|presentation"
    r"|cross-functional|sales team|workshop|mentor)\w*\b"
)
_SUBSTANTIVE_AI = (
    r"\b(LLM|large language model|agentic|multi-agent|RAG"
    r"|retrieval[- ]augmented|fine[- ]tun\w+)\b"
)
_AGENTIC_DEPTH = (
    r"\b(multi-agent|agent orchestration|tool[- ]calling|memory layer|agentic workflow)\b"
)
_ACADEMIC_TRACK = (
    r"\b(publication|published|paper|citation|conference|PhD|postdoc"
    r"|research scientist|arXiv)\b"
)
_ADOPTION = r"\b(serving|serves|served) [\d,]+\+? (users|customers|patients|clients)\b"
_OPS = r"\bon[- ]call\b|\buptime\b|\bSLA\b|\bincident (response|lead)\b"

FORBIDDEN: dict[str, list[tuple[str, str]]] = {
    "demo_specialist": [
        (_DEMO_LABELS, "self-labels as demo-stage; must be inferable only from absence"),
        (r"\bnot (deployed|in production|for production)\b", "explicit disclaimer"),
        (_OPS, "production ownership signal in a no-production archetype"),
        (_ADOPTION, "real adoption in a no-production archetype"),
    ],
    "quiet_builder": [
        (_CLIENT_SIGNAL, "client-communication signal must be absent for this archetype"),
    ],
    "keyword_stuffer": [
        (r"\b\d+(\.\d+)?%", "concrete metric; this archetype must have none"),
        (
            r"\b(reduced|increased|improved|shipped|launched|built and deployed)\b.{0,40}\bby\b",
            "outcome sentence; bullets must stay noun phrases",
        ),
    ],
    "wrong_domain": [
        (_SUBSTANTIVE_AI, "substantive AI work in a wrong-domain archetype"),
    ],
    "academic_researcher": [
        (
            r"\bon[- ]call\b|\buptime\b|\bSLA\b|\bproduction (deployment|system)\b",
            "production/operational signal in a research archetype",
        ),
    ],
    "production_light_ai": [
        (_AGENTIC_DEPTH, "agentic depth in a light-AI archetype"),
    ],
}

# Signals that MUST appear, per archetype.
REQUIRED: dict[str, list[tuple[str, str]]] = {
    "production_generalist": [
        (r"\b(on[- ]call|incident|monitor\w*|production)\b", "production ownership evidence"),
        (r"\b(presented|stakeholder|client|customer|cross-functional)\w*\b", "client-facing evidence"),
    ],
    "quiet_builder": [
        (r"\b(production|deployed|live|users|requests)\b", "production evidence"),
    ],
    "academic_researcher": [
        (_ACADEMIC_TRACK, "academic track evidence"),
    ],
}


def main() -> int:
    if not LABELS.exists():
        print("No labels.json -- generate the corpus first.", file=sys.stderr)
        return 2

    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    problems: list[str] = []

    for filename, meta in sorted(labels.items()):
        path = CORPUS / filename
        if not path.exists():
            problems.append(f"{filename}: listed in labels.json but missing on disk")
            continue

        text = path.read_text(encoding="utf-8")
        archetype = meta["archetype"]

        for pattern, why in FORBIDDEN.get(archetype, []):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                line = text[: match.start()].count("\n") + 1
                problems.append(
                    f"{filename}:{line}  LEAKED {match.group(0)!r} -- {why}"
                )

        for pattern, why in REQUIRED.get(archetype, []):
            if not re.search(pattern, text, re.IGNORECASE):
                problems.append(f"{filename}  MISSING {why}")

    counts: dict[str, int] = {}
    for meta in labels.values():
        counts[meta["label"]] = counts.get(meta["label"], 0) + 1

    print(f"Checked {len(labels)} resumes: {counts}")
    if problems:
        print(f"\n{len(problems)} issues:\n")
        for problem in problems:
            print(f"  {problem}")
        return 1

    print("No leaked or missing signals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
