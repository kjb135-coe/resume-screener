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
- `GET /api/budget` reports spend, limit and remaining. It sits behind
  the password gate like everything else, so it is for whoever holds the
  link, not the open internet. The refusal message itself names the cap
  and its reset, which is what a blocked user actually needs.
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
5. **Set `APP_PASSWORD`.** There is no default. Left unset, the app
   generates a random password per process and prints it to the log —
   which means it changes on every restart and every redeploy.
6. Deploy. Open `/health`, then log in and confirm `/api/budget`
   returns the expected limit.

The free plan sleeps after ~15 minutes idle and takes ~30s to wake. That
is acceptable for a link someone opens once; `plan: starter` removes it.

## When the site says a run failed

Open `/health` first. It needs no password and it answers the two
questions that cause almost every hosted failure:

```json
{
  "ok": true,
  "configured": {"ANTHROPIC_API_KEY": true, "OPENAI_API_KEY": true, "APP_PASSWORD": true},
  "last_failure": {"tag": "APIStatusError 401", "at": "2026-08-31T16:40:02Z"}
}
```

`configured` reports only whether each key is *present*. It never shows a
key or any part of one. All three are `sync: false` in `render.yaml`, so
they are typed by hand and are the most likely thing missing after a
fresh deploy.

`last_failure` carries the exception class and HTTP status of the most
recent provider error. Read it like this:

| Tag | Meaning | Fix |
|---|---|---|
| `401` | The key is wrong or revoked | Re-enter it in **Environment** |
| `429` | Out of credit, or rate limited | Add credit, or wait a minute |
| `500`, `529` | The provider is refusing requests | Wait; nothing to fix here |
| `configured` shows `false` | The key was never set | Add it in **Environment** |

Both the rubric step and the screening step need **both** keys: criteria
generation runs on Opus and evidence extraction runs on Haiku, so
`ANTHROPIC_API_KEY` is required even though scoring runs on Luna. One
missing key breaks both buttons, which looks like a broken app rather
than a missing setting.

## What is NOT protected

- **No rate limiting per user.** The password is shared, so the daily cap
  is the only throttle. Five known colleagues, one week — acceptable. A
  public link would need more.
- **Reviewer decisions do not survive a restart** on the free plan. The
  filesystem is ephemeral and the instance sleeps after ~15 minutes idle,
  so a verdict recorded in the morning is gone by the afternoon. The app
  detects a failed write, keeps decisions in memory for that process, and
  **says so in the review panel** rather than reporting a save that did
  not happen. Attach a Render disk, or move decisions to Postgres, if
  they need to last.
- **Uploaded resumes are never persisted.** They are written to a temp
  path, read, and deleted in a `finally`. Someone's real resume is not
  ours to keep on a demo server.

## Taking it down

Delete the Render service, then **revoke both API keys**. A key that has
been in a hosted environment should not be reused locally.
