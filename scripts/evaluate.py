"""Score the pipeline against the labeled corpus.

    python scripts/evaluate.py                # full corpus
    python scripts/evaluate.py --limit 6      # cheap smoke run
    python scripts/evaluate.py --no-cache     # for the caching comparison

Writes docs/EVAL_RESULTS.md (human-readable) and data/eval_run.json (raw,
for later comparison between configurations).

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
from resume_screener.core.pipeline import default_models, screen_one

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "synthetic_resumes"
LABELS = REPO / "data" / "labels.json"
JD_PATH = REPO / "docs" / "job_description.md"
RESULTS_MD = REPO / "docs" / "EVAL_RESULTS.md"
RESULTS_JSON = REPO / "data" / "eval_run.json"

CLASSES = ("advance", "hold", "reject")

# Published per-million-token rates, used only to turn measured token
# counts into a dollar figure. Token counts themselves are real.
PRICING = {
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-5": {"in": 3.00, "out": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-opus-5": {"in": 15.00, "out": 75.00, "cache_read": 1.50, "cache_write": 18.75},
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
    """Rough dollars from real token counts.

    Approximate: Usage is summed per verdict across tiers that use
    different models, so the model_id recorded is the first tier's. Good
    enough for relative comparison between configurations, which is what
    the number is for -- not for billing.
    """
    total = 0.0
    for v in verdicts:
        u = v.usage
        rates = PRICING.get(u.model_id) or PRICING["claude-sonnet-5"]
        total += (
            u.input_tokens * rates["in"]
            + u.output_tokens * rates["out"]
            + u.cache_read_input_tokens * rates["cache_read"]
            + u.cache_creation_input_tokens * rates["cache_write"]
        ) / 1_000_000
    return total


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--no-cache", action="store_true", help="disable prompt caching")
    parser.add_argument("--tag", default="baseline", help="label for this configuration")
    args = parser.parse_args()

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

    models = default_models()
    semaphore = asyncio.Semaphore(args.concurrency)
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
    add("## Headline\n")
    add("| Metric | Value |")
    add("|---|---|")
    add(f"| **Macro-F1** | **{macro_f1:.3f}** |")
    add(f"| Accuracy | {accuracy:.3f} |")
    add(f"| Escalated to arbiter | {escalated}/{len(rows)} ({escalated / len(rows):.0%}) |")
    add(f"| Flagged for human review | {flagged}/{len(rows)} ({flagged / len(rows):.0%}) |")
    add(f"| Cost per resume | ${cost / len(rows):.4f} |")
    add(f"| Total cost | ${cost:.3f} |")
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

    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    RESULTS_JSON.write_text(
        json.dumps(
            {
                "tag": args.tag,
                "caching": not args.no_cache,
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
    print(f"\nWrote {RESULTS_MD.relative_to(REPO)} and {RESULTS_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
