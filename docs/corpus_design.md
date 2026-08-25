# Synthetic corpus design

60 fictional resumes with ground-truth labels, used to measure screening
accuracy. No real people, no scraped data, nothing that could identify
anyone — the whole corpus ships in the repo.

## Why generation is label-driven

The archetype and its target verdict are defined **first**, and the
generator is told to write a resume matching that spec. Ground truth is
the *input* to generation, never inferred from the output afterward.

Generating resumes freely and then labeling them would measure agreement
between two model passes, not accuracy. It would also leak the scorer's
own biases into the answer key — if both used the same reasoning, the
system would score suspiciously well against a test it effectively wrote.

## The three dimensions being varied

Every archetype targets an explicit level (high / medium / low) on each
rubric dimension, so no dimension can be quietly ignored by a scorer that
happens to do well on the other two.

- **prod** — production reality: shipped systems with real users, on-call,
  monitoring, iteration after launch. Not demos or coursework.
- **tech** — technical/integration depth: agentic systems (memory, tools,
  orchestration), LLM work, integration into real APIs and business
  systems on cloud infrastructure.
- **client** — client-facing and cross-functional signal: explaining
  technical work to non-technical audiences, working with sales/delivery,
  direct client engagement.

## Archetypes

| # | Archetype | Label | prod | tech | client | n |
|---|---|---|---|---|---|---|
| 1 | Production AI generalist | advance | H | H | H | 7 |
| 2 | Strong builder, quiet communicator | advance | H | H | L | 7 |
| 3 | Adjacent-domain shipper (ML infra → agents) | advance | H | M | M | 6 |
| 4 | Demo-stage specialist | hold | L | H | M | 7 |
| 5 | Production engineer, light AI | hold | H | L | M | 7 |
| 6 | Early-career, thin but real | hold | M | M | L | 6 |
| 7 | Keyword stuffer | reject | L | L | L | 7 |
| 8 | Wrong domain | reject | M | L | L | 7 |
| 9 | Academic researcher | reject | L | M | L | 6 |

20 advance / 20 hold / 20 reject.

## What each archetype must and must not contain

**1. Production AI generalist — advance.** Shipped agentic systems with
named scale figures and on-call ownership; integrations into real business
systems; at least one instance of presenting to non-technical stakeholders
or working directly with clients. 4–7 years. The unambiguous yes.

**2. Strong builder, quiet communicator — advance.** Same production and
technical strength as #1, but zero client-facing or cross-functional
evidence — purely heads-down engineering. **Tests that a missing
`client_communication` signal is treated as a non-differentiator rather
than a disqualifier**, which is what the rubric says should happen. If
these systematically land in `hold`, the rubric is over-weighting that
dimension.

**3. Adjacent-domain shipper — advance.** Came from ML infrastructure,
data platform, or backend, and has genuinely shipped agent/LLM systems in
the last 1–2 years. Deep production credibility, moderate agentic depth.
Tests whether the scorer credits real transferable production experience
instead of pattern-matching on job titles.

**4. Demo-stage specialist — hold.** Technically impressive and current —
RAG pipelines, multi-agent frameworks, fine-tuning — but every project is
a prototype, hackathon, side project, or internal POC. **No evidence of
anything reaching real users.** This is the single most important
discriminator in the corpus: the posting explicitly says "not demos or
prototypes, but systems used in production." If these score as `advance`,
the `production_reality` dimension isn't working.

**5. Production engineer, light AI — hold.** Strong, real production
history — APIs, distributed systems, cloud, on-call — with only peripheral
AI exposure (called an LLM API once, shipped a small classifier). The
mirror image of #4, and it catches the opposite failure: a scorer that
rewards "shipped things" without checking the work is actually AI work.

**6. Early-career, thin but real — hold.** 1–3 years. Real production
contribution, but narrow scope and clearly not owning systems yet. Below
the posting's 3–6+ year band without being unqualified. Genuinely
ambiguous by construction — `hold` is the correct label for ambiguous.

**7. Keyword stuffer — reject.** Dense skills sections naming every
current tool (LangChain, RAG, MCP, vector DBs, agents, fine-tuning), but
**every bullet is a noun phrase with no verb describing what was built**.
Titles inflated relative to described substance. Tests the rubric's own
rule that a named tool without a sentence describing what it did is not
evidence.

**8. Wrong domain — reject.** Competent and legitimately experienced, in
something else entirely: frontend, data analytics, IT ops, QA. May mention
"AI" once in passing. Tests basic relevance filtering — and these should
be the cheapest rejections in the whole corpus, ideally caught before any
expensive scoring runs.

**9. Academic researcher — reject.** PhD or research-track, publications,
citations, benchmark results, novel architectures. Real intellectual
depth, but no production deployment, no business integration, no
client-facing work. Rejected for *fit*, not for quality — the posting
wants a solutions engineer. If these score `advance`, the scorer is
rewarding prestige over the actual role.

## Guarding against surface-feature shortcuts

Generation deliberately varies things that must not correlate with the
label, so the scorer can't take a shortcut that looks like accuracy:

- **Length** — strong and weak resumes both span short and long. Otherwise
  "longer = better" scores well for the wrong reason.
- **Formatting** — section order varies; some use bullets, some prose;
  some include a summary, some don't.
- **Names and demographics** — varied fictional names, drawn independently
  of the label so no name pattern predicts the verdict. We are *not*
  currently testing for name-based bias; that's a documented limitation,
  not a solved problem.
- **Company recognizability** — invented company names throughout, mixed
  across all labels, so brand prestige can't stand in for evidence.

## No prompt injections

The corpus contains none. Injection defense is documented and designed
for, but tested separately if at all — deliberately excluded here so that
accuracy numbers measure screening quality and nothing else.

## Format

All 60 as Markdown. Five of those same 60 are **additionally** rendered as
PDF (same candidates, both formats) to exercise the `pypdf` extraction
path. The PDF five span multiple labels so format never correlates with
outcome.

## Mechanics

`scripts/generate_corpus.py`:

- Reads archetype specs, calls a cheap model once per resume.
- Writes `data/synthetic_resumes/<id>_<archetype>.md` and appends ground
  truth to `data/labels.json`.
- Idempotent — skips resumes that already exist; `--force` regenerates.
- `--limit N` to generate a handful first and eyeball quality before
  committing to all 60.
- The shared instruction block is identical across calls and cached, so
  most input tokens are billed at the cached rate.

Estimated cost: roughly 1,200 input + 700 output tokens per resume, 60
resumes, on a cheap model — under a dollar total. Exact pricing gets
verified before the full run.
