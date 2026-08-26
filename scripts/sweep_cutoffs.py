"""Sweep the score-to-recommendation cutoffs against the labeled corpus.

    python scripts/sweep_cutoffs.py
    python scripts/sweep_cutoffs.py --step 0.1 --write

PLAN.md section 8 item 6: the 7.0/5.0 split was hand-picked and never
tested. This tests it. Nothing here calls an API -- it re-thresholds
scores already recorded in data/eval_run.json, so it is free and instant.

## The thing that makes this subtle

`screen_one` does NOT derive the recommendation from the cutoffs for
every candidate. When the panel disagrees, the arbiter returns its own
recommendation *and* that is what the pipeline uses. In the recorded run
that is 33 of 60 candidates, and on 17 of them the arbiter's verdict
differs from what the cutoffs would have said -- always more generously.

So a sweep that simply applies cutoffs to all 60 scores is not measuring
the pipeline. It is measuring a different pipeline, one where the arbiter
returns a number and nothing else. Both are reported below, clearly
separated:

  respect-arbiter : escalated candidates keep the arbiter's verdict.
                    Cutoffs move only the 27 unescalated ones. This is
                    what changing ADVANCE_CUTOFF/HOLD_CUTOFF in
                    pipeline.py would actually do today.

  uniform         : cutoffs applied to all 60 scores. This is a
                    hypothetical, and would require the arbiter to stop
                    returning a recommendation of its own.

Reporting only the second would overstate what a cutoff change buys.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN_JSON = REPO / "data" / "eval_run.json"
OUT_MD = REPO / "docs" / "CUTOFF_SWEEP.md"

CLASSES = ("advance", "hold", "reject")
CURRENT = (7.0, 5.0)


def classify(score: float, advance_at: float, hold_at: float) -> str:
    if score >= advance_at:
        return "advance"
    if score >= hold_at:
        return "hold"
    return "reject"


def macro_f1(truth: list[str], predicted: list[str]) -> float:
    scores = []
    for cls in CLASSES:
        tp = sum(1 for t, p in zip(truth, predicted) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(truth, predicted) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(truth, predicted) if t == cls and p != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return sum(scores) / len(scores)


def predict(rows: list[dict], advance_at: float, hold_at: float, *, uniform: bool) -> list[str]:
    """Recommendations under one cutoff pair.

    `uniform=False` keeps the arbiter's verdict on escalated candidates,
    which is what the running pipeline does.
    """
    out = []
    for row in rows:
        if not uniform and row["escalated"]:
            out.append(row["predicted"])
        else:
            out.append(classify(row["score"], advance_at, hold_at))
    return out


def accuracy(truth: list[str], predicted: list[str]) -> float:
    return sum(1 for t, p in zip(truth, predicted) if t == p) / len(truth)


def sweep(rows: list[dict], step: float, *, uniform: bool) -> list[tuple]:
    truth = [r["expected"] for r in rows]
    scores = sorted({round(r["score"], 2) for r in rows})
    lo, hi = min(scores), max(scores)

    results = []
    advance_at = lo
    while advance_at <= hi + 1e-9:
        hold_at = lo
        while hold_at <= advance_at + 1e-9:
            predicted = predict(rows, advance_at, hold_at, uniform=uniform)
            results.append(
                (macro_f1(truth, predicted), accuracy(truth, predicted), advance_at, hold_at)
            )
            hold_at = round(hold_at + step, 4)
        advance_at = round(advance_at + step, 4)
    # Ties broken toward the cutoffs closest to the current ones, so a
    # tie never recommends churn for its own sake.
    results.sort(key=lambda r: (-r[0], -r[1], abs(r[2] - CURRENT[0]) + abs(r[3] - CURRENT[1])))
    return results


def per_class_recall(truth: list[str], predicted: list[str]) -> dict[str, float]:
    out = {}
    for cls in CLASSES:
        tp = sum(1 for t, p in zip(truth, predicted) if t == cls and p == cls)
        support = sum(1 for t in truth if t == cls)
        out[cls] = tp / support if support else 0.0
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=float, default=0.25, help="cutoff grid step")
    parser.add_argument("--top", type=int, default=8, help="how many rows to show")
    parser.add_argument("--write", action="store_true", help="write docs/CUTOFF_SWEEP.md")
    args = parser.parse_args()

    if not RUN_JSON.exists():
        print(f"{RUN_JSON} not found -- run scripts/evaluate.py first.", file=sys.stderr)
        return 2

    run = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    rows = run["predictions"]
    truth = [r["expected"] for r in rows]
    escalated = sum(1 for r in rows if r["escalated"])

    lines: list[str] = []
    add = lines.append
    add("# Cutoff sweep\n")
    add(
        f"Generated by `scripts/sweep_cutoffs.py` from `data/eval_run.json` "
        f"({run['n']} resumes, step {args.step}). No API calls: this "
        "re-thresholds scores that were already recorded.\n"
    )
    add(
        f"**{escalated} of {run['n']}** candidates were escalated, and the arbiter "
        "returns its own recommendation for those rather than deriving one from "
        "the cutoffs. So two policies are reported. `respect-arbiter` is what "
        "editing `ADVANCE_CUTOFF`/`HOLD_CUTOFF` in `pipeline.py` would actually "
        "change today; `uniform` is a hypothetical in which the arbiter returns "
        "only a score.\n"
    )

    for uniform in (False, True):
        policy = "uniform" if uniform else "respect-arbiter"
        results = sweep(rows, args.step, uniform=uniform)
        baseline_pred = predict(rows, *CURRENT, uniform=uniform)
        baseline_f1 = macro_f1(truth, baseline_pred)
        best_f1, _best_acc, best_adv, best_hold = results[0]

        print(f"\n=== {policy} ===")
        print(f"  current {CURRENT[0]}/{CURRENT[1]}: macro-F1 {baseline_f1:.3f}")
        print(f"  best    {best_adv}/{best_hold}: macro-F1 {best_f1:.3f}  "
              f"({best_f1 - baseline_f1:+.3f})")

        add(f"\n## Policy: `{policy}`\n")
        add(f"Current cutoffs {CURRENT[0]}/{CURRENT[1]} give macro-F1 "
            f"**{baseline_f1:.3f}**, accuracy {accuracy(truth, baseline_pred):.3f}.\n")
        add("| advance ≥ | hold ≥ | macro-F1 | accuracy | Δ vs current |")
        add("|---|---|---|---|---|")
        for f1, acc, adv, hold in results[: args.top]:
            add(f"| {adv:g} | {hold:g} | {f1:.3f} | {acc:.3f} | {f1 - baseline_f1:+.3f} |")

        best_pred = predict(rows, best_adv, best_hold, uniform=uniform)
        add("\nRecall per class at the best cutoffs, against current:\n")
        add("| Class | Current | Best | Δ |")
        add("|---|---|---|---|")
        now, best = per_class_recall(truth, baseline_pred), per_class_recall(truth, best_pred)
        for cls in CLASSES:
            add(f"| {cls} | {now[cls]:.2f} | {best[cls]:.2f} | {best[cls] - now[cls]:+.2f} |")
        print("  per-class recall:",
              {c: f"{now[c]:.2f}->{best[c]:.2f}" for c in CLASSES})

    add("\n## Caveat\n")
    add(
        "These cutoffs are chosen on the same 60 resumes they are scored "
        "against, so the gain is an upper bound rather than a held-out "
        "result. With 20 per class there is no honest train/test split "
        "available. Treat a win here as a reason to re-run the full eval "
        "with the new cutoffs, not as a measured improvement on its own -- "
        "and note that PLAN.md section 3c measured 10% verdict drift "
        "between identical runs, which is larger than several of the "
        "differences in these tables.\n"
    )

    if args.write:
        OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
