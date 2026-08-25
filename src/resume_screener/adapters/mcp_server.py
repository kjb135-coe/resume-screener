"""The MCP adapter -- thin on purpose. Every function below is a translation
layer over resume_screener.core.pipeline; no scoring logic belongs here.
"""

from __future__ import annotations

import uuid

from mcp.server.fastmcp import FastMCP

from resume_screener.core.pipeline import default_models, rank_all, screen_one

mcp = FastMCP("resume-screener")

_sessions: dict[str, list] = {}  # session_id -> list[Verdict], see query_candidates.py


@mcp.tool()
async def screen_resume(resume_path: str, job_description: str) -> dict:
    """Score a single candidate's resume against a job description.

    Runs the resume through extraction and rubric-scoring and returns a
    verdict with a numeric score, a recommendation (advance/hold/reject),
    and quoted evidence from the resume. Use this for one specific
    candidate, not a whole folder.
    """
    verdict = await screen_one(resume_path, job_description)
    return verdict.to_dict()


@mcp.tool()
async def rank_pool(resume_dir: str, job_description: str, top_n: int = 10) -> dict:
    """Screen every resume in a directory and return the top N, ranked.

    Use this when given a folder of resumes and asked for a shortlist,
    e.g. "screen these and show me the top 5". Returns a session_id --
    remember it and pass it to query_candidates for any follow-up
    question about this same pool, instead of re-screening.
    """
    verdicts = await rank_all(resume_dir, job_description, top_n)
    session_id = str(uuid.uuid4())
    _sessions[session_id] = verdicts
    return {
        "session_id": session_id,
        "needs_human_review_count": sum(1 for v in verdicts if v.escalated),
        "candidates": [v.to_dict() for v in verdicts],
    }


@mcp.tool()
async def explain_verdict(session_id: str, candidate_name: str) -> dict:
    """Give the full reasoning behind one candidate's verdict from a prior
    rank_pool or screen_resume call, including each panel agent's rationale.
    """
    for verdict in _sessions.get(session_id, []):
        if verdict.candidate.name == candidate_name:
            return {
                "name": candidate_name,
                "final_rationale": verdict.rationale,
                "panel": [p.__dict__ for p in verdict.panel_scores],
                "escalated": verdict.escalated,
            }
    return {"error": f"No candidate named {candidate_name!r} in session {session_id!r}"}


@mcp.tool()
async def query_candidates(session_id: str, question: str) -> dict:
    """Answer a follow-up question about an already-screened pool --
    filtering, counting, comparing, or judging evidence. Use this after
    rank_pool has already run in this conversation, instead of re-screening.
    """
    from resume_screener.core.query import answer_query

    pool = _sessions.get(session_id)
    if pool is None:
        return {"error": f"Unknown session_id {session_id!r}"}
    return await answer_query(pool, question)


if __name__ == "__main__":
    mcp.run(transport="stdio")
