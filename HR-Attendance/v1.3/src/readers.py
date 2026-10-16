"""Readers: master data, roster, September HRMS transactions, May clock exports.

Every reader is read-only on its source. Anything unreadable is returned as a
problem record for the report, never raised and never guessed.
"""
from __future__ import annotations

import csv
import datetime
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

from src.capture import capture_folder
from src.shifts import parse_code


def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip()).upper()


@dataclass
class Master:
    outlets: dict            # id -> dict(company, name, clock_code, other_names)
    staff: dict              # staff_id -> dict
    holidays: dict           # date -> name
    text_labels: dict        # lower text -> day_type
    by_full_name: dict = field(default_factory=dict)
    by_clock_name: dict = field(default_factory=dict)

    def company_of(self, staff_id: str, home_outlet: str) -> tuple[str, str]:
        s = self.staff.get(staff_id, {})
        if s.get("company"):
            return s["company"], "September transactions"
        o = self.outlets.get(home_outlet or s.get("home_outlet", ""))
        if o:
            return o["company"], "home outlet (not in the September company map)"
        return "UNASSIGNED", "no company information"


def load_master(d: Path) -> Master:
    def rows(name):
        with open(d / name, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    outlets = {r["outlet_id"]: r for r in rows("outlets.csv")}
    staff = {r["staff_id"]: r for r in rows("staff_map.csv")}
    hol = {datetime.date.fromisoformat(r["date"]): r["name"] for r in rows("public_holidays.csv")}
    labels = {r["text_lower"]: r["day_type"] for r in rows("roster_text_labels.csv")}
    m = Master(outlets, staff, hol, labels)
    for sid, r in staff.items():
        if r["full_name"]:
            m.by_full_name[_norm(r["full_name"])] = sid
        for n in filter(None, (r["may_clock_names"] or "").split(";")):
            m.by_clock_name[_norm(n)] = sid
    return m


# ---------------------------------------------------------------- roster
def read_roster(path: Path, month: str, master: Master, sheet: str | None = None):
    """Return (rows, info). rows: person, date, block, raw, hours, shift.
    info: dup_people, unlabelled_blocks."""
    y, mo = map(int, month.split("-"))
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    block = {}
    for rng in ws.merged_cells.ranges:
        if rng.min_row == 1:
            v = ws.cell(1, rng.min_col).value
            for c in range(rng.min_col, rng.max_col + 1):
                block[c] = str(v).strip() if v else ""
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if v and c not in block:
            block[c] = str(v).strip()
    cols, seen, dups = [], set(), []
    for c in range(3, ws.max_column + 1):
        n = ws.cell(2, c).value
        if not n or str(n).strip().upper() == "REMARK":
            continue
        n = str(n).strip().upper()
        if n in seen:
            dups.append(n)
            continue
        seen.add(n)
        cols.append((n, c, block.get(c, "")))
    outlet_ids = set(master.outlets)
    rows = []
    for r in ws.iter_rows(min_row=4, values_only=True):
        d = r[0]
        if isinstance(d, datetime.datetime):
            d = d.date()
        if not isinstance(d, datetime.date) or (d.year, d.month) != (y, mo):
            continue
        for person, c, blk in cols:
            raw = r[c - 1] if c - 1 < len(r) else None
            if raw is None or str(raw).strip() == "":
                continue
            raw = str(raw).strip()
            hrs = r[c] if c < len(r) else None
            rows.append({"person": person, "date": d, "block": blk, "raw": raw,
                         "hours": hrs if isinstance(hrs, (int, float)) else None,
                         "shift": parse_code(raw, outlet_ids, master.text_labels)})
    return rows, {"dup_people": sorted(set(dups)),
                  "unlabelled": sorted({p for p, c, b in cols if not b})}


# ---------------------------------------------------------------- September transactions
@dataclass
class PunchDay:
    times: list              # HH:MM strings, sorted
    outlets: list = field(default_factory=list)
    remark: str = ""


def _t(v):
    if isinstance(v, datetime.datetime):
        if v.hour == 0 and v.minute == 0:
            return None
        return f"{v.hour:02d}:{v.minute:02d}"
    return None


def read_transactions(path: Path, company: str, master: Master):
    """Return (punches {(staff_id,date): PunchDay}, problems, names_seen)."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    out, problems, seen = {}, [], {}
    cur = None
    for r in ws.iter_rows(min_row=3, values_only=True):
        a = r[0]
        if isinstance(a, str) and a.startswith("Calendar Date:"):
            m = re.search(r"(\d{2})/(\d{2})/(\d{4})", a)
            cur = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None
            continue
        if not isinstance(a, str) or " - " not in a or cur is None:
            continue
        name = _norm(a.split(" - ", 1)[1])
        sid = master.by_full_name.get(name)
        if sid is None:
            problems.append({"company": company, "name": name, "date": cur,
                             "detail": "Employee not found in staff_map.csv"})
            continue
        seen[sid] = name
        tin, tout = _t(r[7]), _t(r[8])
        times = [t for t in (tin, tout) if t]
        remark = str(r[21]).strip() if len(r) > 21 and r[21] else ""
        if times or remark:
            out[(sid, cur)] = PunchDay(times, [], remark)
    return out, problems, seen


# ---------------------------------------------------------------- May clock exports
def read_clock_folder(folder: Path, master: Master):
    pl, roster = capture_folder(folder)
    out: dict = {}
    problems = []
    for row in pl:
        sid = master.by_clock_name.get(_norm(row["clock_name"]))
        if sid is None:
            sid = master.by_full_name.get(_norm(row["clock_name"])) or (
                row["clock_name"].upper() if row["clock_name"].upper() in master.staff else None)
        if sid is None:
            problems.append({"company": "", "name": row["clock_name"], "date": row["date"],
                             "detail": f"Clock name not in staff_map.csv ({row['outlet_clock']})"})
            continue
        d = datetime.date.fromisoformat(row["date"])
        times = [t.strip() for t in row["all_punches"].split("|") if t.strip()]
        pd_ = out.setdefault((sid, d), PunchDay([], []))
        pd_.times.extend(times)
        pd_.outlets.extend([row["outlet_clock"]] * len(times))
    # keep (time, outlet) order together
    for (sid, d), pd_ in out.items():
        pairs = sorted(zip(pd_.times, pd_.outlets), key=lambda p: p[0])
        pd_.times = [p[0] for p in pairs]
        pd_.outlets = [p[1] for p in pairs]
    files = sorted({r["outlet_clock"] for r in roster})
    return out, problems, files, roster
