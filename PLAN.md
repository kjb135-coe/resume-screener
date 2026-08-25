# Resume Screener — Project Plan

Living status doc. Three honest buckets: **settled** (decided, with the
actual reasoning), **built** (code that exists — separate from whether
it's been run), and **open** (still needs a real decision or a missing
piece before we can move on).

---

## 1. Goal and hard constraints — settled

- Public GitHub repo + a demo link/video, sent as a follow-up after a
  second-round interview for a remote AI solutions engineering role.
- Standalone repo, not a folder inside the private nanobot monorepo —
  **done**, live at https://github.com/kjb135-coe/resume-screener,
  public, single commit, author `kjb135-coe` only, no Claude/Anthropic
  attribution anywhere in git history.
- Rubric and scoring are built against this specific posting
  (`docs/job_description.md`), not a generic AI-engineer template.
- Microsoft and ADP integration: deprioritized per explicit instruction
  — documented as a mapping (Copilot/VS Code MCP support, Claude models
  GA in Microsoft Foundry, ADP as an undone extension point), not a
  build focus right now.

## 2. Architecture — settled shape, specific config still open (see §8)

- One shared core library (`core/`), with CLI, web UI, and MCP server
  as thin adapters over it. No adapter contains scoring logic.
- MCP is the primary interface — the recruiter talks to an AI client
  they already have, rather than adopting a new app. Web UI is a demo
  instrument for the three evaluators, not the production design.
- Four MCP tools, one per action: `screen_resume`, `rank_pool`,
  `explain_verdict`, `query_candidates`.
- MCP scope: **server-only** for the demo. `core/enrichment.py`
  documents the client-consuming extension point (e.g. verifying a
  candidate's GitHub profile via an external MCP server) without a
  live third-party dependency in the demo path.
- Transport: stdio for local/dev, Streamable HTTP for the real hosted,
  multi-client deployment. Only stdio is wired up in code today.
- The tiered cascade concept — cheap extraction, a panel of judgment
  agents, an arbiter that only runs on disagreement — is settled as a
  *shape*. Whether it actually beats a simpler design is an open,
  three-way bake-off, see §8.
- `query_candidates` composes two general primitives per question:
  a sandboxed structured-query engine (DuckDB, generated SQL, never
  `eval`/`exec`) and an evidence-judgment LLM call, capped to a bounded
  answer. This split does double duty as a real defense against resume
  prompt injection, not just a cost optimization.

## 3. Rubric — settled

Three JD-anchored personas replaced the earlier generic depth/
trajectory/skeptic panel:

| Persona | What it checks | Why |
|---|---|---|
| `production_reality` | Shipped/production evidence vs. demo-stage work | JD explicitly repeats "not demos or prototypes, but systems used in production" |
| `technical_integration` | Agentic systems (memory, tools, orchestration) + real API/business-system integration | JD's own phrase, used verbatim |
| `client_communication` | Cross-functional/client-facing evidence | JD names this explicitly as a required skill; rare in resumes, treated as a differentiator not a requirement |

The old "skeptic" instinct (don't credit unbacked claims) is a shared
instruction across all three personas, not a fourth persona — kept
deliberately to avoid preempting the still-open agent-count question.

## 4. Human-in-the-loop and security — settled as design, partially built

- No MCP tool can take a real-world action — all four only ever return
  information. That boundary defends against prompt injection *and*
  keeps a human in the loop on hiring decisions; same design choice,
  two motivations.
- `Verdict.escalated` is surfaced as `needs_human_review` +
  `review_reason` in every tool's output, and `rank_pool` reports a
  `needs_human_review_count`. **Built.**
- Known blind spot, not yet mitigated in code: disagreement-based
  escalation can't catch a panel that's unanimously and confidently
  wrong for a shared/correlated reason. Documented fix is a governance
  practice (audit a sample of confident unanimous rejects too) —
  belongs in `LIMITATIONS.md`, which **does not exist yet.**

## 5. Cost/latency measurement — methodology settled, nothing implemented

- Real pricing (verified, not assumed): cache reads are a 90% discount,
  writes cost 1.25x (5-min TTL) or 2x (1-hour TTL) base price —
  caching has a real breakeven, isn't automatically a win.
- Methodology: run the same batch cached and uncached, sum the actual
  `usage.cache_read_input_tokens`/`cache_creation_input_tokens` the API
  returns, report the measured delta. Latency as p50/p95, not mean,
  compared against a flat "everything hits all three tiers" run.
- **Nothing here is implemented.** No per-call usage logging exists in
  `pipeline.py` yet — this needs to be added before any real number can
  be produced.

## 6. Local and embedding models — settled

- Full generative models (Ollama): implemented behind the same
  `Model` interface as Anthropic (`core/router.py`), explicitly kept
  off the demo path — your GTX 970 (Maxwell, 4GB) genuinely can't do
  this workload justice. Documented as the on-prem/PII-residency story
  instead.
- Embeddings are a different, much lighter workload and a genuinely
  good local fit even on this hardware: `sentence-transformers` with
  `all-MiniLM-L6-v2`, matching the already-validated choice from your
  StoneStepper project rather than the `nomic-embed-text` I first
  suggested. No persistent vector store needed at this scale — computed
  fresh per `rank_pool` call, discarded after. **Not built yet.**

## 7. What's actually built vs. designed-only (read this before assuming progress)

**Exists as real code:**
`core/models.py`, `core/router.py` (Anthropic + Ollama, temperature
bug now fixed), `core/ingest.py`, `core/pipeline.py` (Tier 0/1/2 logic,
using the JD-anchored personas), `core/query.py` (the two-primitive
query design), `core/enrichment.py` (documented stub),
`adapters/mcp_server.py` (all 4 tools), `prompts/rubric.md`.

**Explicitly does not exist yet:**
- `adapters/api.py` (web UI backend) and `adapters/cli.py` — zero code.
- Any test at all — `tests/` is empty.
- The synthetic resume corpus — `data/synthetic_resumes/` is empty,
  no archetypes generated, no ground-truth labels.
- Any actual execution — dependencies have never been installed in a
  venv, no API call this project has written has ever actually run.
  Everything is syntax-checked, not behavior-checked.
- `docs/ARCHITECTURE.md`, `docs/LIMITATIONS.md` — referenced by the
  README, don't exist.
- The embedding pre-filter, the pydantic validation fix for
  `_parse_json`, any usage/cost logging, any web UI, any demo
  recording, any deployment.

This isn't a criticism of pace — it reflects a deliberate choice to go
deep on research and design correctness before writing more code that
might need to be redone. Flagging it plainly so the plan reads as
accurate, not further ahead than it is.

## 8. Testing and evaluation — ironed out 2026-08-25

Some of this borrows structure from a prior project's ablation study
(`research/stonestepper_ablation_review.md` has the full detail) but
this is now our own list, scoped to what's actually worth testing here
— not a re-run of that methodology for its own sake.

### Corpus size — settled

**60 synthetic resumes**, balanced ~20 each across advance/hold/reject,
with 2-3 distinct archetype flavors inside each class (e.g. "reject"
covers keyword-stuffed, wrong-domain, and genuinely underqualified
separately, not one generic "bad resume" template) so the rubric gets
stress-tested on *why* something fails, not just that it does. No
mandatory train/test split — nothing here trains a model. The one
exception is noted below under the k-NN candidate.

### The list

1. **Self-consistency check — cut.**

2. **Keyword-only floor baseline — cut**, per instruction. Single-pass
   (item 4 below) replaces it as the floor — a better one, since a
   pure keyword match was never going to be a fair comparison for a
   judgment this nuanced (production-vs-prototype isn't a keyword you
   can grep for).

3. **Prompt variant (direct vs. chain-of-thought vs. structured rules)
   — cut**, and I agree with cutting it. Our rubric prompts are already
   closer to StoneStepper's "structured criteria" variant than its bare
   baseline — each persona already gets explicit, named criteria, not
   a loose "classify this." The axis that mattered for their simpler
   3-class email problem has less headroom left for us to gain from.
   Worth stating plainly as a deliberate scope cut in the eventual
   limitations doc, not silently dropped — a reviewer could reasonably
   ask "did you test your prompt phrasing," and the honest answer is no.

4. **The architecture candidates — restructured, not just trimmed.**
   Talking through each on its own merits:

   - **Single-pass (one call, all three dimensions)** — keep, as the
     floor. Cheapest possible, and the number the more complex design
     has to actually beat to justify existing.
   - **Flat ensemble (always run all three personas, never escalate)**
     — keep. This is the one that actually tests our core cost claim:
     does disagreement-gating save money without losing accuracy, or
     were we just adding complexity for a savings that isn't real here?
   - **Our panel + arbiter-on-disagreement** — keep, it's the leading
     design and already built.
   - **Embedding pre-filter** — reclassifying this. It isn't really a
     competing *architecture* — it's orthogonal to all three of the
     above and can sit underneath whichever one wins. Build it once as
     an always-on cheap layer, not as a fourth arm of the bake-off.
   - **Whole-batch long-context ranking — cutting entirely**, not just
     deprioritizing. It structurally conflicts with the per-candidate
     design already built (the session store, `explain_verdict`, the
     human-review flag all assume one `Verdict` per candidate) — giving
     it a fair test would mean building a second, parallel pipeline
     just for the experiment, which isn't worth it for a design we're
     unlikely to adopt anyway.
   - **Embedding k-NN as a standalone scorer — conditional, likely
     cut.** Its whole value depends on having enough labeled examples
     per class for nearest-neighbor voting to mean anything. At 20
     resumes per class, that's thin for a fair train/exemplar-library
     split — I'd lean toward dropping this one too unless the corpus
     size above gets bumped up specifically to support it.

   Net result: **a real 3-way bake-off** (single-pass, flat ensemble,
   panel+arbiter), one always-on layer (embedding pre-filter) that
   applies to all three, and one conditional/likely-cut candidate
   (k-NN) rather than the original six competing designs.

5. **Escalation trigger — kept, confirmed as pure calibration, not a
   design debate.** Right, this needs the numbers played with, not
   decided in the abstract: sweep a handful of disagreement-threshold
   values against the labeled corpus (e.g. 1.0/1.5/2.0/2.5/3.0) and
   look at the tradeoff curve between macro-F1 and how often it
   escalates to a human. Start with the simple score-range version;
   only reach for the fancier three-signal design if the simple one
   demonstrably fails on real cases the corpus surfaces.

6. **Score-to-recommendation cutoffs (currently hardcoded 7/5) — kept,
   same treatment as #5.** Sweep candidate cutoff sets against the
   labeled corpus, pick whichever maximizes macro-F1, rather than
   trusting the hand-picked 7/5 split.

7. **Cost estimate for the whole run plan — kept.** Doing this once
   the scope above is actually locked, not before — pricing out a list
   that's still shifting isn't useful. Coming once corpus generation
   and the 3-way bake-off scope above are final.

### How this gets evaluated

- **Primary metric**: macro-F1 across advance/hold/reject against the
  corpus's ground-truth labels, computed on the auto-scored subset —
  reported *separately* from coverage/escalation-rate, never blended
  into one number.
- **Secondary**: real measured cost per resume (from actual API
  `usage` fields, not estimates) and p50/p95 latency, for the 3-way
  architecture bake-off specifically.
- **Bar for keeping the more complex design over the single-pass
  floor**: the winner needs to beat single-pass's macro-F1 by a real
  margin (proposing +5 macro-F1 points as the bar, open to adjusting)
  — or match it at a materially lower cost. If neither happens, the
  honest conclusion is that the cascade's complexity isn't earning its
  keep, and that's a legitimate result to report, not a failure to hide.

All of this is blocked on the synthetic corpus existing — nothing above
can be measured until those 60 resumes and their labels exist.

## 9. Not started at all

- Synthetic resume corpus generation.
- Web UI and CLI adapters.
- Any tests, any eval harness code.
- `ARCHITECTURE.md`, `LIMITATIONS.md`.
- Demo recordings (MCP-in-Claude-Desktop clip, web UI walkthrough).
- Deployment of the web UI anywhere reachable.
- Exact timeline — mentioned once as "right now," then explicitly
  paused for deeper planning; never re-confirmed.

## 10. Immediate next decision needed

Testing scope is now locked (§8). Next actual step: generate the 60
synthetic resumes and their ground-truth labels — everything else in
§8 is blocked on that existing.
