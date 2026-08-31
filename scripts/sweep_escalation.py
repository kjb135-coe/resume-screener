"""Compare escalation policies against the labeled corpus.

    python scripts/sweep_escalation.py --write

PLAN.md section 8 item 5. Like the cutoff sweep, this re-derives decisions
from scores already in data/eval_run.json. No API calls.

## The question

HISTORICAL. Superseded 2026-08-27 by the margin gate, and again on
2026-08-31 when the parallel panel was replaced by a single scoring call
-- there is no panel spread to sweep any more. Kept because
docs/ESCALATION_SWEEP.md cites it and those numbers must stay
reproducible.

When this was written, the pipeline escalated when the panel's score *spread*
exceeds a threshold. That measures variance, not decision uncertainty,
and those are different things. A panel of 9/7/6 has a spread of 3.0 and
escalates -- but every one of those three scores says "good", so no
arbiter ruling could produce a different verdict. The call is spent
resolving a disagreement that has no decision riding on it.

## Policies compared

  spread(T)    escalate when max-min > T. What the pipeline does today.

  band(lo,hi)  escalate when the mean lands near a decision boundary.
               Confident-high and confident-low resolve themselves.

  split(a,h)   escalate when the three agents do not agree on which
               verdict bucket the candidate belongs in. This is decision
               uncertainty measured directly: if all three imply the same
               bucket, the arbiter cannot change the answer.

## What can and cannot be measured here

**Exactly measurable:** how often each policy escalates, and how often it
escalates a candidate whose panel scores all imply the same verdict --
i.e. a call that cannot change anything.

**Not measurable offline:** the accuracy of a policy that escalates a
candidate the recorded run did not escalate, because no arbiter output
exists for that candidate. Accuracy figures here therefore assume an
un-escalated verdict comes from cutoff(mean), and are reported as such.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN_JSON = REPO / "data" / "eval_run.json"
OUT_MD = REPO / "docs" / "ESCALATION_SWEEP.md"

CLASSES = ("advance", "hold", "reject")


def bucket(score: float, advance_at: float, hold_at: float) -> str:
    if score >= advance_at:
        return "advance"
    if score >= hold_at:
        return "hold"
    return "reject"


def macro_f1(truth: list[str], predicted: list[str]) -> float:
    out = []
    for cls in CLASSES:
        tp = sum(1 for t, p in zip(truth, predicted) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(truth, predicted) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(truth, predicted) if t == cls and p != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        out.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(out) / len(out)


def panel_scores(row: dict) -> list[float]:
    return [a["score"] for a in row["panel"]]


def decisive(row: dict, advance_at: float, hold_at: float) -> bool:
    """Could an arbiter ruling change this verdict?

    Only if the three agents do not already agree on the bucket. When all
    three imply `advance`, every defensible resolution is still `advance`.
    """
    return len({bucket(s, advance_at, hold_at) for s in panel_scores(row)}) > 1


def evaluate(rows, should_escalate, advance_at, hold_at) -> dict:
    truth = [r["expected"] for r in rows]
    predicted, escalations, pointless = [], 0, 0

    for row in rows:
        mean = statistics.mean(panel_scores(row))
        if should_escalate(row):
            escalations += 1
            if not decisive(row, advance_at, hold_at):
                pointless += 1
            # Use the recorded arbiter verdict where we have one; there is
            # no counterfactual for candidates the real run never escalated.
            predicted.append(row["predicted"] if row["escalated"] else bucket(mean, advance_at, hold_at))
        else:
            predicted.append(bucket(mean, advance_at, hold_at))

    return {
        "macro_f1": macro_f1(truth, predicted),
        "escalations": escalations,
        "rate": escalations / len(rows),
        "pointless": pointless,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--advance", type=float, default=7.0)
    parser.add_argument("--hold", type=float, default=5.0)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if not RUN_JSON.exists():
        print(f"{RUN_JSON} not found -- run scripts/evaluate.py first.", file=sys.stderr)
        return 2

    rows = json.loads(RUN_JSON.read_text(encoding="utf-8"))["predictions"]
    a, h = args.advance, args.hold

    policies: list[tuple[str, object]] = []
    for threshold in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        policies.append(
            (f"spread > {threshold}", lambda r, t=threshold: max(panel_scores(r)) - min(panel_scores(r)) > t)
        )
    for lo, hi in ((4.0, 7.0), (5.0, 7.0), (3.0, 7.0)):
        policies.append(
            (
                f"band {lo}-{hi}",
                lambda r, lo=lo, hi=hi: lo <= statistics.mean(panel_scores(r)) < hi,
            )
        )
    policies.append((f"split @ {a}/{h}", lambda r: decisive(r, a, h)))
    policies.append(("never escalate", lambda r: False))

    lines = [
        "# Escalation sweep\n",
        (
            f"Generated by `scripts/sweep_escalation.py` from `data/eval_run.json`, "
            f"cutoffs {a}/{h}. No API calls.\n"
        ),
        (
            "`pointless` counts escalations where all three agents already implied "
            "the same verdict, so no arbiter ruling could have changed the answer. "
            "Those calls are pure cost.\n"
        ),
        "| Policy | Escalations | Rate | Pointless | macro-F1 |",
        "|---|---|---|---|---|",
    ]

    print(f"{'policy':<18}{'esc':>5}{'rate':>8}{'pointless':>11}{'macro-F1':>10}")
    print("-" * 52)
    for name, fn in policies:
        r = evaluate(rows, fn, a, h)
        print(f"{name:<18}{r['escalations']:>5}{r['rate']:>7.0%}{r['pointless']:>11}{r['macro_f1']:>10.3f}")
        lines.append(
            f"| `{name}` | {r['escalations']}/{len(rows)} | {r['rate']:.0%} | "
            f"{r['pointless']} | {r['macro_f1']:.3f} |"
        )

    lines.append(
        "\n## Reading this\n\n"
        "macro-F1 across policies is close because the arbiter's contribution is "
        "small once cutoffs are sane -- see `docs/CUTOFF_SWEEP.md`. The column that "
        "separates the policies is **cost**: escalation rate, and how much of it is "
        "spent on candidates whose verdict was never in doubt.\n"
    )
    if args.write:
        OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
