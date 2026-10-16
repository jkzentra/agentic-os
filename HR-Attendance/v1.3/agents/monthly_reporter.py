"""Monthly report builder + mailer. SKELETON — not yet implemented.

Fires: Windows Task Scheduler, 1st of month 09:00 local time.

Responsibilities (planned):
  1. Ask scope_resolver for the previous calendar month.
  2. Call src.run with scope="month" to produce the xlsx.
  3. Save to 06_REPORTS/Monthly/<stem>.xlsx (e.g. "2026-10_Monthly.xlsx").
  4. Email it to client_config.toml [recipients].monthly.
  5. Log the run to 07_LOGS/monthly_reporter.log.

Shares email logic with weekly_reporter — both will call a small
agents/_mailer.py helper once built, so SMTP wiring lives in one place.

Awaiting PL confirmation on:
  - Final recipient list for monthly (may be a superset of weekly, e.g.
    managers who only want the month-end view)
  - Gmail App Password (same as weekly; delivery-time)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportResult:
    filename: str
    recipients: list[str]
    sent: bool


def run(ctx: dict) -> ReportResult:
    """Entry point called by scheduler and dashboard. Not yet implemented."""
    raise NotImplementedError(
        "monthly_reporter.run() not implemented. "
        "See module docstring for the planned behavior; "
        "awaiting PL recipient list and SMTP credentials (delivery-time)."
    )
