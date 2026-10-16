"""Reply handler agent: turns a client's *_reply.xlsx into a revised report.

Role: triggered by drop_scanner when a *_reply.xlsx is found. Parses the
filename to find the matching original scope, reruns the engine with the
merged reply data, saves <stem>_v2.xlsx (or _v3 if _v2 exists), computes a
cell-level diff against the original, and flags the dashboard "awaiting
review".

Cadence: event-driven (no schedule of its own).

SKELETON: no behaviour yet.
"""
from __future__ import annotations


def run(ctx: dict | None = None, reply_file: str = "") -> dict:
    """Process one reply file. Returns original/revised names and a diff summary."""
    # TODO: parse reply_file stem (e.g. 2026-W42_Weekly_reply) -> original stem.
    # TODO: locate the original report and its scope window.
    # TODO: merge reply data and rerun the engine for that window.
    # TODO: save as <stem>_v2.xlsx, or the next free version (_v3, ...).
    # TODO: compute cell-level diff vs the original.
    # TODO: flag the dashboard "awaiting review".
    return {"original": "", "revised": "", "diff_summary": {}}


if __name__ == "__main__":
    print(run())
