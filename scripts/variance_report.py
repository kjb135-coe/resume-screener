"""Report run-to-run variance across repeated evaluations of one config.

    python scripts/variance_report.py                 # all data/eval_run__var*.json
    python scripts/variance_report.py var1 var2 var3  # explicit tags

Reads recorded runs only. No API calls, no cost.

Why this exists: the pipeline has no temperature knob (the Anthropic SDK
dropped it in 1.0), so repeated runs of an unchanged config do not agree.
PLAN.md section 3c saw 6 of 60 verdicts move between two runs, but those
two runs had a parse fix between them, so only 5 of the flips were
unexplained -- one paired observation, quoted ever since as "10% drift".

A single run cannot support a macro-F1 quoted to three decimals, and
cannot separate a 0.03 improvement from noise. This script turns several
runs of the SAME config into the spread that every comparison in section 8
needs before it means anything.

Writes docs/VARIANCE.md.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CLASSES = ("advance", "hold", "reject")

# Mirrors core.pipeline. Imported by value, not by import, so this script
# reports on runs recorded under whatever cutoffs were live at the time.
ADVANCE_CUTOFF = 4.0
HOLD_CUTOFF = 1.0


def cutoff_distance(score: float) -> float:
    return min(abs(score - ADVANCE_CUTOFF), abs(score - HOLD_CUTOFF))


def macro_f1(rows: list[tuple[str, str]]) -> tuple[float, dict[str, float]]:
    """Recompute macro-F1 over an arbitrary subset of candidates.

    The stored `macro_f1` in each run file covers whatever that run
    managed to score. When one run is partial, comparing stored figures
    compares two different corpora. Recomputing both over the candidates
    they share is the only comparison that means anything.
    """
    per_class = {}
    for cls in CLASSES:
        tp = sum(1 for t, p in rows if t == cls and p == cls)
        fp = sum(1 for t, p in rows if t != cls and p == cls)
        fn = sum(1 for t, p in rows if t == cls and p != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[cls] = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return statistics.mean(per_class.values()), per_class


def spread(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "range": max(values) - min(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def fmt(s: dict[str, float], places: int = 3) -> str:
    p = places
    return (
        f"{s['mean']:.{p}f} | {s['min']:.{p}f}–{s['max']:.{p}f} "
        f"| {s['range']:.{p}f} | {s['stdev']:.{p}f}"
    )


def load(tags: list[str]) -> list[dict]:
    runs = []
    for tag in tags:
        # `baseline` is the only tag that lives in the unsuffixed file.
        path = DATA / ("eval_run.json" if tag == "baseline" else f"eval_run__{tag}.json")
        if not path.exists():
            print(f"missing: {path.relative_to(REPO)}", file=sys.stderr)
            continue
        run = json.loads(path.read_text(encoding="utf-8"))
        run["_tag"] = tag
        # Runs recorded before the 2026-08-27 pricing fix carry inflated
        # dollar figures and no per-model split. Their token counts are
        # still real; only the cost is wrong. `cost_by_model` was added in
        # the same change, so its absence dates the run.
        run["_cost_valid"] = "cost_by_model" in run
        runs.append(run)
    return runs


def main() -> int:
    tags = sys.argv[1:]
    if not tags:
        tags = sorted(p.stem.split("__", 1)[1] for p in DATA.glob("eval_run__var*.json"))
    runs = load(tags)
    if len(runs) < 2:
        print("Need at least 2 recorded runs to report a spread.", file=sys.stderr)
        return 1

    # A run that dropped resumes is not a smaller run -- the failures cluster
    # wherever the batch died, so its class balance is skewed and its STORED
    # macro-F1 is not comparable to a full run's. The fix is not to discard
    # it. Every metric below is recomputed over the candidates that every
    # run scored, so a partial run contributes in full on the subset it
    # covers. One candidate's verdict never depended on which others ran.
    biggest = max(r["n"] for r in runs)
    partial = [r for r in runs if r["n"] != biggest]

    by_run: list[dict[str, dict]] = [
        {p["file"]: p for p in r["predictions"]} for r in runs
    ]
    shared = sorted(set.intersection(*(set(d) for d in by_run)))
    if not shared:
        print("No candidate was scored by every run.", file=sys.stderr)
        return 1
    for run, preds in zip(runs, by_run):
        rows = [(preds[f]["expected"], preds[f]["predicted"]) for f in shared]
        run["_f1"], run["_per_class"] = macro_f1(rows)
        run["_acc"] = sum(1 for t, p in rows if t == p) / len(rows)
        run["_esc"] = sum(1 for f in shared if preds[f]["escalated"]) / len(shared)

    lines: list[str] = []
    add = lines.append
    add("# Run-to-run variance\n")
    add(f"{len(runs)} runs of one unchanged configuration: "
        + ", ".join(f"`{r['_tag']}`" for r in runs)
        + ".\n")
    add("Every difference below is noise, not a change. **Only pass runs that "
        "share the same code.** This script cannot check that for you, and "
        "comparing runs across a code change is the exact error that made the "
        "original 10% drift figure soft.\n")
    if partial:
        add("**Partial runs present:** "
            + ", ".join(f"`{r['_tag']}` ({r['n']}/{biggest})" for r in partial)
            + ".\n")

    add("## Headline spread\n")
    add(f"All figures are recomputed over the **{len(shared)} candidates every "
        "run scored**, not read from the stored per-run totals. That keeps a "
        "partial run comparable instead of throwing it away.\n")
    add("| Metric | Mean | Range | Spread | Stdev |")
    add("|---|---|---|---|---|")
    metrics = [
        ("Macro-F1", [r["_f1"] for r in runs], 3),
        ("Accuracy", [r["_acc"] for r in runs], 3),
        ("Escalation rate", [r["_esc"] for r in runs], 3),
    ]
    priced = [r for r in runs if r["_cost_valid"] and r["n"] == biggest]
    if len(priced) > 1:
        metrics.append(("Cost (USD)", [r["cost_total"] for r in priced], 3))
    for name, values, places in metrics:
        add(f"| {name} | {fmt(spread(values), places)} |")
    add("")
    add("Cost and wall clock cover each run's whole batch, so they are only "
        "comparable between runs that scored the same number of resumes. They "
        "sit in the per-run table below rather than in this spread.\n")

    f1s = [r["_f1"] for r in runs]
    band = max(f1s) - min(f1s)
    add(f"**The noise band on macro-F1 is {band:.3f}.** Any future change "
        f"that moves macro-F1 by less than this has not been measured — it "
        f"has been observed once.\n")

    # A run that lost candidates to network errors does not lose them at
    # random. An escalating candidate makes an extra arbiter call, so it is
    # more exposed to a dropped connection -- and it is also the hard
    # candidate carrying most of the disagreement. A run can therefore end up
    # holding only the easy cases, which quietly understates the variance it
    # is supposed to measure. `var3` did exactly this on 2026-08-27: 29 of 60
    # scored, zero escalations, panel spread capped at 5.0 against 9.0
    # elsewhere. Compare these columns before trusting a run.
    add("## Run health\n")
    add("Check this before reading anything above. A run that dropped "
        "candidates to network errors keeps the easy ones, which makes the "
        "noise look smaller than it is.\n")
    add("| Run | Scored | Escalated (own batch) | Max panel spread | Median spread |")
    add("|---|---|---|---|---|")
    for run in runs:
        spreads = sorted(p["panel_spread"] for p in run["predictions"])
        own_esc = sum(1 for p in run["predictions"] if p["escalated"])
        add(f"| `{run['_tag']}` | {run['n']}/{biggest} | "
            f"{own_esc}/{run['n']} ({own_esc / run['n']:.0%}) | "
            f"{max(spreads):.1f} | {statistics.median(spreads):.1f} |")
    add("")
    tops = [max(p["panel_spread"] for p in r["predictions"]) for r in runs]
    if max(tops) - min(tops) >= 2.0:
        add("**Warning: the runs do not agree on how much the panel disagreed.** "
            "A run with a much lower maximum spread is missing its hard "
            "candidates. Treat it as a biased subset and exclude it.\n")

    add("## Per-class F1\n")
    add("The narrow middle class carries the most instability. It has a "
        "boundary on both sides, so jitter can push a candidate out either way.\n")
    add("| Class | Mean | Range | Spread | Stdev |")
    add("|---|---|---|---|---|")
    for cls in CLASSES:
        values = [r["_per_class"][cls] for r in runs]
        add(f"| `{cls}` | {fmt(spread(values))} |")
    add("")

    # Verdict churn. This is the useful output: not how many verdicts moved,
    # but which candidates cannot hold still.
    per_file: dict[str, dict] = {}
    for run in runs:
        for pred in run["predictions"]:
            entry = per_file.setdefault(
                pred["file"],
                {"expected": pred["expected"], "verdicts": [], "scores": []},
            )
            entry["verdicts"].append(pred["predicted"])
            entry["scores"].append(pred["score"])

    complete = {f: e for f, e in per_file.items() if len(e["verdicts"]) == len(runs)}
    unstable = {f: e for f, e in complete.items() if len(set(e["verdicts"])) > 1}

    add("## Verdict churn\n")
    add(f"- Candidates scored in all {len(runs)} runs: **{len(complete)}**")
    add(f"- Candidates that changed verdict at least once: "
        f"**{len(unstable)}** ({len(unstable) / len(complete):.0%})")
    stable_correct = sum(
        1 for e in complete.values()
        if len(set(e["verdicts"])) == 1 and e["verdicts"][0] == e["expected"]
    )
    add(f"- Candidates correct and stable in every run: **{stable_correct}**")
    add("")

    if unstable:
        add("Every candidate that moved:\n")
        add("| Candidate | Label | Verdicts | Scores | Score range | Nearest cutoff |")
        add("|---|---|---|---|---|---|")
        for f, e in sorted(unstable.items(), key=lambda kv: -(max(kv[1]["scores"]) - min(kv[1]["scores"]))):
            scores = e["scores"]
            rng = max(scores) - min(scores)
            dist = min(cutoff_distance(s) for s in scores)
            add(f"| `{f}` | {e['expected']} | {' → '.join(e['verdicts'])} "
                f"| {', '.join(f'{s:.1f}' for s in scores)} | {rng:.1f} | {dist:.1f} |")
        add("")

        near = sum(1 for e in unstable.values() if min(cutoff_distance(s) for s in e["scores"]) <= 1.0)
        add(f"**{near} of {len(unstable)}** unstable candidates sat within 1.0 of a "
            f"cutoff (`{HOLD_CUTOFF}` or `{ADVANCE_CUTOFF}`). That is the mechanism: "
            "scores bunch near the thresholds, so small jitter crosses a line.\n")

    # Score movement, including candidates whose verdict never changed. A
    # stable verdict can still hide a score swinging under it.
    ranges = [max(e["scores"]) - min(e["scores"]) for e in complete.values()]
    add("## Score movement\n")
    add("Verdict churn undercounts the noise. A score can swing and still land "
        "in the same bucket.\n")
    add(f"- Mean score range across runs: **{statistics.mean(ranges):.2f}** points")
    add(f"- Largest single-candidate swing: **{max(ranges):.1f}** points")
    add(f"- Candidates whose score never moved: "
        f"**{sum(1 for r in ranges if r == 0)}** of {len(complete)}")
    add("")

    # Parse failures separate mechanical noise from judgment noise. A lost
    # panel call scores 0.0, which reads as a confident reject.
    add("## Parse failures\n")
    add("A failed parse scores 0.0, which is indistinguishable from a confident "
        "reject in the final verdict. This is noise with a mechanical cause, not "
        "a judgment the model made.\n")
    add("| Run | Failed panel calls | Of total | Rate |")
    add("|---|---|---|---|")
    pf_rates = []
    for run in runs:
        failed = sum(
            1 for p in run["predictions"] for a in p["panel"] if a.get("parse_failed")
        )
        total = sum(len(p["panel"]) for p in run["predictions"])
        pf_rates.append(failed / total if total else 0.0)
        add(f"| `{run['_tag']}` | {failed} | {total} | {failed / total:.1%} |")
    add("")
    add(f"Rate across runs: {min(pf_rates):.1%}–{max(pf_rates):.1%}.\n")

    add("## Per-run detail\n")
    add(f"`Macro-F1` is on the shared {len(shared)}. `Stored` is what the run "
        "itself reported over whatever it scored — shown only so the two are "
        "not confused.\n")
    add("| Run | n | Macro-F1 | Stored | Accuracy | Escalated | Cost | Wall clock |")
    add("|---|---|---|---|---|---|---|---|")
    for run in runs:
        cost = f"${run['cost_total']:.3f}" + ("" if run["_cost_valid"] else " (stale rates)")
        add(f"| `{run['_tag']}` | {run['n']} | **{run['_f1']:.3f}** "
            f"| {run['macro_f1']:.3f} | {run['_acc']:.3f} "
            f"| {run['_esc']:.0%} | {cost} | {run['wall_clock_s']:.0f}s |")
    add("")

    add("## How to use this\n")
    add(f"Quote macro-F1 as a range, not a point. Treat any difference under "
        f"{band:.3f} as unresolved. With {len(runs)} runs this is a rough band and "
        "not a confidence interval — it is a floor on the noise, and more runs "
        "would likely widen it rather than narrow it.\n")

    out = REPO / "docs" / "VARIANCE.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"macro-F1 {min(f1s):.3f}–{max(f1s):.3f}  (band {band:.3f})")
    print(f"unstable candidates: {len(unstable)}/{len(complete)}")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
