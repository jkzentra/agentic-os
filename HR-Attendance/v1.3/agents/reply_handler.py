"""Reply-file handler. SKELETON — not yet implemented.

Fires: event-driven, invoked by drop_scanner when it finds *_reply.xlsx in
the drop folder. Not scheduled.

Responsibilities (planned):
  1. Parse the reply filename to extract the original scope (e.g.
     `2026-W42_Weekly_reply.xlsx` -> scope=week, period=2026-W42).
  2. Merge the reply's answered/corrected rows into the engine's state.
  3. Re-run src.run for that same scope with the merged data.
  4. Save as <stem>_v2.xlsx (bump to _v3, _v4, ... on each subsequent reply).
  5. Diff against the previous version and write a short changes summary
     into 06_REPORTS/<scope>/<stem>_v2_changes.md.
  6. Flag the dashboard: "Reply received, awaiting review".
  7. Log to 07_LOGS/reply_handler.log.

Awaiting PL confirmation on:
  - Reply filename convention (template default: original stem + "_reply")
  - What fields the reply file is allowed to change (Pending answers?
    Flag resolutions? Both? Neither — only comments?)
  - Should a revised report auto-email, or just appear in the dashboard
    for review before any send
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReplyResult:
    original_stem: str
    new_version: int   # 2 for first reply, 3 for second, etc.
    output_path: str
    changes_summary_path: str


def run(ctx: dict, reply_file: Path) -> ReplyResult:
    """Entry point called by drop_scanner. Not yet implemented."""
    raise NotImplementedError(
        "reply_handler.run() not implemented. "
        "See module docstring for the planned behavior; "
        "awaiting PL confirmation on reply filename + which fields are editable."
    )
