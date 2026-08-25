# What real ATS / AI resume screening actually scores on (2026)

Research pass, not implementation. Sources at bottom.

## The 9-criteria framework in current use

Modern systems run two layers: a classic ATS parser/keyword matcher first,
then an LLM layer that ranks the survivors semantically. The 9 criteria
the ATS layer scores on:

1. Keyword match
2. Job title alignment
3. Required skills coverage
4. Formatting compatibility (can it even be parsed correctly)
5. Standard section structure
6. Experience recency and depth
7. Education match
8. Certifications
9. Quantified impact (did they attach a number to a result)

The semantic layer on top maps synonyms a naive keyword match would miss
("ML engineer" -> "machine learning", "PyTorch", "TensorFlow").

## Where this exposes a gap in our current rubric

`prompts/rubric.md` currently has 3 dimensions: depth, trajectory,
education. That's narrower than what real systems check. Missing,
worth discussing before we lock the rubric:

- **Quantified impact** as its own signal, separate from "depth" — a
  resume that says "reduced inference latency 40%" is different evidence
  than "worked on inference latency," even if both pass the depth check.
- **Formatting/parseability as a first-class signal, not silently
  swallowed** — Tier 0 already emits a `confidence` field; a low-confidence
  extraction should probably surface to the recruiter as "we couldn't
  read this cleanly," not just quietly produce a worse score.
- **Explicit skill coverage against the JD's stated requirements**,
  separate from "depth" — depth asks "is this real," coverage asks
  "does it match what THIS posting asked for."

None of this is decided yet — flagging it as an open input to the
rubric conversation, not a change I've made.

## Sources

- [How AI Resume Screening Works in 2026 — Jobscan](https://www.jobscan.co/blog/blog-ai-resume-screening/)
- [ATS Resume Scoring Criteria: The 9-Point Checklist — ATS Resume AI](https://www.atsresumeai.com/blog/resume-ats-score)
- [Resume screening: AI-powered guide for HR leaders (2026) — MiHCM](https://mihcm.com/resources/blog/resume-screening-in-2026-a-guide-to-ai-powered-screening-ats-integration-bias-governance/)
