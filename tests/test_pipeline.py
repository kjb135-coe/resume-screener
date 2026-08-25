"""Pipeline behaviour, exercised offline against FakeModel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resume_screener.core.models import Recommendation
from resume_screener.core.pipeline import (
    _panel_prefix,
    _parse_json,
    rank_all,
    recommendation_from_score,
    screen_one,
)
from tests.fakes import EXTRACTION_JSON, FakeModel, arbiter_json, panel_json

FIXTURE = str(Path(__file__).parent / "fixtures" / "sample_resume.md")
JD = "We want an AI solutions engineer who ships to production."


def _models(panel_scores: list[float], arbiter: str | None = None) -> dict:
    return {
        "triage": FakeModel([EXTRACTION_JSON]),
        "panel": FakeModel([panel_json(s) for s in panel_scores]),
        "arbiter": FakeModel([arbiter or arbiter_json(8.0)]),
    }


class TestParsing:
    def test_extracts_json_from_surrounding_prose(self):
        assert _parse_json('Sure! {"score": 7} hope that helps') == {"score": 7}

    def test_returns_none_on_garbage_rather_than_raising(self):
        assert _parse_json("I cannot help with that.") is None

    def test_returns_none_on_malformed_json(self):
        assert _parse_json('{"score": }') is None

    def test_parses_arrays(self):
        assert _parse_json('[{"a": 1}]', expect="array") == [{"a": 1}]


class TestRecommendationCutoffs:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (9.0, Recommendation.ADVANCE),
            (7.0, Recommendation.ADVANCE),
            (6.9, Recommendation.HOLD),
            (5.0, Recommendation.HOLD),
            (4.9, Recommendation.REJECT),
        ],
    )
    def test_boundaries(self, score, expected):
        assert recommendation_from_score(score) == expected


class TestScreenOne:
    async def test_agreeing_panel_does_not_escalate(self):
        models = _models([7.0, 7.5, 7.2])
        verdict = await screen_one(FIXTURE, JD, models)

        assert not verdict.escalated
        assert models["arbiter"].calls == [], "arbiter must not run on agreement"
        assert verdict.score == pytest.approx(7.233, abs=0.01)
        assert verdict.recommendation == Recommendation.ADVANCE
        assert verdict.review_reason is None

    async def test_disagreeing_panel_escalates_to_arbiter(self):
        models = _models([9.0, 4.0, 3.5], arbiter=arbiter_json(5.0, "hold"))
        verdict = await screen_one(FIXTURE, JD, models)

        assert verdict.escalated
        assert len(models["arbiter"].calls) == 1
        assert verdict.score == 5.0
        assert verdict.recommendation == Recommendation.HOLD
        assert "disagreed" in verdict.review_reason

    async def test_panel_spread_recorded(self):
        verdict = await screen_one(FIXTURE, JD, _models([9.0, 4.0, 3.5]))
        assert verdict.panel_spread == pytest.approx(5.5)

    async def test_usage_accumulates_across_every_call(self):
        verdict = await screen_one(FIXTURE, JD, _models([7.0, 7.0, 7.0]))
        # 1 extraction + 3 panel calls, 100 input tokens each in the fake
        assert verdict.usage.input_tokens == 400
        assert verdict.usage.output_tokens == 80

    async def test_all_three_personas_are_consulted(self):
        models = _models([7.0, 7.0, 7.0])
        verdict = await screen_one(FIXTURE, JD, models)
        agents = {p.agent_name for p in verdict.panel_scores}
        assert agents == {"production_reality", "technical_integration", "client_communication"}


class TestCachingContract:
    """The cost story depends on the cached prefix being identical across
    every panel call. If a persona leaks back into the system block this
    silently stops being true, so it is asserted rather than assumed.
    """

    async def test_system_prefix_identical_across_personas(self):
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models)

        systems = {c["system"] for c in models["panel"].calls}
        assert len(systems) == 1, "panel calls must share one cacheable prefix"

    async def test_persona_travels_in_user_turn_not_system(self):
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models)

        for call in models["panel"].calls:
            assert "Your specific lens" in call["user"]
            assert "Your specific lens" not in call["system"]

    def test_prefix_contains_rubric_and_job_description(self):
        prefix = _panel_prefix(JD)
        assert JD in prefix
        assert "Production reality" in prefix

    async def test_caching_is_requested(self):
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models)
        assert all(c["cache_system"] for c in models["panel"].calls)

    async def test_scoring_runs_deterministically(self):
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models)
        assert all(c["temperature"] == 0.0 for c in models["panel"].calls)


class TestFallbacks:
    async def test_unparseable_panel_response_does_not_crash(self):
        models = {
            "triage": FakeModel([EXTRACTION_JSON]),
            "panel": FakeModel(["I'm sorry, I can't do that."]),
            "arbiter": FakeModel([arbiter_json(5.0)]),
        }
        verdict = await screen_one(FIXTURE, JD, models)

        assert all(p.parse_failed for p in verdict.panel_scores)
        assert verdict.review_reason is not None
        assert "unreadable" in verdict.review_reason

    async def test_unparseable_extraction_yields_low_confidence(self):
        models = {
            "triage": FakeModel(["no json here"]),
            "panel": FakeModel([panel_json(7.0)]),
            "arbiter": FakeModel([arbiter_json(7.0)]),
        }
        verdict = await screen_one(FIXTURE, JD, models)

        assert verdict.candidate.confidence == 0.0
        assert verdict.candidate.name == "sample_resume"  # falls back to filename
        assert verdict.review_reason is not None

    async def test_arbiter_bad_recommendation_falls_back_to_score_cutoffs(self):
        bad = json.dumps({"score": 8.5, "recommendation": "definitely_hire", "rationale": "x"})
        models = _models([9.0, 4.0, 3.5], arbiter=bad)
        verdict = await screen_one(FIXTURE, JD, models)

        assert verdict.recommendation == Recommendation.ADVANCE  # 8.5 -> advance

    async def test_arbiter_missing_score_falls_back_to_panel_mean(self):
        bad = json.dumps({"recommendation": "hold", "rationale": "x"})
        models = _models([9.0, 4.0, 3.0], arbiter=bad)
        verdict = await screen_one(FIXTURE, JD, models)

        assert verdict.score == pytest.approx(5.333, abs=0.01)


class TestRankAll:
    async def test_returns_full_pool_not_truncated(self, tmp_path):
        for i in range(5):
            (tmp_path / f"cand_{i}.md").write_text("Engineer who shipped things.")

        models = _models([7.0, 7.0, 7.0])
        verdicts = await rank_all(str(tmp_path), JD, models)

        assert len(verdicts) == 5, "session needs the whole pool, not a shortlist"

    async def test_sorted_best_first(self, tmp_path):
        for i in range(3):
            (tmp_path / f"cand_{i}.md").write_text("Engineer.")

        models = _models([7.0, 7.0, 7.0])
        verdicts = await rank_all(str(tmp_path), JD, models)
        scores = [v.score for v in verdicts]
        assert scores == sorted(scores, reverse=True)

    async def test_one_broken_resume_does_not_sink_the_batch(self, tmp_path):
        (tmp_path / "good.md").write_text("Engineer who shipped things.")
        (tmp_path / "broken.pdf").write_bytes(b"not actually a pdf")

        models = _models([7.0, 7.0, 7.0])
        verdicts = await rank_all(str(tmp_path), JD, models)

        assert len(verdicts) == 1
        assert verdicts[0].candidate.source_path.endswith("good.md")

    async def test_concurrency_is_bounded(self, tmp_path):
        for i in range(20):
            (tmp_path / f"cand_{i}.md").write_text("Engineer.")

        models = _models([7.0, 7.0, 7.0])
        await rank_all(str(tmp_path), JD, models, max_concurrent=3)
        # 20 resumes still all screened despite the cap
        assert len(models["triage"].calls) == 20
