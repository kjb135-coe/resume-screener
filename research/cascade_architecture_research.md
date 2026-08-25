# Is a tiered cascade actually justified, or did we just assume it?

Honest answer: the specific 3-tier, disagreement-triggered design was
proposed by reasoning from first principles, not derived from a paper
about resume screening — no such paper appears to exist yet. What DOES
exist is real, recent research on the general pattern (cascades with
multi-agent deliberation at the escalation boundary) applied to other
classification/QA tasks. Worth being precise about what that research
supports and what it doesn't.

## CascadeDebate (ACL Industry 2026) — closest real precedent

Tested on ARC-Easy, ARC-Challenge, MMLU, MedQA, MedMCQA (1,000 sampled
questions each) — **multiple-choice QA, not resume screening.** Their
architecture: a cascade where multi-agent debate is inserted specifically
at the escalation boundary, so cheap tiers handle confident cases alone
and agent deliberation only activates for uncertain ones.

Measured results against a standard (non-debate) cascade, Llama-3.2:

| Benchmark | Standard cascade | CascadeDebate | Delta |
|---|---|---|---|
| ARC-Easy | 93.90% | 95.33% | +1.4pp |
| ARC-Challenge | 84.30% | 92.89% | +8.6pp |
| MMLU | 67.70% | 82.67% | +15.0pp |
| MedQA | 68.20% | 86.44% | +18.2pp |
| MedMCQA | 64.70% | 76.33% | +11.6pp |

And matched or exceeded a pure multi-agent ensemble's accuracy at
20-35% lower token cost.

**Escalation trigger, precisely** (this is the part most relevant to us):
three signals, not one flat threshold —
1. a learned confidence threshold (accept if confidence clears it)
2. a learned uncertainty/abstention threshold (escalate if it doesn't)
3. agent agreement rate, specifically for multi-agent stages — high
   agreement resolves ambiguity without escalating further

And critically: the thresholds are **learned from feedback per task**,
not fixed constants picked in advance.

## What this means for our design, honestly

- The *shape* of what we proposed — cheap triage, escalate only on
  disagreement, reserve the expensive tier for contested cases — matches
  a real, currently-published, Pareto-dominant pattern. That's a
  legitimate thing to cite.
- The specific number I used (`DISAGREEMENT_THRESHOLD = 2.0` on a 0-10
  scale) was picked arbitrarily, not calibrated. CascadeDebate's result
  specifically shows a *fixed* threshold is the weaker version of this
  pattern — theirs is learned per-task from data. We should calibrate
  ours empirically against the labeled synthetic corpus rather than
  hand-pick it, once that corpus exists.
- The domain gap (QA benchmarks vs. resume scoring) means we cannot
  claim "research proves this works for resume screening" — only that
  the general architecture is well-supported for LLM classification
  tasks broadly, and resume scoring is a reasonable candidate for the
  same pattern, not a proven one. Our own eval harness is what actually
  validates it for this domain.

## Alternatives worth weighing, not yet decided between

1. **Single-model, single-pass** — one Sonnet call per resume, all
   rubric dimensions in one prompt. Cheapest to build, no disagreement
   signal, no interpretability into *why* two dimensions might conflict.
2. **Flat ensemble, no cascade** — always run all N agents on every
   resume, average or vote. What CascadeDebate is explicitly shown to
   beat on cost, at comparable accuracy — but simpler to reason about
   and easier to explain to a non-technical panel.
3. **Embedding pre-filter before any generative call** — embed the JD's
   required skills and each resume, cosine-similarity filter obvious
   non-matches at near-zero cost before spending any LLM tokens at all.
   This could sit *under* Tier 0, not replace it — worth testing as an
   addition regardless of what we decide for the panel/arbiter design.
4. **Whole-batch long-context ranking** — one call, all N resumes and
   the JD in context, ask for a ranked list directly. Captures relative
   comparison naturally (a real strength — our per-resume approach never
   sees other candidates), but evidence-per-candidate gets harder to
   pin down reliably, and it doesn't scale past context limits.
5. **Our original proposal** — 3-persona panel (depth/trajectory/
   skeptic), escalate to an arbiter only on disagreement.

Open question worth testing empirically rather than assuming: does a
3-persona panel actually produce better-calibrated disagreement signal
than one well-prompted agent asked to reason through all three lenses
in a single call? That's exactly the kind of thing the eval harness
should answer, not something to assert.

## Sources

- [CascadeDebate: Multi-Agent Deliberation for Cost-Aware LLM Cascades (ACL 2026)](https://aclanthology.org/2026.acl-industry.93.pdf)
- [CascadeDebate — arXiv](https://arxiv.org/html/2604.12262v1)
- [AutoRelAnnotator: Calibrated Model Cascades](https://arxiv.org/pdf/2606.25871)
