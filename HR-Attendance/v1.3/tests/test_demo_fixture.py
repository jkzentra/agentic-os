"""Regression fixture: the demo rebuild (sample_data/) must reproduce the
saved baseline in sample_data/expected_output/ exactly."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import openpyxl

from src.run import run

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "sample_data"


def _rebuild(month: str, out_dir: Path):
    out, res, tabs = run(
        month,
        root=ROOT,
        master_dir=SAMPLE / "master_data",
        roster_path=SAMPLE / "roster_sample.xlsx",
        punches_path=SAMPLE / "punches_sample.xlsx",
        out_dir=out_dir,
    )
    return out


def _workbook_cells(path: Path) -> dict:
    """Cell-value comparison (not raw bytes): openpyxl / Excel write timestamps
    and other zip metadata into the .xlsx container, so two builds of the same
    content are not byte-identical even though every cell value is. Comparing
    sheet names and cell values is the stable, meaningful equality check."""
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for name in wb.sheetnames:
        ws = wb[name]
        out[name] = [[c.value for c in row] for row in ws.iter_rows()]
    return out


def test_demo_rebuild_matches_fixture():
    for month in ("2026-08", "2026-09"):
        expected_path = SAMPLE / "expected_output" / f"Attendance report {month}.xlsx"
        assert expected_path.exists(), f"missing fixture for {month}"
        with tempfile.TemporaryDirectory() as tmp:
            rebuilt_path = _rebuild(month, Path(tmp))
            expected = _workbook_cells(expected_path)
            rebuilt = _workbook_cells(rebuilt_path)
            assert rebuilt.keys() == expected.keys(), f"{month}: sheet names differ"
            for sheet in expected:
                assert rebuilt[sheet] == expected[sheet], f"{month}: sheet {sheet!r} differs from the fixture"
