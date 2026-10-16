"""Daily drop-folder scanner. SKELETON — not yet implemented.

Fires: Windows Task Scheduler, daily 12:00 local time.

Responsibilities (planned):
  1. List new files in 01_INPUTS/ since the last scan (tracked in
     07_LOGS/drop_scanner_state.json).
  2. Classify each file: roster | punches | reply | unknown.
  3. Move to the right archive subfolder with a timestamp.
  4. If classification = "reply", invoke reply_handler.run(ctx, file).
  5. If a scope is now complete (e.g. all September data arrived), optionally
     trigger the matching reporter.
  6. Append one line per file to 07_LOGS/drop_scanner.log.

Must be idempotent — re-running on the same folder does nothing new.

Awaiting PL confirmation on:
  - Reply filename convention (e.g. `2026-W42_Weekly_reply.xlsx`)
  - Alert channel for "unknown" files (deferred: logged only, no alert for now)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScanResult:
    classified: int
    unknown: int
    triggered_reports: list[str]


def run(ctx: dict) -> ScanResult:
    """Entry point called by scheduler and dashboard. Not yet implemented."""
    raise NotImplementedError(
        "drop_scanner.run() not implemented. "
        "See module docstring for the planned behavior; "
        "awaiting PL confirmation on reply filename convention."
    )
