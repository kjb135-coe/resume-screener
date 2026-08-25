"""query_candidates: the structured primitive, the judgment primitive, and
the safety rails around generated SQL.
"""

from __future__ import annotations

import json

import pytest

from resume_screener.core.models import (
    Evidence,
    ExtractedCandidate,
    Recommendation,
    RubricScore,
    Verdict,
)
from resume_screener.core.query import _run_structured_query, _sql_is_safe, answer_query
from tests.fakes import FakeModel


def _verdict(name: str, score: float, years: float, techs: list[str]) -> Verdict:
    return Verdict(
        candidate=ExtractedCandidate(
            source_path=f"/tmp/{name}.md",
            name=name,
            years_experience=years,
            companies=["Acme"],
            technologies=techs,
            education=["BS CS"],
            evidence=[Evidence(quote=f"{name} built an MCP server.", rubric_dimension="depth")],
            confidence=0.9,
            raw_text="...",
        ),
        score=score,
        recommendation=Recommendation.ADVANCE if score >= 7 else Recommendation.REJECT,
        rationale="...",
        panel_scores=[RubricScore(agent_name="depth", score=score, rationale="ok")],
        escalated=False,
    )


@pytest.fixture
def pool():
    return [
        _verdict("Alice", 9.0, 8, ["Python", "MCP"]),
        _verdict("Bob", 6.0, 3, ["Java"]),
        _verdict("Carol", 8.0, 6, ["Python", "MCP", "AWS"]),
    ]


class TestSqlSafety:
    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE candidates",
            "DELETE FROM candidates",
            "INSERT INTO candidates VALUES ('x',1,'y',1,'','','',false)",
            "SELECT name FROM candidates; DROP TABLE candidates",
            "COPY (SELECT 1) TO 'out.txt'",
            "ATTACH 'other.db'",
        ],
    )
    def test_rejects_non_select(self, sql):
        assert not _sql_is_safe(sql)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT name FROM candidates WHERE score > 7",
            "select COUNT(*) from candidates",
            "WITH t AS (SELECT * FROM candidates) SELECT name FROM t",
            "SELECT name FROM candidates WHERE technologies ILIKE '%MCP%';",
        ],
    )
    def test_allows_plain_selects(self, sql):
        assert _sql_is_safe(sql)

    def test_file_access_is_blocked_at_the_engine(self, pool, tmp_path):
        """enable_external_access=false is what actually stops a file escape --
        the keyword guard alone would not catch every spelling.
        """
        secret = tmp_path / "secret.txt"
        secret.write_text("sensitive")
        sql = f"SELECT * FROM read_csv('{secret.as_posix()}', header=false)"

        filtered, aggregate = _run_structured_query(pool, sql)

        # Query fails inside DuckDB; we fall back to the unfiltered pool
        # rather than leaking anything or crashing.
        assert filtered == pool
        assert aggregate is None


class TestStructuredQuery:
    def test_filters_by_name_column(self, pool):
        filtered, aggregate = _run_structured_query(
            pool, "SELECT name FROM candidates WHERE technologies ILIKE '%MCP%'"
        )
        assert aggregate is None
        assert {v.candidate.name for v in filtered} == {"Alice", "Carol"}

    def test_aggregate_returns_rows_not_an_empty_filter(self, pool):
        """Regression: assuming column 0 is a name made every counting
        question silently filter the pool down to nothing.
        """
        filtered, aggregate = _run_structured_query(
            pool, "SELECT COUNT(*) AS total FROM candidates WHERE score > 7"
        )
        assert filtered is None
        assert aggregate == [{"total": 2}]

    def test_finds_name_column_regardless_of_position(self, pool):
        filtered, _ = _run_structured_query(
            pool, "SELECT score, name FROM candidates WHERE years_experience >= 6"
        )
        assert {v.candidate.name for v in filtered} == {"Alice", "Carol"}

    def test_invalid_sql_falls_back_to_full_pool(self, pool):
        filtered, aggregate = _run_structured_query(pool, "SELECT nonexistent FROM candidates")
        assert filtered == pool
        assert aggregate is None


class TestAnswerQuery:
    async def test_objective_question_uses_sql_only(self, pool):
        planner = FakeModel(
            [json.dumps({
                "needs_sql": True,
                "sql": "SELECT name FROM candidates WHERE score >= 8",
                "needs_judgment": False,
                "criterion": None,
            })]
        )
        judge = FakeModel(["[]"])
        result = await answer_query(pool, "who scored 8+?", {"planner": planner, "judge": judge})

        assert judge.calls == [], "no model judgment needed for an objective filter"
        assert {m["name"] for m in result["matches"]} == {"Alice", "Carol"}

    async def test_count_question_returns_an_answer(self, pool):
        planner = FakeModel(
            [json.dumps({
                "needs_sql": True,
                "sql": "SELECT COUNT(*) AS n FROM candidates",
                "needs_judgment": False,
                "criterion": None,
            })]
        )
        result = await answer_query(
            pool, "how many candidates?", {"planner": planner, "judge": FakeModel(["[]"])}
        )
        assert result["answer"] == [{"n": 3}]

    async def test_combined_filter_then_judge(self, pool):
        planner = FakeModel(
            [json.dumps({
                "needs_sql": True,
                "sql": "SELECT name FROM candidates WHERE technologies ILIKE '%MCP%'",
                "needs_judgment": True,
                "criterion": "actually built with MCP",
            })]
        )
        judge = FakeModel(
            [json.dumps([
                {"name": "Alice", "matches": True, "justification": "Built a server."},
                {"name": "Carol", "matches": False, "justification": "Only listed it."},
            ])]
        )
        result = await answer_query(pool, "who really used MCP?", {"planner": planner, "judge": judge})

        assert [m["name"] for m in result["matches"]] == ["Alice"]
        assert "Carol" in result["justifications"]
        assert len(judge.calls) == 1

    async def test_judge_only_sees_candidates_that_survived_sql(self, pool):
        planner = FakeModel(
            [json.dumps({
                "needs_sql": True,
                "sql": "SELECT name FROM candidates WHERE name = 'Alice'",
                "needs_judgment": True,
                "criterion": "built with MCP",
            })]
        )
        judge = FakeModel([json.dumps([{"name": "Alice", "matches": True, "justification": "yes"}])])
        await answer_query(pool, "...", {"planner": planner, "judge": judge})

        assert "Bob" not in judge.calls[0]["user"]
        assert "Alice" in judge.calls[0]["user"]

    async def test_unparseable_plan_returns_error_not_crash(self, pool):
        planner = FakeModel(["I don't understand"])
        result = await answer_query(pool, "???", {"planner": planner, "judge": FakeModel(["[]"])})
        assert "error" in result

    async def test_usage_is_reported(self, pool):
        planner = FakeModel(
            [json.dumps({"needs_sql": False, "sql": None, "needs_judgment": False, "criterion": None})]
        )
        result = await answer_query(pool, "show all", {"planner": planner, "judge": FakeModel(["[]"])})
        assert result["usage"]["input_tokens"] == 100
