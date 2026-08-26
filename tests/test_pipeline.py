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
    rubric_for,
    screen_one,
)
from resume_screener.core.router import Usage
from resume_screener.core.rubric_gen import parse_rubric
from tests.fakes import (
    EXTRACTION_JSON,
    FakeModel,
    arbiter_json,
    panel_json,
    rubric_json,
)

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


class TestUnterminatedJsonRecovery:
    """Measured live on 2026-08-25: the panel model intermittently ends its
    turn (stop_reason 'end_turn', ~324 of 4000 tokens used) having closed
    its final string but never emitted the closing brace. 5 of 180 panel
    calls in the recorded eval run were discarded that way, each becoming
    a spurious 0.0. The score was in the text the whole time.
    """

    def test_recovers_a_missing_closing_brace(self):
        assert _parse_json('{"score": 8, "confidence": 0.7, "rationale": "Solid."') == {
            "score": 8,
            "confidence": 0.7,
            "rationale": "Solid.",
        }

    def test_recovers_a_response_cut_off_mid_string(self):
        parsed = _parse_json('{"score": 6, "rationale": "Shipped to produc')
        assert parsed["score"] == 6
        assert parsed["rationale"].startswith("Shipped to produc")

    def test_recovers_nested_structures(self):
        parsed = _parse_json('{"a": {"b": [1, 2, {"c": "d"')
        assert parsed == {"a": {"b": [1, 2, {"c": "d"}]}}

    def test_recovers_arrays(self):
        assert _parse_json('[{"a": 1}, {"a": 2', expect="array") == [{"a": 1}, {"a": 2}]

    def test_does_not_trip_on_a_brace_inside_a_string(self):
        """rfind finds the brace inside the string first. The repair path
        has to notice the real structure is still open.
        """
        assert _parse_json('{"rationale": "he wrote } on the board"') == {
            "rationale": "he wrote } on the board"
        }

    def test_escaped_quote_does_not_end_the_string_early(self):
        parsed = _parse_json(r'{"rationale": "they said \"shipped\" repeatedly')
        assert parsed["rationale"] == 'they said "shipped" repeatedly'

    def test_dangling_escape_is_dropped(self):
        parsed = _parse_json(r'{"rationale": "ends mid escape \\')
        assert parsed["rationale"].startswith("ends mid escape")

    def test_mismatched_brackets_are_not_forced_to_parse(self):
        """Repair is for unfinished output, not for wrong output."""
        assert _parse_json('{"a": [1, 2}') is None

    def test_well_formed_json_is_untouched(self):
        assert _parse_json('{"score": 7, "rationale": "fine"}') == {
            "score": 7,
            "rationale": "fine",
        }

    def test_raw_newline_inside_a_string_is_tolerated(self):
        """Models put literal newlines in long rationales. Rejecting the
        whole response over one throws away a usable score.
        """
        parsed = _parse_json('{"score": 7, "rationale": "line one\nline two"}')
        assert parsed["score"] == 7
        assert "line two" in parsed["rationale"]

    def test_raw_newline_in_an_unterminated_string(self):
        parsed = _parse_json('{"score": 7, "rationale": "line one\nline two')
        assert parsed["score"] == 7

    @pytest.mark.parametrize("tail", [r"\u", r"\u0", r"\u00", r"\u201"])
    def test_partial_unicode_escape_at_the_cut_is_dropped(self, tail):
        parsed = _parse_json('{"score": 5, "rationale": "cut mid escape ' + tail)
        assert parsed["score"] == 5
        assert parsed["rationale"].startswith("cut mid escape")

    def test_complete_unicode_escape_survives(self):
        parsed = _parse_json(r'{"rationale": "café shipped')
        assert parsed["rationale"] == "café shipped"


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

    async def test_generated_rubric_keeps_one_shared_prefix(self):
        """The whole point of resolving the rubric once per batch. If a
        generated rubric ever leaked per-resume variation into the prefix,
        every panel call would pay a cache write instead of a read.
        """
        rubric = parse_rubric(json.loads(rubric_json()))
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models, rubric)

        systems = {c["system"] for c in models["panel"].calls}
        assert len(systems) == 1
        assert rubric.markdown in systems.pop()


class TestGeneratedRubricDrivesThePanel:
    """A generated rubric has to actually replace the hardcoded one --
    not merely be accepted and ignored.
    """

    async def test_panel_agents_are_named_by_the_generated_dimensions(self):
        rubric = parse_rubric(json.loads(rubric_json(["shipping", "depth", "comms"])))
        models = _models([7.0, 7.0, 7.0])
        verdict = await screen_one(FIXTURE, JD, models, rubric)

        assert {p.agent_name for p in verdict.panel_scores} == {"shipping", "depth", "comms"}

    async def test_static_personas_are_not_used_when_a_rubric_is_given(self):
        rubric = parse_rubric(json.loads(rubric_json(["shipping", "depth", "comms"])))
        models = _models([7.0, 7.0, 7.0])
        await screen_one(FIXTURE, JD, models, rubric)

        sent = " ".join(c["user"] for c in models["panel"].calls)
        assert "You judge shipping only" in sent
        assert "Be skeptical of buzzwords" not in sent, "hand-written persona leaked in"

    async def test_hand_written_rubric_still_used_when_none_given(self):
        """scripts/evaluate.py depends on this: the published metrics were
        measured against the hand-written rubric, so the default path must
        not quietly start generating one.
        """
        models = _models([7.0, 7.0, 7.0])
        verdict = await screen_one(FIXTURE, JD, models)

        assert {p.agent_name for p in verdict.panel_scores} == {
            "production_reality",
            "technical_integration",
            "client_communication",
        }

    async def test_arbiter_sees_the_generated_rubric_too(self):
        rubric = parse_rubric(json.loads(rubric_json(["shipping", "depth", "comms"])))
        models = _models([9.0, 4.0, 3.5], arbiter=arbiter_json(5.0, "hold"))
        await screen_one(FIXTURE, JD, models, rubric)

        assert rubric.markdown in models["arbiter"].calls[0]["system"]

    async def test_rank_all_reuses_one_rubric_across_the_batch(self, tmp_path):
        for i in range(4):
            (tmp_path / f"cand_{i}.md").write_text("Engineer who shipped things.")

        rubric = parse_rubric(json.loads(rubric_json()))
        models = _models([7.0, 7.0, 7.0])
        await rank_all(str(tmp_path), JD, models, rubric=rubric)

        systems = {c["system"] for c in models["panel"].calls}
        assert len(systems) == 1, "one prefix for the whole batch, not one per resume"
        assert len(models["panel"].calls) == 12  # 4 resumes x 3 agents


class TestRubricFor:
    async def test_uses_the_rubric_model_slot(self):
        models = _models([7.0, 7.0, 7.0])
        models["rubric"] = FakeModel([rubric_json()])

        rubric = await rubric_for(JD, models)

        assert rubric.role_title == "AI Solutions Engineer"
        assert len(models["rubric"].calls) == 1
        assert models["panel"].calls == [], "writing a rubric must not score anyone"



class TestScoreShapedLikeSomethingElse:
    """Regression: observed live on 2026-08-25.

    Asked to score one dimension, the panel model sometimes answers for
    ALL of them at once, keyed by dimension name. That is valid JSON with
    no top-level "score". Reading it as 0.0 would reject a candidate on a
    number no agent ever assigned -- and because the parse "succeeded",
    the verdict would not be flagged for review. Silent and wrong is the
    worst combination available, so this must surface as a parse failure.
    """

    ALL_DIMENSIONS_AT_ONCE = json.dumps(
        {
            "Production Reality": {"score": 1, "confidence": 0.85, "rationale": "x"},
            "Integration Depth": {"score": 0, "confidence": 0.85, "rationale": "y"},
            "Client Communication": {"score": 0, "confidence": 0.9, "rationale": "z"},
        }
    )

    async def test_per_dimension_answer_is_flagged_not_scored_as_zero(self):
        models = {
            "triage": FakeModel([EXTRACTION_JSON]),
            "panel": FakeModel([self.ALL_DIMENSIONS_AT_ONCE]),
            "arbiter": FakeModel([arbiter_json(5.0)]),
        }
        verdict = await screen_one(FIXTURE, JD, models)

        assert all(p.parse_failed for p in verdict.panel_scores)
        assert verdict.review_reason is not None
        assert "unreadable" in verdict.review_reason

    @pytest.mark.parametrize(
        "payload",
        [
            '{"confidence": 0.9, "rationale": "no score key at all"}',
            '{"score": null, "confidence": 0.9}',
            '{"score": "not a number"}',
            '{"score": true}',
        ],
    )
    async def test_unusable_score_values_are_parse_failures(self, payload):
        models = {
            "triage": FakeModel([EXTRACTION_JSON]),
            "panel": FakeModel([payload]),
            "arbiter": FakeModel([arbiter_json(5.0)]),
        }
        verdict = await screen_one(FIXTURE, JD, models)
        assert all(p.parse_failed for p in verdict.panel_scores)

    async def test_a_genuine_zero_is_not_a_parse_failure(self):
        """The other half of the contract: 0.0 is a legitimate score, and
        must stay distinguishable from a missing one.
        """
        models = _models([0.0, 0.0, 0.0])
        verdict = await screen_one(FIXTURE, JD, models)

        assert not any(p.parse_failed for p in verdict.panel_scores)
        assert verdict.score == 0.0
        assert verdict.review_reason is None


class TestGeneratedRubricPromptShape:
    """The generated rubric shares one cached prefix across three agents,
    so it cannot name which dimension the reader owns. It must therefore
    tell them to score exactly one -- the ambiguity here is what produced
    the bug above.
    """

    def test_markdown_asks_for_one_dimension_not_all_of_them(self):
        rubric = parse_rubric(json.loads(rubric_json()))
        md = rubric.markdown

        assert "assigned exactly ONE" in md
        assert "Do not return one entry per dimension" in md
        assert "Score the candidate 0-10 on each" not in md


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


class TestEscalationGuard:
    """Spread measures variance; the guard measures decision uncertainty.

    A panel of 9/7/6 has spread 3.0 and clears the threshold, but every one
    of those scores means "advance" -- no arbiter ruling changes the answer,
    so the call is pure cost. 7 of 33 escalations in the recorded run were
    this case.
    """

    async def test_wide_spread_but_unanimous_verdict_does_not_escalate(self):
        # 2.5 spread, clears DISAGREEMENT_THRESHOLD, but 9.0/8.0/7.0 are all
        # >= ADVANCE_CUTOFF so no ruling could change the answer.
        models = _models([9.5, 8.0, 7.0])
        verdict = await screen_one(FIXTURE, JD, models)

        assert not verdict.escalated
        assert models["arbiter"].calls == [], "paid to resolve a settled verdict"
        assert verdict.recommendation == Recommendation.ADVANCE

    async def test_guard_depends_on_where_the_cutoffs_sit(self):
        """9.0/7.0/6.0 -- the case that motivated this -- still escalates at
        the current 7.0/5.0 cutoffs, because 6.0 falls in `hold`. The guard
        removes 7 of 33 escalations on the recorded run; the rest need the
        cutoff correction in PLAN.md 3e. Pinned so the limit is not
        mistaken for a fix.
        """
        models = _models([9.0, 7.0, 6.0], arbiter=arbiter_json(7.5, "advance"))
        verdict = await screen_one(FIXTURE, JD, models)
        assert verdict.escalated

    async def test_wide_spread_across_buckets_still_escalates(self):
        models = _models([9.0, 4.0, 3.5], arbiter=arbiter_json(5.0, "hold"))
        verdict = await screen_one(FIXTURE, JD, models)

        assert verdict.escalated
        assert len(models["arbiter"].calls) == 1

    async def test_narrow_spread_never_escalates(self):
        models = _models([7.0, 7.5, 7.2])
        verdict = await screen_one(FIXTURE, JD, models)
        assert not verdict.escalated

    @pytest.mark.parametrize(
        "scores,expect_escalation",
        [
            ([9.0, 8.0, 7.0], False),   # all advance
            ([4.0, 3.0, 2.0], False),   # all reject
            ([6.5, 6.0, 5.5], False),   # all hold
            ([7.5, 6.5, 4.0], True),    # advance / hold / reject
            ([8.0, 4.5, 4.0], True),    # advance vs reject
        ],
    )
    async def test_escalates_only_when_buckets_differ(self, scores, expect_escalation):
        models = _models(scores, arbiter=arbiter_json(6.0, "hold"))
        verdict = await screen_one(FIXTURE, JD, models)
        assert verdict.escalated is expect_escalation


class TestPerModelUsage:
    """Cost was priced at whichever model ran first -- Haiku, always, since
    extraction leads the cascade. Every Sonnet and Opus token was billed at
    Haiku rates, understating a real run several-fold.
    """

    def test_single_call_records_its_own_model(self):
        usage = Usage(input_tokens=100, output_tokens=20, model_id="claude-opus-5")
        assert usage.by_model == {
            "claude-opus-5": {
                "input_tokens": 100,
                "output_tokens": 20,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            }
        }

    def test_addition_keeps_models_apart(self):
        haiku = Usage(input_tokens=100, output_tokens=10, model_id="claude-haiku-4-5-20251001")
        opus = Usage(input_tokens=50, output_tokens=800, model_id="claude-opus-5")
        total = haiku + opus

        assert set(total.by_model) == {"claude-haiku-4-5-20251001", "claude-opus-5"}
        assert total.by_model["claude-opus-5"]["output_tokens"] == 800
        assert total.by_model["claude-haiku-4-5-20251001"]["output_tokens"] == 10

    def test_same_model_twice_accumulates(self):
        one = Usage(input_tokens=10, output_tokens=5, model_id="claude-sonnet-5")
        total = one + one
        assert total.by_model["claude-sonnet-5"]["input_tokens"] == 20

    def test_scalar_totals_still_agree_with_the_split(self):
        total = (
            Usage(input_tokens=100, output_tokens=10, model_id="a")
            + Usage(input_tokens=50, output_tokens=800, model_id="b")
        )
        assert total.input_tokens == sum(m["input_tokens"] for m in total.by_model.values())
        assert total.output_tokens == sum(m["output_tokens"] for m in total.by_model.values())

    async def test_a_verdict_carries_every_tier_it_used(self):
        models = _models([9.0, 4.0, 3.5], arbiter=arbiter_json(5.0, "hold"))
        for name, tier in (("triage", "t"), ("panel", "p"), ("arbiter", "a")):
            models[name]._model_id = tier
        verdict = await screen_one(FIXTURE, JD, models)

        assert set(verdict.usage.by_model) == {"t", "p", "a"}
