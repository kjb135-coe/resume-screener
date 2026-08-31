"""Shared data shapes for the pipeline. No adapter-specific concerns here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from resume_screener.core.router import Usage


class Recommendation(str, Enum):
    ADVANCE = "advance"
    HOLD = "hold"
    REJECT = "reject"


@dataclass
class Evidence:
    """A quoted snippet from a resume backing one rubric judgment."""

    quote: str
    rubric_dimension: str

    def to_dict(self) -> dict:
        return {"quote": self.quote, "dimension": self.rubric_dimension}


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
    parse_failed: bool = False
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "score": self.score,
            "rationale": self.rationale,
            "parse_failed": self.parse_failed,
        }


@dataclass
class Verdict:
    """Final, human-facing output for one candidate.

    Nothing here authorizes an action. A Verdict is advice: every downstream
    consumer treats it as something a human confirms, never as a decision
    already made. See docs/LIMITATIONS.md.
    """

    candidate: ExtractedCandidate
    score: float
    recommendation: Recommendation
    rationale: str
    panel_scores: list[RubricScore]
    escalated: bool
    panel_spread: float = 0.0
    usage: Usage = field(default_factory=Usage)

    @property
    def review_reason(self) -> str | None:
        """Why a human should look at this one first, if they should."""
        if any(p.parse_failed for p in self.panel_scores):
            return "At least one scoring agent returned an unreadable response."
        if self.candidate.confidence < 0.4:
            return (
                "This resume parsed poorly, so the extracted evidence may be "
                "incomplete. Scores based on it are less reliable."
            )
        if self.escalated:
            # Name the scores rather than the spread. "Spread of 7.0" is an
            # abstraction a reader has to decode; "9.0, 9.0 and 2.0" is the
            # disagreement itself, and makes obvious which agent dissented.
            scored = [p for p in self.panel_scores if not p.parse_failed]
            values = ", ".join(f"{p.score:.1f}" for p in scored)
            return (
                f"The panel disagreed ({values}); an arbiter resolved it, "
                "but a human should confirm."
            )
        return None

    def to_dict(self) -> dict:
        reason = self.review_reason
        return {
            "name": self.candidate.name,
            "source_path": self.candidate.source_path,
            "score": round(self.score, 2),
            "recommendation": self.recommendation.value,
            "rationale": self.rationale,
            "needs_human_review": reason is not None,
            "review_reason": reason,
            "panel_spread": round(self.panel_spread, 2),
            "extraction_confidence": round(self.candidate.confidence, 2),
            "evidence": [e.to_dict() for e in self.candidate.evidence],
        }
