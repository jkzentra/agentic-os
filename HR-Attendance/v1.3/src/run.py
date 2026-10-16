"""Build one monthly attendance report.

Usage: py -m src.run <YYYY-MM>

Reads data_paths (roster, punches, output_dir) from client_config.toml at the
project root, and business rules from 03_MASTER_DATA/rules.toml. This is the
generic, client-agnostic entrypoint: a new client only edits client_config.toml
and 03_MASTER_DATA/rules.toml (and drops their own staff/outlet/holiday CSVs
into 03_MASTER_DATA), never src/.
"""
from __future__ import annotations

import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

from src.engine import Engine
from src.readers import load_master, read_roster, read_transactions
from src.report import write_report
from src.rules import load_rules

ROOT = Path(__file__).resolve().parent.parent


def _load_client_config(root: Path) -> dict:
    p = root / "client_config.toml"
    if p.exists():
        return tomllib.loads(p.read_text(encoding="utf-8"))
    return {}


def run(month: str, root: Path = ROOT, master_dir: Path | None = None,
        roster_path: Path | str | None = None, punches_path: Path | str | None = None,
        out_dir: Path | str | None = None):
    """Build one month's attendance report.

    month: "YYYY-MM"
    root: project root (defaults to the repo this file lives in)
    master_dir: override for 03_MASTER_DATA (defaults to root/03_MASTER_DATA)
    roster_path / punches_path: override the client_config.toml data_paths
      (used by tests and the demo, which point at sample_data/ instead)
    out_dir: override the output folder (defaults to client_config.toml's
      data_paths.output_dir, or 06_REPORTS)
    """
    cfg = _load_client_config(root)
    master_dir = Path(master_dir) if master_dir else (root / "03_MASTER_DATA")
    master = load_master(master_dir)
    # Rules are always the single source of truth at 03_MASTER_DATA/rules.toml,
    # even when master_dir is overridden (e.g. by the demo, which points
    # master_dir at sample_data/master_data for staff/outlet data only).
    rules = load_rules(root / "03_MASTER_DATA" / "rules.toml")

    dp = cfg.get("data_paths", {})
    if roster_path is None and dp.get("roster"):
        roster_path = root / dp["roster"]
    if punches_path is None and dp.get("punches"):
        punches_path = root / dp["punches"]
    if roster_path is None or punches_path is None:
        raise SystemExit(
            "No roster/punches path given. Set [data_paths] roster/punches in "
            "client_config.toml, or pass roster_path/punches_path explicitly."
        )
    roster_path, punches_path = Path(roster_path), Path(punches_path)

    roster, info = read_roster(roster_path, month, master)
    label = cfg.get("client_name") or "attendance transactions"
    punches, problems, seen = read_transactions(punches_path, label, master)
    source_of = {sid: label for sid in seen}

    eng = Engine(master, rules)
    res = eng.run(month, roster, info, punches, source_of, None, problems)

    n_roster = len({r["person"] for r in roster})
    sources = [
        ("Duty roster", str(roster_path), f"{len(roster)} roster cell(s) for {n_roster} people", ""),
        ("Attendance transactions", str(punches_path), f"{len(seen)} staff with at least one punch", ""),
    ]
    ctx = {
        "sources": sources,
        "outlet_cov": [],
        "noclock_reason": lambda P: "Not found in the attendance transactions for this month.",
        "excluded_note": "People on the excluded_names list (rules.toml) are left out of attendance entirely.",
        "offsite_note": "People on the offsite_names list (rules.toml) have punches shown but no shift checks.",
        "clock_source": lambda o: f"{o} outlet clock export",
        "missing_outlets": [],
        "banner": False,
        "scope_line": (f"On the roster: {n_roster}. With punch data: {len(seen)}. "
                       f"Person-days checked: {len(res['day_rows'])}."),
    }

    out_root = Path(out_dir) if out_dir else (
        root / dp["output_dir"] if dp.get("output_dir") else root / "06_REPORTS"
    )
    out_root = out_root / month
    out_root.mkdir(parents=True, exist_ok=True)
    out = out_root / f"Attendance report {month}.xlsx"
    tabs = write_report(out, month, res, ctx, rules, master)
    return out, res, tabs


if __name__ == "__main__":
    o, res, tabs = run(sys.argv[1])
    print(o, tabs)
