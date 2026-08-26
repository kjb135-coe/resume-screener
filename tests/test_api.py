"""The web adapter: error surfaces and the one endpoint that matters.

Every failure here is something the person pasting a posting can act on
(no key, junk response, wrong shape), so each one has to arrive as
readable JSON rather than an opaque 500.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from resume_screener.adapters import api
from resume_screener.core.rubric_gen import RubricGenerationError, parse_rubric
from tests.fakes import rubric_json

JD = "We want an AI solutions engineer who ships agentic systems to production."


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


@pytest.fixture
def stub_rubric(monkeypatch):
    """Swap the model call out. The suite never reaches the network."""

    def _install(result):
        async def _fake(job_description: str):
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(api, "rubric_for", _fake)

    return _install


class TestPage:
    def test_index_serves_the_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Resume Screener" in response.text

    def test_health(self, client):
        assert client.get("/health").json() == {"ok": True}


class TestResults:
    """The recorded run is the landing view. It reads a file, so it must
    work with no API key and cost nothing.
    """

    def test_serves_every_candidate_with_a_verdict(self, client):
        body = client.get("/api/results").json()

        assert body["summary"]["n"] == len(body["candidates"]) == 60
        for candidate in body["candidates"]:
            assert candidate["recommendation"] in {"advance", "hold", "reject"}
            assert len(candidate["panel"]) == 3
            assert candidate["resume_text"], f"{candidate['file']} has no resume text"

    def test_sorted_best_first(self, client):
        scores = [c["score"] for c in client.get("/api/results").json()["candidates"]]
        assert scores == sorted(scores, reverse=True)

    def test_summary_counts_match_the_candidates(self, client):
        body = client.get("/api/results").json()
        summary, candidates = body["summary"], body["candidates"]

        for bucket in ("advance", "hold", "reject"):
            actual = sum(1 for c in candidates if c["recommendation"] == bucket)
            assert summary[bucket] == actual
        assert summary["needs_human_review"] == sum(
            1 for c in candidates if c["needs_human_review"]
        )

    def test_needs_review_always_carries_a_reason(self, client):
        """A flag with no explanation is not actionable for a reviewer."""
        for candidate in client.get("/api/results").json()["candidates"]:
            assert bool(candidate["needs_human_review"]) == bool(candidate["review_reason"])

    def test_escalated_candidates_are_flagged(self, client):
        for candidate in client.get("/api/results").json()["candidates"]:
            if candidate["escalated"]:
                assert candidate["needs_human_review"]

    def test_ground_truth_comparison_is_reported(self, client):
        body = client.get("/api/results").json()
        for candidate in body["candidates"]:
            assert candidate["matches_ground_truth"] == (
                candidate["expected"] == candidate["recommendation"]
            )

    def test_missing_run_returns_a_readable_error(self, client, monkeypatch, tmp_path):
        api.load_recorded_run.cache_clear()
        monkeypatch.setattr(api, "RUN_JSON", tmp_path / "absent.json")

        response = client.get("/api/results")
        api.load_recorded_run.cache_clear()

        assert response.status_code == 404
        assert "evaluate.py" in response.json()["error"]


class TestReviewReason:
    def test_unreadable_response_takes_priority_over_escalation(self):
        reason = api._review_reason(
            {"panel": [{"parse_failed": True}], "escalated": True, "panel_spread": 4.0}
        )
        assert "unreadable" in reason

    def test_escalation_reports_the_spread(self):
        reason = api._review_reason(
            {"panel": [{"parse_failed": False}], "escalated": True, "panel_spread": 4.0}
        )
        assert "4.0" in reason

    def test_clean_agreeing_panel_needs_no_review(self):
        assert api._review_reason(
            {"panel": [{"parse_failed": False}], "escalated": False, "panel_spread": 0.5}
        ) is None


class TestRubricEndpoint:
    def test_returns_the_generated_rubric(self, client, stub_rubric):
        stub_rubric(parse_rubric(json.loads(rubric_json())))

        response = client.post("/api/rubric", json={"job_description": JD})
        body = response.json()

        assert response.status_code == 200
        assert body["role_title"] == "AI Solutions Engineer"
        assert len(body["dimensions"]) == 3
        assert body["markdown"].startswith("# Scoring rubric")

    def test_empty_posting_is_rejected_by_validation(self, client):
        assert client.post("/api/rubric", json={"job_description": ""}).status_code == 422

    def test_oversized_posting_is_rejected(self, client):
        response = client.post("/api/rubric", json={"job_description": "x" * 40_001})
        assert response.status_code == 422

    def test_generation_failure_returns_a_readable_error(self, client, stub_rubric):
        stub_rubric(RubricGenerationError("Rubric must have exactly 3 dimensions, got 5."))

        response = client.post("/api/rubric", json={"job_description": JD})

        assert response.status_code == 422
        assert "exactly 3 dimensions" in response.json()["error"]

    def test_missing_api_key_is_reported_not_swallowed(self, client, stub_rubric):
        """default_models() raises RuntimeError when the key is unset. That
        is a setup problem with an obvious fix, so it must reach the page.
        """
        stub_rubric(RuntimeError("ANTHROPIC_API_KEY is not set."))

        response = client.post("/api/rubric", json={"job_description": JD})

        assert response.status_code == 503
        assert "ANTHROPIC_API_KEY" in response.json()["error"]

    def test_unexpected_failure_does_not_leak_internals(self, client, stub_rubric):
        stub_rubric(ValueError("connection reset by peer at 10.0.0.4:443"))

        response = client.post("/api/rubric", json={"job_description": JD})

        assert response.status_code == 500
        assert "10.0.0.4" not in response.json()["error"]
