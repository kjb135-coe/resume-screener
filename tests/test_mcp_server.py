"""The MCP adapter: tool registration and session handling.

These guard the contract the model actually sees -- tool names and their
descriptions are what a client uses to decide when to call something, so a
silent rename or a dropped tool is a real regression.
"""

from __future__ import annotations

import pytest

from resume_screener.adapters import mcp_server
from resume_screener.core.models import (
    Evidence,
    ExtractedCandidate,
    Recommendation,
    RubricScore,
    Verdict,
)

EXPECTED_TOOLS = {"screen_resume", "rank_pool", "explain_verdict", "query_candidates"}


def _verdict(name: str) -> Verdict:
    return Verdict(
        candidate=ExtractedCandidate(
            source_path=f"/tmp/{name}.md",
            name=name,
            years_experience=5,
            companies=["Acme"],
            technologies=["Python"],
            education=[],
            evidence=[Evidence(quote="Shipped a thing.", rubric_dimension="depth")],
            confidence=0.9,
            raw_text="...",
        ),
        score=8.0,
        recommendation=Recommendation.ADVANCE,
        rationale="Strong.",
        panel_scores=[RubricScore(agent_name="depth", score=8.0, rationale="ok")],
        escalated=False,
    )


@pytest.fixture(autouse=True)
def clean_sessions():
    mcp_server._sessions.clear()
    yield
    mcp_server._sessions.clear()


class TestToolRegistration:
    async def test_all_four_tools_registered(self):
        names = {t.name for t in await mcp_server.mcp.list_tools()}
        assert names == EXPECTED_TOOLS

    async def test_every_tool_has_a_description(self):
        """The description is the model's only basis for choosing a tool."""
        for tool in await mcp_server.mcp.list_tools():
            assert tool.description and len(tool.description.strip()) > 40

    async def test_no_tool_takes_a_generic_action_parameter(self):
        """One tool per action -- a dispatcher with an `action` string would
        push the routing decision into a magic value the model has to guess.
        """
        for tool in await mcp_server.mcp.list_tools():
            assert "action" not in tool.input_schema.get("properties", {})


class TestSessions:
    async def test_explain_verdict_without_session_returns_error(self):
        result = await mcp_server.explain_verdict("nonexistent", "Alice")
        assert "error" in result

    async def test_query_candidates_without_session_returns_error(self):
        result = await mcp_server.query_candidates("nonexistent", "who is best?")
        assert "error" in result

    async def test_explain_verdict_finds_candidate_case_insensitively(self):
        sid = mcp_server._store_session([_verdict("Jane Doe")])
        result = await mcp_server.explain_verdict(sid, "  jane doe  ")
        assert result["name"] == "Jane Doe"
        assert result["panel"][0]["agent"] == "depth"

    async def test_unknown_candidate_lists_known_names(self):
        sid = mcp_server._store_session([_verdict("Jane Doe")])
        result = await mcp_server.explain_verdict(sid, "Nobody")
        assert result["known_candidates"] == ["Jane Doe"]

    async def test_sessions_are_evicted_rather_than_growing_forever(self):
        for _ in range(mcp_server._MAX_SESSIONS + 5):
            mcp_server._store_session([_verdict("X")])
        assert len(mcp_server._sessions) <= mcp_server._MAX_SESSIONS
