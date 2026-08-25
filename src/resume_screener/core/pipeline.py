"""The tiered cascade: extract -> panel -> arbitrate (only on disagreement).

Every function here takes plain arguments and returns plain dataclasses --
no MCP, no HTTP, no CLI concerns. adapters/ is the only code allowed to
import this module and translate its shapes outward.
"""

from __future__ import annotations

import asyncio
import json
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
from resume_screener.core.router import AnthropicModel, Model

RUBRIC = (Path(__file__).parent.parent / "prompts" / "rubric.md").read_text()

DISAGREEMENT_THRESHOLD = 2.0  # points, on a 0-10 scale, before escalating to Tier 2

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
    api_key = os.environ["ANTHROPIC_API_KEY"]
    return {
        "triage": AnthropicModel("claude-haiku-4-5-20251001", api_key),
        "panel": AnthropicModel("claude-sonnet-5", api_key),
        "arbiter": AnthropicModel("claude-opus-5", api_key),
    }


def _parse_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


async def extract_candidate(resume_path: str, model: Model) -> ExtractedCandidate:
    """Tier 0: cheap structured extraction. This is the object query_candidates
    later filters and reasons over, so it must carry evidence, not just facts.
    """
    raw_text = load_resume_text(resume_path)
    system = (
        "Extract structured facts from this resume as JSON with keys: "
        "name, years_experience (number), companies (list of str), "
        "technologies (list of str), education (list of str), "
        "evidence (list of {quote, rubric_dimension}), confidence (0-1)."
    )
    response = await model.complete(system, raw_text, max_tokens=1024)
    data = _parse_json(response)
    return ExtractedCandidate(
        source_path=resume_path,
        name=data.get("name", "Unknown"),
        years_experience=float(data.get("years_experience", 0)),
        companies=data.get("companies", []),
        technologies=data.get("technologies", []),
        education=data.get("education", []),
        evidence=[Evidence(**e) for e in data.get("evidence", [])],
        confidence=float(data.get("confidence", 0.5)),
        raw_text=raw_text,
    )


async def _panel_agent(name: str, candidate: ExtractedCandidate, job_description: str, model: Model) -> RubricScore:
    system = f"{RUBRIC}\n\nYour specific lens: {_PANEL_PERSONAS[name]}\n\nRespond as JSON: {{score, rationale}}."
    user = (
        f"Job description:\n{job_description}\n\n"
        f"Candidate evidence:\n{json.dumps([e.__dict__ for e in candidate.evidence])}"
    )
    response = await model.complete(system, user, max_tokens=512)
    data = _parse_json(response)
    return RubricScore(agent_name=name, score=float(data["score"]), rationale=data["rationale"])


async def _arbitrate(candidate: ExtractedCandidate, panel: list[RubricScore], job_description: str, model: Model) -> Verdict:
    system = (
        f"{RUBRIC}\n\nA panel of three agents disagreed on this candidate. "
        "Read their rationales, resolve the disagreement, and give a final "
        "verdict. Respond as JSON: {score, recommendation (advance|hold|reject), rationale}."
    )
    user = (
        f"Job description:\n{job_description}\n\n"
        f"Panel scores:\n{json.dumps([p.__dict__ for p in panel])}"
    )
    response = await model.complete(system, user, max_tokens=768)
    data = _parse_json(response)
    return Verdict(
        candidate=candidate,
        score=float(data["score"]),
        recommendation=Recommendation(data["recommendation"]),
        rationale=data["rationale"],
        panel_scores=panel,
        escalated=True,
    )


def _recommendation_from_score(score: float) -> Recommendation:
    if score >= 7:
        return Recommendation.ADVANCE
    if score >= 5:
        return Recommendation.HOLD
    return Recommendation.REJECT


async def screen_one(resume_path: str, job_description: str, models: dict[str, Model] | None = None) -> Verdict:
    models = models or default_models()

    candidate = await extract_candidate(resume_path, models["triage"])

    panel = await asyncio.gather(
        *[_panel_agent(name, candidate, job_description, models["panel"]) for name in _PANEL_PERSONAS]
    )
    scores = [p.score for p in panel]

    if len(scores) > 1 and (max(scores) - min(scores)) > DISAGREEMENT_THRESHOLD:
        return await _arbitrate(candidate, list(panel), job_description, models["arbiter"])

    avg = statistics.mean(scores)
    return Verdict(
        candidate=candidate,
        score=avg,
        recommendation=_recommendation_from_score(avg),
        rationale=" | ".join(p.rationale for p in panel),
        panel_scores=list(panel),
        escalated=False,
    )


async def rank_all(resume_dir: str, job_description: str, top_n: int = 10, models: dict[str, Model] | None = None) -> list[Verdict]:
    models = models or default_models()
    paths = iter_resume_paths(resume_dir)
    verdicts = await asyncio.gather(*[screen_one(p, job_description, models) for p in paths])
    return sorted(verdicts, key=lambda v: v.score, reverse=True)[:top_n]
