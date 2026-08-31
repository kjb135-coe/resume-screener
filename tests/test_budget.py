"""The hosted spend cap.

Worth real tests despite being small: it is the only thing between a
shared demo link and an unbounded bill at two providers, and every one of
its failure modes is silent. A cap that under-counts, or that never
resets, or that resets on the wrong clock, all look fine until they do
not.
"""

from __future__ import annotations

import pytest

from resume_screener.adapters.budget import (
    BudgetExceeded,
    DailyBudget,
    cost_of_usage,
)

LUNA_1M_IN = {
    "gpt-5.6-luna": {
        "input_tokens": 1_000_000,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
}


class TestCostOfUsage:
    def test_prices_a_known_model(self):
        # Luna input is $0.20/1M.
        assert cost_of_usage(LUNA_1M_IN) == pytest.approx(0.20)

    def test_sums_across_models_in_one_run(self):
        # A single run spans providers: Haiku extracts, Luna scores.
        usage = {
            "gpt-5.6-luna": {"input_tokens": 1_000_000, "output_tokens": 0},
            "claude-haiku-4-5-20251001": {"input_tokens": 1_000_000, "output_tokens": 0},
        }
        assert cost_of_usage(usage) == pytest.approx(0.20 + 1.00)

    def test_unknown_model_is_priced_high_not_free(self):
        """Under-counting is the failure that costs money.

        A model added to the pipeline but forgotten here must not spend
        silently, so the fallback is the most expensive rates on file.
        """
        unknown = {"some-new-model": {"input_tokens": 1_000_000, "output_tokens": 0}}
        assert cost_of_usage(unknown) == pytest.approx(5.00)

    def test_counts_cached_reads_and_writes(self):
        usage = {
            "claude-haiku-4-5-20251001": {
                "cache_read_input_tokens": 1_000_000,
                "cache_creation_input_tokens": 1_000_000,
            }
        }
        assert cost_of_usage(usage) == pytest.approx(0.10 + 1.25)

    def test_empty_usage_is_free(self):
        assert cost_of_usage({}) == 0.0


class TestDailyBudget:
    def test_starts_with_the_whole_budget(self):
        b = DailyBudget(3.0)
        assert b.spent == 0.0
        assert b.remaining == 3.0
        b.check()  # must not raise

    def test_records_real_spend(self):
        b = DailyBudget(3.0)
        assert b.record(LUNA_1M_IN) == pytest.approx(0.20)
        assert b.remaining == pytest.approx(2.80)

    def test_blocks_once_the_budget_is_gone(self):
        b = DailyBudget(0.10)
        b.record(LUNA_1M_IN)  # $0.20, over the $0.10 limit
        with pytest.raises(BudgetExceeded):
            b.check()

    def test_remaining_never_goes_negative(self):
        b = DailyBudget(0.10)
        b.record(LUNA_1M_IN)
        assert b.remaining == 0.0

    def test_a_started_run_is_not_interrupted(self):
        """check() gates the START of a run, record() happens after.

        Stopping mid-run would leave a half-scored job and no result while
        saving almost nothing, so overshoot by up to one batch is the
        deliberate trade -- bounded by MAX_RESUMES_PER_RUN.
        """
        b = DailyBudget(0.15)
        b.check()  # allowed: $0.15 remains before the run starts
        b.record(LUNA_1M_IN)  # run completes and overshoots
        assert b.spent > 0.0
        with pytest.raises(BudgetExceeded):
            b.check()  # the NEXT run is refused

    def test_resets_when_the_day_rolls_over(self, monkeypatch):
        import datetime as dt

        import resume_screener.adapters.budget as mod

        b = DailyBudget(0.10)
        b.record(LUNA_1M_IN)
        with pytest.raises(BudgetExceeded):
            b.check()

        monkeypatch.setattr(mod, "_utc_day", lambda: dt.date(2099, 1, 1))
        assert b.spent == 0.0
        b.check()  # a new day, a fresh budget

    def test_snapshot_reports_what_a_refused_user_needs(self):
        b = DailyBudget(3.0)
        b.record(LUNA_1M_IN)
        snap = b.snapshot()
        assert snap["limit_usd"] == 3.0
        assert snap["spent_usd"] == pytest.approx(0.20)
        assert snap["remaining_usd"] == pytest.approx(2.80)
        assert "day" in snap and "max_resumes_per_run" in snap


class TestProviderFailureMessages:
    """Out of credit must not surface as "check the server log".

    It fails per-request, so without this the page shows a message no
    visitor can act on and the operator cannot see from outside. It
    happened four times during development.
    """

    def _explain(self, text):
        from resume_screener.adapters.budget import explain_provider_failure

        return explain_provider_failure(RuntimeError(text))

    def test_anthropic_out_of_credit(self):
        msg = self._explain(
            "Error code: 400 - {'error': {'message': 'Your credit balance is too "
            "low to access the Anthropic API.'}}"
        )
        assert msg and "out of credit" in msg
        assert "your resume" in msg, "must say it is not the visitor's fault"

    def test_openai_quota_exhausted(self):
        assert "out of credit" in self._explain("insufficient_quota: exceeded")

    def test_bad_key_is_distinguished_from_no_money(self):
        msg = self._explain("Error code: 401 - invalid_api_key")
        assert msg and "not being accepted" in msg

    def test_an_ordinary_failure_is_not_dressed_up(self):
        # Only real billing/auth problems get a friendly message; anything
        # else must keep its generic error so it is not hidden.
        assert self._explain("Connection reset by peer") is None
        assert self._explain("Malformed JSON in model response") is None
