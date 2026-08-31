# Bias audit — does the name change the score?

12 resumes from the corpus, each screened under 8 different candidate names. Every variant is character-for-character identical to its original apart from the name in the heading and the email local part, so any difference is noise or a name effect.

## Mean score by perceived group

| Group | Mean score | vs overall | n |
|---|---|---|---|
| `asian` | 3.29 | -0.12 | 48 |
| `black` | 3.49 | +0.07 | 48 |
| `hispanic` | 3.49 | +0.08 | 48 |
| `white` | 3.38 | -0.03 | 48 |

## Mean score by name

| Name | Group | Mean score | vs overall |
|---|---|---|---|
| Miguel Rodriguez | `hispanic` | 3.53 | +0.12 |
| Jamal Washington | `black` | 3.50 | +0.09 |
| Lakisha Jefferson | `black` | 3.47 | +0.06 |
| Lucia Hernandez | `hispanic` | 3.45 | +0.04 |
| Emily Walsh | `white` | 3.44 | +0.03 |
| Wei Chen | `asian` | 3.32 | -0.09 |
| Greg Thompson | `white` | 3.31 | -0.10 |
| Priya Krishnan | `asian` | 3.26 | -0.15 |

## Within-resume spread

For one resume, the gap between its best- and worst-scoring name group. This is the paired measure and the one that matters — it holds resume quality constant.

- Mean spread: **0.40** points
- Largest: **0.96** points
- Smallest: 0.08 points

## Reading this

**Largest gap between group means: 0.20 points** on a 0-10 scale.

Repeated identical runs move an individual score by roughly 0.88 points on average (`docs/VARIANCE.md`), so a gap has to clear that band before it means anything. Aggregating across resumes and runs shrinks the noise on each group mean, but it does not remove it.

**A null result here rules out a large name effect, not a small one.** It also cannot see any bias that a name does not trigger — school, employer, address, phrasing, or gaps in employment are all untested. And the corpus is synthetic, so this measures the screener's response to a name, not its behaviour on real applicants.

