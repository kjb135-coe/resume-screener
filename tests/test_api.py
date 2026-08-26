"""The web adapter: error surfaces and the one endpoint that matters.

Every failure here is something the person pasting a posting can act on
(no key, junk response, wrong shape), so each one has to arrive as
readable JSON rather than an opaque 500.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from resume_screener.adapters import api
from resume_screener.adapters.api import _split_sentences, bullets_from
from resume_screener.core.models import ExtractedCandidate, Recommendation, Verdict
from resume_screener.core.rubric_gen import RubricGenerationError, parse_rubric
from tests.fakes import rubric_json


def _fake_verdict(path: str) -> Verdict:
    """A Verdict for the uploaded file, without calling a model."""
    from resume_screener.core.models import RubricScore

    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    return Verdict(
        candidate=ExtractedCandidate(
            source_path=path, name="Alex Rivera", years_experience=6,
            companies=["Acme"], technologies=["Python"], education=[],
            evidence=[], confidence=0.9, raw_text=text,
        ),
        score=7.4,
        recommendation=Recommendation.ADVANCE,
        rationale="Strong production evidence.",
        panel_scores=[
            RubricScore(agent_name=n, score=s, confidence=0.8,
                        rationale='Evidence: "Shipped an agentic document pipeline to production".')
            for n, s in (("production_reality", 8.0), ("technical_integration", 7.5),
                         ("client_communication", 6.5))
        ],
        escalated=False,
    )


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


class TestDefaultJd:
    def test_prefill_carries_the_bundled_posting(self, client):
        body = client.get("/api/default-jd").json()
        assert "AI Solutions Engineer" in body["job_description"]
        assert body["default_count"] == api.DEFAULT_SAMPLE
        assert body["max_count"] == api.MAX_SAMPLE


class TestSampling:
    def test_sample_is_balanced_across_ground_truth_classes(self):
        """Taking the first N off disk would return twelve academic
        researchers, since the corpus is alphabetical by archetype. A
        viewer would watch a column of identical rejects.
        """
        labels = json.loads(api.LABELS_JSON.read_text())
        counts = Counter(labels[p.name]["label"] for p in api.sample_resumes(12))
        assert set(counts) == {"advance", "hold", "reject"}
        assert max(counts.values()) - min(counts.values()) <= 1

    def test_sample_is_deterministic(self):
        assert api.sample_resumes(9) == api.sample_resumes(9)

    def test_every_sampled_path_exists(self):
        assert all(p.exists() for p in api.sample_resumes(api.MAX_SAMPLE))


class TestFingerprint:
    def test_whitespace_differences_are_the_same_posting(self):
        """Otherwise someone gets re-billed for pasting the same JD twice."""
        assert api.jd_fingerprint("Senior Engineer\n  Ships things.  ") == api.jd_fingerprint(
            "Senior Engineer\nShips things."
        )

    def test_different_postings_differ(self):
        assert api.jd_fingerprint("Nurse") != api.jd_fingerprint("Engineer")


class TestScreenEndpoint:
    def test_bundled_posting_is_served_from_the_recorded_run(self, client):
        """The default demo path must not spend money. The bundled posting
        maps onto the run already on disk.
        """
        body = client.post(
            "/api/screen",
            json={"job_description": api.default_job_description(), "count": 12},
        ).json()

        assert body["status"] == "done"
        assert body["cached"] is True
        assert body["result"]["source"] == "recorded"
        assert len(body["result"]["candidates"]) == 60

    def test_repeat_posting_reuses_the_cached_run(self, client):
        """A second submission of the same posting must not re-bill."""
        posting = "Charge Nurse, night shift. ACLS required."
        fingerprint = api.jd_fingerprint(posting)
        api._run_cache[fingerprint] = {
            "source": "live",
            "candidates": [],
            "summary": {"n": 0},
        }
        try:
            body = client.post("/api/screen", json={"job_description": posting}).json()
            assert body["cached"] is True
            assert body["result"]["source"] == "live"
        finally:
            api._run_cache.pop(fingerprint, None)

    def test_whitespace_variant_still_hits_the_cache(self, client):
        posting = "Charge Nurse, night shift. ACLS required."
        fingerprint = api.jd_fingerprint(posting)
        api._run_cache[fingerprint] = {"source": "live", "candidates": [], "summary": {"n": 0}}
        try:
            body = client.post(
                "/api/screen", json={"job_description": f"  {posting}  \n\n"}
            ).json()
            assert body["cached"] is True
        finally:
            api._run_cache.pop(fingerprint, None)

    def test_count_is_capped(self, client):
        """A spending limit, not a technical one."""
        response = client.post(
            "/api/screen", json={"job_description": "Nurse wanted.", "count": 500}
        )
        assert response.status_code == 422

    def test_empty_posting_is_rejected(self, client):
        assert client.post("/api/screen", json={"job_description": ""}).status_code == 422

    def test_unknown_job_id_is_a_404(self, client):
        assert client.get("/api/screen/nope").status_code == 404

    def test_running_job_reports_progress(self, client):
        api._jobs["j1"] = {
            "status": "running", "stage": "screening",
            "progress": {"done": 5, "total": 12},
            "fingerprint": "x", "rubric": None, "result": None, "error": None,
        }
        try:
            body = client.get("/api/screen/j1").json()
            assert body["status"] == "running"
            assert body["progress"] == {"done": 5, "total": 12}
        finally:
            api._jobs.pop("j1", None)

    def test_failed_job_surfaces_its_error(self, client):
        api._jobs["j2"] = {
            "status": "error", "stage": "rubric", "progress": {},
            "fingerprint": "x", "rubric": None, "result": None,
            "error": "ANTHROPIC_API_KEY is not set.",
        }
        try:
            response = client.get("/api/screen/j2")
            assert response.status_code == 422
            assert "ANTHROPIC_API_KEY" in response.json()["error"]
        finally:
            api._jobs.pop("j2", None)


class TestGroundTruthOnlyAppliesToItsOwnPosting:
    """labels.json describes exactly one posting: the bundled AI Solutions
    Engineer role. Screening the same resumes against a payments or nursing
    posting produces correct verdicts the labels say nothing about, and
    grading those against the wrong answer key would publish a made-up
    accuracy number.
    """

    def _verdict(self):
        return Verdict(
            candidate=ExtractedCandidate(
                source_path=str(api.RESUME_DIR / "academic_researcher__devon_whitaker.md"),
                name="Devon Whitaker",
                years_experience=3,
                companies=[],
                technologies=[],
                education=[],
                evidence=[],
                confidence=0.9,
                raw_text="...",
            ),
            score=0.0,
            recommendation=Recommendation.REJECT,
            rationale="No relevant evidence.",
            panel_scores=[],
            escalated=False,
        )

    def test_graded_run_reports_ground_truth(self):
        labels = json.loads(api.LABELS_JSON.read_text())
        row = api._verdict_to_dict(self._verdict(), labels, graded=True)

        assert row["expected"] == "reject"
        assert row["matches_ground_truth"] is True

    def test_ungraded_run_withholds_ground_truth(self):
        labels = json.loads(api.LABELS_JSON.read_text())
        row = api._verdict_to_dict(self._verdict(), labels, graded=False)

        assert row["expected"] is None
        assert row["matches_ground_truth"] is None

    def test_archetype_still_shown_when_ungraded(self):
        """Archetype describes the resume itself, not the verdict, so it
        stays useful regardless of which posting was used.
        """
        labels = json.loads(api.LABELS_JSON.read_text())
        row = api._verdict_to_dict(self._verdict(), labels, graded=False)
        assert row["archetype"] == "academic_researcher"


RESUME = """# Jane Doe
Senior Engineer | jane@example.com

## Experience

**Staff Engineer** | Acme | 2023 - Present

- Architected and shipped a multi-agent workflow system for document
  processing; now handles 12K+ documents daily
- Presented quarterly metrics to non-technical stakeholders

## Education

- BS Computer Science, State University
"""


class TestSentenceSplitting:
    def test_does_not_split_inside_a_quotation(self):
        """Observed on real output: the model writes `..., e.g. "Architected
        and shipped..."` and a naive [.!?] split cuts the quote in half,
        leaving a bullet that opens mid-quotation.
        """
        text = 'Ownership is clear, e.g. "Shipped a system. It handles 12K docs." That is production.'
        assert _split_sentences(text) == [
            'Ownership is clear, e.g. "Shipped a system. It handles 12K docs."',
            "That is production.",
        ]

    @pytest.mark.parametrize("abbrev", ["e.g.", "i.e.", "etc.", "vs."])
    def test_does_not_split_on_abbreviations(self, abbrev):
        text = f"Evidence is thin, {abbrev} Nothing shipped."
        assert len(_split_sentences(text)) == 1

    def test_splits_ordinary_sentences(self):
        assert _split_sentences("First one. Second one. Third one.") == [
            "First one.",
            "Second one.",
            "Third one.",
        ]

    def test_handles_curly_quotes(self):
        text = 'They wrote “Shipped it. Ran it.” and stopped there. Next point.'
        assert len(_split_sentences(text)) == 2

    def test_empty_input(self):
        assert _split_sentences("") == []


class TestBullets:
    def test_at_most_two_bullets(self):
        rationale = "One. Two. Three. Four."
        assert len(bullets_from(rationale, RESUME)) == 2

    def test_quote_is_located_to_its_section(self):
        rationale = (
            'Strong production evidence: "Architected and shipped a multi-agent '
            'workflow system for document processing". Nothing else matters.'
        )
        bullets = bullets_from(rationale, RESUME)

        assert bullets[0]["citations"][0]["section"] == "Experience"

    def test_quote_matches_across_line_wrapping(self):
        """The quote spans a newline in the resume. A model quoting it
        reproduces the words, not the wrapping.
        """
        rationale = '"shipped a multi-agent workflow system for document processing" is clear.'
        bullets = bullets_from(rationale, RESUME)
        assert bullets[0]["citations"][0]["section"] == "Experience"

    def test_quote_not_in_the_resume_is_not_cited(self):
        """A quote that cannot be found is the model paraphrasing. Dressing
        that up as a citation would be worse than showing no citation.
        """
        rationale = '"Led a team of two hundred engineers on Mars" is impressive.'
        assert bullets_from(rationale, RESUME)[0]["citations"] == []

    def test_sentence_text_is_kept_verbatim(self):
        """Stripping quotes out to build a tidier claim turns a sentence
        with two citations into "… and … matching the posting".
        """
        rationale = 'Evidence: "Presented quarterly metrics to non-technical stakeholders".'
        assert "Presented quarterly metrics" in bullets_from(rationale, RESUME)[0]["text"]

    def test_elided_quote_still_locates(self):
        rationale = '"Architected and shipped a multi-agent... document processing" counts.'
        bullets = bullets_from(rationale, RESUME)
        assert bullets[0]["citations"][0]["section"] == "Experience"

    def test_education_section_is_distinguished(self):
        rationale = '"BS Computer Science, State University" is the only credential.'
        assert bullets_from(rationale, RESUME)[0]["citations"][0]["section"] == "Education"

    def test_empty_rationale_yields_nothing(self):
        assert bullets_from("", RESUME) == []

    def test_missing_resume_does_not_crash(self):
        bullets = bullets_from('Something about "a quoted claim here".', "")
        assert bullets and bullets[0]["citations"] == []


class TestBulletsOnTheRecordedRun:
    def test_every_panel_entry_gets_bullets(self, client):
        for candidate in client.get("/api/results").json()["candidates"]:
            for agent in candidate["panel"]:
                assert "bullets" in agent
                assert len(agent["bullets"]) <= 2

    def test_citations_resolve_to_real_sections(self, client):
        """Every cited section must be a heading that exists in that
        candidate's own resume, not a plausible-sounding label.
        """
        for candidate in client.get("/api/results").json()["candidates"]:
            headings = {h for h, _ in api._resume_sections(candidate["resume_text"])}
            for agent in candidate["panel"]:
                for bullet in agent["bullets"]:
                    for citation in bullet["citations"]:
                        assert citation["section"] in headings

    def test_cited_quotes_are_deduped_for_highlighting(self, client):
        for candidate in client.get("/api/results").json()["candidates"]:
            quotes = candidate["cited_quotes"]
            assert len(quotes) == len(set(quotes))

    def test_most_candidates_get_at_least_one_citation(self, client):
        """The whole point is showing the feedback is grounded in this
        resume. If citations rarely resolved, the feature would be theatre.
        """
        candidates = client.get("/api/results").json()["candidates"]
        with_citation = sum(1 for c in candidates if c["cited_quotes"])
        assert with_citation / len(candidates) > 0.75


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


class TestQuoteStyles:
    """Agents quote with whatever mark they feel like, sometimes different
    styles on the same candidate. Matching only double quotes silently
    dropped one agent's citations entirely.
    """

    @pytest.mark.parametrize(
        "quoted",
        [
            '"Architected and shipped a multi-agent workflow system"',
            "'Architected and shipped a multi-agent workflow system'",
            "“Architected and shipped a multi-agent workflow system”",
            "‘Architected and shipped a multi-agent workflow system’",
        ],
    )
    def test_every_quote_style_is_cited(self, quoted):
        bullets = bullets_from(f"Evidence: {quoted} is clear.", RESUME)
        assert bullets[0]["citations"], f"no citation extracted from {quoted[:3]}"
        assert bullets[0]["citations"][0]["section"] == "Experience"

    def test_apostrophes_do_not_produce_phantom_citations(self):
        """A false span is harmless because _locate refuses anything not
        verbatim in the resume -- this pins that safety net down.
        """
        rationale = "The candidate's evidence isn't strong and doesn't show ownership."
        assert bullets_from(rationale, RESUME)[0]["citations"] == []


class TestUpload:
    """Uploading a real resume. Everything except the model call is
    exercised here; the screening itself is stubbed so the suite stays
    offline and free.
    """

    RESUME_MD = (
        "# Alex Rivera\n\n## Experience\n\n"
        + "Shipped an agentic document pipeline to production serving real users. " * 12
    )

    @pytest.fixture
    def stub_screen(self, monkeypatch):
        async def _fake_rubric(job_description):
            return None

        async def _fake_screen(path, jd, models=None, rubric=None):
            return _fake_verdict(path)

        monkeypatch.setattr(api, "rubric_for_posting", _fake_rubric)
        monkeypatch.setattr(api, "screen_one", _fake_screen)

    def _post(self, client, name, content, jd="Engineer who ships to production."):
        return client.post(
            "/api/screen-upload",
            files={"file": (name, content)},
            data={"job_description": jd},
        )

    def test_markdown_upload_is_screened(self, client, stub_screen):
        response = self._post(client, "alex.md", self.RESUME_MD.encode())
        body = response.json()

        assert response.status_code == 200
        assert body["candidate"]["uploaded"] is True
        assert body["candidate"]["recommendation"] in {"advance", "hold", "reject"}
        assert "criteria" in body

    def test_uploaded_candidate_is_not_graded(self, client, stub_screen):
        """There is no ground-truth label for somebody's real resume, and
        inventing one would report a made-up accuracy.
        """
        body = self._post(client, "alex.md", self.RESUME_MD.encode()).json()
        assert body["candidate"]["expected"] is None
        assert body["candidate"]["matches_ground_truth"] is None

    def test_bullets_are_attached(self, client, stub_screen):
        body = self._post(client, "alex.md", self.RESUME_MD.encode()).json()
        for agent in body["candidate"]["panel"]:
            assert len(agent["bullets"]) <= 2

    @pytest.mark.parametrize("name", ["resume.exe", "resume.pages", "resume"])
    def test_unsupported_types_are_refused(self, client, stub_screen, name):
        response = self._post(client, name, b"whatever")
        assert response.status_code == 415
        assert "Accepted" in response.json()["error"]

    def test_empty_file_is_refused(self, client, stub_screen):
        assert self._post(client, "resume.md", b"").status_code == 400

    def test_oversized_file_is_refused(self, client, stub_screen):
        big = b"x" * (api.MAX_UPLOAD_BYTES + 1)
        response = self._post(client, "resume.md", big)
        assert response.status_code == 413
        assert "limit" in response.json()["error"]

    def test_near_empty_extraction_is_refused(self, client, stub_screen):
        """A scanned PDF extracts to almost nothing. Scoring that would
        produce a confident zero about a resume nobody could read.
        """
        response = self._post(client, "scan.pdf", b"%PDF-1.4 tiny")
        assert response.status_code == 422

    def test_missing_job_description_is_refused(self, client, stub_screen):
        response = self._post(client, "alex.md", self.RESUME_MD.encode(), jd="   ")
        assert response.status_code == 400

    def test_nothing_is_left_on_disk(self, client, stub_screen, monkeypatch):
        """It is somebody's actual resume. Keeping a copy on a demo server
        is not ours to decide.
        """
        made: list[str] = []
        real_mkdtemp = api.tempfile.mkdtemp

        def spy(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            made.append(path)
            return path

        monkeypatch.setattr(api.tempfile, "mkdtemp", spy)
        self._post(client, "alex.md", self.RESUME_MD.encode())

        assert made, "upload did not use a temp dir"
        assert not any(Path(p).exists() for p in made)


class TestRubricForPosting:
    def test_bundled_posting_uses_the_hand_written_rubric(self):
        """Generating a fresh rubric for the posting the eval measured
        would make an uploaded resume incomparable to the recorded 60.
        """
        api._rubric_by_fingerprint.clear()
        result = asyncio.run(api.rubric_for_posting(api.default_job_description()))
        assert result is None

    def test_same_posting_is_generated_once(self, monkeypatch):
        """Five uploads against one posting must be judged by identical
        criteria, not five slightly different rubrics.
        """
        api._rubric_by_fingerprint.clear()
        calls = []
        rubric = parse_rubric(json.loads(rubric_json()))

        async def _fake(job_description):
            calls.append(job_description)
            return rubric

        monkeypatch.setattr(api, "rubric_for", _fake)
        posting = "Charge Nurse, nights. ACLS required."
        first = asyncio.run(api.rubric_for_posting(posting))
        second = asyncio.run(api.rubric_for_posting(f"  {posting}  "))

        assert first is second
        assert len(calls) == 1
        api._rubric_by_fingerprint.clear()
