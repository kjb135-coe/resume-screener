"""Generate the synthetic resume corpus.

    python scripts/generate_corpus.py --limit 4      # sample first
    python scripts/generate_corpus.py                # full 60
    python scripts/generate_corpus.py --force        # regenerate everything

Idempotent: existing files are skipped unless --force. Ground truth is
written to data/labels.json as each resume is produced, so an interrupted
run leaves a consistent corpus rather than orphaned files.

Uses a cheap model deliberately -- writing plausible fictional resumes is
not a task that needs a frontier model, and there are 60 of them. The
instruction block is identical across every call so it is cached.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from archetypes import ARCHETYPES, NAMES, Archetype

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_screener.core.router import AnthropicModel, Usage

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "synthetic_resumes"
LABELS_PATH = REPO / "data" / "labels.json"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Decorrelated from label on purpose: if strong resumes were consistently
# longer or more polished, a scorer could hit high accuracy by reading
# surface features instead of evidence.
LENGTHS = ("short (about 250 words)", "medium (about 450 words)", "long (about 700 words)")
STYLES = (
    "terse bullets, no summary section",
    "a short professional summary followed by bullets",
    "prose-heavy paragraphs under each role",
    "bullets with a dense skills block near the top",
)

SYSTEM = """You write realistic fictional resumes for testing a resume screening system.

Rules that apply to every resume you write:
- The person is entirely fictional. Invent all company names. Never use a real
  company, real person, or real contact details.
- Write only the resume itself in Markdown. No preamble, no commentary, no
  code fences, no notes about the archetype.
- Make it read like a real resume a real person submitted: specific job
  titles, plausible date ranges, concrete detail. Not a template.
- Vary sentence construction between resumes. Avoid reusing distinctive
  phrasings across candidates.
- Include a header with the name, a job title, and fictional contact details.

You will be given a target profile. Follow its must-include and must-avoid
constraints exactly -- they define what this resume is testing. The
must-avoid list matters as much as the must-include list: a resume that
leaks a forbidden signal is unusable as test data."""


def build_prompt(arch: Archetype, name: str, length: str, style: str, seed_hint: str) -> str:
    return f"""Write one resume for this target profile.

Candidate name: {name}
Length: {length}
Formatting style: {style}
Make this one distinct from others in the same profile by emphasising: {seed_hint}

PROFILE: {arch.brief}

Signal levels this resume must convey:
- Production reality (shipped, used by real people): {arch.production_reality}
- Technical / integration depth (agents, LLMs, APIs, cloud): {arch.technical_integration}
- Client-facing and cross-functional signal: {arch.client_communication}

MUST INCLUDE:
{chr(10).join(f"- {item}" for item in arch.must_include)}

MUST AVOID:
{chr(10).join(f"- {item}" for item in arch.must_avoid)}

Output the resume in Markdown, nothing else."""


SEED_HINTS = (
    "a healthcare or life-sciences context",
    "a fintech or payments context",
    "a logistics or supply-chain context",
    "a developer-tools or infrastructure context",
    "an e-commerce or retail context",
    "a government or public-sector context",
    "a media or entertainment context",
)


def plan_corpus(limit: int | None) -> list[tuple[Archetype, str, str, str, str]]:
    """Deterministic plan so reruns produce the same corpus."""
    rng = random.Random(42)
    names = list(NAMES)
    rng.shuffle(names)

    jobs: list[tuple[Archetype, str, str, str, str]] = []
    name_index = 0
    for arch in ARCHETYPES:
        for i in range(arch.count):
            jobs.append(
                (
                    arch,
                    names[name_index % len(names)],
                    LENGTHS[(name_index) % len(LENGTHS)],
                    STYLES[(name_index) % len(STYLES)],
                    SEED_HINTS[i % len(SEED_HINTS)],
                )
            )
            name_index += 1

    if limit is None:
        return jobs

    # Sample across archetypes AND rotate through labels, so a small run
    # shows the actual spread (a strong hire next to a demo-stage hold next
    # to a keyword stuffer) rather than four variations on "advance".
    by_arch: dict[str, list] = {}
    for job in jobs:
        by_arch.setdefault(job[0].key, []).append(job)

    label_order = ("advance", "hold", "reject")
    keys_by_label = {
        label: [a.key for a in ARCHETYPES if a.label == label] for label in label_order
    }
    rotation: list[str] = []
    for round_index in range(max(len(v) for v in keys_by_label.values())):
        for label in label_order:
            keys = keys_by_label[label]
            if round_index < len(keys):
                rotation.append(keys[round_index])

    sampled: list = []
    while len(sampled) < limit and any(by_arch.values()):
        progressed = False
        for key in rotation:
            if by_arch.get(key) and len(sampled) < limit:
                sampled.append(by_arch[key].pop(0))
                progressed = True
        if not progressed:
            break
    return sampled


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def load_labels() -> dict:
    if LABELS_PATH.exists():
        return json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    return {}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="generate only N, sampled across archetypes")
    parser.add_argument("--force", action="store_true", help="regenerate files that already exist")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="print the plan, call nothing")
    args = parser.parse_args()

    jobs = plan_corpus(args.limit)

    if args.dry_run:
        for arch, name, length, style, hint in jobs:
            print(f"{arch.label:8} {arch.key:22} {name:24} {length.split()[0]:7} {hint}")
        print(f"\n{len(jobs)} resumes planned")
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model = AnthropicModel(args.model, api_key)
    labels = load_labels()
    semaphore = asyncio.Semaphore(args.concurrency)
    total_usage = Usage()

    async def generate(job) -> None:
        nonlocal total_usage
        arch, name, length, style, hint = job
        path = OUT_DIR / f"{arch.key}__{slugify(name)}.md"
        if path.exists() and not args.force:
            print(f"  skip   {path.name}")
            return

        async with semaphore:
            response = await model.complete(
                SYSTEM,
                build_prompt(arch, name, length, style, hint),
                max_tokens=2000,
            )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        path.write_text(text + "\n", encoding="utf-8")
        labels[path.name] = {
            "archetype": arch.key,
            "label": arch.label,
            "production_reality": arch.production_reality,
            "technical_integration": arch.technical_integration,
            "client_communication": arch.client_communication,
            "candidate_name": name,
        }
        total_usage = total_usage + response.usage
        print(f"  wrote  {path.name}  ({len(text.split())} words)")

    print(f"Generating {len(jobs)} resumes with {args.model}\n")
    await asyncio.gather(*[generate(j) for j in jobs])

    LABELS_PATH.write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"\nlabels.json now holds {len(labels)} entries")
    print(
        f"tokens: {total_usage.input_tokens} in "
        f"({total_usage.cache_read_input_tokens} cached read, "
        f"{total_usage.cache_creation_input_tokens} cache write), "
        f"{total_usage.output_tokens} out"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
