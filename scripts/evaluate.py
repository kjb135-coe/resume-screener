"""Score the pipeline against the labeled corpus.

    python scripts/evaluate.py                # full corpus
    python scripts/evaluate.py --limit 6      # cheap smoke run
    python scripts/evaluate.py --no-cache     # for the caching comparison
    python scripts/evaluate.py --panel-model claude-haiku-4-5-20251001 \\
        --tag cheap-panel                     # tier bake-off, PLAN.md section 8

Writes docs/EVAL_RESULTS.md and data/eval_run.json for `--tag baseline`
(the default) -- these are the canonical run every other doc, the web
app, and CANDIDATE_REPORTS.md read from. Any other `--tag` writes to
`docs/EVAL_RESULTS__<tag>.md` and `data/eval_run__<tag>.json` instead, so
a comparison run can never silently overwrite the baseline everything
else depends on.

Metrics follow the plan: macro-F1 over advance/hold/reject as the primary
number, reported SEPARATELY from escalation rate rather than blended, plus
real measured cost and latency taken from API usage fields rather than
estimated.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_screener.core.models import Verdict
from resume_screener.core.pipeline import DEFAULT_MODEL_IDS, default_models, screen_one

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "synthetic_resumes"
LABELS = REPO / "data" / "labels.json"
JD_PATH = REPO / "docs" / "job_description.md"

CLASSES = ("advance", "hold", "reject")

# Published per-million-token rates, used only to turn measured token
# counts into a dollar figure. Token counts themselves are real.
#
# Verified against platform.claude.com/docs/en/about-claude/pricing on
# 2026-08-27. Two of these three were WRONG before that check, and every
# cost figure this repo published was inflated as a result:
#   sonnet-5 was carrying Sonnet 4.6 rates ($3/$15) -- it is $2/$10
#   opus-5   was carrying Opus 4.1 rates ($15/$75)  -- it is $5/$25
# The recorded run reported $1.796; at correct rates the same token
# counts come to roughly $1.20. See docs/COST_ANALYSIS.md.
#
# cache_write is the 5-minute rate (1.25x base). This code never sets
# ttl="1h", so the 2x rate does not apply -- see COST_ANALYSIS.md on why
# the 1-hour TTL would be a pure loss for a continuous batch run.
PRICING = {
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
}


def prf(y_true: list[str], y_pred: list[str], cls: str) -> tuple[float, float, float, int]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
    support = sum(1 for t in y_true if t == cls)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, support


def estimate_cost(verdicts: list[Verdict]) -> float:
    """Real measured cost, priced per model that actually spent the tokens.

    Earlier this priced a whole Verdict at whichever model ran first --
    Haiku, always, since extraction leads the cascade. Every Sonnet panel
    call and every Opus arbiter call was billed at Haiku rates, which
    understated a run several-fold. Usage.by_model exists to fix that.
    """
    cost = 0.0
    for verdict in verdicts:
        for model_id, counts in verdict.usage.by_model.items():
            rates = PRICING.get(model_id) or PRICING["claude-sonnet-5"]
            cost += (
                counts.get("input_tokens", 0) / 1e6 * rates["in"]
                + counts.get("output_tokens", 0) / 1e6 * rates["out"]
                + counts.get("cache_read_input_tokens", 0) / 1e6 * rates["cache_read"]
                + counts.get("cache_creation_input_tokens", 0) / 1e6 * rates["cache_write"]
            )
    return cost


def cost_by_model(verdicts: list[Verdict]) -> dict[str, float]:
    """Same arithmetic, kept split so the expensive tier is visible."""
    out: dict[str, float] = {}
    for verdict in verdicts:
        for model_id, counts in verdict.usage.by_model.items():
            rates = PRICING.get(model_id) or PRICING["claude-sonnet-5"]
            out[model_id] = out.get(model_id, 0.0) + (
                counts.get("input_tokens", 0) / 1e6 * rates["in"]
                + counts.get("output_tokens", 0) / 1e6 * rates["out"]
                + counts.get("cache_read_input_tokens", 0) / 1e6 * rates["cache_read"]
                + counts.get("cache_creation_input_tokens", 0) / 1e6 * rates["cache_write"]
            )
    return out


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--no-cache", action="store_true", help="disable prompt caching")
    parser.add_argument("--tag", default="baseline", help="label for this configuration")
    for slot in DEFAULT_MODEL_IDS:
        parser.add_argument(
            f"--{slot}-model",
            default=None,
            help=f"override the {slot!r} model slot (default: {DEFAULT_MODEL_IDS[slot]})",
        )
    args = parser.parse_args()

    overrides = {
        slot: getattr(args, f"{slot}_model")
        for slot in DEFAULT_MODEL_IDS
        if getattr(args, f"{slot}_model")
    }

    # Only `--tag baseline` (the default) is allowed to touch the files
    # everything else in the repo reads: the web app's recorded-run tab,
    # CANDIDATE_REPORTS.md, RESULTS_HISTORY.md's numbers. Any other tag is
    # a comparison run and gets its own filenames so it cannot clobber
    # that baseline by accident.
    suffix = "" if args.tag == "baseline" else f"__{args.tag}"
    results_md = REPO / "docs" / f"EVAL_RESULTS{suffix}.md"
    results_json = REPO / "data" / f"eval_run{suffix}.json"

    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    job_description = JD_PATH.read_text(encoding="utf-8")
    items = sorted(labels.items())
    if args.limit:
        # Stratify across labels. Taking the first N alphabetically lands
        # entirely inside one archetype, which makes macro-F1 meaningless
        # (one class present, two scoring zero by definition).
        buckets: dict[str, list] = {}
        for entry in items:
            buckets.setdefault(entry[1]["label"], []).append(entry)
        stratified: list = []
        while len(stratified) < args.limit and any(buckets.values()):
            for label in CLASSES:
                if buckets.get(label) and len(stratified) < args.limit:
                    stratified.append(buckets[label].pop(0))
        items = stratified

    if args.no_cache:
        from resume_screener.core import router

        original = router.AnthropicModel.complete

        async def uncached(self, system, user, *, max_tokens=1024, cache_system=True):
            return await original(self, system, user, max_tokens=max_tokens, cache_system=False)

        router.AnthropicModel.complete = uncached

    models = default_models(overrides)
    semaphore = asyncio.Semaphore(args.concurrency)
    if overrides:
        print(f"Model overrides: {overrides}")
    print(f"Evaluating {len(items)} resumes [{args.tag}]...\n")
    started = time.monotonic()

    async def run(filename: str, meta: dict):
        async with semaphore:
            try:
                verdict = await screen_one(str(CORPUS / filename), job_description, models)
                print(f"  {meta['label']:8} -> {verdict.recommendation.value:8} "
                      f"{verdict.score:4.1f}  {filename}")
                return filename, meta, verdict
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED {filename}: {exc}")
                return filename, meta, None

    results = await asyncio.gather(*[run(f, m) for f, m in items])
    wall_clock = time.monotonic() - started

    rows = [(f, m, v) for f, m, v in results if v is not None]
    y_true = [m["label"] for _, m, _ in rows]
    y_pred = [v.recommendation.value for _, _, v in rows]
    verdicts = [v for _, _, v in rows]

    per_class = {c: prf(y_true, y_pred, c) for c in CLASSES}
    macro_f1 = statistics.mean(per_class[c][2] for c in CLASSES)
    if not rows:
        print(
            "\nNo resume was scored successfully, so there is nothing to report.\n"
            "The log above has the reason for each failure. A run that dies this "
            "way most often means the API key is unusable -- an exhausted credit "
            "balance returns HTTP 400 per request rather than failing up front, "
            "so every resume fails individually and the batch looks like a "
            "scoring problem instead of a billing one.",
            file=sys.stderr,
        )
        return 1

    if len(rows) < len(items):
        # A partial run is not a smaller run. The failures are not random --
        # they cluster wherever the batch stopped -- so the class balance is
        # skewed and macro-F1 over the survivors is not comparable to a full
        # run. Loud, because the number below still looks perfectly credible.
        print(
            f"\n!! PARTIAL RUN: {len(rows)} of {len(items)} resumes scored. "
            f"{len(items) - len(rows)} failed -- see the log above.\n"
            "!! Metrics below cover only the survivors and are NOT comparable "
            "to a full run. Do not record them in docs/RESULTS_HISTORY.md.",
            file=sys.stderr,
        )

    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(rows)
    escalated = sum(1 for v in verdicts if v.escalated)
    flagged = sum(1 for v in verdicts if v.review_reason is not None)
    latencies = sorted(v.usage.latency_s for v in verdicts)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    cost = estimate_cost(verdicts)

    by_archetype: dict[str, list[bool]] = {}
    for _, meta, verdict in rows:
        by_archetype.setdefault(meta["archetype"], []).append(
            meta["label"] == verdict.recommendation.value
        )

    confusion = Counter((t, p) for t, p in zip(y_true, y_pred))

    lines: list[str] = []
    add = lines.append
    add(f"# Evaluation results — `{args.tag}`\n")
    add(f"{len(rows)} of {len(items)} resumes scored. "
        f"Prompt caching: {'off' if args.no_cache else 'on'}.\n")
    if overrides:
        add("**Model overrides from baseline:**\n")
        for slot, model_id in overrides.items():
            add(f"- `{slot}`: `{DEFAULT_MODEL_IDS[slot]}` → `{model_id}`")
        add("")
    add("## Headline\n")
    add("| Metric | Value |")
    add("|---|---|")
    add(f"| **Macro-F1** | **{macro_f1:.3f}** |")
    add(f"| Accuracy | {accuracy:.3f} |")
    add(f"| Escalated to arbiter | {escalated}/{len(rows)} ({escalated / len(rows):.0%}) |")
    add(f"| Flagged for human review | {flagged}/{len(rows)} ({flagged / len(rows):.0%}) |")
    add(f"| Cost per resume | ${cost / len(rows):.4f} |")
    add(f"| Total cost | ${cost:.3f} |")
    add("")
    add("## Cost by model\n")
    add("Priced per model that actually spent the tokens. This used to be "
        "billed entirely at the first model in the cascade -- Haiku -- which "
        "understated real spend several-fold.\n")
    add("| Model | Cost | Share |")
    add("|---|---|---|")
    for model_id, amount in sorted(cost_by_model(verdicts).items(), key=lambda kv: -kv[1]):
        add(f"| `{model_id}` | ${amount:.3f} | {amount / cost:.0%} |")
    add(f"| Latency p50 / p95 (model time) | {p50:.1f}s / {p95:.1f}s |")
    add(f"| Wall clock, whole batch | {wall_clock:.0f}s |")

    add("\n## Per class\n")
    add("| Class | Precision | Recall | F1 | Support |")
    add("|---|---|---|---|---|")
    for c in CLASSES:
        p, r, f, s = per_class[c]
        add(f"| {c} | {p:.3f} | {r:.3f} | {f:.3f} | {s} |")

    add("\n## Confusion matrix\n")
    add("Rows are ground truth, columns are predictions.\n")
    add("| | " + " | ".join(f"pred {c}" for c in CLASSES) + " |")
    add("|---|" + "---|" * len(CLASSES))
    for t in CLASSES:
        add(f"| **true {t}** | " + " | ".join(str(confusion[(t, p)]) for p in CLASSES) + " |")

    add("\n## Accuracy by archetype\n")
    add("This is the diagnostic that matters most — a headline number can look "
        "fine while one archetype fails completely.\n")
    add("| Archetype | Correct | Accuracy |")
    add("|---|---|---|")
    for archetype, hits in sorted(by_archetype.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        add(f"| {archetype} | {sum(hits)}/{len(hits)} | {sum(hits) / len(hits):.0%} |")

    add("\n## Every candidate\n")
    add("| Candidate | Archetype | Expected | Predicted | Score | Spread | Arbiter | Reasoning |")
    add("|---|---|---|---|---|---|---|---|")
    for filename, meta, verdict in sorted(rows, key=lambda r: -r[2].score):
        ok = "" if meta["label"] == verdict.recommendation.value else " ⚠"
        reasoning = verdict.rationale.replace("|", "\\|").replace("\n", " ")
        if len(reasoning) > 240:
            reasoning = reasoning[:237] + "..."
        add(
            f"| {verdict.candidate.name} | {meta['archetype']} | {meta['label']} | "
            f"{verdict.recommendation.value}{ok} | {verdict.score:.1f} | "
            f"{verdict.panel_spread:.1f} | {'yes' if verdict.escalated else 'no'} | {reasoning} |"
        )

    results_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    results_json.write_text(
        json.dumps(
            {
                "tag": args.tag,
                "caching": not args.no_cache,
                "model_ids": {**DEFAULT_MODEL_IDS, **overrides},
                "n": len(rows),
                "macro_f1": macro_f1,
                "accuracy": accuracy,
                "per_class": {c: dict(zip(("precision", "recall", "f1", "support"), per_class[c])) for c in CLASSES},
                "escalation_rate": escalated / len(rows),
                "review_flag_rate": flagged / len(rows),
                "cost_total": cost,
                "cost_per_resume": cost / len(rows),
                "latency_p50": p50,
                "latency_p95": p95,
                "wall_clock_s": wall_clock,
                "cost_by_model": {k: round(v, 4) for k, v in cost_by_model(verdicts).items()},
                "tokens": {
                    "input": sum(v.usage.input_tokens for v in verdicts),
                    "output": sum(v.usage.output_tokens for v in verdicts),
                    "cache_read": sum(v.usage.cache_read_input_tokens for v in verdicts),
                    "cache_write": sum(v.usage.cache_creation_input_tokens for v in verdicts),
                },
                "predictions": [
                    {
                        "file": f,
                        "archetype": m["archetype"],
                        "expected": m["label"],
                        "predicted": v.recommendation.value,
                        "score": v.score,
                        "panel_spread": v.panel_spread,
                        "escalated": v.escalated,
                        "panel": [p.to_dict() for p in v.panel_scores],
                        "rationale": v.rationale,
                    }
                    for f, m, v in rows
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\n{'=' * 60}")
    print(f"  Macro-F1 {macro_f1:.3f} | accuracy {accuracy:.3f} | "
          f"escalated {escalated}/{len(rows)} | ${cost:.3f}")
    print(f"{'=' * 60}")
    print(f"\nWrote {results_md.relative_to(REPO)} and {results_json.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
