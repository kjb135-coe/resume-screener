# Why macro-F1, and what it hides

Every headline number in this repo is macro-F1. This is the reasoning
behind that choice, the alternatives that were rejected, and the things
it does not tell you.

## The task

Each resume gets exactly one of three verdicts:

    advance | hold | reject

The corpus holds 60 resumes, 20 per class. Ground truth comes from the
archetype each resume was generated from, not from a human rater — see
`docs/corpus_design.md`.

## What macro-F1 is

F1 is the harmonic mean of precision and recall for **one** class:

| Term | For `hold` | Plain meaning |
|---|---|---|
| Precision | of everything we called `hold`, how much really was | are we crying wolf? |
| Recall | of everything that really was `hold`, how much we caught | are we missing them? |
| F1 | harmonic mean of the two | one number, punishes a lopsided pair |

**Macro**-F1 computes F1 separately for `advance`, `hold` and `reject`,
then takes a plain average. Each class counts one third, regardless of
how many resumes are in it.

    macro-F1 = (F1_advance + F1_hold + F1_reject) / 3

## Why not plain accuracy

Accuracy is "how many did we get right", and on a balanced corpus it
usually tracks macro-F1 closely — the two sit within about 0.02 of each
other in most runs here. It is still reported alongside, because it is
the number a non-specialist reads without training.

It was rejected as the primary metric for one reason: **it hides which
class is failing.** A screener that nails `advance` and `reject` while
being useless at `hold` still scores well on accuracy, because the two
easy classes carry two thirds of the corpus.

That is not hypothetical. It is exactly what this system does:

| Run | Accuracy | Macro-F1 | `hold` F1 |
|---|---|---|---|
| Recorded baseline | 0.850 | 0.847 | 0.743 |

`hold` has been the weakest class in every run, and macro-F1 is the
metric that keeps saying so. Accuracy alone would let the middle class
rot quietly.

**The middle class is the one that matters commercially.** `advance` and
`reject` are the candidates a keyword filter could mostly find. `hold` is
"this one is genuinely borderline, a human should look" — the judgment a
screener is actually being bought for.

## Why not weighted or micro-F1

- **Micro-F1** on a single-label problem is mathematically identical to
  accuracy. It would add a more technical-sounding name and no
  information.
- **Weighted F1** weights each class by how many resumes it has. On a
  20/20/20 corpus that is the same as macro-F1 today, but it would drift
  the moment the corpus stopped being balanced, and it would drift in the
  wrong direction — hiding the rare class, which is the one worth
  watching.

## Why the escalation rate is reported separately, never blended

A tempting single number is "accuracy on the cases we did not escalate".
It is a bad number, because a system can improve it by escalating
everything hard to a human. Perfect score, no work done.

So the two are always reported side by side and never combined:

| Reported | What it answers |
|---|---|
| Macro-F1 | when it decides, is it right? |
| Escalation rate | how often does it decide at all? |

A change that raises macro-F1 while also raising escalation has not
necessarily improved anything.

## What macro-F1 does not tell you

**1. It is one draw from a wide distribution.** Four identical runs of
one unchanged configuration span **0.051** macro-F1 (`docs/VARIANCE.md`).
On a 20-resume sample the band is roughly **0.098**. A macro-F1 quoted to
three decimals is false precision. **Quote it as a range.**

**2. It says nothing about the direction of errors.** Macro-F1 treats
"scored too high" and "scored too low" identically. It should not: for a
hiring screener, wrongly rejecting a good candidate is not the same
mistake as wrongly advancing a weak one. The direction has to be read off
the confusion matrix separately, and in this system errors run
overwhelmingly *below* the label.

**3. It is measured against a scale that had to be fitted.** The score is
0-10; the verdict comes from cutoffs. Those cutoffs were swept on this
same corpus. A model that grades on a different scale scores badly for
the calibration, not the judgment — see the Luna arm in
`docs/BAKEOFF.md`, which moved 0.517 → 0.896 on cutoffs alone.

**4. The corpus is synthetic and the labels come from the generator.**
Macro-F1 measures agreement with an archetype's intended verdict, not
with a hiring manager. See `docs/LIMITATIONS.md`.

## Where the numbers live

- `docs/VARIANCE.md` — the noise band. Read before comparing anything.
- `docs/RESULTS_HISTORY.md` — every measured run, with what changed.
- `docs/LIMITATIONS.md` — what the headline is worth.
