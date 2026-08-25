"""The MCP adapter -- thin on purpose. Every function below is a translation
layer over resume_screener.core; no scoring logic belongs here.

None of these tools takes an action. They read and report; they cannot
reject a candidate, send mail, or write to any system of record. That
boundary is deliberate and does double duty: it keeps a human in the loop
on every hiring decision, and it means a prompt injection that survives
into a tool call still has nothing to actuate.
"""

from __future__ import annotations

import uuid

from mcp.server.mcpserver import MCPServer

from resume_screener.core.models import Verdict
from resume_screener.core.pipeline import rank_all, screen_one
from resume_screener.core.query import answer_query

# mcp>=2 renamed FastMCP to MCPServer; pyproject pins >=2.1 accordingly.
mcp = MCPServer("resume-screener")

# session_id -> full screened pool. Holds every candidate, not just the
# shortlist that was displayed, so query_candidates can reach the ones that
# fell below the top N.
_sessions: dict[str, list[Verdict]] = {}
_MAX_SESSIONS = 20


def _store_session(verdicts: list[Verdict]) -> str:
    if len(_sessions) >= _MAX_SESSIONS:
        _sessions.pop(next(iter(_sessions)))
    session_id = str(uuid.uuid4())
    _sessions[session_id] = verdicts
    return session_id


@mcp.tool()
async def screen_resume(resume_path: str, job_description: str) -> dict:
    """Score one candidate's resume against a job description.

    Returns a score, a recommendation (advance/hold/reject), quoted evidence
    from the resume, and a needs_human_review flag. Use this for a single
    named candidate; use rank_pool for a whole folder.

    The result is advisory. It is never a hiring decision -- a human
    confirms before anything is acted on.
    """
    verdict = await screen_one(resume_path, job_description)
    session_id = _store_session([verdict])
    return {"session_id": session_id, **verdict.to_dict()}


@mcp.tool()
async def rank_pool(resume_dir: str, job_description: str, top_n: int = 10) -> dict:
    """Screen every resume in a directory and return the top N, ranked.

    Use when given a folder of resumes and asked for a shortlist, e.g.
    "screen these and show me the top 5". Returns a session_id: remember it
    and pass it to query_candidates or explain_verdict for any follow-up
    about this same pool, rather than screening again.

    Note that the session retains the FULL pool, so follow-up questions can
    reach candidates below the top N even though only the top N are listed
    here. Results are advisory; a human confirms before anything is acted on.
    """
    verdicts = await rank_all(resume_dir, job_description)
    session_id = _store_session(verdicts)
    flagged = [v for v in verdicts if v.review_reason is not None]
    return {
        "session_id": session_id,
        "screened_count": len(verdicts),
        "needs_human_review_count": len(flagged),
        "candidates": [v.to_dict() for v in verdicts[:top_n]],
    }


@mcp.tool()
async def explain_verdict(session_id: str, candidate_name: str) -> dict:
    """Show the full reasoning behind one candidate's verdict, including each
    panel agent's individual score and rationale, and whether the panel
    disagreed enough to require an arbiter.

    Use after screen_resume or rank_pool, with the session_id they returned.
    """
    pool = _sessions.get(session_id)
    if pool is None:
        return {"error": f"Unknown session_id {session_id!r}. Run rank_pool first."}

    target = candidate_name.strip().lower()
    for verdict in pool:
        if verdict.candidate.name.strip().lower() == target:
            return {
                "name": verdict.candidate.name,
                "score": round(verdict.score, 2),
                "recommendation": verdict.recommendation.value,
                "final_rationale": verdict.rationale,
                "panel": [p.to_dict() for p in verdict.panel_scores],
                "panel_spread": round(verdict.panel_spread, 2),
                "escalated_to_arbiter": verdict.escalated,
                "needs_human_review": verdict.review_reason is not None,
                "review_reason": verdict.review_reason,
                "evidence": [e.to_dict() for e in verdict.candidate.evidence],
            }

    known = [v.candidate.name for v in pool]
    return {
        "error": f"No candidate named {candidate_name!r} in this session.",
        "known_candidates": known,
    }


@mcp.tool()
async def query_candidates(session_id: str, question: str) -> dict:
    """Answer a follow-up question about an already-screened pool: filtering,
    counting, comparing, or judging evidence.

    Handles both objective questions ("how many scored above 7", "who has 5+
    years") and interpretive ones ("who actually built with MCP rather than
    just listing it"), including combinations of the two. Use this instead of
    re-screening when the pool has already been through rank_pool.
    """
    pool = _sessions.get(session_id)
    if pool is None:
        return {"error": f"Unknown session_id {session_id!r}. Run rank_pool first."}
    return await answer_query(pool, question)


if __name__ == "__main__":
    mcp.run(transport="stdio")
