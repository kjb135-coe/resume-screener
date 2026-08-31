"""Score-to-verdict thresholds, and the margins built on them.

A leaf module by necessity: `models.py` needs these for its human-review
rule and `pipeline.py` already imports `models`, so anything shared has
to sit below both or the import graph becomes a cycle. Nothing here
imports from `core`.

Two different questions get asked of a cutoff, and they are not the same
question:

    "could the arbiter still change this verdict?"   -> ESCALATION_MARGIN
    "should a human look at this verdict?"           -> REVIEW_MARGIN_FRACTION

The first is asked of the PANEL MEAN, before the arbiter runs. The second
is asked of the FINAL score, after it. The first is absolute (points),
the second is a fraction of the model's own band -- each in the unit its
own evidence supports; see the comments on each. They used to be one decision --
escalating both called the arbiter and flagged the candidate for review
-- and welding them together was wrong in both directions. See
docs/RESULTS_HISTORY.md.
"""

from __future__ import annotations

from typing import NamedTuple, Protocol


class _HasModelId(Protocol):
    @property
    def model_id(self) -> str: ...


ADVANCE_CUTOFF = 4.0
HOLD_CUTOFF = 1.0


class Cutoffs(NamedTuple):
    """The two thresholds that turn a 0-10 score into a verdict."""

    advance: float
    hold: float


DEFAULT_CUTOFFS = Cutoffs(ADVANCE_CUTOFF, HOLD_CUTOFF)

# Cutoffs are per MODEL, not global.
#
# The thresholds above were swept against Sonnet's score distribution,
# then used to judge every other model. A model that grades on a
# different scale then loses macro-F1 to the mismatch rather than to its
# judgment.
#
# Measured 2026-08-27 on 60 resumes, 3 runs per model, cutoffs fitted per
# model and tested on folds they never saw (scripts/fit_cutoffs.py):
#
#   model            shipped 4.0/1.0    own cutoffs   held-out macro-F1
#   claude-sonnet-5       0.823           3.1/0.7           0.787
#   gpt-5.6-luna          0.563           5.8/2.6           0.861
#
# Luna's mean score is 4.60 against Sonnet's 2.35. Under one global pair
# it looked 0.26 worse; calibrated to itself it is better, and it won 4
# of 5 folds while losing none.
#
# A model absent from this table falls back to DEFAULT_CUTOFFS, which is
# honest rather than safe: the fallback is Sonnet's calibration, so an
# unfitted model is being judged on another model's scale. Fit it before
# trusting its score -- docs/CUTOFF_FIT.md.
#
# These are fitted on 60 synthetic resumes and cross-validated on folds of
# those same 60. That is better than fitting and scoring on all of them,
# and it is still not fresh data. See docs/LIMITATIONS.md.
MODEL_CUTOFFS: dict[str, Cutoffs] = {
    "claude-sonnet-5": Cutoffs(3.1, 0.7),
    "gpt-5.6-luna": Cutoffs(5.8, 2.6),
}

# How close the PANEL MEAN must sit to a cutoff before paying for an
# arbiter call.
#
# The arbiter can only change a verdict by moving the score across a
# cutoff. Measured over 84 recorded escalations, it moves the score off
# the panel mean by a median of 0.33, p75 0.50, p95 1.00, and never more
# than 1.50. So a mean sitting further from a cutoff than that is a call
# the arbiter cannot win, and 92% of escalations were exactly that -- the
# arbiter returned a different number and the verdict did not move.
#
# 0.5 is twice the largest distance at which an escalation has ever
# changed a verdict (0.33 across 7 such events), and equal to the
# arbiter's p75 movement. Simulated over var1/var3/var4: escalation
# 46.9% -> 12.3%, keeping all 7 that mattered, macro-F1 unchanged.
#
# If this proves too tight, the principled retreat is 1.0 -- the
# arbiter's p95 movement -- which still cuts calls by 39%. Do not tune it
# below 0.33 without new evidence; that is where the useful escalations
# actually live.
ESCALATION_MARGIN = 0.5

# How close the FINAL score must sit to a cutoff before a human is asked
# to look -- as a FRACTION of the model's own hold band, not an absolute
# number of points.
#
# This replaced "escalated" as the review trigger. That proxy was
# dominated on both axes: it queued 53% of the stack and caught only 36%
# of the system's errors, because panel disagreement is a poor predictor
# of a wrong answer. A near-cutoff test catches far more at the same size.
#
# It is a fraction because an absolute margin means different things to
# different models -- the same mistake the single global cutoff pair made.
# Sonnet's hold band is 2.4 wide (0.7-3.1) and Luna's is 3.2 (2.6-5.8),
# and Sonnet's scores cluster tightly inside its narrower band. Measured
# live on 120 screenings, a flat 0.4 gave:
#
#   Sonnet  queue 43%   Luna  queue 15%
#
# and the same fraction of each band gives:
#
#   Sonnet  queue 30% (catches 50% of errors)
#   Luna    queue 15% (catches 33%)
#
# 0.125 of the band = 0.30 for Sonnet, 0.40 for Luna.
#
# Raising it trades queue size for recall, roughly linearly. It cannot
# approach full recall at any tolerable queue size: the system is wrong on
# ~15% of candidates, so reviewing a third of them cannot catch most
# errors. That is arithmetic, not a tuning failure.
REVIEW_MARGIN_FRACTION = 0.125


def cutoffs_for(model: _HasModelId | str | None) -> Cutoffs:
    """The verdict thresholds for whichever model scored the panel."""
    if model is None:
        return DEFAULT_CUTOFFS
    model_id = model if isinstance(model, str) else getattr(model, "model_id", "")
    return MODEL_CUTOFFS.get(model_id, DEFAULT_CUTOFFS)


def band_width(cutoffs: Cutoffs | None = None) -> float:
    """The width of the `hold` band -- the model's own unit of scale.

    Margins expressed in raw points are not comparable across models: a
    0.4 gap is a sixth of Sonnet's band and an eighth of Luna's. Dividing
    by this is what makes a single constant mean the same thing to both.
    """
    bounds = cutoffs or DEFAULT_CUTOFFS
    return max(bounds.advance - bounds.hold, 1e-9)


def distance_to_cutoff(score: float, cutoffs: Cutoffs | None = None) -> float:
    """How far this score sits from the nearest verdict boundary.

    The unit both margins are measured in. A small distance means a small
    change in judgment flips the answer.
    """
    bounds = cutoffs or DEFAULT_CUTOFFS
    return min(abs(score - bounds.advance), abs(score - bounds.hold))
