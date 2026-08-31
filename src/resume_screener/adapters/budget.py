"""A hard daily spend cap for a hosted deployment.

The app is fronted by a shared password, so anyone with the link can
start a run that spends real money at two providers. A password stops
strangers; it does not stop five colleagues each starting ten runs.

Design notes, in order of how much they matter:

- **It counts what was actually spent, not what was requested.** Every
  Verdict carries real token counts per model (`Usage.by_model`), so the
  ledger is priced from the same numbers the eval reports. An estimate
  would drift from the bill.
- **It is checked BEFORE a run and recorded AFTER.** A run therefore can
  overshoot the cap by at most the cost of one batch, which is why the
  per-request resume limit exists as well. Refusing mid-run would leave
  a half-scored job and no result.
- **It is a backstop, not the backstop.** The real limit is the hard cap
  set in each provider's own dashboard, which no bug in this file can
  bypass. This exists so a user hits a friendly message instead of a
  dead site. See docs/HOSTING.md.
- **State is in memory.** A restart resets the day's ledger. For a
  week-long demo behind a provider-level cap that is an acceptable
  trade; a real deployment would persist it.
"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime

# Published per-million-token rates. Kept next to the ledger rather than
# imported from scripts/ so the adapter does not depend on the eval
# tooling. Verified 2026-08-27; see docs/COST_ANALYSIS.md, which records
# the two that were wrong before that check.
PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "gpt-5.6-luna": {"in": 0.20, "out": 1.20, "cache_read": 0.02, "cache_write": 0.0},
}

# An unknown model is priced at the most expensive rates on file rather
# than skipped. Under-counting spend is the failure that costs money.
_FALLBACK = {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25}

def _utc_day():
    """UTC, explicitly. The reset time has to be the same for everyone
    looking at a shared link, and it has to be the same after a restart
    on a host in another region."""
    return datetime.now(UTC).date()


DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", "3.00"))
MAX_RESUMES_PER_RUN = int(os.environ.get("MAX_RESUMES_PER_RUN", "20"))


def cost_of_usage(by_model: dict[str, dict[str, int]]) -> float:
    """Dollar cost of one run's real token counts."""
    total = 0.0
    for model_id, counts in by_model.items():
        rates = PRICING.get(model_id, _FALLBACK)
        total += (
            counts.get("input_tokens", 0) / 1e6 * rates["in"]
            + counts.get("output_tokens", 0) / 1e6 * rates["out"]
            + counts.get("cache_read_input_tokens", 0) / 1e6 * rates["cache_read"]
            + counts.get("cache_creation_input_tokens", 0) / 1e6 * rates["cache_write"]
        )
    return total


class DailyBudget:
    """Spend for one UTC day, with a hard ceiling."""

    def __init__(self, limit_usd: float | None = None):
        self.limit = DAILY_BUDGET_USD if limit_usd is None else limit_usd
        self._lock = threading.Lock()
        self._day = _utc_day()
        self._spent = 0.0

    def _roll(self) -> None:
        today = _utc_day()
        if today != self._day:
            self._day, self._spent = today, 0.0

    @property
    def spent(self) -> float:
        with self._lock:
            self._roll()
            return self._spent

    @property
    def remaining(self) -> float:
        return max(self.limit - self.spent, 0.0)

    def check(self) -> None:
        """Raise if today's budget is already gone.

        Called before a run starts. A run that has begun is allowed to
        finish -- stopping halfway leaves a half-scored job and no
        result, which is worse for the user and saves very little.
        """
        if self.remaining <= 0:
            raise BudgetExceeded(
                f"The daily demo budget of ${self.limit:.2f} is spent. "
                "It resets at midnight UTC. This cap exists so a shared "
                "demo link cannot run up a real bill."
            )

    def record(self, by_model: dict[str, dict[str, int]]) -> float:
        """Add a finished run's real cost to today's ledger."""
        cost = cost_of_usage(by_model)
        with self._lock:
            self._roll()
            self._spent += cost
        return cost

    def snapshot(self) -> dict:
        with self._lock:
            self._roll()
            return {
                "day": self._day.isoformat(),
                "limit_usd": round(self.limit, 2),
                "spent_usd": round(self._spent, 4),
                "remaining_usd": round(max(self.limit - self._spent, 0.0), 4),
                "max_resumes_per_run": MAX_RESUMES_PER_RUN,
            }


class BudgetExceeded(RuntimeError):
    """Today's spend cap is used up."""


budget = DailyBudget()


# Substrings that mean "the account cannot pay", across providers. Matched
# on the exception text because neither SDK raises a distinct class for
# it: Anthropic returns HTTP 400 per request with the reason in the body,
# and OpenAI a 429 that reads the same as a rate limit.
_OUT_OF_CREDIT = (
    "credit balance is too low",
    "insufficient_quota",
    "exceeded your current quota",
    "billing_hard_limit_reached",
)
_BAD_KEY = ("invalid_api_key", "invalid x-api-key", "incorrect api key", "unauthorized")


def explain_provider_failure(exc: BaseException) -> str | None:
    """A message a visitor can act on, or None if this is not that.

    A run out of credit fails per-request, so without this the page shows
    "Screening failed, check the server log" for something no visitor can
    check and the operator cannot see from the outside. It happened four
    times during development; each time the surface error said nothing
    useful.
    """
    text = str(exc).lower()
    if any(marker in text for marker in _OUT_OF_CREDIT):
        return (
            "The API account behind this site is out of credit, so nothing "
            "can be scored right now. Nothing is wrong with your resume or "
            "your posting. Try again later."
        )
    if any(marker in text for marker in _BAD_KEY):
        return (
            "The API key behind this site is not being accepted, so nothing "
            "can be scored right now. This is a server configuration "
            "problem, not something you did."
        )
    return None
