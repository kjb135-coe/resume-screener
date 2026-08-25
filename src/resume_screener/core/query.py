"""The two general primitives behind query_candidates.

Every question about an already-screened pool decomposes into one of two
kinds of operation: something mechanically computable over structured
fields (must be deterministic code, never a model), or something that
requires interpreting meaning in free text (must be a model, and its
authority is capped to a bounded answer). Nothing else is needed --
that split is necessary and sufficient, see docs/ARCHITECTURE.md.

Security note: the structured-query primitive executes model-generated
SQL, not model-generated Python, and only against a read-only in-memory
DuckDB connection with no filesystem or network access. Never eval()
or exec() a model-generated expression directly -- see ARCHITECTURE.md's
security section on resume prompt injection.
"""

from __future__ import annotations

import json
import os

import duckdb

from resume_screener.core.models import Verdict
from resume_screener.core.router import AnthropicModel

_PLANNER_SYSTEM = (
    "You route a question about a table of screened job candidates. "
    "Respond as JSON: {needs_sql: bool, sql: str|null, needs_judgment: bool, "
    "criterion: str|null}. The table is named candidates with columns: "
    "name, score, recommendation, years_experience, companies (text, "
    "comma-joined), technologies (text, comma-joined). Only set needs_sql "
    "true for objective/relational asks (counts, filters, comparisons, "
    "sorts) expressible as a SELECT against that table. Only set "
    "needs_judgment true when answering requires reading free-text "
    "evidence and making a subjective call (e.g. 'actually built with X, "
    "not just listed it'). Both may be true, e.g. filter then judge."
)

_JUDGE_SYSTEM = (
    "For each candidate below, answer the criterion strictly from their "
    "quoted evidence. Respond as JSON: a list of {name, matches: bool, "
    "justification: str}. If the evidence doesn't support a claim, say so "
    "-- do not infer beyond what's quoted."
)


def _pool_to_table(pool: list[Verdict]) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:", read_only=False)
    con.execute(
        "CREATE TABLE candidates (name TEXT, score DOUBLE, recommendation TEXT, "
        "years_experience DOUBLE, companies TEXT, technologies TEXT)"
    )
    for v in pool:
        con.execute(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?)",
            [
                v.candidate.name,
                v.score,
                v.recommendation.value,
                v.candidate.years_experience,
                ", ".join(v.candidate.companies),
                ", ".join(v.candidate.technologies),
            ],
        )
    return con


async def answer_query(pool: list[Verdict], question: str) -> dict:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    planner = AnthropicModel("claude-haiku-4-5-20251001", api_key)

    plan_raw = await planner.complete(_PLANNER_SYSTEM, question, max_tokens=300)
    plan = json.loads(plan_raw[plan_raw.find("{") : plan_raw.rfind("}") + 1])

    candidates = pool
    if plan.get("needs_sql") and plan.get("sql"):
        con = _pool_to_table(pool)
        try:
            rows = con.execute(plan["sql"]).fetchall()  # read-only in-memory table, no eval/exec
            names = {r[0] for r in rows}
            candidates = [v for v in candidates if v.candidate.name in names]
        finally:
            con.close()

    if plan.get("needs_judgment") and plan.get("criterion"):
        judge = AnthropicModel("claude-sonnet-5", api_key)
        payload = [
            {
                "name": v.candidate.name,
                "evidence": [e.quote for e in v.candidate.evidence],
            }
            for v in candidates
        ]
        judged_raw = await judge.complete(
            _JUDGE_SYSTEM,
            f"Criterion: {plan['criterion']}\n\nCandidates:\n{json.dumps(payload)}",
            max_tokens=1024,
        )
        judged = json.loads(judged_raw[judged_raw.find("[") : judged_raw.rfind("]") + 1])
        matching_names = {j["name"] for j in judged if j.get("matches")}
        candidates = [v for v in candidates if v.candidate.name in matching_names]
        return {
            "matches": [v.to_dict() for v in candidates],
            "justifications": {j["name"]: j["justification"] for j in judged},
        }

    return {"matches": [v.to_dict() for v in candidates]}
