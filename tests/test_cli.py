"""The terminal adapter.

pyproject.toml advertises a `resume-screener` console script. For a while
it pointed at a module that did not exist, so installing the package and
running the documented command raised ImportError. These tests exist so
that cannot happen again quietly.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from resume_screener.adapters import cli
from resume_screener.core.models import (
    Evidence,
    ExtractedCandidate,
    Recommendation,
    RubricScore,
    Verdict,
)
from resume_screener.core.rubric_gen import RubricGenerationError, parse_rubric
from tests.fakes import rubric_json

runner = CliRunner()


@pytest.fixture
def jd(tmp_path):
    path = tmp_path / "posting.md"
    path.write_text("We want an AI solutions engineer who ships to production.")
    return path


@pytest.fixture
def resume(tmp_path):
    path = tmp_path / "candidate.md"
    path.write_text("# Jane Doe\nShipped an agentic system to production.")
    return path


def _verdict(name: str = "Jane Doe", score: float = 8.0) -> Verdict:
    return Verdict(
        candidate=ExtractedCandidate(
            source_path=f"/tmp/{name}.md",
            name=name,
            years_experience=7,
            companies=["Acme"],
            technologies=["Python"],
            education=[],
            evidence=[Evidence(quote="Shipped it.", rubric_dimension="production_reality")],
            confidence=0.9,
            raw_text="...",
        ),
        score=score,
        recommendation=Recommendation.ADVANCE,
        rationale="Strong production evidence.",
        panel_scores=[
            RubricScore(agent_name="production_reality", score=score, rationale="ok")
        ],
        escalated=False,
    )


class TestConsoleScript:
    def test_entry_point_target_is_importable(self):
        """pyproject points at resume_screener.adapters.cli:app."""
        assert cli.app is not None

    def test_help_lists_every_command(self):
        result = runner.invoke(cli.app, ["--help"])
        assert result.exit_code == 0
        for command in ("rubric", "screen", "rank"):
            assert command in result.stdout


class TestRubricCommand:
    def test_prints_the_rubric(self, jd, monkeypatch):
        async def fake(job_description):
            return parse_rubric(json.loads(rubric_json()))

        monkeypatch.setattr(cli, "rubric_for", fake)
        result = runner.invoke(cli.app, ["rubric", str(jd)])

        assert result.exit_code == 0
        assert "AI Solutions Engineer" in result.stdout
        assert "production_reality" in result.stdout

    def test_json_flag_emits_parseable_json(self, jd, monkeypatch):
        async def fake(job_description):
            return parse_rubric(json.loads(rubric_json()))

        monkeypatch.setattr(cli, "rubric_for", fake)
        result = runner.invoke(cli.app, ["rubric", str(jd), "--json"])

        payload = json.loads(result.stdout)
        assert len(payload["dimensions"]) == 3

    def test_generation_failure_exits_nonzero(self, jd, monkeypatch):
        async def fake(job_description):
            raise RubricGenerationError("Rubric must have exactly 3 dimensions, got 5.")

        monkeypatch.setattr(cli, "rubric_for", fake)
        result = runner.invoke(cli.app, ["rubric", str(jd)])

        assert result.exit_code == 1

    def test_missing_key_exits_nonzero_rather_than_tracebacks(self, jd, monkeypatch):
        async def fake(job_description):
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")

        monkeypatch.setattr(cli, "rubric_for", fake)
        result = runner.invoke(cli.app, ["rubric", str(jd)])

        assert result.exit_code == 1
        assert not isinstance(result.exception, RuntimeError)


class TestScreenCommand:
    def test_prints_score_and_recommendation(self, resume, jd, monkeypatch):
        async def fake(path, job_description, rubric=None):
            return _verdict()

        monkeypatch.setattr(cli, "screen_one", fake)
        result = runner.invoke(cli.app, ["screen", str(resume), str(jd)])

        assert result.exit_code == 0
        assert "Jane Doe" in result.stdout
        assert "ADVANCE" in result.stdout

    def test_default_uses_the_hand_written_rubric(self, resume, jd, monkeypatch):
        """No -g means rubric=None, which is the reproducible default that
        scripts/evaluate.py also uses.
        """
        seen = {}

        async def fake(path, job_description, rubric=None):
            seen["rubric"] = rubric
            return _verdict()

        monkeypatch.setattr(cli, "screen_one", fake)
        runner.invoke(cli.app, ["screen", str(resume), str(jd)])

        assert seen["rubric"] is None

    def test_generate_flag_passes_a_rubric_through(self, resume, jd, monkeypatch):
        seen = {}

        async def fake_rubric(job_description):
            return parse_rubric(json.loads(rubric_json()))

        async def fake_screen(path, job_description, rubric=None):
            seen["rubric"] = rubric
            return _verdict()

        monkeypatch.setattr(cli, "rubric_for", fake_rubric)
        monkeypatch.setattr(cli, "screen_one", fake_screen)
        runner.invoke(cli.app, ["screen", str(resume), str(jd), "-g"])

        assert seen["rubric"] is not None
        assert seen["rubric"].role_title == "AI Solutions Engineer"

    def test_missing_resume_is_rejected_before_any_api_call(self, jd):
        result = runner.invoke(cli.app, ["screen", "/nope/missing.md", str(jd)])
        assert result.exit_code != 0


class TestRankCommand:
    def test_lists_top_n_and_reports_the_full_count(self, tmp_path, jd, monkeypatch):
        async def fake(resume_dir, job_description, rubric=None):
            return [_verdict(f"Cand {i}", 9.0 - i) for i in range(5)]

        monkeypatch.setattr(cli, "rank_all", fake)
        result = runner.invoke(cli.app, ["rank", str(tmp_path), str(jd), "--top", "2"])

        assert result.exit_code == 0
        assert "Cand 0" in result.stdout
        assert "Cand 4" not in result.stdout
        assert "5 screened" in result.stdout

    def test_warns_that_results_are_advisory(self, tmp_path, jd, monkeypatch):
        """Nothing here is a hiring decision, and the output has to say so."""

        async def fake(resume_dir, job_description, rubric=None):
            return [_verdict()]

        monkeypatch.setattr(cli, "rank_all", fake)
        result = runner.invoke(cli.app, ["rank", str(tmp_path), str(jd)])

        assert "Advisory only" in result.stdout

    def test_empty_directory_exits_nonzero(self, tmp_path, jd, monkeypatch):
        async def fake(resume_dir, job_description, rubric=None):
            return []

        monkeypatch.setattr(cli, "rank_all", fake)
        result = runner.invoke(cli.app, ["rank", str(tmp_path), str(jd)])

        assert result.exit_code == 1
