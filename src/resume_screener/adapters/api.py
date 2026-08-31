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
bundled posting maps to the recorded 60-resume eval run, so the
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
import hmac
import json
import logging
import os
import re
import shutil
import tempfile
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from resume_screener.adapters.budget import (
    MAX_RESUMES_PER_RUN,
    BudgetExceeded,
    budget,
    explain_provider_failure,
)
from resume_screener.core.ingest import load_resume_text
from resume_screener.core.models import Verdict
from resume_screener.core.pipeline import (
    default_models,
    hand_written_personas,
    rank_paths,
    rubric_for,
    screen_one,
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

RESUME_PDF_DIR = REPO / "data" / "resume_pdfs"
DECISIONS_JSON = REPO / "data" / "reviewer_decisions.json"

# Shared-secret gate. Not authentication -- there are no accounts, and
# every viewer is the same anonymous reviewer. It exists so a hosted demo
# link is not an open invoice: every live screening call costs money, and
# an ungated public page with an API key behind it is a page anyone can
# spend from. See PLAN.md 11.
ACCESS_PASSWORD = os.environ.get("APP_PASSWORD", "screener")
SESSION_COOKIE = "rs_session"

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
        values = ", ".join(
            f"{a['score']:.1f}" for a in prediction["panel"] if not a.get("parse_failed")
        )
        return (
            f"The panel disagreed ({values}); an arbiter resolved it, "
            "but a human should confirm."
        )
    return None


# Agents quote with whatever mark they feel like -- straight doubles,
# curly doubles, and single quotes all show up in real output, sometimes
# from different agents on the same candidate. Matching only one style
# silently drops that agent's citations.
#
# Single quotes risk catching an apostrophe pair ("candidate's ... system's"),
# but a false extraction is harmless here: _locate refuses anything that is
# not verbatim in the resume, so a bogus span produces no citation at all.
_QUOTE_PATTERNS = (
    re.compile(r'["“]([^"”]{15,400})["”]'),
    re.compile(r"['‘]([^'’]{15,400})['’]"),
)


def _quoted_spans(text: str) -> list[str]:
    """Every quoted span in `text`, in the order they appear."""
    found: list[tuple[int, str]] = []
    for pattern in _QUOTE_PATTERNS:
        found += [(m.start(), m.group(1).strip()) for m in pattern.finditer(text)]
    found.sort()
    return [quote for _, quote in found if quote]


_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
_ABBREVIATION = re.compile(
    r"(?:e\.g|i\.e|etc|vs|approx|no|fig|cf|Dr|Mr|Mrs|Ms|Inc|Ltd|Jr|Sr|Ph\.D)\.$",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    """Split prose into sentences without breaking inside a quotation.

    A regex on `[.!?]\\s+` looks sufficient until the model writes
    `...ownership, e.g. "Architected and shipped..."`. It then splits on
    the period in "e.g." and again inside the quote, turning one cited
    claim into two fragments, one of which opens mid-quotation. Both
    guards below exist because that happened to real output.
    """
    sentences: list[str] = []
    start = 0
    in_double = False   # straight " toggles
    in_curly = False    # “ opens, ” closes

    for i, char in enumerate(text):
        closing_quote = False
        if char == '"':
            closing_quote = in_double
            in_double = not in_double
        elif char == "“":
            in_curly = True
        elif char == "”":
            closing_quote = in_curly
            in_curly = False

        if closing_quote:
            # `... docs." That is production.` -- the period that ends the
            # sentence sits inside the quotation, so the only real boundary
            # is just past the closing mark.
            boundary = text[i - 1 : i] in (".", "!", "?")
        elif char in ".!?" and not in_double and not in_curly:
            boundary = True
        else:
            continue

        if not boundary:
            continue
        following = text[i + 1 : i + 2]
        if following and not following.isspace():
            continue
        if _ABBREVIATION.search(text[start : i + 1]):
            continue
        rest = text[i + 1 :].lstrip()
        if not rest or not (rest[0].isupper() or rest[0].isdigit() or rest[0] in "\"“‘'"):
            continue
        sentences.append(text[start : i + 1].strip())
        start = i + 1

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return [s for s in sentences if s]


def _normalise(text: str) -> str:
    """Collapse whitespace so a quote matches across line wrapping.

    A model quoting a resume reproduces the words, not the line breaks
    the PDF or Markdown happened to have.
    """
    return " ".join(text.split())


def _resume_sections(resume_text: str) -> list[tuple[str, str]]:
    """Split a resume into (heading, normalised body) pairs.

    Anything before the first heading is attributed to "Summary" -- most
    resumes open with a contact block and a profile paragraph that no
    heading covers, and quotes do land there.
    """
    matches = list(_HEADING.finditer(resume_text))
    if not matches:
        return [("Résumé", _normalise(resume_text))]

    sections: list[tuple[str, str]] = []
    preamble = resume_text[: matches[0].start()].strip()
    if preamble:
        sections.append(("Summary", _normalise(preamble)))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(resume_text)
        sections.append((match.group(1).strip(), _normalise(resume_text[match.end() : end])))
    return sections


def _locate(quote: str, sections: list[tuple[str, str]]) -> str | None:
    """Which section of the resume a quote came from, or None if it isn't there.

    Returning None matters as much as returning a heading: a quote that
    cannot be found in the resume is the model paraphrasing rather than
    citing, and the page should not dress that up as a citation.
    """
    needle = _normalise(quote)
    # Models elide with "..."; match on the longest contiguous run instead.
    if "..." in needle or "…" in needle:
        parts = re.split(r"\.\.\.|…", needle)
        needle = max((p.strip() for p in parts), key=len, default="")
    if len(needle) < 15:
        return None
    for heading, body in sections:
        if needle in body:
            return heading
    return None


def bullets_from(rationale: str, resume_text: str, limit: int = 1) -> list[dict]:
    """Turn an agent's prose into at most `limit` bullets with citations.

    One bullet by default: three agents plus an arbiter on one screen is
    already four blocks of prose, and a reviewer scanning a queue reads the
    first line of each or none of them. The panel prompt asks for a single
    sentence, so this is normally the whole rationale rather than a crop.

    The panel is prompted to quote the evidence it relied on, so the
    quotes are already in the prose. Pulling them out and locating them in
    the resume is what separates "this reads like feedback about a
    person" from "this reads like feedback about anyone" -- a bullet that
    names the section it came from cannot be generic boilerplate.

    Done at the display layer rather than by changing the panel's response
    schema, so the recorded run and every future live run render the same
    way with no re-scoring.
    """
    text = (rationale or "").strip()
    if not text:
        return []

    sections = _resume_sections(resume_text or "")
    out: list[dict] = []
    for sentence in _split_sentences(text):
        # The sentence is kept verbatim. Stripping the quotes out of it to
        # build a tidier "claim" turns a sentence with two citations into
        # "… and … matching the posting", which is worse than the original.
        citations: list[dict] = []
        seen: set[str] = set()
        for quote in _quoted_spans(sentence):
            section = _locate(quote, sections)
            if section and quote not in seen:
                seen.add(quote)
                citations.append({"quote": quote, "section": section})
        out.append({"text": sentence, "citations": citations})
        if len(out) == limit:
            break
    return out


RULING_MAX_CHARS = 420


def shorten_ruling(text: str, limit: int = 2, max_chars: int = RULING_MAX_CHARS) -> str:
    """The arbiter's ruling, capped at `limit` sentences and `max_chars`.

    The prompt now asks for two sentences and new runs comply. Runs
    recorded before that prompt existed carry rulings that restate every
    panelist in turn, and those are what the page shows today. Capping at
    the display layer fixes the archive without paying to re-score it.

    The character budget is not redundant with the sentence cap. These
    rulings quote the resume heavily, and `_split_sentences` deliberately
    refuses to break inside a quotation -- so a ruling can be *one*
    sentence and still run 992 characters. Sentence-capping alone bounded
    nothing on the worst offenders.
    """
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text

    kept = " ".join(_split_sentences(text)[:limit]).strip() or text
    if len(kept) <= max_chars:
        return kept

    # Still over budget: cut at the last word boundary that fits, so the
    # ruling ends on a whole word rather than mid-quote.
    clipped = kept[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:-—")
    return f"{clipped}…"


def _attach_bullets(candidate: dict) -> dict:
    """Give every panel entry its bullets, and collect quotes for highlighting."""
    resume_text = candidate.get("resume_text", "")
    quotes: list[str] = []
    for agent in candidate.get("panel", []):
        agent["bullets"] = bullets_from(agent.get("rationale", ""), resume_text)
        for bullet in agent["bullets"]:
            quotes += [c["quote"] for c in bullet["citations"]]
    # Deduped, preserving order: the page highlights these in the resume,
    # and the same line is often cited by more than one agent.
    candidate["cited_quotes"] = list(dict.fromkeys(quotes))
    return candidate


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
                "rationale": shorten_ruling(prediction["rationale"])
                if prediction["escalated"]
                else prediction["rationale"],
                "panel": prediction["panel"],
                "resume_text": resume_path.read_text(encoding="utf-8")
                if resume_path.exists()
                else "",
            }
        )

    candidates = [_attach_bullets(c) for c in candidates]
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
        "rationale": shorten_ruling(verdict.rationale)
        if verdict.escalated
        else verdict.rationale,
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
        candidates = [
            _attach_bullets(_verdict_to_dict(v, labels, graded=graded)) for v in verdicts
        ]
        matched = [c for c in candidates if c["matches_ground_truth"] is not None]
        usage = sum((v.usage for v in verdicts), Usage())
        # Record what this run actually cost, from the same token counts
        # the eval prices. Recorded AFTER the fact: a run that has started
        # is allowed to finish, so the cap can overshoot by at most one
        # batch -- which is what MAX_RESUMES_PER_RUN bounds.
        budget.record(usage.by_model)

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
    except Exception as exc:
        log.exception("Screening job %s failed", job_id)
        job["status"] = "error"
        job["error"] = (
            explain_provider_failure(exc) or "Screening failed. Check the server log."
        )


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------

class ScreenRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=40_000)
    """Capped because the whole posting becomes part of a cached prompt
    prefix. A pasted novel is a cost problem, not a correctness one, but
    it is still worth refusing at the edge."""

    count: int = Field(default=DEFAULT_SAMPLE, ge=1, le=MAX_SAMPLE)


# --------------------------------------------------------------------------
# access gate, reviewer decisions, resume PDFs
# --------------------------------------------------------------------------

def _session_token() -> str:
    """Derived from the password, so changing the password logs everyone out."""
    return hashlib.sha256(f"rs::{ACCESS_PASSWORD}".encode()).hexdigest()[:32]


def is_authorised(request: Request) -> bool:
    return hmac.compare_digest(request.cookies.get(SESSION_COOKIE, ""), _session_token())


PUBLIC_PATHS = {"/health", "/api/login", "/login", "/", "/favicon.ico"}


@app.middleware("http")
async def require_password(request: Request, call_next):
    """Gate everything except the login page and the health check.

    A middleware rather than a per-route dependency because the failure
    mode that matters is a *new* endpoint being added without the guard.
    Default-closed means forgetting to annotate a route makes it
    inaccessible, which someone notices immediately, instead of making it
    public, which nobody notices at all.
    """
    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/static"):
        return await call_next(request)
    if is_authorised(request):
        return await call_next(request)
    return JSONResponse({"error": "Not authorised.", "login_required": True}, status_code=401)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


@app.post("/api/login")
async def post_login(request: LoginRequest) -> JSONResponse:
    # compare_digest rather than ==, so the check does not leak the
    # password's length or prefix through response timing.
    if not hmac.compare_digest(request.password, ACCESS_PASSWORD):
        return JSONResponse({"error": "Wrong password."}, status_code=401)
    response = JSONResponse({"ok": True})
    response.set_cookie(
        SESSION_COOKIE, _session_token(),
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7,
    )
    return response


@app.post("/api/logout")
async def post_logout() -> JSONResponse:
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


def load_decisions() -> dict[str, dict]:
    if DECISIONS_JSON.exists():
        try:
            return json.loads(DECISIONS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("reviewer_decisions.json is malformed; starting empty")
    return {}


def save_decisions(decisions: dict[str, dict]) -> None:
    DECISIONS_JSON.write_text(json.dumps(decisions, indent=2, sort_keys=True), encoding="utf-8")


class DecisionRequest(BaseModel):
    file: str = Field(min_length=1, max_length=300)
    decision: str = Field(pattern="^(approve|reject|clear)$")
    note: str = Field(default="", max_length=2000)


@app.post("/api/decision")
async def post_decision(request: DecisionRequest) -> JSONResponse:
    """Record a human's verdict on a flagged candidate.

    Stored separately from the model's output rather than overwriting it.
    The point of the review queue is to compare the two: a decision file
    that silently replaced the score would destroy the only record of
    where the model and a person disagreed, which is the most useful data
    this thing produces.
    """
    decisions = load_decisions()
    if request.decision == "clear":
        decisions.pop(request.file, None)
    else:
        decisions[request.file] = {
            "decision": request.decision,
            "note": request.note.strip(),
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    save_decisions(decisions)
    return JSONResponse({"ok": True, "decisions": decisions})


@app.get("/api/decisions")
async def get_decisions() -> JSONResponse:
    return JSONResponse(load_decisions())


@app.get("/api/resume-pdf/{filename}", response_model=None)
async def get_resume_pdf(filename: str) -> FileResponse | JSONResponse:
    """Serve a candidate's resume as a PDF.

    `Path(filename).name` strips any directory component, so a crafted
    `../../.env` resolves to `.env` and then fails the suffix check below
    rather than escaping the corpus directory.
    """
    stem = Path(filename).name.rsplit(".", 1)[0]
    pdf = RESUME_PDF_DIR / f"{stem}.pdf"
    if not pdf.is_file() or pdf.parent != RESUME_PDF_DIR:
        return JSONResponse(
            {"error": "No PDF for that candidate. Run scripts/build_resume_pdfs.py."},
            status_code=404,
        )
    return FileResponse(pdf, media_type="application/pdf", filename=f"{stem}.pdf")


@app.get("/api/stats")
async def get_stats() -> JSONResponse:
    """Run-level numbers for the results page, plus reviewer progress."""
    try:
        run = load_recorded_run()
    except FileNotFoundError:
        return JSONResponse({"error": "No recorded run yet."}, status_code=404)

    raw = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    candidates = run["candidates"]
    decisions = load_decisions()
    flagged = [c for c in candidates if c["needs_human_review"]]
    reviewed = [c for c in flagged if c["file"] in decisions]

    agreed = sum(
        1
        for c in flagged
        if c["file"] in decisions
        and decisions[c["file"]]["decision"]
        == ("approve" if c["recommendation"] == "advance" else "reject")
    )

    return JSONResponse(
        {
            "run": {
                "tag": raw.get("tag"),
                "n": raw.get("n"),
                "macro_f1": round(raw.get("macro_f1", 0), 3),
                "accuracy": round(raw.get("accuracy", 0), 3),
                "cost_total": round(raw.get("cost_total", 0), 3),
                "cost_per_resume": round(raw.get("cost_per_resume", 0), 4),
                "latency_p50": round(raw.get("latency_p50", 0), 1),
                "latency_p95": round(raw.get("latency_p95", 0), 1),
                "escalation_rate": round(raw.get("escalation_rate", 0), 3),
                "cost_by_model": raw.get("cost_by_model") or {},
                "model_ids": raw.get("model_ids") or {},
                "per_class": raw.get("per_class") or {},
            },
            "verdicts": {
                "advance": run["summary"]["advance"],
                "hold": run["summary"]["hold"],
                "reject": run["summary"]["reject"],
            },
            "review": {
                "flagged": len(flagged),
                "reviewed": len(reviewed),
                "remaining": len(flagged) - len(reviewed),
                "agreed_with_model": agreed,
                "overridden": len(reviewed) - agreed,
            },
            "by_archetype": _accuracy_by_archetype(candidates),
        }
    )


def _accuracy_by_archetype(candidates: list[dict]) -> list[dict]:
    buckets: dict[str, list[bool]] = defaultdict(list)
    for c in candidates:
        if c.get("expected"):
            buckets[c["archetype"]].append(bool(c["matches_ground_truth"]))
    return sorted(
        (
            {
                "archetype": name,
                "correct": sum(hits),
                "total": len(hits),
                "accuracy": round(sum(hits) / len(hits), 3),
            }
            for name, hits in buckets.items()
        ),
        key=lambda row: row["accuracy"],
    )


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/budget")
async def get_budget() -> JSONResponse:
    """What the demo has spent today, and what is left.

    Public on purpose: a visitor who gets refused should be able to see
    that it was a spend cap and when it resets, rather than guessing the
    app is broken.
    """
    return JSONResponse(budget.snapshot())


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
        run = load_recorded_run()
        decisions = load_decisions()
        # Attached at read time rather than baked into the cached run, so a
        # reviewer's decision shows up without invalidating the cache or
        # touching the model's recorded output.
        for candidate in run["candidates"]:
            candidate["reviewer"] = decisions.get(candidate["file"])
        return JSONResponse(run)
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


_rubric_by_fingerprint: dict[str, GeneratedRubric | None] = {}


def rubric_view(rubric: GeneratedRubric | None) -> dict:
    """The criteria as the page shows them, generated or hand-written."""
    if rubric is None:
        return _hand_written_rubric_view()
    return rubric.to_dict()


async def rubric_for_posting(job_description: str) -> GeneratedRubric | None:
    """The criteria for a posting, reusing whatever this posting already has.

    Returns a GeneratedRubric, or None meaning "use the hand-written
    rubric". Raises RubricGenerationError if the model returns something
    unusable, and RuntimeError if there is no API key.

    Caching on the posting fingerprint matters for uploads specifically:
    screening five resumes against one posting should write the criteria
    once, not five times, and all five must be judged against *identical*
    criteria. Regenerating per upload would quietly score each candidate
    by a slightly different standard, which is exactly the unfairness this
    whole project is supposed to avoid.
    """
    fingerprint = jd_fingerprint(job_description)
    if fingerprint in _rubric_by_fingerprint:
        return _rubric_by_fingerprint[fingerprint]

    if fingerprint == jd_fingerprint(default_job_description()):
        # The bundled posting is the one prompts/rubric.md was written for,
        # and is what the recorded eval measured. Generating a fresh rubric
        # for it would make an uploaded resume incomparable to the 60.
        _rubric_by_fingerprint[fingerprint] = None
        return None

    rubric = await rubric_for(job_description)
    _rubric_by_fingerprint[fingerprint] = rubric
    return rubric


UPLOAD_SUFFIXES = {".pdf", ".docx", ".md", ".txt"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@app.post("/api/screen-upload")
async def post_screen_upload(
    # FastAPI declares multipart fields exactly this way; B008 is about
    # mutable defaults in ordinary functions and does not apply.
    file: UploadFile = File(...),  # noqa: B008
    job_description: str = Form(...),
) -> JSONResponse:
    """Screen one uploaded resume against a posting.

    Cheap enough to be synchronous: one extraction plus three panel calls,
    a few cents and a handful of seconds, versus the minute a sampled batch
    takes.

    The uploaded file is written to a temporary path, read, and deleted in
    a `finally`. Nothing is persisted and nothing is added to the corpus.
    This is somebody's actual resume -- keeping a copy on a demo server is
    not ours to decide.

    An uploaded resume is untrusted input. It cannot make anything happen:
    no tool here takes an action, so the worst an injected instruction can
    do is argue for its own score, and the verdict is advisory in the first
    place. Worth stating rather than assuming.
    """
    try:
        budget.check()
    except BudgetExceeded as exc:
        return JSONResponse({"error": str(exc)}, status_code=429)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in UPLOAD_SUFFIXES:
        return JSONResponse(
            {
                "error": f"Unsupported file type {suffix or '(none)'}. "
                f"Accepted: {', '.join(sorted(UPLOAD_SUFFIXES))}."
            },
            status_code=415,
        )

    payload = await file.read()
    if not payload:
        return JSONResponse({"error": "That file is empty."}, status_code=400)
    if len(payload) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            {
                "error": f"That file is {len(payload) / 1e6:.1f} MB. "
                f"The limit is {MAX_UPLOAD_BYTES // 1024 // 1024} MB."
            },
            status_code=413,
        )
    if not job_description.strip():
        return JSONResponse({"error": "Paste a job posting first."}, status_code=400)

    tmp_dir = Path(tempfile.mkdtemp(prefix="resume-upload-"))
    tmp_path = tmp_dir / f"upload{suffix}"
    try:
        tmp_path.write_bytes(payload)
        try:
            resume_text = load_resume_text(str(tmp_path))
        except Exception as exc:  # noqa: BLE001 - pypdf/python-docx raise anything
            log.warning("Could not read uploaded %s: %s", suffix, exc)
            return JSONResponse(
                {"error": f"Could not read that {suffix} file. Is it a valid document?"},
                status_code=422,
            )
        if len(resume_text.split()) < 40:
            # Scanned PDFs extract to almost nothing. Scoring that would
            # produce a confident zero about a resume nobody could read.
            return JSONResponse(
                {
                    "error": "Almost no text came out of that file. If it is a "
                    "scanned or image-only PDF, export a text version and retry."
                },
                status_code=422,
            )

        rubric = await rubric_for_posting(job_description)
        verdict = await screen_one(str(tmp_path), job_description, rubric=rubric)
        budget.record(verdict.usage.by_model)
    except RubricGenerationError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except RuntimeError as exc:  # no API key
        return JSONResponse({"error": str(exc)}, status_code=503)
    except Exception as exc:
        log.exception("Screening an uploaded resume failed")
        friendly = explain_provider_failure(exc)
        return JSONResponse(
            {"error": friendly or "Screening failed. Check the server log."},
            status_code=503 if friendly else 500,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    candidate = _attach_bullets(_verdict_to_dict(verdict, {}, graded=False))
    candidate["name"] = verdict.candidate.name or Path(file.filename or "resume").stem
    candidate["file"] = file.filename or "upload"
    candidate["uploaded"] = True
    return JSONResponse(
        {
            "candidate": candidate,
            "criteria": rubric_view(rubric),
        }
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
    # A cached or recorded result costs nothing, so the cap is checked
    # only on the paths that would actually call a model -- below.
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

    try:
        budget.check()
    except BudgetExceeded as exc:
        return JSONResponse({"error": str(exc)}, status_code=429)

    if request.count > MAX_RESUMES_PER_RUN:
        return JSONResponse(
            {
                "error": (
                    f"This demo screens at most {MAX_RESUMES_PER_RUN} resumes "
                    "per run, so one submission cannot exhaust the daily budget."
                )
            },
            status_code=400,
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
