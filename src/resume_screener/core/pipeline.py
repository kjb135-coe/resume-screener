"""The tiered cascade: extract -> panel -> arbitrate (only on disagreement).

Every function here takes plain arguments and returns plain dataclasses --
no MCP, no HTTP, no CLI concerns. adapters/ is the only code allowed to
import this module and translate its shapes outward.

Caching contract (load-bearing, do not break casually):
the system block passed to any panel call is `RUBRIC + job_description`
and nothing else. It is byte-identical across all three personas and
across every resume in a batch, so one cache write serves every
subsequent panel call. The persona and the candidate's evidence go in
the user turn. Putting the persona back into the system string would
silently create one cache entry per persona and gut the savings.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import statistics
from pathlib import Path

from resume_screener.core.ingest import iter_resume_paths, load_resume_text
from resume_screener.core.models import (
    Evidence,
    ExtractedCandidate,
    Recommendation,
    RubricScore,
    Verdict,
)
from resume_screener.core.router import AnthropicModel, Model, Usage

log = logging.getLogger(__name__)

RUBRIC = (Path(__file__).parent.parent / "prompts" / "rubric.md").read_text(encoding="utf-8")

# Both of these are deliberately un-calibrated placeholders. They get swept
# against the labeled corpus (PLAN.md section 8) rather than hand-tuned.
DISAGREEMENT_THRESHOLD = 2.0  # spread across panel scores before escalating
ADVANCE_CUTOFF = 7.0
HOLD_CUTOFF = 5.0

# Caps simultaneous in-flight resumes. Each resume fans out to 1 extraction
# + 3 panel calls, so 60 unbounded resumes would mean ~240 concurrent
# requests and immediate rate limiting.
MAX_CONCURRENT_RESUMES = 6

# Extended thinking consumes the same max_tokens budget as the visible
# answer. Budgets sized only for the JSON payload get eaten by thinking
# and truncate the answer mid-string, which then looks like a parse
# failure rather than the budget problem it actually is.
EXTRACT_MAX_TOKENS = 3000
PANEL_MAX_TOKENS = 4000
ARBITER_MAX_TOKENS = 3000

_PANEL_PERSONAS = {
    "production_reality": "You judge whether the evidence describes systems "
    "that shipped and are used in production, versus research, coursework, "
    "or proof-of-concept work that stopped at the demo stage. This posting "
    "explicitly wants production experience, not demos -- weight it heavily. "
    "Be skeptical of buzzwords; a tool named without a sentence describing "
    "what it did is not evidence.",
    "technical_integration": "You judge hands-on depth building agentic "
    "systems (memory, tools, orchestration) and integrating AI into real "
    "APIs, business systems, or automation platforms on cloud-native or "
    "hybrid infrastructure. Evidence must describe what they built, not a "
    "skills line.",
    "client_communication": "You judge evidence of explaining technical work "
    "to non-technical audiences, cross-functional collaboration (engineering, "
    "sales, delivery), or direct client engagement. This is the hardest "
    "signal to find in a typical resume -- its absence is not automatically "
    "disqualifying, but this posting names it as a required skill, so its "
    "presence is a genuine differentiator.",
}


def default_models() -> dict[str, Model]:
    try:
        api_key = os.environ["ANTHROPIC_API_KEY"]
    except KeyError:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it, or pass an explicit "
            "`models` dict to screen_one/rank_all (tests do this)."
        ) from None
    return {
        "triage": AnthropicModel("claude-haiku-4-5-20251001", api_key),
        "panel": AnthropicModel("claude-sonnet-5", api_key),
        "arbiter": AnthropicModel("claude-opus-5", api_key),
    }


def _panel_prefix(job_description: str) -> str:
    """The cacheable system prefix -- see the caching contract in the module
    docstring. Identical for every panel call in a batch, by construction.
    """
    return f"{RUBRIC}\n\n---\n\nJob description:\n{job_description}"


def _parse_json(text: str, *, expect: str = "object") -> dict | list | None:
    """Best-effort extraction of a JSON value from a model response.

    Returns None rather than raising -- callers decide what a failed parse
    means for their tier, since 'the model returned junk' is a real runtime
    condition, not an exceptional one.
    """
    open_c, close_c = ("{", "}") if expect == "object" else ("[", "]")
    start, end = text.find(open_c), text.rfind(close_c)
    if start == -1 or end == -1 or end < start:
        log.warning("No JSON %s found in model response: %.200s", expect, text)
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        log.warning("Malformed JSON in model response: %.200s", text)
        return None


def _coerce_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def extract_candidate(
    resume_path: str, model: Model
) -> tuple[ExtractedCandidate, Usage]:
    """Tier 0: cheap structured extraction. This is the object
    query_candidates later filters and reasons over, so it must carry
    evidence, not just facts.
    """
    raw_text = load_resume_text(resume_path)
    system = (
        "Extract structured facts from this resume as JSON with keys: "
        "name, years_experience (number), companies (list of str), "
        "technologies (list of str), education (list of str), "
        "evidence (list of {quote, rubric_dimension}), confidence (0-1). "
        "Evidence quotes must be verbatim from the resume."
    )
    response = await model.complete(system, raw_text, max_tokens=EXTRACT_MAX_TOKENS)
    data = _parse_json(response.text) or {}

    evidence = []
    for item in data.get("evidence") or []:
        if isinstance(item, dict) and item.get("quote"):
            evidence.append(
                Evidence(
                    quote=str(item["quote"]),
                    rubric_dimension=str(item.get("rubric_dimension", "unspecified")),
                )
            )

    candidate = ExtractedCandidate(
        source_path=resume_path,
        name=str(data.get("name") or Path(resume_path).stem),
        years_experience=_coerce_float(data.get("years_experience"), 0.0),
        companies=[str(c) for c in (data.get("companies") or [])],
        technologies=[str(t) for t in (data.get("technologies") or [])],
        education=[str(e) for e in (data.get("education") or [])],
        evidence=evidence,
        # A failed parse is genuinely low-confidence, not average-confidence.
        confidence=_coerce_float(data.get("confidence"), 0.0 if not data else 0.5),
        raw_text=raw_text,
    )
    return candidate, response.usage


async def _panel_agent(
    name: str, candidate: ExtractedCandidate, job_description: str, model: Model
) -> tuple[RubricScore, Usage]:
    evidence_json = json.dumps(
        [{"quote": e.quote, "rubric_dimension": e.rubric_dimension} for e in candidate.evidence]
    )
    user = (
        f"Your specific lens: {_PANEL_PERSONAS[name]}\n\n"
        f"Candidate evidence:\n{evidence_json}\n\n"
        "Respond as JSON: {score (0-10), confidence (0-1), rationale}. "
        "Keep the rationale to two sentences, quoting the evidence you relied on."
    )
    response = await model.complete(_panel_prefix(job_description), user, max_tokens=PANEL_MAX_TOKENS)
    data = _parse_json(response.text) or {}
    score = RubricScore(
        agent_name=name,
        score=_coerce_float(data.get("score"), 0.0),
        confidence=_coerce_float(data.get("confidence"), 0.0),
        rationale=str(data.get("rationale") or "No rationale returned."),
        parse_failed=not data,
    )
    return score, response.usage


async def _arbitrate(
    candidate: ExtractedCandidate,
    panel: list[RubricScore],
    job_description: str,
    model: Model,
) -> tuple[float, Recommendation, str, Usage]:
    user = (
        "The scoring panel disagreed on this candidate. Read their rationales, "
        "resolve the disagreement, and give a final verdict.\n\n"
        f"Panel scores:\n{json.dumps([p.to_dict() for p in panel])}\n\n"
        "Respond as JSON: {score (0-10), recommendation (advance|hold|reject), rationale}."
    )
    response = await model.complete(_panel_prefix(job_description), user, max_tokens=ARBITER_MAX_TOKENS)
    data = _parse_json(response.text) or {}

    score = _coerce_float(data.get("score"), statistics.mean([p.score for p in panel]))
    try:
        recommendation = Recommendation(str(data.get("recommendation", "")).strip().lower())
    except ValueError:
        recommendation = recommendation_from_score(score)
    rationale = str(data.get("rationale") or "Arbiter returned no rationale.")
    return score, recommendation, rationale, response.usage


def recommendation_from_score(score: float) -> Recommendation:
    if score >= ADVANCE_CUTOFF:
        return Recommendation.ADVANCE
    if score >= HOLD_CUTOFF:
        return Recommendation.HOLD
    return Recommendation.REJECT


async def screen_one(
    resume_path: str, job_description: str, models: dict[str, Model] | None = None
) -> Verdict:
    models = models or default_models()

    candidate, usage = await extract_candidate(resume_path, models["triage"])

    panel_results = await asyncio.gather(
        *[
            _panel_agent(name, candidate, job_description, models["panel"])
            for name in _PANEL_PERSONAS
        ]
    )
    panel = [score for score, _ in panel_results]
    for _, panel_usage in panel_results:
        usage = usage + panel_usage

    scores = [p.score for p in panel]
    spread = max(scores) - min(scores) if len(scores) > 1 else 0.0

    if spread > DISAGREEMENT_THRESHOLD:
        score, recommendation, rationale, arb_usage = await _arbitrate(
            candidate, panel, job_description, models["arbiter"]
        )
        return Verdict(
            candidate=candidate,
            score=score,
            recommendation=recommendation,
            rationale=rationale,
            panel_scores=panel,
            escalated=True,
            panel_spread=spread,
            usage=usage + arb_usage,
        )

    avg = statistics.mean(scores)
    return Verdict(
        candidate=candidate,
        score=avg,
        recommendation=recommendation_from_score(avg),
        rationale=" | ".join(f"[{p.agent_name}] {p.rationale}" for p in panel),
        panel_scores=panel,
        escalated=False,
        panel_spread=spread,
        usage=usage,
    )


async def rank_all(
    resume_dir: str,
    job_description: str,
    models: dict[str, Model] | None = None,
    max_concurrent: int = MAX_CONCURRENT_RESUMES,
) -> list[Verdict]:
    """Screen every resume in a directory, ranked best-first.

    Returns the FULL pool, not a truncated shortlist -- truncation is the
    caller's job. query_candidates has to be able to ask about candidates
    outside the top N, so the session must retain everything.
    """
    models = models or default_models()
    paths = iter_resume_paths(resume_dir)
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded(path: str) -> Verdict | None:
        async with semaphore:
            try:
                return await screen_one(path, job_description, models)
            except Exception:
                # One unreadable resume shouldn't sink a 60-resume batch.
                log.exception("Failed to screen %s", path)
                return None

    results = await asyncio.gather(*[_bounded(p) for p in paths])
    verdicts = [v for v in results if v is not None]
    return sorted(verdicts, key=lambda v: v.score, reverse=True)
