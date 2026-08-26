"""The web adapter -- thin on purpose, same rule as mcp_server.py.

Two things, and a deliberate line between them:

**Results** (`/api/results`) serve the *recorded* run in data/eval_run.json
-- all 60 candidates, their verdicts, every panel agent's score and
reasoning, and which ones want a human. Reading a file costs nothing, so
this loads instantly and works with no API key at all.

**Rubric** (`/api/rubric`) is the one live call: paste a posting, read the
rubric the panel would be given. This exists because "the rubric is
generated, not hardcoded" is a claim that should be shown, not asserted.

What is deliberately NOT here is a button that screens a pool live. That
is a minutes-long, dollars-scale job; it belongs behind the CLI, the MCP
server, or scripts/evaluate.py, where the person starting it knows they
started it. Re-run scripts/evaluate.py and this page shows the new run.

    uvicorn resume_screener.adapters.api:app --reload

ANTHROPIC_API_KEY is needed only for rubric generation. Without it the
page still loads, results still work, and the rubric tab says why.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from resume_screener.core.pipeline import rubric_for
from resume_screener.core.rubric_gen import RubricGenerationError

log = logging.getLogger(__name__)

STATIC = Path(__file__).parent / "static"
REPO = Path(__file__).resolve().parents[3]
RUN_JSON = REPO / "data" / "eval_run.json"
LABELS_JSON = REPO / "data" / "labels.json"
RESUME_DIR = REPO / "data" / "synthetic_resumes"

app = FastAPI(
    title="Resume Screener — rubric preview",
    description="Paste a job posting, see the rubric the panel would score against.",
)


class RubricRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=40_000)
    """Capped because the whole posting becomes part of a cached prompt
    prefix. A pasted novel is a cost problem, not a correctness one, but
    it is still worth refusing at the edge.
    """


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


@lru_cache(maxsize=1)
def load_recorded_run() -> dict:
    """Read the last scripts/evaluate.py run into what the page needs.

    Cached: it is a static file, and re-reading 60 resumes per request to
    serve the same bytes is waste. Restart the server after a new eval run.
    """
    run = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    labels = json.loads(LABELS_JSON.read_text(encoding="utf-8"))

    candidates = []
    for prediction in run["predictions"]:
        file = prediction["file"]
        resume_path = RESUME_DIR / file
        label = labels.get(file, {})
        reason = _review_reason(prediction)
        candidates.append(
            {
                "file": file,
                "name": label.get("candidate_name") or Path(file).stem,
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
        "summary": {
            "n": run["n"],
            "macro_f1": round(run["macro_f1"], 3),
            "accuracy": round(run["accuracy"], 3),
            "cost_total": round(run["cost_total"], 3),
            "cost_per_resume": round(run["cost_per_resume"], 4),
            "latency_p50": round(run["latency_p50"], 1),
            "needs_human_review": sum(1 for c in candidates if c["needs_human_review"]),
            "advance": sum(1 for c in candidates if c["recommendation"] == "advance"),
            "hold": sum(1 for c in candidates if c["recommendation"] == "hold"),
            "reject": sum(1 for c in candidates if c["recommendation"] == "reject"),
        },
        "candidates": candidates,
    }


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/api/results")
async def get_results() -> JSONResponse:
    """The recorded run: every candidate, verdict, and panel rationale.

    Costs nothing and needs no API key -- it is a file on disk. Returns a
    readable error rather than a 500 if no eval has been run yet.
    """
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


@app.post("/api/rubric")
async def post_rubric(request: RubricRequest) -> JSONResponse:
    """Generate the scoring rubric for a posting.

    Errors are returned as JSON with a readable `error`, not raised as
    500s: every failure mode here (no API key, model returned junk, wrong
    dimension count) is something the person pasting the posting can act
    on, so it belongs on the page.
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
            {"error": "Rubric generation failed. Check the server log."},
            status_code=500,
        )
    return JSONResponse(rubric.to_dict())
