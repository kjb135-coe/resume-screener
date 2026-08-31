# Hosting this for a week

Deploying an LLM app behind a shared link means anyone with the link can
spend your money. This is the checklist that makes that safe, in the
order it has to be done.

## Spend caps — do these FIRST, before deploying

Three layers, and only the first two are outside this codebase's control.
**A bug in the app cannot bypass the provider caps; that is the point.**

| Layer | Where | Setting |
|---|---|---|
| 1. Provider hard cap | OpenAI billing dashboard | **$20/month** |
| 2. Provider hard cap | Anthropic console billing | **$10/month** |
| 3. App daily cap | `DAILY_BUDGET_USD` | **$3.00/day** |
| 4. Per-run cap | `MAX_RESUMES_PER_RUN` | **20 resumes** |

**Both providers are needed.** The panel and arbiter run on GPT-5.6 Luna;
evidence extraction still runs on Haiku. Two keys, two caps.

### Why these numbers

A full 60-resume run costs about **$0.31**. The demo is capped at 20
resumes per run, so roughly $0.10 a run.

Five users doing three runs a day for seven days is about **$11**. The
$3/day app cap allows ~30 runs a day, comfortably above real use. The
combined $30 provider cap is the backstop that survives any bug here.

### How the app cap behaves

- Checked **before** a run starts; recorded **after** it finishes, from
  real token counts (`Usage.by_model`), not estimates.
- A run already underway is allowed to finish. Overshoot is bounded by
  `MAX_RESUMES_PER_RUN`, which is why that limit exists.
- Refused requests get **HTTP 429** and a message saying it is a spend
  cap and when it resets — not a generic error.
- `GET /api/budget` reports spend, limit and remaining. Public on
  purpose: a refused visitor should be able to see why.
- The ledger is **in memory** and resets on restart and at midnight UTC.
  For a week-long demo behind provider caps that is an accepted trade;
  a real deployment would persist it.

## Deploying

1. Set the two provider caps above. Do not skip this.
2. Push the repo to GitHub.
3. In Render: **New → Blueprint**, point at the repo. It reads
   `render.yaml`.
4. Fill in the three prompted secrets: `ANTHROPIC_API_KEY`,
   `OPENAI_API_KEY`, `APP_PASSWORD`.
5. **Change `APP_PASSWORD` from the default `marco1`.**
6. Deploy. Check `/health`, then log in and confirm `/api/budget`
   returns the expected limit.

The free plan sleeps after ~15 minutes idle and takes ~30s to wake. That
is acceptable for a link someone opens once; `plan: starter` removes it.

## What is NOT protected

- **No rate limiting per user.** The password is shared, so the daily cap
  is the only throttle. Five known colleagues, one week — acceptable. A
  public link would need more.
- **Reviewer decisions do not survive a restart** on the free plan. The
  demo is read-mostly, so this is cosmetic.
- **Uploaded resumes are never persisted.** They are written to a temp
  path, read, and deleted in a `finally`. Someone's real resume is not
  ours to keep on a demo server.

## Taking it down

Delete the Render service, then **revoke both API keys**. A key that has
been in a hosted environment should not be reused locally.
