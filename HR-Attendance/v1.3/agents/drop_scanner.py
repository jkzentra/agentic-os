"""Drop scanner agent: watches 01_INPUTS/ and routes new files.

Role: scans 01_INPUTS/ for files that arrived since the last scan (tracked in
a last_scan.txt), classifies each as roster / punches / reply / unknown, moves
it to the matching archive subfolder, and auto-runs the engine (src/run.py)
when a scope is now complete. A *_reply.xlsx hands off to reply_handler.

Cadence: daily 12:00 (Windows Task Scheduler). Must be idempotent: running it
twice on the same folder state does nothing the second time.

SKELETON: no behaviour yet. Returns an empty result.
"""
from __future__ import annotations


def run(ctx: dict | None = None) -> dict:
    """Scan the drop folder once. Returns a summary dict."""
    # TODO: read last_scan.txt (missing file = first run, scan everything).
    # TODO: list files in 01_INPUTS/ newer than the last scan timestamp.
    # TODO: classify each file: roster | punches | reply | unknown.
    # TODO: move each file to its archive subfolder (skip if already moved).
    # TODO: for each *_reply.xlsx, call reply_handler.run(ctx, reply_file).
    # TODO: if a scope is now complete, call the engine and record it in "triggered".
    # TODO: write last_scan.txt only after all files are handled.
    return {"scanned": 0, "classified": {}, "triggered": []}


if __name__ == "__main__":
    print(run())
