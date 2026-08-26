"""The web adapter -- thin on purpose, same rule as mcp_server.py.

The demo flow it serves is the whole product in one screen:

    submit a posting -> it writes 3 scoring criteria -> resumes are
    screened against those criteria -> ranked results with reasoning

Three things make that affordable enough to put behind a button:

**A live run screens a stratified sample, not the whole corpus.** Twelve
resumes spread across the ground-truth classes costs about $0.19 and
takes under a minute. The full 60 is a four-minute, dollar-scale job and
lives in the CLI, where whoever starts it knows they started it.

**Identical postings are served from cache.** The posting is hashed; a
repeat submission returns the stored run instantly and bills nothing. The
bundled Marco posting maps to the recorded 60-resume eval run, so the
default demo path costs zero.

**Screening is a job, not a request.** A minute-long blocking HTTP call
with no feedback is indistinguishable from a hang, so POST starts a job
and the page polls it for progress.

    uvicorn resume_screener.adapters.api:app --reload

ANTHROPIC_API_KEY is needed only for live runs. Without it the page still
loads and the recorded run still works.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from resume_screener.core.models import Verdict
from resume_screener.core.pipeline import (
    default_models,
    hand_written_personas,
    rank_paths,
    rubric_for,
)
from resume_screener.core.router import Usage
from resume_screener.core.rubric_gen import GeneratedRubric, RubricGenerationError

log = logging.getLogger(__name__)

STATIC = Path(__file__).parent / "static"
REPO = Path(__file__).resolve().parents[3]
RUN_JSON = REPO / "data" / "eval_run.json"
LABELS_JSON = REPO / "data" / "labels.json"
RESUME_DIR = REPO / "data" / "synthetic_resumes"
DEFAULT_JD_PATH = REPO / "docs" / "job_description.md"

DEFAULT_SAMPLE = 12
MAX_SAMPLE = 24
"""Ceiling on a live run. Not a technical limit -- a spending one. The
full corpus stays reachable through the CLI."""

_MAX_JOBS = 40
_jobs: dict[str, dict] = {}
_run_cache: dict[str, dict] = {}

app = FastAPI(
    title="Resume Screener",
    description="Submit a posting, get scoring criteria, screen resumes against them.",
)


# --------------------------------------------------------------------------
# the recorded run
# --------------------------------------------------------------------------

def _review_reason(prediction: dict) -> str | None:
    """Why a human should look at this one first, if they should.

    Mirrors Verdict.review_reason, rebuilt from the recorded run. The
    extraction-confidence branch is absent because eval_run.json does not
    record it -- so this can under-flag relative to a live verdict, never
    over-flag.
    """
    if any(agent.get("parse_failed") for agent in prediction["panel"]):
        return "At least one scoring agent returned an unreadable response."
    if prediction["escalated"]:
        return (
            f"The scoring panel disagreed (spread of {prediction['panel_spread']:.1f} "
            "points); an arbiter resolved it, but a human should confirm."
        )
    return None


def _summarise(candidates: list[dict], **extra) -> dict:
    return {
        "n": len(candidates),
        "advance": sum(1 for c in candidates if c["recommendation"] == "advance"),
        "hold": sum(1 for c in candidates if c["recommendation"] == "hold"),
        "reject": sum(1 for c in candidates if c["recommendation"] == "reject"),
        "needs_human_review": sum(1 for c in candidates if c["needs_human_review"]),
        **extra,
    }


def _hand_written_rubric_view() -> dict:
    """The built-in panel, shaped like a generated rubric for display.

    The recorded run used the hand-written rubric, which has no
    GeneratedRubric object behind it. Returning None here would leave the
    page's "criteria" step blank on first load, which is the step that
    explains what the scores below it even mean.

    `criteria` is left empty rather than duplicating prose from
    prompts/rubric.md, which would be a second copy free to drift from
    the one the panel actually reads. The agent brief is the real text.
    """
    return {
        "role_title": "AI Solutions Engineer (bundled posting)",
        "summary": (
            "The built-in rubric, hand-written against docs/job_description.md "
            "and used for the recorded run below. Submit a different posting "
            "above and these three are replaced by criteria written for it."
        ),
        "dimensions": [
            {
                "name": name,
                "title": name.replace("_", " ").title(),
                "criteria": "",
                "lens": lens,
            }
            for name, lens in hand_written_personas().items()
        ],
        "hand_written": True,
    }


@lru_cache(maxsize=1)
def load_recorded_run() -> dict:
    """The last scripts/evaluate.py run, shaped for the page.

    Cached: it is a static file, and re-reading 60 resumes per request to
    serve the same bytes is waste. Restart the server after a new eval run.
    """
    run = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    labels = json.loads(LABELS_JSON.read_text(encoding="utf-8"))

    candidates = []
    for prediction in run["predictions"]:
        file = prediction["file"]
        resume_path = RESUME_DIR / file
        reason = _review_reason(prediction)
        candidates.append(
            {
                "file": file,
                "name": labels.get(file, {}).get("candidate_name") or Path(file).stem,
                "archetype": prediction["archetype"],
                "score": round(prediction["score"], 1),
                "recommendation": prediction["predicted"],
                "expected": prediction["expected"],
                "matches_ground_truth": prediction["expected"] == prediction["predicted"],
                "escalated": prediction["escalated"],
                "panel_spread": round(prediction["panel_spread"], 1),
                "needs_human_review": reason is not None,
                "review_reason": reason,
                "rationale": prediction["rationale"],
                "panel": prediction["panel"],
                "resume_text": resume_path.read_text(encoding="utf-8")
                if resume_path.exists()
                else "",
            }
        )

    candidates.sort(key=lambda c: -c["score"])
    return {
        "source": "recorded",
        "graded": True,
        "rubric": _hand_written_rubric_view(),
        "summary": _summarise(
            candidates,
            macro_f1=round(run["macro_f1"], 3),
            accuracy=round(run["accuracy"], 3),
            cost_total=round(run["cost_total"], 3),
            latency_p50=round(run["latency_p50"], 1),
        ),
        "candidates": candidates,
    }


# --------------------------------------------------------------------------
# live runs
# --------------------------------------------------------------------------

def jd_fingerprint(job_description: str) -> str:
    """Stable id for a posting, insensitive to trailing/incidental whitespace.

    Whitespace-only differences are not different jobs, and treating them
    as such would re-bill someone for pasting the same posting twice.
    """
    normalised = "\n".join(line.strip() for line in job_description.strip().splitlines())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def default_job_description() -> str:
    return DEFAULT_JD_PATH.read_text(encoding="utf-8")


def sample_resumes(count: int) -> list[Path]:
    """Pick `count` resumes spread evenly across the ground-truth classes.

    Taking the first N off disk would return twelve academic researchers,
    since the corpus is alphabetical by archetype. A viewer would watch a
    column of identical rejects and learn nothing about the system.
    Stratifying keeps advance/hold/reject all represented, and the
    ordering is deterministic so the same request gives the same sample.
    """
    labels = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    by_class: dict[str, list[str]] = defaultdict(list)
    for file in sorted(labels):
        by_class[labels[file]["label"]].append(file)

    picked: list[str] = []
    index = 0
    # Round-robin across classes so a small count stays balanced.
    while len(picked) < count and any(index < len(v) for v in by_class.values()):
        for label in sorted(by_class):
            if index < len(by_class[label]) and len(picked) < count:
                picked.append(by_class[label][index])
        index += 1
    return [RESUME_DIR / f for f in picked]


def _verdict_to_dict(verdict: Verdict, labels: dict, *, graded: bool) -> dict:
    """Shape one verdict for the page.

    `graded` says whether ground truth applies. The labels in labels.json
    describe one posting: the bundled AI Solutions Engineer role. Screening
    the same resumes against a payments or nursing posting produces
    perfectly correct verdicts that the labels say nothing about, and
    scoring them against the wrong answer key would report a made-up
    accuracy figure as if it meant something.
    """
    file = Path(verdict.candidate.source_path).name
    label = labels.get(file, {})
    expected = label.get("label") if graded else None
    return {
        "file": file,
        "name": verdict.candidate.name,
        "archetype": label.get("archetype", ""),
        "score": round(verdict.score, 1),
        "recommendation": verdict.recommendation.value,
        "expected": expected,
        "matches_ground_truth": expected == verdict.recommendation.value
        if expected
        else None,
        "escalated": verdict.escalated,
        "panel_spread": round(verdict.panel_spread, 1),
        "needs_human_review": verdict.review_reason is not None,
        "review_reason": verdict.review_reason,
        "rationale": verdict.rationale,
        "panel": [p.to_dict() for p in verdict.panel_scores],
        "resume_text": verdict.candidate.raw_text,
    }


async def _run_screening(job_id: str, job_description: str, count: int) -> None:
    """Generate a rubric, then screen the sample against it.

    Every failure is recorded on the job rather than raised: the caller is
    a poll loop, and an exception escaping here would leave the page
    waiting on a job that can never finish.
    """
    job = _jobs[job_id]
    try:
        job["stage"] = "rubric"
        models = default_models()
        rubric: GeneratedRubric = await rubric_for(job_description, models)
        job["rubric"] = rubric.to_dict()

        paths = sample_resumes(count)
        job["stage"] = "screening"
        job["progress"] = {"done": 0, "total": len(paths)}

        def progress(done: int, total: int) -> None:
            job["progress"] = {"done": done, "total": total}

        verdicts = await rank_paths(
            [str(p) for p in paths],
            job_description,
            models,
            rubric=rubric,
            on_progress=progress,
        )

        labels = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
        graded = job["fingerprint"] == jd_fingerprint(default_job_description())
        candidates = [_verdict_to_dict(v, labels, graded=graded) for v in verdicts]
        matched = [c for c in candidates if c["matches_ground_truth"] is not None]
        usage = sum((v.usage for v in verdicts), Usage())

        result = {
            "source": "live",
            "graded": graded,
            "rubric": rubric.to_dict(),
            "summary": _summarise(
                candidates,
                agreement=round(
                    sum(1 for c in matched if c["matches_ground_truth"]) / len(matched), 3
                )
                if matched
                else None,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            ),
            "candidates": candidates,
        }
        _run_cache[job["fingerprint"]] = result
        job["result"] = result
        job["stage"] = "done"
        job["status"] = "done"
    except RubricGenerationError as exc:
        job["status"], job["error"] = "error", str(exc)
    except RuntimeError as exc:
        # default_models() raises this when ANTHROPIC_API_KEY is unset.
        job["status"], job["error"] = "error", str(exc)
    except Exception:
        log.exception("Screening job %s failed", job_id)
        job["status"] = "error"
        job["error"] = "Screening failed. Check the server log."


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------

class ScreenRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=40_000)
    """Capped because the whole posting becomes part of a cached prompt
    prefix. A pasted novel is a cost problem, not a correctness one, but
    it is still worth refusing at the edge."""

    count: int = Field(default=DEFAULT_SAMPLE, ge=1, le=MAX_SAMPLE)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/api/default-jd")
async def get_default_jd() -> dict:
    """The bundled posting, used to prefill the box on first load."""
    return {
        "job_description": default_job_description(),
        "default_count": DEFAULT_SAMPLE,
        "max_count": MAX_SAMPLE,
    }


@app.get("/api/results")
async def get_results() -> JSONResponse:
    """The recorded 60-resume run. Reads a file, so it is free and instant."""
    try:
        return JSONResponse(load_recorded_run())
    except FileNotFoundError:
        return JSONResponse(
            {"error": "No recorded run found. Run scripts/evaluate.py first."},
            status_code=404,
        )
    except (json.JSONDecodeError, KeyError) as exc:
        log.exception("Recorded run is unreadable")
        return JSONResponse(
            {"error": f"data/eval_run.json is malformed ({exc}). Re-run scripts/evaluate.py."},
            status_code=500,
        )


class RubricRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=40_000)


@app.post("/api/rubric")
async def post_rubric(request: RubricRequest) -> JSONResponse:
    """Write the criteria for a posting without screening anyone.

    The cheap look: one call and a few cents, against roughly $0.19 for a
    full run. Someone deciding whether a posting is even set up right
    shouldn't have to pay for twelve screenings to find out.

    Errors come back as readable JSON rather than 500s -- every failure
    here (no key, junk response, wrong dimension count) is something the
    person pasting the posting can act on.
    """
    try:
        rubric = await rubric_for(request.job_description)
    except RubricGenerationError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except RuntimeError as exc:
        # default_models() raises this when ANTHROPIC_API_KEY is unset.
        return JSONResponse({"error": str(exc)}, status_code=503)
    except Exception:
        log.exception("Rubric generation failed")
        return JSONResponse(
            {"error": "Rubric generation failed. Check the server log."}, status_code=500
        )
    return JSONResponse(rubric.to_dict())


@app.post("/api/screen")
async def post_screen(request: ScreenRequest) -> JSONResponse:
    """Start a run: write criteria for this posting, then screen against them.

    Returns a finished result immediately when the posting has been seen
    before, otherwise a job_id to poll. The caller handles both, so a
    cache hit and a cold run look the same from the page's side.
    """
    fingerprint = jd_fingerprint(request.job_description)

    if fingerprint == jd_fingerprint(default_job_description()):
        try:
            return JSONResponse({"status": "done", "cached": True, "result": load_recorded_run()})
        except FileNotFoundError:
            pass  # no recorded run on disk; fall through and screen live

    if fingerprint in _run_cache:
        return JSONResponse(
            {"status": "done", "cached": True, "result": _run_cache[fingerprint]}
        )

    if len(_jobs) >= _MAX_JOBS:
        for stale in [k for k, v in _jobs.items() if v["status"] != "running"][:10]:
            _jobs.pop(stale, None)

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "running",
        "stage": "rubric",
        "progress": {"done": 0, "total": request.count},
        "fingerprint": fingerprint,
        "rubric": None,
        "result": None,
        "error": None,
    }
    asyncio.create_task(_run_screening(job_id, request.job_description, request.count))
    return JSONResponse({"status": "running", "cached": False, "job_id": job_id}, status_code=202)


@app.get("/api/screen/{job_id}")
async def get_screen(job_id: str) -> JSONResponse:
    """Poll a run. Carries the rubric as soon as it exists, before the
    screening finishes, so the page can show the criteria while it works.
    """
    job = _jobs.get(job_id)
    if job is None:
        return JSONResponse({"error": f"Unknown job {job_id!r}."}, status_code=404)
    if job["status"] == "error":
        return JSONResponse({"status": "error", "error": job["error"]}, status_code=422)
    return JSONResponse(
        {
            "status": job["status"],
            "stage": job["stage"],
            "progress": job["progress"],
            "rubric": job["rubric"],
            "result": job["result"],
        }
    )
