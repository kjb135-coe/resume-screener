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
        assert "Rubric preview" in response.text

    def test_health(self, client):
        assert client.get("/health").json() == {"ok": True}


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
