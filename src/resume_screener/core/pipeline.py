"""The tiered cascade: extract -> panel -> arbitrate (only on disagreement).

Every function here takes plain arguments and returns plain dataclasses --
no MCP, no HTTP, no CLI concerns. adapters/ is the only code allowed to
import this module and translate its shapes outward.

Caching contract (load-bearing, do not break casually):
the system block passed to any panel call is `rubric + job_description`
and nothing else. It is byte-identical across all three personas and
across every resume in a batch, so one cache write serves every
subsequent panel call. The persona and the candidate's evidence go in
the user turn. Putting the persona back into the system string would
silently create one cache entry per persona and gut the savings.

The rubric half is either the hand-written `prompts/rubric.md` (anchored
to docs/job_description.md) or a GeneratedRubric written for whatever
posting the caller supplied -- see core/rubric_gen.py. Either way it must
be resolved ONCE and reused for the whole batch: a rubric regenerated per
resume would differ slightly each time and defeat the cache.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import statistics
from collections.abc import Callable, Sequence
from pathlib import Path

from resume_screener.core.cutoffs import (
    ADVANCE_CUTOFF,
    DEFAULT_CUTOFFS,
    ESCALATION_MARGIN,
    HOLD_CUTOFF,
    MODEL_CUTOFFS,
    REVIEW_MARGIN_FRACTION,
    Cutoffs,
    band_width,
    cutoffs_for,
    distance_to_cutoff,
)
from resume_screener.core.ingest import iter_resume_paths, load_resume_text
from resume_screener.core.models import (
    Evidence,
    ExtractedCandidate,
    Recommendation,
    RubricScore,
    Verdict,
)
from resume_screener.core.router import (
    AnthropicModel,
    Model,
    OpenAICompatibleModel,
    Usage,
)
from resume_screener.core.rubric_gen import GeneratedRubric, generate_rubric

log = logging.getLogger(__name__)

# Cutoffs and their margins live in core/cutoffs.py -- models.py needs
# them for the human-review rule, and importing them from here would make
# that a cycle. Listed here so they stay importable from `pipeline`, which
# is where scripts/ and tests/ already reach for them.
__all__ = [
    "ADVANCE_CUTOFF",
    "DEFAULT_CUTOFFS",
    "DEFAULT_MODEL_IDS",
    "ESCALATION_MARGIN",
    "HOLD_CUTOFF",
    "MODEL_CUTOFFS",
    "REVIEW_MARGIN_FRACTION",
    "Cutoffs",
    "band_width",
    "cutoffs_for",
    "default_models",
    "distance_to_cutoff",
    "hand_written_personas",
    "rank_all",
    "recommendation_from_score",
    "rubric_for",
    "screen_one",
    "screen_one_single_pass",
]

RUBRIC = (Path(__file__).parent.parent / "prompts" / "rubric.md").read_text(encoding="utf-8")

DISAGREEMENT_THRESHOLD = 2.0  # spread across panel scores before escalating

# Swept against the labeled corpus rather than hand-picked -- see
# scripts/sweep_cutoffs.py and PLAN.md 3e. The previous 7.0/5.0 were
# guesses, and they were badly wrong: every candidate labelled `advance`
# scored at or above 4.0 and every `reject` at or below 1.0, so a 7.0 bar
# was rejecting most of the people it was supposed to advance. All 22
# errors in that run ran the same direction, downward.
#
# These are fitted on the same 60 resumes they are scored against, which
# makes them an informed setting rather than a validated one. The plateau
# is narrow on the advance side (3.1-3.3 on panel means), so treat this as
# provisional until the corpus grows.
# Cutoffs, and the two margins built on them, live in core/cutoffs.py --
# models.py needs them for its human-review rule and importing them from
# here would make that a cycle. Re-exported so existing callers in
# scripts/ and tests/ keep working unchanged.
# Caps simultaneous in-flight resumes. Each resume fans out to 1 extraction
# + 3 panel calls, so 60 unbounded resumes would mean ~240 concurrent
# requests and immediate rate limiting.
MAX_CONCURRENT_RESUMES = 6

# Extended thinking consumes the same max_tokens budget as the visible
# answer. Budgets sized only for the JSON payload get eaten by thinking
# and truncate the answer mid-string, which then looks like a parse
# failure rather than the budget problem it actually is.
EXTRACT_MAX_TOKENS = 3000
PANEL_MAX_TOKENS = 4000
ARBITER_MAX_TOKENS = 3000

# The hand-written panel, paired with prompts/rubric.md. Used when no
# GeneratedRubric is supplied, which keeps scripts/evaluate.py reproducible
# against the corpus these were calibrated on.
#
# client_communication runs low for nearly everyone -- mean 1.00 vs 7.55
# and 6.39 for the other two, on candidates the corpus labels `advance`.
# Most resumes never document client-facing work, and this persona reads
# that silence close to disqualifying rather than neutral, which drags
# every composite down. A fairer version (silence -> mid-scale, not near-
# zero) was built and measured: client_communication's own numbers
# improved (mean 0.60 -> 3.34, zeros 35/60 -> 0/60) but corpus macro-F1
# fell 0.880 -> 0.796 at each version's own best cutoffs. Reverted --
# accuracy on the only evidence available (this corpus) was kept over a
# more defensible reading of an individual resume. See docs/SCORE_SCALE.md
# for the full numbers and the caveat that the archetypes were generated
# with an intended client_communication level, so this persona's harshness
# specifically correlates with the answer key -- a real applicant may be
# judged more harshly here than the corpus comparison implies.
_PANEL_PERSONAS = {
    "production_reality": "You judge whether the evidence describes systems "
    "that shipped and are used in production, versus research, coursework, "
    "or proof-of-concept work that stopped at the demo stage. This posting "
    "explicitly wants production experience, not demos -- weight it heavily. "
    "Be skeptical of buzzwords; a tool named without a sentence describing "
    "what it did is not evidence.",
    "technical_integration": "You judge hands-on depth building agentic "
    "systems (memory, tools, orchestration) and integrating AI into real "
    "APIs, business systems, or automation platforms on cloud-native or "
    "hybrid infrastructure. Evidence must describe what they built, not a "
    "skills line.",
    "client_communication": "You judge evidence of explaining technical work "
    "to non-technical audiences, cross-functional collaboration (engineering, "
    "sales, delivery), or direct client engagement. This is the hardest "
    "signal to find in a typical resume -- its absence is not automatically "
    "disqualifying, but this posting names it as a required skill, so its "
    "presence is a genuine differentiator.",
}


DEFAULT_MODEL_IDS = {
    "triage": "claude-haiku-4-5-20251001",
    # GPT-5.6 Luna, not Sonnet 5. Measured on the full 60-resume corpus
    # (docs/CUTOFF_FIT.md, docs/BAKEOFF.md), each model given cutoffs
    # fitted to its own scale and tested on folds it had not seen:
    #
    #                   macro-F1   review queue   escalation   cost/60
    #   claude-sonnet-5   0.857         30%           5%        $0.84
    #   gpt-5.6-luna      0.853         15%          23%        $0.31
    #
    # Same accuracy inside a 0.051 noise band, half the human review
    # queue, a third of the cost, and 0 parse failures in 180 panel calls
    # against Sonnet's 5. Sonnet keeps two advantages: p50 latency 11s vs
    # 13s, and a lower escalation rate.
    #
    # Under a single global cutoff pair this arm looked 0.26 WORSE. That
    # was calibration, not judgment -- see MODEL_CUTOFFS in core/cutoffs.py.
    "panel": "gpt-5.6-luna",
    # Sonnet, not Opus. The arbiter adjudicates between three
    # rationales already written for it -- reading and choosing,
    # not fresh analysis. Measured on the recorded run it was ~57%
    # of total spend while running on 55% of candidates, because
    # Opus output is 15x Haiku and 5x Sonnet. See PLAN.md 3g.
    #
    # Now matched to the panel: the arbiter adjudicates between panel
    # rationales, so it must read them on the same scale the panel wrote
    # them on. A Sonnet arbiter ruling on Luna scores would be judging a
    # 4.6-mean distribution with 2.4-mean instincts.
    "arbiter": "gpt-5.6-luna",
    # Writing the rubric sets the standard every later score is judged
    # against, and it runs once per batch rather than once per resume.
    # It is the cheapest place in the cascade to buy the best model.
    "rubric": "claude-opus-5",
}


# How to reach a model that is not Anthropic. Anything absent from this
# table is built as an AnthropicModel against ANTHROPIC_API_KEY.
#
# This is production wiring and is deliberately separate from
# config/bakeoff.json, which exists to make experiments cheap to add. A
# model only lands here once a bake-off has earned it a place.
MODEL_PROVIDERS: dict[str, dict] = {
    "gpt-5.6-luna": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "token_param": "max_completion_tokens",
        "send_temperature": False,
        # "low", not "medium". Measured 2026-08-31 over 3 runs of 60:
        #
        #             macro-F1              out-tokens   p50      cost
        #   medium  0.847 (0.804-0.884)       74,617    13.5s    $0.310
        #   low     0.872 (0.832-0.901)       65,469    11.3s    $0.299
        #
        # Accuracy is unchanged -- the +0.025 sits inside the 0.051 noise
        # band -- but the paired test over the same 60 resumes has low
        # ahead 9 to 6, so it is certainly not worse. 12% fewer output
        # tokens and 16% faster.
        #
        # Worth recording that the predicted win did NOT arrive. Output is
        # 69% of the bill and ~75% of it is reasoning, so effort looked
        # like a 30-50% cost lever. It moved cost 3.5%. The reasoning
        # budget shrank far less than "low" suggests.
        "extra_body": {"reasoning_effort": "low"},
    },
}


def _build_model(model_id: str) -> Model:
    spec = MODEL_PROVIDERS.get(model_id)
    if spec is None:
        try:
            return AnthropicModel(model_id, os.environ["ANTHROPIC_API_KEY"])
        except KeyError:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it, or pass an explicit "
                "`models` dict to screen_one/rank_all (tests do this)."
            ) from None
    try:
        api_key = os.environ[spec["api_key_env"]]
    except KeyError:
        raise RuntimeError(
            f"{spec['api_key_env']} is not set, and it is required for "
            f"{model_id!r}. Note that evidence extraction still runs on "
            "Haiku, so ANTHROPIC_API_KEY is needed as well."
        ) from None
    return OpenAICompatibleModel(
        model_id,
        api_key,
        spec["base_url"],
        token_param=spec.get("token_param", "max_tokens"),
        send_temperature=spec.get("send_temperature", True),
        extra_body=spec.get("extra_body") or {},
    )


def default_models(overrides: dict[str, str] | None = None) -> dict[str, Model]:
    """The four model slots, each an independent knob.

    `overrides` swaps individual slots (e.g. `{"panel": "claude-haiku-4-5-
    20251001"}`) for the tier bake-off in PLAN.md section 8 -- comparing
    what cheaper models cost the pipeline in accuracy, without touching
    the caching contract, the escalation logic, or anything else that
    lives downstream of "which model answered this call".
    """
    model_ids = {**DEFAULT_MODEL_IDS, **(overrides or {})}
    return {slot: _build_model(model_id) for slot, model_id in model_ids.items()}


def _panel_prefix(job_description: str, rubric: GeneratedRubric | None = None) -> str:
    """The cacheable system prefix -- see the caching contract in the module
    docstring. Identical for every panel call in a batch, by construction.

    `rubric=None` uses the hand-written rubric anchored to
    docs/job_description.md.
    """
    body = rubric.markdown if rubric is not None else RUBRIC
    return f"{body}\n\n---\n\nJob description:\n{job_description}"


def _personas_for(rubric: GeneratedRubric | None) -> dict[str, str]:
    return _PANEL_PERSONAS if rubric is None else rubric.personas


def hand_written_personas() -> dict[str, str]:
    """The default panel: agent name -> that agent's brief.

    Public because adapters need to *display* the criteria behind a run
    that used the built-in rubric, not just the generated ones. Returns a
    copy so a caller cannot reach in and edit the panel.
    """
    return dict(_PANEL_PERSONAS)


# A \u escape the model never finished emitting, at the very end of a cut
# fragment. Anchored to the end so a complete é mid-string is untouched.
_RE_PARTIAL_ESCAPE = re.compile(r"\\u[0-9a-fA-F]{0,3}$")


def _close_unterminated(fragment: str) -> str | None:
    """Add the closers an unfinished JSON fragment is missing.

    Returns None if the fragment is already balanced (nothing to repair)
    or is too broken to repair safely.

    This exists because of a measured, intermittent model behaviour: the
    response ends with `stop_reason="end_turn"` and well under the token
    budget, having closed its final string but never emitted the closing
    brace. Roughly 3% of panel calls in the recorded eval run were thrown
    away that way, each becoming a spurious 0.0. The score is right there
    in the text -- refusing to read it is a self-inflicted wound.
    """
    stack: list[str] = []
    in_string = False
    escaped = False

    for char in fragment:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]" and (
            not stack or (stack.pop(), char) not in (("{", "}"), ("[", "]"))
        ):
            return None  # mismatched, not merely unfinished

    if not stack and not in_string:
        return None

    repaired = fragment[:-1] if escaped else fragment
    if in_string:
        # A cut can land inside a \uXXXX escape, leaving something like
        # "\u12" that no amount of closing braces will make parseable.
        repaired = _RE_PARTIAL_ESCAPE.sub("", repaired)
        repaired += '"'
    repaired += "".join("}" if opener == "{" else "]" for opener in reversed(stack))
    return repaired


def _parse_json(text: str, *, expect: str = "object") -> dict | list | None:
    """Best-effort extraction of a JSON value from a model response.

    Returns None rather than raising -- callers decide what a failed parse
    means for their tier, since 'the model returned junk' is a real runtime
    condition, not an exceptional one.

    Tries the well-formed reading first, then repairs an unterminated one.
    A repaired value can be missing fields the model never got to emit, so
    callers must still validate what they actually need -- _panel_agent
    treats a missing score as a failure rather than a zero.
    """
    open_c, close_c = ("{", "}") if expect == "object" else ("[", "]")
    start = text.find(open_c)
    if start == -1:
        log.warning("No JSON %s found in model response: %.200s", expect, text)
        return None

    # strict=False tolerates raw newlines and tabs inside strings. Models
    # emit them in long rationales, and rejecting the whole response over
    # an unescaped newline throws away a perfectly good score.
    end = text.rfind(close_c)
    if end > start:
        try:
            return json.loads(text[start : end + 1], strict=False)
        except json.JSONDecodeError:
            pass  # fall through to repair -- a closer may sit inside a string

    repaired = _close_unterminated(text[start:])
    if repaired is not None:
        try:
            value = json.loads(repaired, strict=False)
        except json.JSONDecodeError:
            pass
        else:
            log.info("Recovered an unterminated JSON %s from the model.", expect)
            return value

    log.warning("Malformed JSON in model response: %.200s", text)
    return None


def _coerce_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _maybe_float(value) -> float | None:
    """float(value), or None if it isn't a number at all.

    Distinct from _coerce_float because for a panel score the difference
    between "the model said 0" and "the model said nothing usable" is
    load-bearing -- see _panel_agent.
    """
    if isinstance(value, bool):  # bools are ints; a True score is not a score
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def extract_candidate(
    resume_path: str, model: Model
) -> tuple[ExtractedCandidate, Usage]:
    """Tier 0: cheap structured extraction. This is the object
    query_candidates later filters and reasons over, so it must carry
    evidence, not just facts.
    """
    raw_text = load_resume_text(resume_path)
    system = (
        "Extract structured facts from this resume as JSON with keys: "
        "name, years_experience (number), companies (list of str), "
        "technologies (list of str), education (list of str), "
        "evidence (list of {quote, rubric_dimension}), confidence (0-1). "
        "Evidence quotes must be verbatim from the resume."
    )
    response = await model.complete(system, raw_text, max_tokens=EXTRACT_MAX_TOKENS)
    data = _parse_json(response.text) or {}

    evidence = []
    for item in data.get("evidence") or []:
        if isinstance(item, dict) and item.get("quote"):
            evidence.append(
                Evidence(
                    quote=str(item["quote"]),
                    rubric_dimension=str(item.get("rubric_dimension", "unspecified")),
                )
            )

    candidate = ExtractedCandidate(
        source_path=resume_path,
        name=str(data.get("name") or Path(resume_path).stem),
        years_experience=_coerce_float(data.get("years_experience"), 0.0),
        companies=[str(c) for c in (data.get("companies") or [])],
        technologies=[str(t) for t in (data.get("technologies") or [])],
        education=[str(e) for e in (data.get("education") or [])],
        evidence=evidence,
        # A failed parse is genuinely low-confidence, not average-confidence.
        confidence=_coerce_float(data.get("confidence"), 0.0 if not data else 0.5),
        raw_text=raw_text,
    )
    return candidate, response.usage


def _unwrap_panel_score(data: dict, name: str, siblings: frozenset[str]) -> dict:
    """Find this agent's object when the model wrapped it in an envelope.

    Asked to score one dimension, weaker models routinely answer with a
    well-formed object that simply is not the shape requested:

        {"production_reality": {"score": 9, "rationale": "..."}}
        {"result": {"score": 9, ...}}

    That is valid JSON with no top-level `score`, so it used to count as a
    parse failure and the score was thrown away. Measured on the
    2026-08-27 bake-off, **60 of 78 Haiku panel failures were this shape**
    -- the model had done the work and the parser discarded it. PLAN.md
    section 8a rejected an all-Haiku panel over "unparseable JSON" on
    exactly this evidence; the JSON parsed fine.

    Matching is deliberately conservative, because the cheap wrong move
    here is to award this agent a score another agent wrote:

    - an envelope keyed by THIS agent's name is taken;
    - a single-key envelope is taken only when that key is not one of the
      sibling agents -- a lone `{"client_communication": ...}` returned to
      the `production_reality` agent is a real error, not a wrapper;
    - anything else is left alone and still fails.
    """
    if _maybe_float(data.get("score")) is not None:
        return data

    named = data.get(name)
    if isinstance(named, dict) and _maybe_float(named.get("score")) is not None:
        return named

    if len(data) == 1:
        (key, value), = data.items()
        if (
            isinstance(value, dict)
            and key not in siblings - {name}
            and _maybe_float(value.get("score")) is not None
        ):
            return value

    # Flat variant: {"production_reality_score": 9, "rationale": "..."}.
    flat = data.get(f"{name}_score")
    if _maybe_float(flat) is not None:
        return {**data, "score": flat}

    return data


async def _panel_agent(
    name: str,
    lens: str,
    candidate: ExtractedCandidate,
    job_description: str,
    model: Model,
    rubric: GeneratedRubric | None = None,
    siblings: frozenset[str] = frozenset(),
) -> tuple[RubricScore, Usage]:
    evidence_json = json.dumps(
        [{"quote": e.quote, "rubric_dimension": e.rubric_dimension} for e in candidate.evidence]
    )
    user = (
        f"Your specific lens: {lens}\n\n"
        f"Candidate evidence:\n{evidence_json}\n\n"
        "Respond as JSON: {score (0-10), rationale}. "
        "The rationale must be ONE sentence that quotes verbatim the single "
        "piece of resume evidence that decided your score. No preamble, no "
        "summary of the resume, no second sentence."
    )
    response = await model.complete(
        _panel_prefix(job_description, rubric), user, max_tokens=PANEL_MAX_TOKENS
    )
    data = _parse_json(response.text) or {}
    if not isinstance(data, dict):
        data = {}
    # Recover this agent's object when the model wrapped it in an envelope
    # keyed by dimension name. Conservative by design -- see the docstring.
    data = _unwrap_panel_score(data, name, siblings)

    # A missing score must not become a confident-looking 0.0. The failure
    # this guards against is real and observed: asked for one dimension,
    # the model sometimes answers for all of them at once, keyed by
    # dimension name. _unwrap_panel_score recovers the cases that can be
    # attributed to THIS agent safely; what is left really is unusable, and
    # scoring it 0.0 would silently reject a candidate on a number no agent
    # ever assigned -- and, because the parse "succeeded", would not flag
    # the verdict for human review.
    score_value = _maybe_float(data.get("score"))
    if score_value is None:
        log.warning(
            "Panel agent %s returned no usable score (truncated=%s): %.200s",
            name,
            response.truncated,
            response.text,
        )

    score = RubricScore(
        agent_name=name,
        score=score_value if score_value is not None else 0.0,
        rationale=str(data.get("rationale") or "No rationale returned."),
        parse_failed=score_value is None,
    )
    return score, response.usage


async def _arbitrate(
    candidate: ExtractedCandidate,
    panel: list[RubricScore],
    job_description: str,
    model: Model,
    rubric: GeneratedRubric | None = None,
) -> tuple[float, str, Usage]:
    """Resolve a split panel into one score.

    The arbiter no longer returns a recommendation. It used to, and the
    pipeline used it directly, which meant the verdict for a given score
    depended on whether that candidate happened to escalate: an
    unescalated 6.5 was mapped by the cutoffs, an escalated 6.5 was
    whatever the arbiter said. Two candidates, same score, different
    answers, decided by a coin flip they had no part in.

    Now there is one place that turns a score into a verdict --
    recommendation_from_score -- and the arbiter does the job it is
    actually good at, which is reconciling three disagreeing scores into
    one number.
    """
    user = (
        "The scoring panel disagreed on this candidate. Read their rationales "
        "and resolve the disagreement into a single score.\n\n"
        f"Panel scores:\n{json.dumps([p.to_dict() for p in panel])}\n\n"
        "Respond as JSON: {score (0-10), rationale}. The rationale must be "
        "AT MOST TWO SENTENCES -- state what decided the score, quoting the "
        "single most important piece of evidence. Do not restate each "
        "panelist in turn. Do not recommend a hiring decision; score the "
        "evidence and the cutoffs will map it."
    )
    response = await model.complete(
        _panel_prefix(job_description, rubric), user, max_tokens=ARBITER_MAX_TOKENS
    )
    data = _parse_json(response.text) or {}

    score = _coerce_float(data.get("score"), statistics.mean([p.score for p in panel]))
    rationale = str(data.get("rationale") or "Arbiter returned no rationale.")
    return score, rationale, response.usage


def recommendation_from_score(
    score: float, cutoffs: Cutoffs | None = None
) -> Recommendation:
    """Score -> verdict. The single place a recommendation is decided.

    `cutoffs=None` keeps the historical global pair, so every existing
    caller and every recorded run is unaffected.
    """
    bounds = cutoffs or DEFAULT_CUTOFFS
    if score >= bounds.advance:
        return Recommendation.ADVANCE
    if score >= bounds.hold:
        return Recommendation.HOLD
    return Recommendation.REJECT


def _verdict_is_in_doubt(
    scores: list[float], cutoffs: Cutoffs | None = None
) -> bool:
    """Could an arbiter ruling actually change the verdict?

    Only if the agents do not already agree on which bucket the candidate
    falls in. A panel of 9.0/7.0/6.0 has a spread of 3.0 and escalates
    under the threshold alone, but all three of those scores mean
    "advance" -- there is no ruling the arbiter could return that changes
    the answer, so the call is pure cost.

    Measured on the recorded run: 7 of 33 escalations were this case,
    including two candidates where every agent scored 6.0 or higher.

    Spread measures variance. This measures decision uncertainty, which is
    the thing actually worth paying to resolve. Both must hold.
    """
    return len({recommendation_from_score(s, cutoffs) for s in scores}) > 1


SINGLE_PASS_MAX_TOKENS = 4000


async def screen_one_single_pass(
    resume_path: str,
    job_description: str,
    models: dict[str, Model] | None = None,
    rubric: GeneratedRubric | None = None,
) -> Verdict:
    """The control arm: one call scores all three dimensions at once.

    This exists to test the cascade's own justification. `screen_one`
    makes 4-5 calls per resume (extract, three panel agents in parallel,
    sometimes an arbiter) and the entire argument for that cost is that
    it beats asking one model once. That was asserted for the life of
    this project and never measured. PLAN.md section 8.

    Deliberately kept as close to the cascade as possible so the
    comparison isolates ARCHITECTURE rather than prompt quality:

    - Same cached system block (`rubric + job_description`), so the
      caching contract and the standard being scored against are
      identical.
    - Same extraction step, on the same model. Feeding this arm the raw
      resume while the cascade gets curated evidence would confound the
      shape of the pipeline with the quality of its input.
    - Same personas, verbatim, concatenated into one user turn instead of
      split across three calls.
    - Same cutoffs and the same `recommendation_from_score`.

    So the ONLY difference is whether the three dimensions are judged
    independently or together. The expected weakness of judging them
    together is anchoring: one call sees all three lenses at once and
    cannot help letting a strong answer on one colour the others. Whether
    that costs anything is the question.

    There is no arbiter here, and there is nothing to arbitrate -- a
    single response cannot disagree with itself. Its `panel_spread` is
    therefore 0.0 and it never escalates, which is part of what makes it
    cheap.
    """
    models = models or default_models()
    personas = _personas_for(rubric)

    candidate, usage = await extract_candidate(resume_path, models["triage"])

    evidence_json = json.dumps(
        [{"quote": e.quote, "rubric_dimension": e.rubric_dimension} for e in candidate.evidence]
    )
    lenses = "\n\n".join(f"{name}: {lens}" for name, lens in personas.items())
    user = (
        f"Score this candidate on ALL THREE dimensions below.\n\n"
        f"{lenses}\n\n"
        f"Candidate evidence:\n{evidence_json}\n\n"
        "Respond as JSON: an object whose keys are the three dimension "
        "names above, each mapping to {score (0-10), rationale}. The "
        "rationale must be ONE sentence that quotes verbatim the single "
        "piece of resume evidence that decided that score. No preamble."
    )
    response = await models["panel"].complete(
        _panel_prefix(job_description, rubric), user, max_tokens=SINGLE_PASS_MAX_TOKENS
    )
    usage = usage + response.usage
    data = _parse_json(response.text) or {}
    if not isinstance(data, dict):
        data = {}

    scores: list[RubricScore] = []
    for name in personas:
        entry = data.get(name)
        entry = entry if isinstance(entry, dict) else {}
        value = _maybe_float(entry.get("score"))
        if value is None:
            log.warning(
                "Single-pass response had no usable score for %s: %.200s",
                name,
                response.text,
            )
        scores.append(
            RubricScore(
                agent_name=name,
                score=value if value is not None else 0.0,
                rationale=str(entry.get("rationale") or "No rationale returned."),
                parse_failed=value is None,
            )
        )

    usable = [p.score for p in scores if not p.parse_failed] or [0.0]
    mean_score = statistics.mean(usable)
    cutoffs = cutoffs_for(models["panel"])
    return Verdict(
        candidate=candidate,
        score=mean_score,
        recommendation=recommendation_from_score(mean_score, cutoffs),
        rationale=" | ".join(f"[{p.agent_name}] {p.rationale}" for p in scores),
        panel_scores=scores,
        escalated=False,
        panel_spread=0.0,
        cutoff_distance=distance_to_cutoff(mean_score, cutoffs),
        cutoff_band_width=band_width(cutoffs),
        usage=usage,
    )


async def screen_one(
    resume_path: str,
    job_description: str,
    models: dict[str, Model] | None = None,
    rubric: GeneratedRubric | None = None,
) -> Verdict:
    """Screen one candidate.

    `rubric=None` scores against the hand-written rubric anchored to
    docs/job_description.md. Pass a GeneratedRubric to score against any
    other posting -- see rubric_for().
    """
    models = models or default_models()
    personas = _personas_for(rubric)

    candidate, usage = await extract_candidate(resume_path, models["triage"])

    panel_results = await asyncio.gather(
        *[
            _panel_agent(
                name,
                lens,
                candidate,
                job_description,
                models["panel"],
                rubric,
                siblings=frozenset(personas),
            )
            for name, lens in personas.items()
        ]
    )
    panel = [score for score, _ in panel_results]
    for _, panel_usage in panel_results:
        usage = usage + panel_usage

    # A parse failure is missing data, not a score of zero. Averaging the
    # placeholder 0.0 in fabricates a judgment no agent made: it drags the
    # mean down, inflates the spread, and buys an arbiter call to resolve a
    # "disagreement" with a value that was never an opinion. Observed on a
    # real upload -- one failed agent turned 7.0/2.0 into a 7.0 spread and
    # a 4.5 composite.
    scored = [p for p in panel if not p.parse_failed]
    if scored:
        scores = [p.score for p in scored]
    else:
        # Every agent failed. There is nothing to average, and pretending
        # otherwise would publish a confident 0.0 about a resume the panel
        # never actually read. review_reason already flags this.
        scores = [0.0]
    spread = max(scores) - min(scores) if len(scores) > 1 else 0.0

    cutoffs = cutoffs_for(models["panel"])
    mean_score = statistics.mean(scores)

    # Three conditions, each removing a different kind of wasted call:
    #   spread          -- the agents actually disagree
    #   _verdict_is_in_doubt -- they disagree about the VERDICT, not just
    #                      the number
    #   margin          -- and the mean sits close enough to a cutoff that
    #                      the arbiter could realistically cross it
    #
    # The third is the one that does the work. Measured over 84 recorded
    # escalations, 92% of them returned a different score and the SAME
    # verdict -- the arbiter was being paid to move a number that was
    # never going to cross a line. See ESCALATION_MARGIN in core/cutoffs.py
    # for the movement distribution this threshold comes from.
    if (
        spread > DISAGREEMENT_THRESHOLD
        and _verdict_is_in_doubt(scores, cutoffs)
        and distance_to_cutoff(mean_score, cutoffs) <= ESCALATION_MARGIN
    ):
        score, rationale, arb_usage = await _arbitrate(
            candidate, panel, job_description, models["arbiter"], rubric
        )
        return Verdict(
            candidate=candidate,
            score=score,
            recommendation=recommendation_from_score(score, cutoffs),
            rationale=rationale,
            panel_scores=panel,
            escalated=True,
            panel_spread=spread,
            cutoff_distance=distance_to_cutoff(score, cutoffs),
            cutoff_band_width=band_width(cutoffs),
            usage=usage + arb_usage,
        )

    return Verdict(
        candidate=candidate,
        score=mean_score,
        recommendation=recommendation_from_score(mean_score, cutoffs),
        rationale=" | ".join(f"[{p.agent_name}] {p.rationale}" for p in panel),
        panel_scores=panel,
        escalated=False,
        panel_spread=spread,
        cutoff_distance=distance_to_cutoff(mean_score, cutoffs),
        cutoff_band_width=band_width(cutoffs),
        usage=usage,
    )


async def rubric_for(
    job_description: str, models: dict[str, Model] | None = None
) -> GeneratedRubric:
    """Write a rubric for a posting, using the cascade's rubric model.

    Thin convenience wrapper so callers don't have to know which model
    slot writes rubrics. Call once, then pass the result to rank_all.
    """
    models = models or default_models()
    return await generate_rubric(job_description, models["rubric"])


async def rank_paths(
    paths: Sequence[str],
    job_description: str,
    models: dict[str, Model] | None = None,
    max_concurrent: int = MAX_CONCURRENT_RESUMES,
    rubric: GeneratedRubric | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[Verdict]:
    """Screen an explicit list of resumes, ranked best-first.

    `on_progress(done, total)` fires as each resume finishes, including
    the ones that fail. A caller showing a progress bar needs the count to
    reach `total` regardless of outcome, or the bar stalls forever on a
    batch containing one bad file.
    """
    models = models or default_models()
    semaphore = asyncio.Semaphore(max_concurrent)
    total = len(paths)
    done = 0

    async def _bounded(path: str) -> Verdict | None:
        nonlocal done
        async with semaphore:
            try:
                return await screen_one(path, job_description, models, rubric)
            except Exception:
                # One unreadable resume shouldn't sink a 60-resume batch.
                log.exception("Failed to screen %s", path)
                return None
            finally:
                done += 1
                if on_progress is not None:
                    on_progress(done, total)

    results = await asyncio.gather(*[_bounded(p) for p in paths])
    verdicts = [v for v in results if v is not None]
    return sorted(verdicts, key=lambda v: v.score, reverse=True)


async def rank_all(
    resume_dir: str,
    job_description: str,
    models: dict[str, Model] | None = None,
    max_concurrent: int = MAX_CONCURRENT_RESUMES,
    rubric: GeneratedRubric | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[Verdict]:
    """Screen every resume in a directory, ranked best-first.

    Returns the FULL pool, not a truncated shortlist -- truncation is the
    caller's job. query_candidates has to be able to ask about candidates
    outside the top N, so the session must retain everything.

    `rubric` is resolved once here and reused for every resume, which is
    what keeps the cached panel prefix identical across the batch.
    """
    return await rank_paths(
        iter_resume_paths(resume_dir),
        job_description,
        models,
        max_concurrent,
        rubric,
        on_progress,
    )
