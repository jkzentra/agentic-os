"""Core rule tests: the examples agreed with {admin} on 13 Oct 2026 and by Boss on 14 Oct."""
import datetime
from pathlib import Path

import pytest

from src.engine import Engine, ceil_to, floor_to
from src.readers import PunchDay, load_master
from src.rules import load_rules
from src.shifts import parse_code

ROOT = Path(__file__).resolve().parent.parent
OUTLETS = {"OUT1", "OUT2", "OUT3", "OUT4", "OUT5", "OUT6", "Admin"}


def mm(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


@pytest.mark.parametrize("punch,expected", [("13:19", "13:30"), ("10:01", "10:30"), ("10:31", "11:00"), ("10:00", "10:00")])
def test_late_round_up(punch, expected):
    assert ceil_to(mm(punch), 30) == mm(expected)


def test_early_out_round_down():
    assert floor_to(mm("19:58"), 30) == mm("19:30")


@pytest.mark.parametrize("code,start,end", [("10-8PM", "10:00", "20:00"), ("12-8:30PM", "12:00", "20:30"),
                                            ("2-8PM", "14:00", "20:00"), ("12-10", "12:00", "22:00"), ("FULL", "10:00", "22:00")])
def test_parse_code(code, start, end):
    s = parse_code(code, OUTLETS)
    assert (s.day_type, s.start, s.end) == ("WORK", start, end)


def test_transfer_marker_and_unreadable():
    assert parse_code("OUT4 / 10-8PM", OUTLETS).outlet == "OUT4"
    assert parse_code("OUT1/6.30PM", OUTLETS).day_type == "UNKNOWN"


def _day(code, times):
    master = load_master(ROOT / "03_MASTER_DATA")
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    d = datetime.date(2026, 9, 7)
    roster = [{"person": "SAM", "date": d, "block": "OUT1", "raw": code, "hours": None,
               "shift": parse_code(code, OUTLETS)}]
    res = Engine(master, rules).run("2026-09", roster, {}, {("SAM", d): PunchDay(times)}, {"SAM": "HRMS transactions PLM"}, None, [])
    return res["day_rows"][0]


def test_system_in_keeps_real_punch_and_hq_rounds_up():
    r = _day("10-8PM", ["10:12", "20:00"])
    assert (r["sys_in"], r["hq_in"]) == ("10:12", "10:30")


def test_cap_after_shift_end_is_flagged():
    r = _day("12-10PM", ["11:58", "22:06"])
    assert (r["sys_out"], r["hq_out"], r["capped"]) == ("22:06", "22:00", True)


def test_early_out_down():
    r = _day("10-8PM", ["09:55", "19:58"])
    assert r["hq_out"] == "19:30" and "Clock-out before shift end (early)" in r["flags"]


def test_ot_and_shortfall():
    r = _day("FULL", ["09:50", "22:00"])
    assert r["working"] == 12 and r["ot"] == 3.5 and r["early"] == 0


def test_ti_excluded_no_rows_no_flags():
    master = load_master(ROOT / "03_MASTER_DATA")
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    rules._rules["excluded_names"].value = ["DIR1"]  # client-configured via rules.toml
    d = datetime.date(2026, 9, 7)
    roster = [{"person": p, "date": d, "block": "OUT1", "raw": "10-8PM", "hours": None,
               "shift": parse_code("10-8PM", OUTLETS)} for p in ("SAM", "DIR1")]
    res = Engine(master, rules).run("2026-09", roster, {}, {("SAM", d): PunchDay(["10:00", "20:00"]),
                                    ("DIR1", d): PunchDay(["09:00", "21:00"])}, {"SAM": "HRMS transactions PLM"}, None, [])
    assert "DIR1" not in res["people"]
    assert all(r["person"] != "DIR1" for r in res["day_rows"])
    assert all(f.person != "DIR1" for f in res["flags"])


def test_offsite_angel_rows_no_flags_remark():
    master = load_master(ROOT / "03_MASTER_DATA")
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    rules._rules["offsite_names"].value = ["REMOTE1"]  # client-configured via rules.toml
    d = datetime.date(2026, 9, 7)
    res = Engine(master, rules).run("2026-09", [], {}, {("REMOTE1", d): PunchDay(["09:12", "18:40"])},
                                    {"REMOTE1": "HRMS transactions PLG"}, None, [])
    rows = [r for r in res["day_rows"] if r["person"] == "REMOTE1"]
    assert len(rows) == 1
    r = rows[0]
    assert (r["sys_in"], r["sys_out"], r["remark"]) == ("09:12", "18:40", "Off-site WFH, no roster")
    assert abs(r["working"] - (9 + 28 / 60)) < 1e-9
    assert r["hq_in"] is None and r["hq_out"] is None and not r["capped"] and r["ot"] is None
    assert [f for f in res["flags"] if f.person == "REMOTE1"] == []


# ---- 14 Oct fixes: capped tolerance, partial-data people, flag count reconciliation ----
def _run(code, punch_days, extra_days=0):
    """One person SAM, roster on Mon 7 Sep + extra_days following days; punches only on punch_days."""
    master = load_master(ROOT / "03_MASTER_DATA")
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    ds = [datetime.date(2026, 9, 7) + datetime.timedelta(days=i) for i in range(1 + extra_days)]
    roster = [{"person": "SAM", "date": d, "block": "OUT1", "raw": code, "hours": None,
               "shift": parse_code(code, OUTLETS)} for d in ds]
    punches = {("SAM", ds[i]): PunchDay(t) for i, t in punch_days.items()}
    return Engine(master, rules).run("2026-09", roster, {}, punches, {"SAM": "HRMS transactions PLM"}, None, [])


# ---- 16 Oct flag reduction: one test per changed rule -------------------------------------------------
import statistics

from src.closing import derive_closing
from src.engine import fmt_dates


def _multi(rows, month="2026-09", extra_holidays=None):
    """rows: (person, day offset from 7 Sep, raw code, roster hours or None, punch list or None)."""
    master = load_master(ROOT / "03_MASTER_DATA")
    if extra_holidays:
        master.holidays.update(extra_holidays)
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    base = datetime.date(2026, 9, 7)
    roster, punches, src = [], {}, {}
    for person, off, raw, hrs, times in rows:
        d = base + datetime.timedelta(days=off)
        roster.append({"person": person, "date": d, "block": "", "raw": raw, "hours": hrs,
                       "shift": parse_code(raw, OUTLETS, master.text_labels)})
        if times:
            punches[(person, d)] = PunchDay(times)
        src[person] = "HRMS transactions PLM"
    return Engine(master, rules).run(month, roster, {}, punches, src, None, [])


def test_d1_overrun_never_flagged_or_texted():          # decisions 1 and 10
    for out in ("22:20", "22:30", "22:02", "22:48"):
        res = _run("12-10PM", {0: ["12:00", out]})
        assert not [f for f in res["flags"] if "Out after shift end" in f.flag]
        assert "Out after shift end" not in res["day_rows"][0]["flags"]
        assert res["day_rows"][0]["hq_out"] == "22:00"       # still capped at the shift end


def test_d1_ot_candidate_only_above_threshold():
    minor = _run("12-10PM", {0: ["12:00", "22:30"]})          # exactly 30 min: no count
    assert minor["day_rows"][0]["ot_cand"] == 0 and "OT candidate" not in minor["day_rows"][0]["remark"]
    assert minor["people"]["SAM"].m["otc_days"] == 0
    big = _run("10-18:30", {0: ["10:00", "22:02"]})           # 212 min
    r = big["day_rows"][0]
    assert r["ot_cand"] == 212 and "Clocked out after shift end (OT candidate, pending approval)" in r["remark"] and r["hq_out"] == "18:30"
    m = big["people"]["SAM"].m
    assert (m["otc_days"], m["otc_min"], m["otc_max"]) == (1, 212, 212)
    assert big["ledger"]["otc_days"] == 1


def test_d1_closing_time_from_roster_not_punches():
    sh = lambda raw, outlet=None: parse_code(raw, OUTLETS)
    mk = lambda p, raw: {"person": p, "shift": parse_code(raw, OUTLETS)}
    generic = {("10:00", "22:00"), ("14:00", "22:00"), ("12:00", "22:00")}
    rows = [mk("A", "10-8PM")] * 5 + [mk("A", "FULL")] * 2 + [mk("B", "11-9PM")] * 4
    tab = derive_closing(rows, {"A": "OUT1", "B": "OUT6"}, generic)
    assert tab["OUT1"]["time"] == "20:00" and tab["OUT6"]["time"] == "21:00"
    assert tab["Admin"]["time"] is None and "20:00" not in tab["OUT1"]["minority"] and "22:00" in tab["OUT1"]["minority"]
    # generic-only labelled codes cannot decide on their own: falls through to the home-outlet staff codes
    rows2 = [mk("A", "OUT4 / FULL")] * 3 + [mk("C", "10-8PM")] * 4
    assert derive_closing(rows2, {"A": "OUT4", "C": "OUT4"}, generic)["OUT4"]["time"] == "20:00"


def test_d1_past_closing_remark_only():
    res = _multi([("SAM", 0, "10-8PM", None, ["10:00", "20:20"])])
    r = res["day_rows"][0]
    closing = res["closing"].get(res["people"]["SAM"].home_outlet, {}).get("time")
    assert r["closing"] == closing
    if closing and closing < "20:20":
        assert "Past closing time (reference)" in r["remark"]
    assert [f for f in res["flags"] if "closing" in f.flag.lower()] == []


def test_d2_unlabelled_stats_inputs():
    res = _multi([("SAM", i, "10-6.30PM", None, ["10:00", t]) for i, t in enumerate(["19:00", "19:30", "20:00"])])
    P = res["people"]["SAM"]
    assert P.deltas == [30, 60, 90] and statistics.median(P.deltas) == 60 and P.codes == {"10-6.30PM": 3}


def test_d3_partial_one_row_per_person_with_dates():
    res = _run("10-8PM", {0: ["10:00", "20:00"], 2: ["10:00", "20:00"], 3: ["10:00", "20:00"]}, extra_days=19)
    rows = [f for f in res["flags"] if f.flag == "Data incomplete in the trial"]
    assert len(rows) == 1 and "punches only on 7 and 9 to 10 Sep" in rows[0].details
    assert rows[0].remark_type == "Pending question" and "partial export" in rows[0].remark
    assert not [f for f in res["flags"] if "No punch" in f.flag]
    assert res["ledger"]["partial_nopunch_days"] == 17


def test_d3_fmt_dates():
    d = lambda n: datetime.date(2026, 9, n)
    assert fmt_dates([d(25), d(26), d(27), d(28)]) == "25 to 28 Sep"
    assert fmt_dates([d(24)] + [d(n) for n in range(26, 31)]) == "24 and 26 to 30 Sep"


def test_d4_implausible_late_is_one_check_not_a_late():
    res = _run("12-10PM", {0: ["20:01", "22:00"]})
    fl = [f for f in res["flags"] if f.flag == "Possible missing clock-in"]
    assert len(fl) == 1 and fl[0].severity == "Check"
    assert res["people"]["SAM"].m["late_days"] == 0 and not [f for f in res["flags"] if f.flag.startswith("Clock-in after shift start")]


def test_d5_late_has_no_grace():
    r = _day("10-8PM", ["10:01", "20:00"])
    assert r["hq_in"] == "10:30"
    res = _run("10-8PM", {0: ["10:01", "20:00"]})
    assert res["people"]["SAM"].m["late_days"] == 1


def test_d6_public_holiday_merged_one_row_per_date():
    ph = datetime.date(2026, 9, 9)
    off = (ph - datetime.date(2026, 9, 7)).days
    res = _multi([(p, off, "10-8PM", None, ["10:00", "20:00"]) for p in ("SAM", "JORDAN")],
                 extra_holidays={ph: "Sample public holiday"})
    rows = [f for f in res["flags"] if f.flag == "Worked on a public holiday"]
    assert len(rows) == 1 and rows[0].date == ph and "OT rate pending Q3/Q21" in rows[0].remark
    assert res["ledger"]["ph_person_days"] == 2 and res["ledger"]["ph_rows"] == 1


def test_d7_info_rows_move_to_data_coverage():
    res = _multi([("SAM", 0, "10-8PM*", None, ["10:00", "20:00"])])
    assert not [f for f in res["flags"] if f.severity == "Info" and "asterisk" in f.flag.lower()]
    assert [m for m in res["moved"] if m[0] == "Roster code carries an asterisk" and m[1] == "SAM" and m[4] == 1]


def test_d8_end_only_code_assumed_start_flagged():
    res = _multi([("TAYLOR", 0, "OUT1/6.30PM", None, ["10:12", "18:40"])])
    r = res["day_rows"][0]
    fl = [f for f in res["flags"] if f.flag == "Roster start time missing"]
    assert len(fl) == 1 and fl[0].severity == "Check" and fl[0].remark_type == "Pending question"
    assert (r["start"], r["end"]) == ("10:00", "18:30")
    assert r["hq_in"] == "10:12" and r["hq_out"] == "18:30"  # no rounding on end-only: Admin In = max(10:00, first punch) = 10:12 exactly
    assert res["people"]["TAYLOR"].m["late_days"] == 0 and not [f for f in res["flags"] if f.flag.startswith("Clock-in after shift start")]


def test_d8_end_only_first_punch_far_after_start_leaves_hq_blank():
    # Boss, 16 Oct option 3: Admin In = max(10:00, first punch). 13:32 is after 10:00 so Admin In = 13:32 (not blank).
    res = _multi([("TAYLOR", 0, "OUT1/6.30PM", None, ["13:32", "18:40"])])
    r = res["day_rows"][0]
    assert r["hq_in"] == "13:32" and r["hq_out"] == "18:30"
    assert [f for f in res["flags"] if f.flag == "Roster start time missing"]


def test_d9_hours_mismatch_one_remark_per_person_trusting_code():
    res = _multi([("SAM", i, "FULL", 8, ["10:00", "22:00"]) for i in range(3)])
    fl = [f for f in res["flags"] if f.flag.startswith("Roster hours differ")]
    assert len(fl) == 1 and "code FULL = 12 h vs roster hours column 8 (3 day(s))" in fl[0].details
    assert res["day_rows"][0]["working"] == 12            # code trusted, hours column ignored


def test_full_data_missing_day_stays_red():
    res = _run("10-8PM", {i: ["10:00", "20:00"] for i in range(9)}, extra_days=9)  # 9 of 10 = 90%
    assert not res["people"]["SAM"].partial
    red = [f for f in res["flags"] if f.remark_type == "Possible error" and "No punch" in f.flag]
    assert len(red) == 1


def test_summary_total_formula_not_stale_and_consistent():
    src = (ROOT / "src" / "report.py").read_text(encoding="utf-8")
    assert "A2:A137" not in src and "COUNT(Flags!A:A)" in src
    assert "D{k1}+D{k2}+D{k3}=D{kt}" in src and "D{r1}+D{r2}+D{r3}=D{kt}" in src




# ---- 16 Oct data gaps: one test per changed rule ----------------------------------------------------------
import pytest as _pt
from src.report import _merge_same_ref
from src.run import run as _run_month

NAL = "Not assessed, missing data"


def _multi_src(rows, source):
    master = load_master(ROOT / "03_MASTER_DATA")
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    base = datetime.date(2026, 9, 7)
    roster, punches, src = [], {}, {}
    for person, off, raw, times in rows:
        d = base + datetime.timedelta(days=off)
        roster.append({"person": person, "date": d, "block": "", "raw": raw, "hours": None,
                       "shift": parse_code(raw, OUTLETS, master.text_labels)})
        if times:
            punches[(person, d)] = PunchDay(times)
        if source.get(person):
            src[person] = source[person]
    return Engine(master, rules).run("2026-09", roster, {}, punches, src, None, [])


def test_g_label_is_one_exact_string_in_rules():
    rules = load_rules(ROOT / "03_MASTER_DATA" / "rules.toml")
    assert rules.get("not_assessed_label") == NAL and rules.get("no_data_day_remark") == "No data (source gap)"
    assert rules.get("large_late_min") == 90 and rules.status("not_assessed_label") == "ASSUMED"


def test_g1_not_assessed_rule_no_clock_file_partial_and_adequate():
    rows = [("SAM", i, "10-8PM", ["10:00", "20:00"]) for i in range(10)]                          # 100% adequate
    rows += [("JORDAN", i, "10-8PM", ["10:00", "20:00"] if i == 0 else None) for i in range(10)]       # 10% partial
    rows += [("ROBIN", i, "10-8PM", None) for i in range(10)]                                          # no clock file
    res = _multi_src(rows, {"SAM": "HRMS transactions PLM", "JORDAN": "HRMS transactions PLM"})
    P = res["people"]
    assert (P["SAM"].not_assessed, P["JORDAN"].not_assessed, P["ROBIN"].not_assessed) == (False, True, True)
    assert P["JORDAN"].partial and not P["ROBIN"].partial and P["JORDAN"].punch_dates == "7 Sep"
    half = _multi_src([("SAM", i, "10-8PM", ["10:00", "20:00"] if i < 5 else None) for i in range(10)], {"SAM": "x"})
    assert not half["people"]["SAM"].not_assessed        # exactly 50% is adequate (rule is "fewer than")


def test_g4_gap_day_remark_and_no_flag():
    rows = [("JORDAN", i, "10-8PM", ["10:00", "20:00"] if i == 0 else None) for i in range(10)] + \
           [("ROBIN", i, "10-8PM", None) for i in range(4)]
    res = _multi_src(rows, {"JORDAN": "HRMS transactions PLM"})
    gap = [r for r in res["day_rows"] if r["remark"] == "No data (source gap)"]
    assert len(gap) == 9 + 4 and all(r["flags"] == "" for r in gap)
    assert not [f for f in res["flags"] if f.person in ("JORDAN",) and "No punch" in f.flag]
    assert [f for f in res["flags"] if f.flag == "Data incomplete in the trial" and f.person == "JORDAN"]   # per-person row stays
    assert res["people"]["JORDAN"].m["missing_days"] == 0       # a source gap is not a missing punch


def test_g3_weekly_counts_punch_days_per_week():
    rows = [("JORDAN", i, "10-8PM", ["10:00", "20:00"] if i in (8, 9) else None) for i in range(14)]
    res = _multi_src(rows, {"JORDAN": "HRMS transactions PLM"})
    wk = {k[1]: v for k, v in res["weekly"].items() if k[0] == "JORDAN"}
    assert wk[datetime.date(2026, 9, 7)]["punches"] == 0 and wk[datetime.date(2026, 9, 14)]["punches"] == 2


@_pt.mark.parametrize("first,flag_late,remark", [("11:29", True, False), ("11:30", True, True), ("12:30", True, True),
                                                 ("13:59", True, True), ("14:01", False, False)])
def test_g9_large_late_remark_only(first, flag_late, remark):
    res = _run("10-8PM", {0: [first, "20:00"]})        # start 10:00: 89 / 90 / 150 / 239 / 241 min late
    r = res["day_rows"][0]
    late_flags = [f for f in res["flags"] if f.flag.startswith("Clock-in after shift start")]
    assert bool(late_flags) == flag_late
    assert ("Large late, check roster shift (Admin)" in r["remark"]) == remark
    assert res["people"]["SAM"].m["late_days"] == (1 if flag_late else 0)
    assert len([f for f in res["flags"]]) == len(late_flags) + len([f for f in res["flags"] if not f.flag.startswith("Clock-in after shift start")])


def test_g8_pending_merge_keeps_every_assumption():
    rows = [["Q19", "A", "why1", "did1", "{admin} or Admin"], ["Q19", "B", "why2", "did2", "{admin} or Admin"], ["Q19", "A", "why1", "did3", "Boss"],
            ["Q7", "C", "w", "d", "Boss"], ["Q7", "D", "w", "d", "Boss"]]
    out = _merge_same_ref(rows, " / ")
    assert [r[0] for r in out] == ["Q19", "Q7", "Q7"]          # only Boss's refs (Q19, Q15, Q2) are merged
    q19 = out[0]
    assert "A" in q19[1] and "B" in q19[1] and q19[1].count("A") == 1
    assert all(x in q19[3] for x in ("did1", "did2", "did3")) and q19[4] == "{admin} or Admin / Boss"


# ---- 16 Oct merged AB+C --------------------------------------------------------------------------
from src.comments import CODES, CANON, canon, JOIN
NAL = "Not assessed, missing data"


def test_a_end_only_max_opening_and_first_punch():
    # First punch 09:46 -> Admin In = 10:00; first punch 10:05 -> Admin In = 10:05.
    for first, want_in in (("09:46", "10:00"), ("10:05", "10:05")):
        res = _run("OUT1/6.30PM", {0: [first, "19:00"]})
        r = res["day_rows"][0]
        assert r["hq_in"] == want_in, (first, want_in, r["hq_in"])
        assert r["early"] == 0, "Early 1.5 shortfall must be 0 on end-only days"
        assert "Roster start time missing" in r["remark"]


def test_a_end_only_no_clock_in_day():
    res = _run("OUT1/6.30PM", {})          # no punches at all
    r = res["day_rows"][0]
    assert r["hq_in"] is None and r["hq_out"] is None and r["remark"].startswith("Roster start missing and no clock-in")
    assert any(f.flag == "Roster start missing and no clock-in" for f in res["flags"])
