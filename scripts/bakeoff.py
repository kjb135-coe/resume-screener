"""Score several models on the same resumes, under the same pipeline.

    python scripts/bakeoff.py --check     # validate config + keys, spend nothing
    python scripts/bakeoff.py             # run every enabled arm
    python scripts/bakeoff.py --arm glm-5.3-flash
    python scripts/bakeoff.py --runs 1    # override runs_per_arm

Arms, model ids, endpoints, and prices live in `config/bakeoff.json`.
Adding a provider is a config edit, not a code change.

Writes `data/bakeoff__<arm>__run<i>.json` per run and, at the end,
`docs/BAKEOFF.md`. Nothing here touches `data/eval_run.json` or any
other baseline artifact.

WHAT THIS CAN AND CANNOT SETTLE
-------------------------------
The sample is 20 resumes (`data/bakeoff_sample.json`). Measured on four
recorded runs of one unchanged configuration, the macro-F1 noise band is
0.051 over ~51 resumes and roughly **0.098 over a stratified 20** --
resampled 2000 times, with 48% of draws above 0.10. See docs/VARIANCE.md.

So a single 20-resume run per arm cannot rank models by accuracy. It can
settle two things that are far more stable, and that decided the last
bake-off outright:

- **JSON reliability.** PLAN.md section 8a rejected an all-Haiku panel on
  49% unparseable responses against Sonnet's 2.2%. That is unmissable at
  any sample size, and it is a property of the model, not the sample.
- **Cost and latency per resume.** Cost varied by one cent across three
  full runs while macro-F1 varied by 0.051.

`runs_per_arm` defaults to 3 so accuracy gets a per-arm band rather than
a point. Read that band before believing any ranking.

EVERY ARM STILL NEEDS AN ANTHROPIC KEY
--------------------------------------
`swap_slots` replaces the panel and arbiter only. Evidence extraction
stays on Haiku in every arm, deliberately: it isolates the comparison to
scoring, and matches how section 8a was run. `ANTHROPIC_API_KEY` is
therefore required even for an arm that is otherwise all-OpenAI.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_screener.core.pipeline import (
    DEFAULT_MODEL_IDS,
    screen_one,
)
from resume_screener.core.router import (
    AnthropicModel,
    Model,
    OpenAICompatibleModel,
)

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "synthetic_resumes"
LABELS = REPO / "data" / "labels.json"
SAMPLE = REPO / "data" / "bakeoff_sample.json"
JD_PATH = REPO / "docs" / "job_description.md"
CONFIG = REPO / "config" / "bakeoff.json"

CLASSES = ("advance", "hold", "reject")
PLACEHOLDER = "FILL_IN"


def load_dotenv() -> list[str]:
    """Read `.env` into the environment, without overwriting what is set.

    Nothing else in this repo does this, and that cost a run: three
    variance evaluations died instantly on 2026-08-27 because the key sat
    in `.env` and was never exported. A bake-off spans several providers
    and several minutes per arm, so failing that way here would be worse.

    Real values are never printed -- only the names of the variables
    loaded, so a missing key is diagnosable without leaking a secret.
    """
    path = REPO / ".env"
    if not path.exists():
        return []
    loaded = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip().strip("'\"")
        # An already-exported value wins, so a one-off override on the
        # command line is not silently undone by the file.
        if name and name not in os.environ:
            os.environ[name] = value
            loaded.append(name)
    return loaded

# Anthropic rates, for the slots that stay Anthropic in every arm
# (extraction) and for the control arm. Verified 2026-08-27; see
# docs/COST_ANALYSIS.md, which documents the two that were wrong before.
ANTHROPIC_PRICING = {
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
}


def macro_f1(rows: list[tuple[str, str]]) -> tuple[float, dict[str, float]]:
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


def build_models(arm: dict) -> tuple[dict[str, Model], Model]:
    """One Model per slot, with the arm's model in the swapped slots.

    Unswapped slots stay on their Anthropic defaults, so a run differs
    from the control in exactly one dimension.
    """
    anthropic_key = os.environ["ANTHROPIC_API_KEY"]
    models: dict[str, Model] = {
        slot: AnthropicModel(model_id, anthropic_key)
        for slot, model_id in DEFAULT_MODEL_IDS.items()
    }
    if arm["provider"] == "anthropic":
        replacement: Model = AnthropicModel(
            arm["model_id"],
            os.environ[arm["api_key_env"]],
            prefill=arm.get("prefill", ""),
        )
    elif arm["provider"] == "openai_compatible":
        replacement = OpenAICompatibleModel(
            arm["model_id"],
            os.environ[arm["api_key_env"]],
            arm["base_url"],
            send_temperature=arm.get("send_temperature", True),
            token_param=arm.get("token_param", "max_tokens"),
            extra_body=arm.get("extra_body") or {},
        )
    else:
        raise ValueError(f"{arm['name']}: unknown provider {arm['provider']!r}")
    return models, replacement


def pricing_for(arm: dict) -> dict[str, dict] | None:
    """Rates keyed by model id, or None when the arm has no prices set.

    Returning None rather than guessing is deliberate: a run with unknown
    rates still reports real token counts and latency, and simply omits
    dollars. An invented price would look exactly like a measured one.
    """
    prices = dict(ANTHROPIC_PRICING)
    arm_prices = arm.get("pricing") or {}
    if any(arm_prices.get(k) is None for k in ("in", "out")):
        return None
    prices[arm["model_id"]] = {
        "in": arm_prices["in"],
        "out": arm_prices["out"],
        "cache_read": arm_prices.get("cache_read") or 0.0,
        "cache_write": arm_prices.get("cache_write") or 0.0,
    }
    return prices


def cost_of(verdicts, prices: dict[str, dict] | None) -> float | None:
    if prices is None:
        return None
    total = 0.0
    for verdict in verdicts:
        for model_id, counts in verdict.usage.by_model.items():
            rates = prices.get(model_id)
            if rates is None:
                return None
            total += (
                counts.get("input_tokens", 0) / 1e6 * rates["in"]
                + counts.get("output_tokens", 0) / 1e6 * rates["out"]
                + counts.get("cache_read_input_tokens", 0) / 1e6 * rates["cache_read"]
                + counts.get("cache_creation_input_tokens", 0) / 1e6 * rates["cache_write"]
            )
    return total


def validate(config: dict, arms: list[dict]) -> list[str]:
    """Everything that would make a paid run fail or lie, checked up front."""
    problems: list[str] = []
    if not SAMPLE.exists():
        problems.append(
            f"{SAMPLE.relative_to(REPO)} is missing. "
            "Run: python scripts/make_bakeoff_sample.py"
        )
    if "ANTHROPIC_API_KEY" not in os.environ:
        problems.append(
            "ANTHROPIC_API_KEY is not set. Every arm needs it — extraction "
            "stays on Haiku so the comparison isolates scoring."
        )
    for arm in arms:
        name = arm["name"]
        if arm.get("model_id") == PLACEHOLDER or not arm.get("model_id"):
            problems.append(f"{name}: model_id is still {PLACEHOLDER}.")
        if arm["provider"] == "openai_compatible" and not arm.get("base_url"):
            problems.append(f"{name}: base_url is required for openai_compatible.")
        key_env = arm.get("api_key_env")
        if not key_env:
            problems.append(f"{name}: api_key_env is missing.")
        elif key_env not in os.environ:
            problems.append(f"{name}: ${key_env} is not set.")
        if pricing_for(arm) is None:
            # Not fatal. The run still measures tokens and latency.
            print(
                f"  note: {name} has no pricing set — the run will report "
                "tokens and latency but no dollar figures.",
                file=sys.stderr,
            )
    return problems


async def run_once(arm: dict, files: list[str], labels: dict, jd: str, concurrency: int):
    models, replacement = build_models(arm)
    for slot in arm["_swap_slots"]:
        models[slot] = replacement

    semaphore = asyncio.Semaphore(concurrency)

    async def one(filename: str):
        async with semaphore:
            try:
                verdict = await screen_one(str(CORPUS / filename), jd, models)
                print(
                    f"  {labels[filename]['label']:8} -> "
                    f"{verdict.recommendation.value:8} {verdict.score:4.1f}  {filename}"
                )
                return filename, verdict
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED {filename}: {exc}")
                return filename, None

    started = time.monotonic()
    results = await asyncio.gather(*[one(f) for f in files])
    wall_clock = time.monotonic() - started
    return [(f, v) for f, v in results if v is not None], wall_clock


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG))
    parser.add_argument(
        "--sample",
        default=None,
        help="resume sample file (default data/bakeoff_sample.json)",
    )
    parser.add_argument("--arm", action="append", help="run only this arm (repeatable)")
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--check", action="store_true", help="validate and exit")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="rebuild docs/BAKEOFF.md from saved data/bakeoff__*.json, no API calls",
    )
    args = parser.parse_args()

    loaded = load_dotenv()
    if loaded:
        print(f"Loaded from .env: {', '.join(loaded)}")

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    run_cfg = config.get("run", {})
    swap_slots = run_cfg.get("swap_slots") or ["panel", "arbiter"]
    runs_per_arm = args.runs if args.runs is not None else run_cfg.get("runs_per_arm", 3)
    concurrency = run_cfg.get("concurrency", 5)

    arms = [a for a in config["arms"] if a.get("enabled", True)]
    if args.arm:
        wanted = set(args.arm)
        arms = [a for a in arms if a["name"] in wanted]
        missing = wanted - {a["name"] for a in arms}
        if missing:
            print(f"No such enabled arm: {sorted(missing)}", file=sys.stderr)
            return 1
    for arm in arms:
        arm["_swap_slots"] = swap_slots

    if not arms:
        print("No enabled arms.", file=sys.stderr)
        return 1

    print(f"Arms: {', '.join(a['name'] for a in arms)}")
    print(f"Swapping slots: {swap_slots}")
    problems = validate(config, arms)
    if problems:
        print("\nNot ready to run:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nFix these in config/bakeoff.json (or export the keys) and "
            "re-run with --check.",
            file=sys.stderr,
        )
        return 1

    sample_path = Path(args.sample) if args.sample else SAMPLE
    sample = json.loads(sample_path.read_text(encoding="utf-8"))

    if args.report_only:
        # Re-derives every metric from what was already paid for, so the
        # report can gain a section without re-running a single call.
        saved: dict[str, list[dict]] = {}
        for arm in arms:
            runs = sorted(REPO.glob(f"data/bakeoff__{arm['name']}__run*.json"))
            saved[arm["name"]] = [
                json.loads(path.read_text(encoding="utf-8")) for path in runs
            ]
            print(f"  {arm['name']}: {len(runs)} saved run(s)")
        if not any(saved.values()):
            print("No saved runs to report on.", file=sys.stderr)
            return 1
        write_report(saved, sample, swap_slots, runs_per_arm)
        return 0

    files = sample["files"]
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    jd = JD_PATH.read_text(encoding="utf-8")

    est = len(arms) * runs_per_arm * len(files)
    print(f"Sample: {len(files)} resumes, {sample['labels']}")
    print(f"Plan: {len(arms)} arms x {runs_per_arm} runs = {est} screenings")
    if args.check:
        print("\nConfig and keys look good. Remove --check to run.")
        return 0

    all_results: dict[str, list[dict]] = {}
    for arm in arms:
        all_results[arm["name"]] = []
        prices = pricing_for(arm)
        for run_index in range(1, runs_per_arm + 1):
            print(
                f"\n=== {arm['name']} run {run_index}/{runs_per_arm} "
                f"(concurrency {arm.get('concurrency', concurrency)}) ==="
            )
            rows, wall_clock = await run_once(
                arm, files, labels, jd, arm.get("concurrency", concurrency)
            )
            if not rows:
                print(f"  !! {arm['name']} run {run_index} scored nothing.", file=sys.stderr)
                continue
            verdicts = [v for _, v in rows]
            pairs = [(labels[f]["label"], v.recommendation.value) for f, v in rows]
            f1, per_class = macro_f1(pairs)
            accuracy = sum(1 for t, p in pairs if t == p) / len(pairs)
            latencies = sorted(v.usage.latency_s for v in verdicts)
            cost = cost_of(verdicts, prices)
            parse_failed = sum(
                1 for _, v in rows for p in v.panel_scores if getattr(p, "parse_failed", False)
            )
            panel_calls = sum(len(v.panel_scores) for _, v in rows)

            record = {
                "arm": arm["name"],
                "run": run_index,
                "model_id": arm["model_id"],
                "provider": arm["provider"],
                "swap_slots": swap_slots,
                "n": len(rows),
                "requested": len(files),
                "macro_f1": f1,
                "per_class_f1": per_class,
                "accuracy": accuracy,
                "cost_total": cost,
                "cost_per_resume": (cost / len(rows)) if cost is not None else None,
                "latency_p50": latencies[len(latencies) // 2],
                "latency_mean": statistics.mean(latencies),
                "wall_clock_s": wall_clock,
                "parse_failed": parse_failed,
                "panel_calls": panel_calls,
                "escalated": sum(1 for v in verdicts if v.escalated),
                "tokens": {
                    "input": sum(v.usage.input_tokens for v in verdicts),
                    "output": sum(v.usage.output_tokens for v in verdicts),
                    "cache_read": sum(v.usage.cache_read_input_tokens for v in verdicts),
                    "cache_write": sum(v.usage.cache_creation_input_tokens for v in verdicts),
                },
                "predictions": [
                    {
                        "file": f,
                        "expected": labels[f]["label"],
                        "predicted": v.recommendation.value,
                        "score": v.score,
                        "escalated": v.escalated,
                    }
                    for f, v in rows
                ],
            }
            all_results[arm["name"]].append(record)
            out = REPO / "data" / f"bakeoff__{arm['name']}__run{run_index}.json"
            out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            cost_str = f"${cost:.3f}" if cost is not None else "n/a"
            print(
                f"  -> macro-F1 {f1:.3f} | acc {accuracy:.3f} | {cost_str} | "
                f"p50 {record['latency_p50']:.1f}s | parse-fail "
                f"{parse_failed}/{panel_calls}"
            )

    write_report(all_results, sample, swap_slots, runs_per_arm)
    return 0


def _recommend(score: float, advance: float, hold: float) -> str:
    if score >= advance:
        return "advance"
    return "hold" if score >= hold else "reject"


def _best_cutoffs(runs: list[dict]) -> tuple[float, float, float]:
    """Best macro-F1 reachable on these recorded scores, and where.

    Offline and free -- it re-thresholds scores that were already paid
    for, the same trick as scripts/sweep_cutoffs.py.

    This exists because the shipped cutoffs (4.0/1.0) were fitted to
    Sonnet's score distribution. A model that grades on a different scale
    is then punished for the scale rather than for its judgment, and the
    bake-off silently measures "agrees with Sonnet's calibration" instead
    of "judges well". That is not hypothetical: on 2026-08-27 an arm
    scored 0.517 under the shipped cutoffs and 0.896 under its own.
    """
    best = (0.0, 0.0, 0.0)
    grid = [x / 10 for x in range(101)]
    for advance in grid:
        for hold in grid:
            if hold >= advance:
                continue
            score = statistics.mean(
                macro_f1(
                    [
                        (p["expected"], _recommend(p["score"], advance, hold))
                        for p in run["predictions"]
                    ]
                )[0]
                for run in runs
            )
            if score > best[0]:
                best = (score, advance, hold)
    return best


def _calibration_section(results: dict[str, list[dict]]) -> str:
    lines = ["## Calibration — read this before the ranking above\n"]
    lines.append(
        "The verdict cutoffs in `core/pipeline.py` (`ADVANCE_CUTOFF = 4.0`, "
        "`HOLD_CUTOFF = 1.0`) were swept against **Sonnet's** score "
        "distribution. A model that grades on a different scale loses "
        "macro-F1 to the mismatch, not to bad judgment. The right-hand "
        "columns re-threshold each arm's own recorded scores offline — free, "
        "no new calls — and show what it would reach with cutoffs fitted to "
        "itself.\n"
    )
    lines.append("| Arm | Mean score | As shipped (4.0/1.0) | Own best cutoffs | Best macro-F1 |")
    lines.append("|---|---|---|---|---|")
    for name, runs in results.items():
        if not runs:
            continue
        shipped = statistics.mean(r["macro_f1"] for r in runs)
        best, advance, hold = _best_cutoffs(runs)
        mean_score = statistics.mean(
            p["score"] for r in runs for p in r["predictions"]
        )
        gain = "" if best - shipped < 0.02 else f" **(+{best - shipped:.3f})**"
        lines.append(
            f"| `{name}` | {mean_score:.2f} | {shipped:.3f} | "
            f"{advance}/{hold} | {best:.3f}{gain} |"
        )
    lines.append("")
    lines.append(
        "**These fitted cutoffs are an upper bound, not a result.** They are "
        "chosen on the same resumes they are scored against, on a sample of "
        "20 — a smaller corpus than the 60 that `docs/LIMITATIONS.md` already "
        "calls overfitted. Read the right-hand column as *\"this model is not "
        "out of the running\"*, never as its accuracy. A model that needs its "
        "own cutoffs also needs them re-fitted on a corpus it has not seen "
        "before any of it counts.\n"
    )
    return "\n".join(lines)


def write_report(results: dict[str, list[dict]], sample: dict, swap_slots, runs_per_arm) -> None:
    lines: list[str] = []
    add = lines.append
    add("# Model bake-off\n")
    add(f"{len(results)} arms, {runs_per_arm} runs each, on the same "
        f"{sample['size']} resumes (`data/bakeoff_sample.json`, seed "
        f"{sample['seed']}). Swapped slots: `{'`, `'.join(swap_slots)}`. "
        "Extraction stays on Haiku in every arm.\n")
    add("**Read this before ranking anything by accuracy.** The macro-F1 "
        "noise band on a stratified 20 is roughly **0.098** (median of 2000 "
        "resamples of four identical runs; see `docs/VARIANCE.md`). Treat any "
        "accuracy gap smaller than the per-arm spread below as unresolved. "
        "Cost, latency and parse-failure rate are far more stable and can be "
        "read directly.\n")

    add("## Summary\n")
    add("| Arm | Macro-F1 (range) | Accuracy | Cost/resume | Latency p50 | Parse failures |")
    add("|---|---|---|---|---|---|")
    for name, runs in results.items():
        if not runs:
            add(f"| `{name}` | — | — | — | — | **no successful run** |")
            continue
        f1s = [r["macro_f1"] for r in runs]
        accs = [r["accuracy"] for r in runs]
        costs = [r["cost_per_resume"] for r in runs if r["cost_per_resume"] is not None]
        lat = [r["latency_p50"] for r in runs]
        pf = sum(r["parse_failed"] for r in runs)
        calls = sum(r["panel_calls"] for r in runs)
        f1_cell = (
            f"{statistics.mean(f1s):.3f} ({min(f1s):.3f}–{max(f1s):.3f})"
            if len(f1s) > 1 else f"{f1s[0]:.3f} (1 run)"
        )
        cost_cell = f"${statistics.mean(costs):.4f}" if costs else "n/a"
        add(f"| `{name}` | {f1_cell} | {statistics.mean(accs):.3f} | {cost_cell} "
            f"| {statistics.mean(lat):.1f}s | {pf}/{calls} ({pf / calls:.1%}) |")
    add("")

    add("## Per-run detail\n")
    add("| Arm | Run | n | Macro-F1 | Accuracy | Cost | p50 | Parse failures |")
    add("|---|---|---|---|---|---|---|---|")
    for name, runs in results.items():
        for r in runs:
            cost = f"${r['cost_total']:.3f}" if r["cost_total"] is not None else "n/a"
            flag = "" if r["n"] == r["requested"] else f" (PARTIAL {r['n']}/{r['requested']})"
            add(f"| `{name}` | {r['run']}{flag} | {r['n']} | {r['macro_f1']:.3f} "
                f"| {r['accuracy']:.3f} | {cost} | {r['latency_p50']:.1f}s "
                f"| {r['parse_failed']}/{r['panel_calls']} |")
    add("")

    add(_calibration_section(results))

    add("## How to read this\n")
    add("0. **Calibration before anything else.** See the section above. The "
        "cutoffs in `core/pipeline.py` were fitted to one model's score "
        "distribution; a model that grades on a different scale is penalised "
        "for the scale, not for its judgment.")
    add("1. **Parse failures first.** A model that cannot reliably emit JSON "
        "is disqualified regardless of its scores — a failed parse scores 0.0, "
        "which is indistinguishable from a confident reject. This is what "
        "decided the previous bake-off (PLAN.md section 8a).")
    add("2. **Then cost and latency.** These are stable across runs and can be "
        "compared directly.")
    add("3. **Accuracy last, and only against the spread.** If two arms' "
        "macro-F1 ranges overlap, the bake-off has not separated them. Say so "
        "rather than picking the higher mean.\n")

    out = REPO / "docs" / "BAKEOFF.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
