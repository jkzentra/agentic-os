"""Weekly reporter agent: builds and emails the prior-week attendance report.

Role: resolves the previous Mon-Sun week window via
agents.scope_resolver.resolve("week", previous=True), calls the src.run engine
for that window, writes 06_REPORTS/Weekly/<stem>.xlsx, and emails it via SMTP to
the [recipients.weekly] list in client_config.toml.

Cadence: Monday 09:00 (Windows Task Scheduler).

SKELETON: no behaviour yet. SMTP config is deferred until delivery.
"""
from __future__ import annotations

from datetime import date

from agents import scope_resolver  # noqa: F401  (dependency made visible)


def run(ctx: dict | None = None, as_of: date | None = None) -> dict:
    """Generate and send the week report. Returns a summary dict."""
    # TODO: window = scope_resolver.resolve("week", as_of=as_of, previous=True)
    # TODO: call the src.run engine for that window.
    # TODO: write 06_REPORTS/Weekly/<stem>.xlsx (skip send if it already exists).
    # TODO: email via SMTP to [recipients.weekly] from client_config.toml.
    return {"filename": "", "sent_to": [], "status": "stub"}


if __name__ == "__main__":
    print(run())
