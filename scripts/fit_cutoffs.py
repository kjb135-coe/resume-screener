"""Fit the score-to-verdict cutoffs per model, and test them honestly.

    python scripts/fit_cutoffs.py anthropic-control-60 gpt-5.6-luna-60

Reads recorded bake-off runs. No API calls, no cost.

WHY THIS EXISTS
---------------
The pipeline turns a 0-10 score into a verdict with two cutoffs
(`ADVANCE_CUTOFF = 4.0`, `HOLD_CUTOFF = 1.0`). Those were swept against
**Sonnet's** score distribution. A model that grades on a different scale
is then penalised for the scale rather than for its judgment.

That is not hypothetical. On the 20-resume bake-off, GPT-5.6 Luna scored
0.517 under the shipped cutoffs and 0.896 under cutoffs fitted to itself
-- a swing of 0.379 with the model untouched. Its mean score was 4.60
against Sonnet's 2.65, and every one of its 27 errors was a candidate
graded too generously.

WHY "BEST CUTOFFS" IS NOT AN ACCURACY NUMBER
--------------------------------------------
Sweeping every cutoff pair and keeping the winner fits the cutoffs to the
same resumes they are then scored on. That is the definition of
overfitting, and `docs/LIMITATIONS.md` already flags it for the shipped
values. It answers "how good could this model be if perfectly calibrated"
-- an upper bound, not a measurement.

So this script reports BOTH:

  fitted   -- best macro-F1 on the data used to choose the cutoffs.
              An upper bound. Never quote it as accuracy.
  held-out -- cutoffs chosen on one split, scored on resumes they have
              never seen, averaged over every fold. This is the honest
              number, and it is the one to compare across models.

The gap between them is the overfitting, made visible.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
LABELS = REPO / "data" / "labels.json"
CLASSES = ("advance", "hold", "reject")
GRID = [x / 10 for x in range(101)]


def macro_f1(rows: list[tuple[str, str]]) -> float:
    scores = []
    for cls in CLASSES:
        tp = sum(1 for t, p in rows if t == cls and p == cls)
        fp = sum(1 for t, p in rows if t != cls and p == cls)
        fn = sum(1 for t, p in rows if t == cls and p != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return statistics.mean(scores)


def verdict(score: float, advance: float, hold: float) -> str:
    if score >= advance:
        return "advance"
    return "hold" if score >= hold else "reject"


def best_cutoffs(rows: list[tuple[str, float]]) -> tuple[float, float, float]:
    """Grid-search both cutoffs. rows = [(true_label, score)]."""
    best = (-1.0, 4.0, 1.0)
    for advance in GRID:
        for hold in GRID:
            if hold >= advance:
                continue
            score = macro_f1([(t, verdict(s, advance, hold)) for t, s in rows])
            if score > best[0]:
                best = (score, advance, hold)
    return best


def load_arm(arm: str) -> list[list[tuple[str, str, float]]]:
    """Each recorded run as [(file, true_label, score)].

    Accepts either a bake-off arm name or an `eval_run` tag, so cutoffs
    can be fitted on the 60-resume variance runs as well as on bake-off
    arms. Partial runs are skipped: their surviving candidates are not a
    random subset (see the discarded var3 in docs/RESULTS_HISTORY.md), so
    cutoffs fitted on them would be fitted to the survivorship.
    """
    runs = []
    paths = sorted(DATA.glob(f"bakeoff__{arm}__run*.json"))
    paths += sorted(DATA.glob(f"eval_run__{arm}.json"))
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        requested = data.get("requested")
        if requested and data.get("n", 0) < requested:
            print(
                f"  skipping {path.name}: partial ({data['n']}/{requested})",
                file=sys.stderr,
            )
            continue
        runs.append(
            [(p["file"], p["expected"], p["score"]) for p in data["predictions"]]
        )
    return runs


def stratified_folds(rows: list[tuple[str, str, float]], k: int) -> list[list[int]]:
    """k folds, each holding roughly the same label mix as the whole.

    Random folds would let one fold miss a class entirely, and macro-F1
    scores a missing class as zero -- which looks like a catastrophic
    model failure and is really a sampling artefact.
    """
    by_label: dict[str, list[int]] = {}
    for index, (_, label, _) in enumerate(rows):
        by_label.setdefault(label, []).append(index)
    folds: list[list[int]] = [[] for _ in range(k)]
    for indices in by_label.values():
        for position, index in enumerate(indices):
            folds[position % k].append(index)
    return folds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("arms", nargs="+")
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    results = {}
    for arm in args.arms:
        runs = load_arm(arm)
        if not runs:
            print(f"no recorded runs for {arm}", file=sys.stderr)
            continue

        # Pool every run's scores. More points behind each cutoff, and it
        # averages out the run-to-run jitter that docs/VARIANCE.md measures
        # at 0.051 -- cutoffs fitted to a single noisy run would themselves
        # be noise.
        pooled = [(f, t, s) for run in runs for f, t, s in run]

        shipped = statistics.mean(
            macro_f1([(t, verdict(s, 4.0, 1.0)) for _, t, s in run]) for run in runs
        )
        fitted_f1, advance, hold = best_cutoffs([(t, s) for _, t, s in pooled])

        # Held-out: choose cutoffs without ever seeing the fold they are
        # scored on.
        folds = stratified_folds(pooled, args.folds)
        held = []
        for fold in folds:
            test_ids = set(fold)
            train = [(t, s) for i, (_, t, s) in enumerate(pooled) if i not in test_ids]
            test = [(t, s) for i, (_, t, s) in enumerate(pooled) if i in test_ids]
            _, fold_advance, fold_hold = best_cutoffs(train)
            held.append(
                macro_f1([(t, verdict(s, fold_advance, fold_hold)) for t, s in test])
            )

        mean_score = statistics.mean(s for _, _, s in pooled)
        results[arm] = {
            "runs": len(runs),
            "n_per_run": len(runs[0]),
            "mean_score": mean_score,
            "shipped_f1": shipped,
            "fitted_f1": fitted_f1,
            "fitted_cutoffs": (advance, hold),
            "heldout_f1": statistics.mean(held),
            "heldout_spread": max(held) - min(held),
        }

    lines: list[str] = []
    add = lines.append
    add("# Verdict cutoffs, fitted and tested per model\n")
    add("The pipeline ships `ADVANCE_CUTOFF = 4.0` / `HOLD_CUTOFF = 1.0`, "
        "swept against Sonnet. A model that grades on a different scale loses "
        "macro-F1 to the mismatch rather than to its judgment. This refits "
        "them per model on recorded scores — offline, no API calls.\n")
    add("| Arm | Mean score | Shipped 4.0/1.0 | Fitted cutoffs | Fitted (upper bound) | **Held-out (honest)** |")
    add("|---|---|---|---|---|---|")
    for arm, r in results.items():
        a, h = r["fitted_cutoffs"]
        add(f"| `{arm}` | {r['mean_score']:.2f} | {r['shipped_f1']:.3f} | {a}/{h} "
            f"| {r['fitted_f1']:.3f} | **{r['heldout_f1']:.3f}** |")
    add("")
    add("**Read the held-out column, not the fitted one.** `Fitted` chooses "
        "the cutoffs on the same resumes it then scores, which is overfitting "
        "by construction — it answers \"how good could this model be if "
        "perfectly calibrated\". `Held-out` chooses cutoffs on "
        f"{args.folds - 1}/{args.folds} of the corpus and scores the fold it "
        "never saw, averaged over all folds. The gap between the two columns "
        "is the overfitting, made visible.\n")
    add("Cutoffs are fitted on every run pooled, not one run, because "
        "run-to-run noise is 0.051 macro-F1 (`docs/VARIANCE.md`) and cutoffs "
        "fitted to a single run would partly be fitted to that noise.\n")

    out = REPO / "docs" / "CUTOFF_FIT.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for arm, r in results.items():
        print(f"{arm:24} shipped {r['shipped_f1']:.3f}  fitted {r['fitted_f1']:.3f} "
              f"@{r['fitted_cutoffs'][0]}/{r['fitted_cutoffs'][1]}  "
              f"held-out {r['heldout_f1']:.3f}")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
