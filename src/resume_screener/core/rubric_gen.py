"""Tier -1: write the rubric before anything is scored.

`prompts/rubric.md` is hand-written and anchored to one posting
(`docs/job_description.md`). That is the right rubric for that job and
the wrong rubric for any other. This module removes the hardcoding: give
it a job posting, it returns the rubric and the three panel personas to
score against, generated from what the posting actually asks for.

Two properties this deliberately preserves:

**One rubric per batch, not per resume.** The panel's cacheable system
prefix is `rubric + job_description`. Generating the rubric once and
reusing it across every resume keeps that prefix byte-identical, so the
caching contract in `pipeline.py` survives. Generating per resume would
produce a slightly different rubric each time and silently destroy it.

**Exactly three dimensions.** `DISAGREEMENT_THRESHOLD` is a spread across
panel scores, calibrated against a three-agent panel. A generated rubric
with four dimensions would change what that spread means without
changing the threshold, so the count is enforced here rather than
trusted to the model.

Generation failure raises rather than falling back to the hand-written
rubric. Silently scoring candidates for one job against another job's
rubric is a worse outcome than a visible error.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from resume_screener.core.router import Model, Usage

log = logging.getLogger(__name__)

GENERATOR_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "rubric_generator.md"
).read_text(encoding="utf-8")

REQUIRED_DIMENSIONS = 3
GENERATOR_MAX_TOKENS = 4000

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


class RubricGenerationError(RuntimeError):
    """The model did not return a usable rubric.

    Raised rather than swallowed: every downstream score depends on the
    rubric being the right one for the posting, so there is no safe
    default to fall back to.
    """


@dataclass(frozen=True)
class RubricDimension:
    """One scored dimension, plus the brief for the agent that owns it."""

    name: str
    title: str
    criteria: str
    lens: str


@dataclass(frozen=True)
class GeneratedRubric:
    """A complete scoring standard for one job posting.

    Interchangeable with the hand-written `prompts/rubric.md`: both end up
    as the `markdown` half of the panel's cacheable system prefix.
    """

    role_title: str
    summary: str
    dimensions: tuple[RubricDimension, ...]
    usage: Usage = field(default_factory=Usage)

    @property
    def personas(self) -> dict[str, str]:
        """agent_name -> that agent's lens. Replaces `_PANEL_PERSONAS`."""
        return {d.name: d.lens for d in self.dimensions}

    @property
    def markdown(self) -> str:
        """The rubric as the panel reads it.

        Mirrors the shape of the hand-written rubric.md on purpose -- the
        panel prompt should not be able to tell whether a rubric was
        written by hand or generated.
        """
        lines = [
            f"# Scoring rubric — generated for: {self.role_title}",
            "",
            "This rubric was written from the job posting below, not from a",
            "generic AI-engineer template. Score against this posting",
            "specifically.",
            "",
            self.summary,
            "",
            f"The {len(self.dimensions)} dimensions below are the full scoring",
            "standard for this role. They are listed here so you understand what",
            "the other dimensions cover and do not double-count them.",
            "",
            "You are assigned exactly ONE of them. Score only your assigned",
            "dimension, 0-10, and report a confidence (0-1) alongside it. Return",
            "a single score object. Do not return one entry per dimension, and do",
            "not key your answer by dimension name.",
            "",
        ]
        for i, dim in enumerate(self.dimensions, start=1):
            lines.append(f"{i}. **{dim.title}** — {dim.criteria}")
        lines += [
            "",
            "Every claim you make must cite a direct quote from the",
            "candidate's extracted evidence. If the evidence doesn't support",
            "a claim, say so rather than inferring it — do not give credit",
            "for what a skills line implies if no evidence backs it.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "role_title": self.role_title,
            "summary": self.summary,
            "dimensions": [
                {
                    "name": d.name,
                    "title": d.title,
                    "criteria": d.criteria,
                    "lens": d.lens,
                }
                for d in self.dimensions
            ],
            "markdown": self.markdown,
        }


def _require_text(raw: dict, key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RubricGenerationError(f"{where}: missing or empty {key!r}.")
    return value.strip()


def parse_rubric(data: object, usage: Usage | None = None) -> GeneratedRubric:
    """Validate a generated rubric payload into a GeneratedRubric.

    Split out from the model call so the validation rules are testable
    without a model, and so a payload from any source (a cached file, a
    hand-edited rubric) goes through exactly the same checks.
    """
    if not isinstance(data, dict):
        raise RubricGenerationError("Rubric response was not a JSON object.")

    role_title = _require_text(data, "role_title", "rubric")
    summary = _require_text(data, "summary", "rubric")

    raw_dimensions = data.get("dimensions")
    if not isinstance(raw_dimensions, list):
        raise RubricGenerationError("Rubric response has no 'dimensions' list.")
    if len(raw_dimensions) != REQUIRED_DIMENSIONS:
        raise RubricGenerationError(
            f"Rubric must have exactly {REQUIRED_DIMENSIONS} dimensions, got "
            f"{len(raw_dimensions)}. The panel's disagreement threshold is "
            f"calibrated for {REQUIRED_DIMENSIONS}."
        )

    dimensions: list[RubricDimension] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_dimensions):
        where = f"dimension {i}"
        if not isinstance(raw, dict):
            raise RubricGenerationError(f"{where} is not an object.")
        name = _require_text(raw, "name", where)
        if not _IDENTIFIER.match(name):
            raise RubricGenerationError(
                f"{where}: {name!r} is not a snake_case identifier."
            )
        if name in seen:
            raise RubricGenerationError(f"{where}: duplicate name {name!r}.")
        seen.add(name)
        dimensions.append(
            RubricDimension(
                name=name,
                title=_require_text(raw, "title", where),
                criteria=_require_text(raw, "criteria", where),
                lens=_require_text(raw, "lens", where),
            )
        )

    return GeneratedRubric(
        role_title=role_title,
        summary=summary,
        dimensions=tuple(dimensions),
        usage=usage or Usage(),
    )


async def generate_rubric(job_description: str, model: Model) -> GeneratedRubric:
    """Write a rubric and three panel personas for one job posting.

    Call this once per batch and pass the result down -- see the module
    docstring on why per-resume generation breaks prompt caching.
    """
    if not job_description.strip():
        raise RubricGenerationError("Job description is empty.")

    response = await model.complete(
        GENERATOR_PROMPT,
        f"Job posting:\n\n{job_description}",
        max_tokens=GENERATOR_MAX_TOKENS,
        # One call per batch with a different posting every time. There is
        # no shared prefix across batches to hit, so a cache write here
        # would cost 1.25x base and never be read.
        cache_system=False,
    )

    start, end = response.text.find("{"), response.text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RubricGenerationError(
            f"No JSON object in rubric response: {response.text[:200]!r}"
        )
    try:
        data = json.loads(response.text[start : end + 1])
    except json.JSONDecodeError as exc:
        detail = "truncated -- raise GENERATOR_MAX_TOKENS" if response.truncated else str(exc)
        raise RubricGenerationError(f"Malformed JSON in rubric response: {detail}") from exc

    rubric = parse_rubric(data, response.usage)
    log.info(
        "Generated rubric for %r: %s",
        rubric.role_title,
        ", ".join(d.name for d in rubric.dimensions),
    )
    return rubric
