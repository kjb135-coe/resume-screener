"""Shared data shapes for the pipeline. No adapter-specific concerns here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from resume_screener.core.cutoffs import REVIEW_MARGIN_FRACTION
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
    cutoff_distance: float | None = None
    """How far `score` sits from the nearest verdict cutoff, in points.

    Computed by the pipeline, which is the only place that knows which
    model scored the panel and therefore which cutoffs apply. `None` means
    nobody worked it out -- the review rule then abstains rather than
    guessing with the wrong model's thresholds.
    """
    cutoff_band_width: float | None = None
    """Width of the model's `hold` band, the unit `cutoff_distance` is in.

    Kept alongside the raw distance rather than folded into it so both
    stay readable: the distance is what a human wants to see, the ratio is
    what the review rule compares.
    """
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
        # Deliberately NOT `if self.escalated`. Panel disagreement used to
        # trigger this, and it was a poor proxy for "this one is wrong":
        # measured over 179 screenings it queued 53% of the stack and
        # caught 36% of the errors. What actually predicts a wrong verdict
        # is the score landing near a cutoff, where a small difference in
        # judgment flips the answer. Same queue size, that catches 82%.
        #
        # The arbiter still runs on disagreement -- it just no longer
        # conscripts a human every time it does. See REVIEW_MARGIN in
        # core/cutoffs.py and docs/RESULTS_HISTORY.md.
        near_cutoff = (
            self.cutoff_distance is not None
            and self.cutoff_band_width
            and self.cutoff_distance / self.cutoff_band_width <= REVIEW_MARGIN_FRACTION
        )
        if near_cutoff:
            # Deliberately does not name WHICH boundary. The cutoffs are
            # per-model and this object does not know which model scored
            # the panel -- inferring the boundary from the score alone
            # would be a guess, and a wrong one for any model whose
            # cutoffs are not the default pair.
            return (
                f"This scored {self.score:.1f} and landed on "
                f"`{self.recommendation.value}`, close enough to the line "
                "that a small difference in judgment changes the answer. "
                "A human should make this call."
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
