# agents/

Four agents sit above one engine (`src/run.py`). Each decides **when** and
**what scope** to run, then calls the engine. All expose `run(ctx)`; the
scheduler and the Streamlit dashboard call the same functions (one codepath).
`scope_resolver.py` is the shared helper for day/week/month windows.

| Agent | Trigger | Cadence | Input | Output |
|---|---|---|---|---|
| `drop_scanner` | Scheduler | Daily 12:00 | `01_INPUTS/` new files | Archived files, `last_scan.txt`, engine runs |
| `weekly_reporter` | Scheduler | Monday 09:00 | Prior Mon-Sun data | `06_REPORTS/Weekly/2026-W42_Weekly.xlsx` + email |
| `monthly_reporter` | Scheduler | 1st of month 09:00 | Prior month data | `06_REPORTS/Monthly/2026-10_Monthly.xlsx` + email |
| `reply_handler` | Event (from `drop_scanner`) | On `*_reply.xlsx` | Client reply file | `<stem>_v2.xlsx`, diff, dashboard flag |

## Filename convention

- Daily `2026-10-17_Daily.xlsx`, weekly `2026-W42_Weekly.xlsx`, monthly `2026-10_Monthly.xlsx`
- Reply `*_reply.xlsx`; revision `*_v2.xlsx` (bumps to `_v3`, ...)

## When each fires

- **Sat 17 Oct, 12:00** — `drop_scanner` finds `punches_oct.csv` and `roster.xlsx`,
  files them, and runs the engine if the scope is now complete.
- **Mon 19 Oct, 09:00** — `weekly_reporter` resolves 12-18 Oct (ISO week 42),
  writes `2026-W42_Weekly.xlsx`, emails `[recipients.weekly]`.
- **Sun 1 Nov** (the 1st, 09:00) — `monthly_reporter` builds `2026-10_Monthly.xlsx`
  and emails `[recipients.monthly]`.
- **Tue 20 Oct, 12:00** — the client returns `2026-W42_Weekly_reply.xlsx`;
  `drop_scanner` spots it and calls `reply_handler`, which writes
  `2026-W42_Weekly_v2.xlsx` and flags the dashboard "awaiting review".

## Owned by

All four are client-PC Windows Task Scheduler jobs (`reply_handler` runs
inside the `drop_scanner` job). The dashboard may call the same `run()` functions.

## Status

Skeletons only: every `run()` returns a stub dict. Logic lands once PL confirms.
SMTP sending is deferred until delivery; the sender address and password live in `.env` (gitignored).
