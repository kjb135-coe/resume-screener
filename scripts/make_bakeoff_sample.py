"""Pick the fixed resume sample every bake-off arm is scored on.

    python scripts/make_bakeoff_sample.py            # 20, the default
    python scripts/make_bakeoff_sample.py --size 30

Writes data/bakeoff_sample.json. No API calls, no cost.

Why this is a separate, saved artifact rather than a `--limit` flag:
every arm and every repeat run must score the *identical* set. If arms
were sampled independently, a model difference and a sample difference
would be indistinguishable, which is the whole thing the bake-off exists
to measure.

Selection is stratified across all 9 archetypes and all 3 labels, and
seeded, so re-running reproduces the same set exactly.

**The sample is small enough to matter.** Measured on four recorded runs
of one unchanged config, the macro-F1 noise band is 0.051 over ~51
resumes but roughly 0.098 over a stratified 20 -- see docs/VARIANCE.md.
The bake-off runs each arm 3 times for that reason. A 20-resume single
run cannot rank models by accuracy; it can only catch large gaps and
outright JSON-reliability failures.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LABELS = REPO / "data" / "labels.json"
OUT = REPO / "data" / "bakeoff_sample.json"

# Same cutoffs as core.pipeline, used only to describe how hard the drawn
# sample is. A candidate scoring near a cutoff is one small jitter away
# from a different verdict, so a sample loaded with them is noisier than
# one that is not -- worth knowing before reading any result.
ADVANCE_CUTOFF = 4.0
HOLD_CUTOFF = 1.0
SEED = 20260827


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--out",
        default=None,
        help="write here instead of data/bakeoff_sample.json, so a larger "
             "sample does not orphan results recorded against a smaller one",
    )
    args = parser.parse_args()

    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    by_archetype: dict[str, list[str]] = {}
    for filename, meta in sorted(labels.items()):
        by_archetype.setdefault(meta["archetype"], []).append(filename)

    archetypes = sorted(by_archetype)
    if args.size < len(archetypes):
        print(
            f"--size {args.size} is smaller than the {len(archetypes)} archetypes. "
            "Every archetype must appear or the sample is not representative.",
            file=sys.stderr,
        )
        return 1

    rng = random.Random(args.seed)
    pools = {a: rng.sample(by_archetype[a], len(by_archetype[a])) for a in archetypes}

    # Balance the LABELS first, then the archetypes inside each label.
    #
    # Doing it the other way round -- one pass round-robin over all 9
    # archetypes -- looks fair and is not: 20 does not divide by 9, so the
    # remainder lands on whichever archetypes come first in the order, and
    # those all belong to one label. That produced 8/6/6 rather than 7/7/6.
    # Macro-F1 averages per-class F1, so an under-represented class carries
    # more noise per candidate and drags the whole metric around.
    archetypes_by_label: dict[str, list[str]] = {}
    for archetype in archetypes:
        label = labels[by_archetype[archetype][0]]["label"]
        archetypes_by_label.setdefault(label, []).append(archetype)

    label_order = sorted(archetypes_by_label)
    base, remainder = divmod(args.size, len(label_order))
    quota = {label: base for label in label_order}
    # The remainder goes to the labels with the most candidates available,
    # so a quota is never larger than the corpus can fill.
    for label in sorted(
        label_order,
        key=lambda x: -sum(len(by_archetype[a]) for a in archetypes_by_label[x]),
    )[:remainder]:
        quota[label] += 1

    chosen: list[str] = []
    for label in label_order:
        want = quota[label]
        ring = archetypes_by_label[label]
        taken = 0
        while taken < want:
            progressed = False
            for archetype in ring:
                if taken >= want:
                    break
                if pools[archetype]:
                    chosen.append(pools[archetype].pop())
                    taken += 1
                    progressed = True
            if not progressed:
                break

    chosen.sort()
    label_counts = Counter(labels[f]["label"] for f in chosen)
    archetype_counts = Counter(labels[f]["archetype"] for f in chosen)

    missing = set(archetypes) - set(archetype_counts)
    if missing:
        print(f"Archetypes missing from the sample: {sorted(missing)}", file=sys.stderr)
        return 1

    # Describe the sample's difficulty from the recorded baseline scores,
    # where they exist. This does not influence selection -- selecting on
    # recorded scores would fit the sample to one run's noise -- it only
    # reports what was drawn.
    difficulty = {"near_cutoff": 0, "scored": 0}
    recorded = REPO / "data" / "eval_run.json"
    if recorded.exists():
        scores = {
            p["file"]: p["score"]
            for p in json.loads(recorded.read_text(encoding="utf-8"))["predictions"]
        }
        for filename in chosen:
            if filename in scores:
                difficulty["scored"] += 1
                distance = min(
                    abs(scores[filename] - ADVANCE_CUTOFF),
                    abs(scores[filename] - HOLD_CUTOFF),
                )
                if distance <= 1.0:
                    difficulty["near_cutoff"] += 1

    out_path = Path(args.out).resolve() if args.out else OUT
    out_path.write_text(
        json.dumps(
            {
                "seed": args.seed,
                "size": len(chosen),
                "labels": dict(sorted(label_counts.items())),
                "archetypes": dict(sorted(archetype_counts.items())),
                "difficulty_from_recorded_baseline": difficulty,
                "files": chosen,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"{len(chosen)} resumes, seed {args.seed}")
    print(f"  labels     {dict(sorted(label_counts.items()))}")
    print(f"  archetypes {dict(sorted(archetype_counts.items()))}")
    if difficulty["scored"]:
        print(
            f"  {difficulty['near_cutoff']} of {difficulty['scored']} scored within "
            "1.0 of a cutoff in the recorded baseline"
        )
    print(f"wrote {out_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
