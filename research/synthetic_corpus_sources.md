# Grounding the synthetic resume corpus in something real

## What exists publicly

`datasetmaster/resumes` on Hugging Face — 4,817 rows, hybrid real +
synthetic. Real resumes normalized into a JSON schema from actual CV
submissions; synthetic ones generated with the Faker library on top of
that schema. Schema: personal info, work experience, education,
technical skills (categorized by language / framework / database /
cloud platform), projects. Focused on technical roles generally — no
confirmation it specifically covers AI/ML engineering titles, so it's
useful as a schema/structure reference, not as a drop-in source of
AI-engineer-specific examples.

GitHub has individual real CVs from ML/deep-learning engineers (e.g.
`vladserkoff/cv`) — useful for seeing real structure and phrasing
conventions in the wild, not usable as bulk training/eval data (single
examples, real people, not licensed for redistribution).

## What this means for how we build the corpus

Borrow the *schema shape* from `datasetmaster/resumes` (it's a
reasonable, precedented structure) rather than inventing one from
scratch, but generate every actual resume ourselves via LLM prompting
against real AI-engineer role archetypes — not reuse or derive from
the real CVs in that dataset or on GitHub, to keep this fully synthetic
and avoid any real-person content ending up in a public repo.

Still needed, not done: the actual archetype list (clear-hire,
clear-reject, keyword-stuffed, career-changer, overqualified, borderline)
with enough of each to be statistically meaningful, and hand/LLM-assisted
ground-truth labels per archetype for the eval harness to score against.

## Sources

- [datasetmaster/resumes — Hugging Face](https://huggingface.co/datasets/datasetmaster/resumes)
- [vladserkoff/cv — GitHub](https://github.com/vladserkoff/cv)
