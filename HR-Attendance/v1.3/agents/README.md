# agents/

Thin trigger layer above `src.run`. Each agent is a plain Python module
with one `run(ctx)` function. The scheduler calls them; the dashboard
calls the same functions. One codepath, whether a human or cron fires.

## Files

| File | Fires | Status |
|---|---|---|
| `scope_resolver.py` | shared helper — called by all agents | ✅ implemented |
| `drop_scanner.py` | daily 12:00 (Task Scheduler) | 🔲 skeleton |
| `weekly_reporter.py` | Mon 09:00 (Task Scheduler) | 🔲 skeleton |
| `monthly_reporter.py` | 1st of month 09:00 (Task Scheduler) | 🔲 skeleton |
| `reply_handler.py` | event-driven (triggered by `drop_scanner`) | 🔲 skeleton |

Skeletons raise `NotImplementedError` with a module docstring explaining
the planned behavior and what's blocking (usually: a PL confirmation).

## Date logic lives in one place

Every agent imports from `scope_resolver` for "what week/month am I in?"
No agent does its own date arithmetic. Filename stems come from
`ScopeWindow.filename_stem` — change the convention in one place.

Current filename convention (ISO):

- Daily: `2026-10-17_Daily.xlsx`
- Weekly: `2026-W42_Weekly.xlsx`
- Monthly: `2026-10_Monthly.xlsx`
- Reply: `<stem>_reply.xlsx` → regenerated as `<stem>_v2.xlsx`

## Config

Agent behavior is driven by `client_config.toml`:

- `[recipients].weekly` / `[recipients].monthly` — email lists
- `[schedule].*` — override default times
- `[week].starts_on` — business week start (`"Mon"` default)

SMTP sender password lives in `.env` (gitignored), never in TOML.

## Build order (once PL replies)

1. `scope_resolver.py` ✅ (done — add tests next)
2. `weekly_reporter.py` — highest value, delivers the main new capability
3. `drop_scanner.py` + `reply_handler.py` — the ingestion loop
4. `monthly_reporter.py` — reuses weekly's shape
5. Streamlit `dashboard.py` — last, built once agents are real
