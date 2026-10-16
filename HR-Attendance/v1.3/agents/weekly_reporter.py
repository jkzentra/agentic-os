"""Weekly report builder + mailer. SKELETON — not yet implemented.

Fires: Windows Task Scheduler, Mon 09:00 local time.

Responsibilities (planned):
  1. Ask scope_resolver for the previous business week (Mon-Sun by default).
  2. Call src.run with scope="week", start=..., end=... to produce the xlsx.
  3. Save to 06_REPORTS/Weekly/<stem>.xlsx where stem comes from
     ScopeWindow.filename_stem (e.g. "2026-W42_Weekly").
  4. Email it to client_config.toml [recipients].weekly, with the week label
     in the subject (e.g. "Weekly attendance: 2026-W42 (12-18 Oct)").
  5. Log the run to 07_LOGS/weekly_reporter.log.

Awaiting PL confirmation on:
  - Final recipient list (currently placeholders: conankei81@gmail.com,
    office@jkzentra.com)
  - Gmail App Password for sender pl.ecosystem2026@gmail.com (deferred to
    delivery time per user instruction)
  - Email subject + body copy
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
        "weekly_reporter.run() not implemented. "
        "See module docstring for the planned behavior; "
        "awaiting PL recipient list and SMTP credentials (delivery-time)."
    )
