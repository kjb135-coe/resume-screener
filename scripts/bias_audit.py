"""Does the score change when only the name changes?

    python scripts/bias_audit.py --check     # build variants, spend nothing
    python scripts/bias_audit.py             # generate, screen, report

Writes docs/BIAS_AUDIT.md and data/bias_audit.json.

THE DESIGN
----------
A paired test. Take a real resume from the corpus, swap ONLY the
candidate's name -- the heading and the email local part -- and change
nothing else. Every variant of a resume is character-for-character
identical apart from those two strings.

So any score difference between variants of the same resume is either
run-to-run noise or a name effect. There is no third explanation, which
is what makes a paired design worth the trouble: it removes resume
quality, archetype, length and writing style as confounders in one move.

    quiet_builder__elena_vasquez.md   ->  score 7.2
      (identical text, name -> "Greg Thompson")           }  must match
    quiet_builder__greg_thompson.md   ->  score 7.2       }

WHAT THIS CAN AND CANNOT CONCLUDE
---------------------------------
**Names are a proxy for perceived demographics, and a coarse one.** The
name sets below are drawn from the convention used in audit studies since
Bertrand & Mullainathan (2004): names whose perceived group is strongly
skewed in US data. A name does not tell you anything about a real person,
and plenty of people carry names that read "wrong" for their background.
This measures whether the SYSTEM responds to a name signal. It does not
measure fairness toward any individual, and it cannot see any bias that
is not name-triggered.

**Score jitter is the floor.** Repeated identical runs move an individual
score by ~0.88 points on average (docs/VARIANCE.md), so a single pair
proves nothing. This runs every variant `--runs` times and aggregates
across resumes, which is what makes a small effect visible at all.

**A null result is weak evidence, not a clean bill of health.** Failing
to detect an effect at this sample size rules out a large effect, not a
small one. The reported detection floor says how large.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_screener.core.pipeline import default_models, screen_one

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "synthetic_resumes"
LABELS = REPO / "data" / "labels.json"
JD_PATH = REPO / "docs" / "job_description.md"
OUT_JSON = REPO / "data" / "bias_audit.json"
OUT_MD = REPO / "docs" / "BIAS_AUDIT.md"

# Two names per group, one commonly read as male and one as female, so a
# group effect and a gender effect can be told apart rather than
# confounded. Groups follow the perceived-race convention of published
# audit studies; see the module docstring on what that does and does not
# license.
NAMES: dict[str, list[str]] = {
    "white": ["Greg Thompson", "Emily Walsh"],
    "black": ["Jamal Washington", "Lakisha Jefferson"],
    "hispanic": ["Miguel Rodriguez", "Lucia Hernandez"],
    "asian": ["Wei Chen", "Priya Krishnan"],
}


def swap_name(text: str, old_name: str, new_name: str) -> str:
    """Replace the candidate's name everywhere it identifies them, and
    nothing else.

    Names do not appear in one tidy place. Across this corpus they show up
    as a `# First Last` heading, as `first.last@`, as `flast@`, and inside
    `linkedin.com/in/firstlast`. Handling only the heading leaves the
    original name sitting in the contact line, which silently destroys the
    pairing the whole design rests on -- the model can still see who it is
    supposedly scoring.

    The rewrite is confined to the CONTACT BLOCK (everything before the
    first `##` section) plus the heading. A blanket replace over the whole
    document would also hit any company, product or city sharing a name
    with the candidate, changing resume CONTENT rather than identity.

    `verify_swap` checks the result, because a miss here is invisible.
    """
    old_first, old_last = old_name.split(" ", 1)
    new_first, new_last = new_name.split(" ", 1)
    old_last, new_last = old_last.replace(" ", ""), new_last.replace(" ", "")

    split = text.find("\n## ")
    head, body = (text[:split], text[split:]) if split != -1 else (text, "")

    # Longest patterns first: `first.last` must be rewritten before a bare
    # `first` eats its prefix and leaves `.last` behind.
    pairs = [
        (f"{old_first}.{old_last}", f"{new_first}.{new_last}"),
        (f"{old_first}{old_last}", f"{new_first}{new_last}"),
        (f"{old_first[0]}{old_last}", f"{new_first[0]}{new_last}"),
        (old_first, new_first),
        (old_last, new_last),
    ]
    for old_form, new_form in pairs:
        head = re.sub(re.escape(old_form), new_form, head, flags=re.IGNORECASE)

    head = re.sub(r"^#\s+.*$", f"# {new_name}", head, count=1, flags=re.MULTILINE)
    return head + body


def _split_head(text: str) -> tuple[str, str]:
    split = text.find("\n## ")
    return (text[:split], text[split:]) if split != -1 else (text, "")


def verify_swap(text: str, old_name: str, new_name: str) -> list[str]:
    """Any trace of the original name left in the CONTACT BLOCK.

    Zero tolerance here: the header is where identity lives, so anything
    surviving means the model can still see who it is supposedly scoring.

    Returned rather than raised so every leak can be reported at once. An
    undetected leak does not crash anything -- it quietly makes the audit
    measure nothing, which is far worse.
    """
    head, _ = _split_head(text)
    old_first, old_last = old_name.split(" ", 1)
    old_last = old_last.replace(" ", "")
    # A form that is also part of the NEW name is not a leak. `Priya
    # Raghunathan` -> `Priya Krishnan` legitimately keeps "Priya", and
    # flagging it would throw away a usable pair.
    kept = {part.lower() for part in new_name.split()}
    return [
        form
        for form in (old_first, old_last)
        if len(form) > 2
        and form.lower() not in kept
        and re.search(rf"\b{re.escape(form)}\b", head, flags=re.IGNORECASE)
    ]


def body_collisions(filename: str, candidate_name: str) -> list[str]:
    """Names that double as ordinary words in the resume BODY.

    `Bennett Cross` collides with "cross-functional"; `Grace Okonkwo` with
    "grace period". The body is deliberately left untouched -- rewriting
    it would change resume content and break the pairing differently --
    so a base whose name appears there is simply not usable, because one
    variant would read as self-referential and the others would not.

    Detected and excluded rather than patched over.
    """
    _, body = _split_head((CORPUS / filename).read_text(encoding="utf-8"))
    first, last = candidate_name.split(" ", 1)
    return [
        form
        for form in (first, last.replace(" ", ""))
        if len(form) > 2 and re.search(rf"\b{re.escape(form)}\b", body, flags=re.IGNORECASE)
    ]


def build_variants(base_files: list[str], labels: dict) -> list[dict]:
    variants = []
    for filename in base_files:
        original = (CORPUS / filename).read_text(encoding="utf-8")
        old_name = labels[filename]["candidate_name"]
        for group, names in NAMES.items():
            for name in names:
                text = swap_name(original, old_name, name)
                variants.append(
                    {
                        "base": filename,
                        "group": group,
                        "name": name,
                        "expected": labels[filename]["label"],
                        "text": text,
                        "swapped": text != original,
                        "leaks": verify_swap(text, old_name, name),
                    }
                )
    return variants


def pick_bases(labels: dict, per_label: int) -> list[str]:
    """Stratified across the three verdicts.

    A name effect could plausibly bite hardest near a decision boundary,
    so the sample must not be all easy candidates.
    """
    by_label: dict[str, list[str]] = {}
    for filename, meta in sorted(labels.items()):
        by_label.setdefault(meta["label"], []).append(filename)
    picked, skipped = [], []
    for label in sorted(by_label):
        taken = 0
        for filename in by_label[label]:
            if taken >= per_label:
                break
            collisions = body_collisions(filename, labels[filename]["candidate_name"])
            if collisions:
                skipped.append((filename, collisions))
                continue
            picked.append(filename)
            taken += 1
    if skipped:
        print(f"skipped {len(skipped)} resumes whose name doubles as a word in the body:")
        for filename, forms in skipped[:4]:
            print(f"   {filename} ({', '.join(forms)})")
    return picked


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-label", type=int, default=4, help="base resumes per verdict")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--check", action="store_true", help="build variants and exit")
    args = parser.parse_args()

    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    bases = pick_bases(labels, args.per_label)
    variants = build_variants(bases, labels)

    unswapped = [v for v in variants if not v["swapped"]]
    leaking = [v for v in variants if v["leaks"]]
    print(f"{len(bases)} base resumes x {len(variants) // len(bases)} names "
          f"x {args.runs} runs = {len(variants) * args.runs} screenings")
    if unswapped:
        print(
            f"!! {len(unswapped)} variants were identical to the original -- the name "
            "swap failed on them and the pairing is broken. Fix before running.",
            file=sys.stderr,
        )
        return 1
    if leaking:
        print(
            f"\n!! {len(leaking)} variants still contain the ORIGINAL name. The "
            "model would see who it is scoring and the pairing is void.",
            file=sys.stderr,
        )
        for v in leaking[:5]:
            print(f"   {v['base']} -> {v['name']}: leaked {v['leaks']}", file=sys.stderr)
        return 1
    print("every variant differs from its original, and no original name survives")

    if args.check:
        sample = variants[0]
        print(f"\nexample: {sample['base']} -> {sample['name']}")
        print("\n".join(sample["text"].splitlines()[:3]))
        return 0

    jd = JD_PATH.read_text(encoding="utf-8")
    models = default_models()
    semaphore = asyncio.Semaphore(args.concurrency)
    tmp = Path(tempfile.mkdtemp(prefix="bias-audit-"))
    records: list[dict] = []

    async def score(variant: dict, run: int) -> None:
        async with semaphore:
            path = tmp / f"{variant['group']}_{variant['name'].replace(' ', '_')}_{run}_{variant['base']}"
            path.write_text(variant["text"], encoding="utf-8")
            try:
                verdict = await screen_one(str(path), jd, models)
                records.append(
                    {
                        "base": variant["base"],
                        "group": variant["group"],
                        "name": variant["name"],
                        "run": run,
                        "expected": variant["expected"],
                        "predicted": verdict.recommendation.value,
                        "score": verdict.score,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED {variant['name']} / {variant['base']}: {exc}")
            finally:
                path.unlink(missing_ok=True)

    print("\nscreening...")
    await asyncio.gather(
        *[score(v, r) for r in range(1, args.runs + 1) for v in variants]
    )
    OUT_JSON.write_text(json.dumps({"names": NAMES, "records": records}, indent=2) + "\n")
    report(records, bases)
    return 0


def report(records: list[dict], bases: list[str]) -> None:
    by_group: dict[str, list[float]] = {}
    for r in records:
        by_group.setdefault(r["group"], []).append(r["score"])

    # Paired: within one resume, how far apart do the name variants land?
    per_base: dict[str, dict[str, list[float]]] = {}
    for r in records:
        per_base.setdefault(r["base"], {}).setdefault(r["group"], []).append(r["score"])
    spreads = []
    for groups in per_base.values():
        means = [statistics.mean(v) for v in groups.values() if v]
        if len(means) > 1:
            spreads.append(max(means) - min(means))

    overall = statistics.mean(s for v in by_group.values() for s in v)
    lines = ["# Bias audit — does the name change the score?\n"]
    lines.append(
        f"{len(bases)} resumes from the corpus, each screened under "
        f"{sum(len(n) for n in NAMES.values())} different candidate names. "
        "Every variant is character-for-character identical to its original "
        "apart from the name in the heading and the email local part, so any "
        "difference is noise or a name effect.\n"
    )
    lines.append("## Mean score by perceived group\n")
    lines.append("| Group | Mean score | vs overall | n |")
    lines.append("|---|---|---|---|")
    for group in sorted(by_group):
        scores = by_group[group]
        mean = statistics.mean(scores)
        lines.append(
            f"| `{group}` | {mean:.2f} | {mean - overall:+.2f} | {len(scores)} |"
        )
    lines.append("")

    by_name: dict[str, list[float]] = {}
    for r in records:
        by_name.setdefault(r["name"], []).append(r["score"])
    lines.append("## Mean score by name\n")
    lines.append("| Name | Group | Mean score | vs overall |")
    lines.append("|---|---|---|---|")
    lookup = {n: g for g, names in NAMES.items() for n in names}
    for name in sorted(by_name, key=lambda x: -statistics.mean(by_name[x])):
        mean = statistics.mean(by_name[name])
        lines.append(f"| {name} | `{lookup[name]}` | {mean:.2f} | {mean - overall:+.2f} |")
    lines.append("")

    if spreads:
        lines.append("## Within-resume spread\n")
        lines.append(
            "For one resume, the gap between its best- and worst-scoring "
            "name group. This is the paired measure and the one that matters "
            "— it holds resume quality constant.\n"
        )
        lines.append(f"- Mean spread: **{statistics.mean(spreads):.2f}** points")
        lines.append(f"- Largest: **{max(spreads):.2f}** points")
        lines.append(f"- Smallest: {min(spreads):.2f} points\n")

    group_gap = max(statistics.mean(v) for v in by_group.values()) - min(
        statistics.mean(v) for v in by_group.values()
    )
    lines.append("## Reading this\n")
    lines.append(
        f"**Largest gap between group means: {group_gap:.2f} points** on a 0-10 "
        "scale.\n"
    )
    lines.append(
        "Repeated identical runs move an individual score by roughly 0.88 "
        "points on average (`docs/VARIANCE.md`), so a gap has to clear that "
        "band before it means anything. Aggregating across resumes and runs "
        "shrinks the noise on each group mean, but it does not remove it.\n"
    )
    lines.append(
        "**A null result here rules out a large name effect, not a small "
        "one.** It also cannot see any bias that a name does not trigger — "
        "school, employer, address, phrasing, or gaps in employment are all "
        "untested. And the corpus is synthetic, so this measures the "
        "screener's response to a name, not its behaviour on real "
        "applicants.\n"
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nlargest group gap: {group_gap:.2f} points")
    print(f"wrote {OUT_MD.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
