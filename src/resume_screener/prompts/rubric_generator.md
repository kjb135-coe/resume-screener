# Meta-prompt — write a scoring rubric from a job posting

You are given a job posting. Write the scoring rubric and the panel
personas that a resume-screening panel will use to judge candidates
against *this* posting.

You are writing instructions for other agents, not scoring anyone.
No resume is in front of you. Do not invent a candidate.

## What makes a good rubric here

Anchor every dimension to something the posting actually says. If the
posting repeats a requirement, or phrases it emphatically ("not demos
or prototypes"), that is a signal to weight it heavily and to quote its
own language back in the criteria. If the posting never mentions
something, it does not belong in the rubric — a generic
"AI engineer checklist" is exactly what this is meant to replace.

Prefer dimensions that a resume can actually supply evidence for.
"Culture fit" is unscoreable from a resume; "shipped systems that carry
production load" is scoreable. Where a dimension is real but rarely
evidenced, say so in the criteria and tell the panel how to treat its
absence, rather than making absence automatically disqualifying.

Every dimension must be discriminative: it must separate a strong
candidate from a weak one for this role. A dimension that every
applicant would score the same on is wasted panel capacity.

## Output contract

Return **exactly three** dimensions. Three is fixed, not a suggestion:
the panel's disagreement threshold and escalation behaviour are
calibrated against a three-agent spread, so a different count silently
invalidates that calibration.

Respond as JSON, and nothing else:

```json
{
  "role_title": "short human-readable role name, from the posting",
  "summary": "ONE sentence: what profile this posting wants, and what it does not",
  "dimensions": [
    {
      "name": "snake_case_identifier",
      "title": "Short title case name",
      "criteria": "AT MOST 40 WORDS. What separates a high score from a low one, quoting the posting's own decisive words. No 'high/mid/low scores show...' enumeration.",
      "lens": "AT MOST 25 WORDS, second person: 'You judge whether...'. One instruction, not a checklist."
    }
  ]
}
```

## Length is a hard requirement, not a style note

These strings are read by a human in a UI, next to two others just like
them. A reader who has to work through 150 words per dimension to learn
what the agent is looking for will not read any of them.

Write the shortest text that would let a careful reader score a resume
the same way you would. If a clause could be removed and a scorer would
still reach the same answer, remove it. Do not pad with restatements of
the posting; the agent is given the posting separately.

`name` must be a valid snake_case identifier, unique across the three,
and stable enough to read in a report — it is used as the agent's name
in every output.

Do not add commentary before or after the JSON.
