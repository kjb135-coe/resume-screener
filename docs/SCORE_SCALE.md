# Why a good candidate scores 6, not 8

The question this answers: looking at the ranked list, candidates at 4.7
and 5.0 are being advanced while anything under 4 is `hold`. On a 0-10
scale that reads wrong — 7+ ought to be the advance line.

It reads wrong because it *is* wrong, and the cause is measurable.

## The panel does not use the top of the scale

For the 20 candidates the corpus labels `advance`:

| Agent | Their average | Max across all 60 |
|---|---|---|
| `production_reality` | 7.55 | 9.0 |
| `technical_integration` | 6.39 | 9.0 |
| `client_communication` | **1.00** | **4.0** |

Two agents behave sensibly. The third has never scored above 4.0 for
anyone in the corpus and averages 1.0, because resumes rarely document
client-facing work and the agent was reading silence as a zero.

The composite is the mean of three:

```
(7.55 + 6.39 + 1.00) / 3 = 4.98   ← a strong candidate
(7.55 + 6.39)        / 2 = 6.97   ← the same candidate without agent 3
```

So the cutoffs are not arbitrary. **4.0 is where `advance` actually
begins once one agent is dragging every composite down two points.** The
cutoffs were compensating for the scale, which is why they look low.

## Fixing the scale was tested, and it costs accuracy

The obvious fix: tell the agents to use the full range, and tell
`client_communication` that silence is a 3-4 rather than a 0. That was
implemented and run against the full corpus (`--tag recalibrated`).

It worked on its own terms. `client_communication` went from mean 0.60,
max 4.0, 35 zeros, to mean 3.34, max 7.0, **zero** zeros. Composites for
`advance` candidates rose from 5.51 to 6.37.

And accuracy fell:

| Scoring | Best cutoffs | macro-F1 | `advance` composite |
|---|---|---|---|
| Original | 3.7 / 0.9 | **0.880** | 5.8 |
| Recalibrated | 6.1 / 3.1 | 0.796 | 6.6 |
| Recalibrated, drop `client_comm` | 5.6 / 3.1 | 0.756 | **7.4** |

Every configuration is shown at *its own* best cutoffs, so this is not a
cutoff artifact. Interpretability and accuracy trade against each other
here, and the trade is roughly 0.08 macro-F1 for one point of composite.

**Why.** Scoring silence at 0 was destroying information about the
candidate — but it was *useful* information for this corpus. The nine
archetypes were generated with an intended `client_communication` level
baked in, so an agent that punishes silence harshly correlates with the
answer key. Telling it to be fairer to a real applicant makes it agree
with the synthetic labels less.

That is worth stating plainly: the measured accuracy drop is partly a
property of the corpus, not proof that the fairer agent is worse at
judging real people. A resume that never mentions client work is not
evidence the person cannot do it, and 0 is a harsh reading of silence.
On real applicants the recalibrated agent is probably the better one.
On this corpus it scores worse, and this corpus is the only evidence
available.

## What is not achievable

**7+ as the automatic advance line does not survive contact with the
data.** Even after recalibration, and even dropping the weak agent
entirely, the best `advance` line the sweep finds is 5.6-6.2. Candidates
the labels call `advance` simply do not average 7+, because the two
strong agents themselves average 6.4-7.6 and a mean of those with
anything else lands below 7.

Forcing the cutoff to 7.0 anyway costs a great deal:

| Cutoffs | macro-F1 (recalibrated scores) |
|---|---|
| 5.7 / 3.1 (swept) | 0.776 |
| 7.0 / 4.0 | 0.593 |
| 7.0 / 5.0 | 0.481 |

## Where this leaves it

Reverted to the original scoring, because 0.880 beats 0.796 and the
corpus is the only measurement available. `docs/RESULTS_HISTORY.md`
records the recalibrated run so the experiment is not lost.

The remaining problem is presentational rather than numerical: a reader
seeing "5.5 / 10 — advance" has no way to know 5.5 is a good score here.
That is fixable in the UI by showing where the line is, rather than by
moving the scores to where a reader expects the line to be. Distorting
the number to match an intuition is how a scale stops meaning anything.

Open, and a genuine decision rather than a technical one: whether to
take the accuracy hit for a scale that reads naturally. The numbers for
both are above.
