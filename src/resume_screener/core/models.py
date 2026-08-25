"""Shared data shapes for the pipeline. No adapter-specific concerns here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Recommendation(str, Enum):
    ADVANCE = "advance"
    HOLD = "hold"
    REJECT = "reject"


@dataclass
class Evidence:
    """A quoted snippet from a resume backing one rubric judgment."""

    quote: str
    rubric_dimension: str


@dataclass
class ExtractedCandidate:
    """Output of Tier 0 -- structured facts pulled from a raw resume.

    This is the object that gets cached in a session for query_candidates,
    so it carries everything a later free-form question might need without
    re-reading the original file.
    """

    source_path: str
    name: str
    years_experience: float
    companies: list[str]
    technologies: list[str]
    education: list[str]
    evidence: list[Evidence]
    confidence: float
    raw_text: str


@dataclass
class RubricScore:
    """One panel agent's judgment on one candidate."""

    agent_name: str
    score: float
    rationale: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class Verdict:
    """Final, human-facing output for one candidate."""

    candidate: ExtractedCandidate
    score: float
    recommendation: Recommendation
    rationale: str
    panel_scores: list[RubricScore]
    escalated: bool

    def to_dict(self) -> dict:
        return {
            "name": self.candidate.name,
            "source_path": self.candidate.source_path,
            "score": self.score,
            "recommendation": self.recommendation.value,
            "rationale": self.rationale,
            "needs_human_review": self.escalated,
            "review_reason": (
                "The scoring panel disagreed on this candidate; an arbiter "
                "resolved it, but a human should confirm before acting on it."
                if self.escalated
                else None
            ),
            "evidence": [
                {"quote": e.quote, "dimension": e.rubric_dimension}
                for e in self.candidate.evidence
            ],
        }
