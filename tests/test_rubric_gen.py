"""Rubric generation, exercised offline against FakeModel.

The rubric decides what every later score means, so the validation here
is deliberately strict: a malformed or wrong-shaped rubric must fail
loudly rather than quietly scoring candidates against something nobody
reviewed.
"""

from __future__ import annotations

import json

import pytest

from resume_screener.core.rubric_gen import (
    REQUIRED_DIMENSIONS,
    GeneratedRubric,
    RubricGenerationError,
    generate_rubric,
    parse_rubric,
)
from tests.fakes import FakeModel, rubric_json

JD = "We want an AI solutions engineer who ships agentic systems to production."


class TestParseRubric:
    def test_builds_dimensions_and_personas(self):
        rubric = parse_rubric(json.loads(rubric_json()))

        assert rubric.role_title == "AI Solutions Engineer"
        assert len(rubric.dimensions) == REQUIRED_DIMENSIONS
        assert set(rubric.personas) == {
            "production_reality",
            "technical_integration",
            "client_communication",
        }

    def test_personas_keys_match_dimension_names(self):
        """The panel is built from personas but reported under dimension
        names. If those two ever diverge, an agent scores one dimension and
        gets filed under another.
        """
        rubric = parse_rubric(json.loads(rubric_json()))
        assert set(rubric.personas) == {d.name for d in rubric.dimensions}

    def test_rejects_non_object(self):
        with pytest.raises(RubricGenerationError, match="not a JSON object"):
            parse_rubric([1, 2, 3])

    def test_rejects_missing_role_title(self):
        data = json.loads(rubric_json())
        del data["role_title"]
        with pytest.raises(RubricGenerationError, match="role_title"):
            parse_rubric(data)

    def test_rejects_blank_summary(self):
        data = json.loads(rubric_json())
        data["summary"] = "   "
        with pytest.raises(RubricGenerationError, match="summary"):
            parse_rubric(data)

    @pytest.mark.parametrize("count", [1, 2, 4, 5])
    def test_rejects_wrong_dimension_count(self, count):
        """Three is load-bearing: DISAGREEMENT_THRESHOLD is a spread across
        a three-agent panel, so a different count silently changes what
        escalation means.
        """
        data = json.loads(rubric_json())
        base = data["dimensions"][0]
        data["dimensions"] = [{**base, "name": f"dim_{i}"} for i in range(count)]
        with pytest.raises(RubricGenerationError, match="exactly 3 dimensions"):
            parse_rubric(data)

    def test_rejects_duplicate_dimension_names(self):
        data = json.loads(rubric_json())
        data["dimensions"][1]["name"] = data["dimensions"][0]["name"]
        with pytest.raises(RubricGenerationError, match="duplicate"):
            parse_rubric(data)

    @pytest.mark.parametrize("bad", ["Production Reality", "9lives", "has-dash", "has space"])
    def test_rejects_non_identifier_names(self, bad):
        data = json.loads(rubric_json())
        data["dimensions"][0]["name"] = bad
        with pytest.raises(RubricGenerationError, match="snake_case"):
            parse_rubric(data)

    def test_rejects_dimension_missing_lens(self):
        data = json.loads(rubric_json())
        del data["dimensions"][2]["lens"]
        with pytest.raises(RubricGenerationError, match="lens"):
            parse_rubric(data)


class TestMarkdown:
    def test_contains_every_dimension(self):
        rubric = parse_rubric(json.loads(rubric_json()))
        md = rubric.markdown
        for dim in rubric.dimensions:
            assert dim.title in md
            assert dim.criteria in md

    def test_carries_the_evidence_rule(self):
        """Every generated rubric inherits the no-unbacked-claims rule --
        it is not left to the generating model to remember it.
        """
        rubric = parse_rubric(json.loads(rubric_json()))
        assert "direct quote" in rubric.markdown

    def test_does_not_leak_agent_briefs_into_the_shared_prefix(self):
        """The lens is one agent's private brief and travels in the user
        turn. In the shared prefix it would tell all three agents how the
        other two are being told to think.
        """
        rubric = parse_rubric(json.loads(rubric_json()))
        for dim in rubric.dimensions:
            assert dim.lens not in rubric.markdown

    def test_to_dict_round_trips_through_parse(self):
        rubric = parse_rubric(json.loads(rubric_json()))
        assert parse_rubric(rubric.to_dict()) == GeneratedRubric(
            role_title=rubric.role_title,
            summary=rubric.summary,
            dimensions=rubric.dimensions,
        )


class TestGenerateRubric:
    async def test_generates_from_a_posting(self):
        model = FakeModel([rubric_json()])
        rubric = await generate_rubric(JD, model)

        assert rubric.role_title == "AI Solutions Engineer"
        assert len(model.calls) == 1
        assert JD in model.calls[0]["user"]

    async def test_posting_travels_in_the_user_turn(self):
        """The meta-prompt is the constant; the posting is the variable.
        Putting the posting in the system block would make the cacheable
        half differ on every call.
        """
        model = FakeModel([rubric_json()])
        await generate_rubric(JD, model)

        assert JD not in model.calls[0]["system"]
        assert "Output contract" in model.calls[0]["system"]

    async def test_does_not_pay_for_a_cache_write(self):
        """One call per batch with a different posting each time. A cache
        write here costs 1.25x base and is never read back.
        """
        model = FakeModel([rubric_json()])
        await generate_rubric(JD, model)
        assert model.calls[0]["cache_system"] is False

    async def test_usage_is_carried_on_the_rubric(self):
        model = FakeModel([rubric_json()])
        rubric = await generate_rubric(JD, model)
        assert rubric.usage.input_tokens == 100

    async def test_extracts_json_from_surrounding_prose(self):
        model = FakeModel([f"Here you go:\n{rubric_json()}\nHope that helps!"])
        rubric = await generate_rubric(JD, model)
        assert rubric.role_title == "AI Solutions Engineer"

    async def test_empty_posting_raises_before_spending_a_call(self):
        model = FakeModel([rubric_json()])
        with pytest.raises(RubricGenerationError, match="empty"):
            await generate_rubric("   ", model)
        assert model.calls == [], "must not call the model on empty input"

    async def test_unparseable_response_raises_rather_than_falling_back(self):
        """There is no safe default. Falling back to the hand-written rubric
        would score this posting's candidates against a different job.
        """
        model = FakeModel(["I'm sorry, I can't help with that."])
        with pytest.raises(RubricGenerationError, match="No JSON object"):
            await generate_rubric(JD, model)

    async def test_malformed_json_raises(self):
        model = FakeModel(['{"role_title": "X", "dimensions": [}'])
        with pytest.raises(RubricGenerationError, match="Malformed JSON"):
            await generate_rubric(JD, model)
