"""One-click demo: rebuild the attendance report for the bundled sample_data.

Usage: py -m src.demo [YYYY-MM]
Defaults to 2026-08 (the complete sample month). 2026-09 has a deliberate
data gap for one staff member, to show the "Not assessed, missing data" path.

Writes into 06_REPORTS/<month>/, same as a normal py -m src.run call, but
using sample_data/ as the data source and sample_data/master_data/ as the
staff/outlet master data (business rules still come from the single
03_MASTER_DATA/rules.toml, same as production).
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.run import run

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "sample_data"


def main(month: str = "2026-08"):
    out, res, tabs = run(
        month,
        root=ROOT,
        master_dir=SAMPLE / "master_data",
        roster_path=SAMPLE / "roster_sample.xlsx",
        punches_path=SAMPLE / "punches_sample.xlsx",
        out_dir=ROOT / "06_REPORTS",
    )
    print(f"Demo report written to: {out}")
    print(f"Tabs: {tabs}")
    print(f"Compare against sample_data/expected_output/ to see the baseline.")
    return out, res, tabs


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-08")
