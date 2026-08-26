"""The web adapter -- thin on purpose, same rule as mcp_server.py.

Scope is deliberately narrow: paste a job posting, read the rubric the
system would score against. It does not screen resumes. Screening a pool
is a minutes-long, dollars-scale job that belongs behind the MCP server
or the eval script, not behind a button someone can lean on.

This exists because "the rubric is generated, not hardcoded" is a claim
that should be *shown*. A reviewer can paste in any posting and read what
the panel would be told to look for.

    uvicorn resume_screener.adapters.api:app --reload

Needs ANTHROPIC_API_KEY. Without it the page still loads and says so,
rather than failing at import time.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from resume_screener.core.pipeline import rubric_for
from resume_screener.core.rubric_gen import RubricGenerationError

log = logging.getLogger(__name__)

STATIC = Path(__file__).parent / "static"

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


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


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
