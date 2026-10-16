"""Write the monthly Attendance report workbook (one file, tabs PLM and PLG)."""
from __future__ import annotations

import datetime
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L

from src.comments import CODES, SEVERITY_ORDER, glossary_rows, code_for, canon
from src.engine import EXCLUDED, NOT_ASSESSED, OFFSITE

RED, AMBER, GREEN = "FFFFC7CE", "FFFFEB9C", "FFC6EFCE"
NEUTRAL = "FFE7E6E6"
HEAD = PatternFill("solid", fgColor="FF1A1A1A")
HEAD_FONT = Font(bold=True, color="FFFFFFFF")
FILL = {"Possible error": RED, "Pending question": AMBER, "Confirmed rule": GREEN}
SEV = {"Blocker": 0, "Check": 1, "Info": 2}

PENDING = {
    "duplicate_punch_window_minutes": ("A double tap can look like a full in/out pair.", "Collapsed taps within the window, kept the first."),
    "duplicate_punch_keep": ("Decides which tap of a pair counts.", "Kept the first; flagged each person with collapsed taps."),
    "single_punch_classification": ("A lone punch could be a clock-in or a clock-out.", "Nearest-boundary reading, flagged Check, no Admin times."),
    "single_punch_tie_minutes": ("Lone punches near the shift middle cannot be told apart.", "Not guessed: flagged as unclassifiable."),
    "leave_day_hours": ("Record tabs show 8:00, the legend says 8:30.", "Credited 8.5 h to the weekly total for leave and PH days; shown amber."),
    "upl_absent_unpaid": ("Decides pay for UPL and ABSENT days.", "Counted and listed on the Leave summary tab; nothing deducted."),
    "half_day_leave_hours": ("Half-day leave such as 12-3PM / AL has no agreed hours.", "Day flagged, hours not computed."),
    "ot_rate_day_types": ("OT 2.0 and 3.0 need the day type rules.", "Punches on rest or holiday days listed with no rate."),
    "asterisk_code_meaning": ("PH*, MC*, OFF*, UPL* and shift codes with * are not defined.", "Base code used; asterisk days flagged Info."),
    "named_shift_times": ("FULL, AM and PM have no written times.", "FULL 10:00-22:00, AM 10:00-18:00, PM 14:00-22:00."),
    "break_handling": ("The HRMS transactions carry break columns.", "Ignored: Working = Admin Out minus Admin In, as in the HR sheet."),
    "offsite_treatment": ("REMOTE1 is off-site WFH with no roster, so there is no shift to check against.", "Real punches and Working shown; no rounding, late, early or capped flags; weekly hours counted, OT not assessed."),
    "partial_data_threshold_pct": ("Some people's data was withheld for the trial, so most of their days have no punch.", "Below the threshold: one Flags row per person (punches only on the listed dates), no no-punch rows; listed on Data coverage."),
    "daily_vs_weekly_ot": ("HR sheet nets daily; the Admin answer is weekly over 51 h.", "Both shown: net OT 1.5 (daily) and weekly hours over 51."),
}
WHO = {}
EXTRA_PENDING_FIXED = [
    ("Q19", "End-only roster code (e.g. OUT1/6.30PM): roster gives outlet and end, no start.",
     "The roster lists a shift end but no start, so no scheduled start to check lates against.",
     "Admin In = max(10:00, first punch); flagged for HR attention. Shortfall set to 0."),
]
EXTRA_PENDING = [
    ("Q2", "OT candidates (punch-out more than 30 min after the shift end, e.g. CASEY 22:02 on a 10-18:30 shift): authorised OT or roster not updated? HR decides.",
     "Time after the shift end is not counted unless authorised.", "Admin Out capped at the shift end; no flag. Listed per person (days, total and max minutes) on Summary and Weekly OT. Pending approval, never an approval."),
    ("Q21", "Company PH calendar: which public holidays does {client} observe (federal, state, company-specific)? Please supply or confirm the calendar.",
     "Decides which days count as public-holiday work (excluded from OT 1.5) and which roster PH codes are valid.",
     "Used the 2026 list in public_holidays.csv; PH codes on dates outside it are flagged."),
    ("Q6", "Staff and outlet aliases: which block do CASEY, MORGAN and TAYLOR sit in?",
     "Wrong aliases put people in the wrong company or outlet.", "Used the staff map; each case is flagged in Flags. DIR1 is a shareholder and director, excluded."),
]


MERGE_REFS = {"Q19", "Q15", "Q2"}   # Boss, 16 Oct 2026 (change 8): one row per Ref; no assumption is dropped


def _merge_same_ref(rows, who_sep):
    """Merge rows sharing a Ref in MERGE_REFS. Every distinct text of every column is kept."""
    groups, order_ = {}, []
    for r in rows:
        k = r[0] if r[0] in MERGE_REFS else id(r)
        if k not in groups:
            groups[k] = []
            order_.append(k)
        groups[k].append(r)
    out = []
    for k in order_:
        g = groups[k]
        if len(g) == 1:
            out.append(g[0])
            continue
        merged = [g[0][0]]
        for c in range(1, len(g[0])):
            items = []
            for r in g:
                if r[c] and r[c] not in items:
                    items.append(r[c])
            if not items:
                merged.append(None)
            elif len(items) == 1:
                merged.append(items[0])
            elif c == len(g[0]) - 1:
                merged.append(who_sep.join(items))      # last column: who can correct / source
            else:
                merged.append("\n".join(f"• {x}" for x in items))
        out.append(merged)
    return out


def _head(ws, row, headers, widths=None):
    for i, h in enumerate(headers, 1):
        c = ws.cell(row, i, h)
        c.fill, c.font = HEAD, HEAD_FONT
        c.alignment = Alignment(wrap_text=True, vertical="center")
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[L(i)].width = w


def write_report(path: Path, month: str, res: dict, ctx: dict, rules, master):
    y, mo = map(int, month.split("-"))
    title = datetime.date(y, mo, 1).strftime("%B %Y")
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    people, order = res["people"], res["order"]
    NAL = rules.get("not_assessed_label")
    led = res["ledger"]
    mv = res["moved"]
    flags = sorted(res["flags"], key=lambda f: (SEV.get(f.severity, 9), f.company, order.index(f.person) if f.person in order else 99,
                                                0 if f.date == "Month" else 1, str(f.date)))
    # ---------------------------------------------------------------- Flags (written first for row refs)
    wf = wb.create_sheet("Flags")
    _head(wf, 1, ["#", "Severity", "Flag", "Code", "Person", "Home outlet (tab)", "Date", "Details", "Remark",
                  "Remark type", "Ref", "Company"], [5, 10, 40, 7, 11, 12, 12, 70, 50, 15, 9, 10])
    for i, f in enumerate(flags, 1):
        flag_std = canon(f.flag)
        vals = [i, f.severity, flag_std, code_for(flag_std), f.person, f.home_outlet, f.date, f.details, f.remark, f.remark_type, f.ref, f.company]
        for j, v in enumerate(vals, 1):
            c = wf.cell(i + 1, j, v)
            if j == 7 and isinstance(v, datetime.date):
                c.number_format = "yyyy-mm-dd"
            if j in (9, 10, 11):
                c.fill = PatternFill("solid", fgColor=FILL.get(f.remark_type, AMBER))
            if j in (8, 9):
                c.alignment = Alignment(wrap_text=True, vertical="top")
    wf.freeze_panes = "A2"
    wf.auto_filter.ref = f"A1:L{max(2, len(flags) + 1)}"
    nflags = len(flags) + 1

    # ---------------------------------------------------------------- Day tabs
    cols = ["Person", "Date", "Day", "Schedule code", "Type", "Shift start", "Shift end", "Closing time", "Punches", "Clock outlet",
            "System In", "System Out", "Admin In", "Admin Out", "Flags", "Working (h)", "OT 1.5 (h)", "Early 1.5 (h)", "Day remark"]
    widths = [11, 11, 6, 15, 9, 10, 10, 10, 26, 13, 10, 10, 16, 16, 50, 11, 10, 11, 44]
    for co in ("PLM", "PLG"):
        wd = wb.create_sheet(co)
        _head(wd, 1, cols, widths)
        rr = 2
        pidx = {p: i for i, p in enumerate(order)}
        for r in sorted([x for x in res["day_rows"] if x["company"] == co], key=lambda x: (pidx[x["person"]], x["date"])):
            vals = [r["person"], r["date"], r["day"], r["code"], r["type"], r["start"], r["end"], r["closing"], r["punches"], r["outlet"],
                    r["sys_in"], r["sys_out"], r["hq_in"], r["hq_out"], r["flags"],
                    r["working"], r["ot"], r["early"], r["remark"]]
            for j, v in enumerate(vals, 1):
                c = wd.cell(rr, j, v)
                if j == 2:
                    c.number_format = "yyyy-mm-dd"
                if j in (15, 19):
                    c.alignment = Alignment(wrap_text=True, vertical="top")
                if j in (16, 17, 18) and v is not None:
                    c.number_format = "0.00"
            rr += 1
        wd.freeze_panes = "B2"
        wd.page_setup.orientation = "landscape"; wd.page_setup.fitToWidth = 1; wd.page_setup.fitToHeight = 0
        wd.sheet_properties.pageSetUpPr.fitToPage = True; wd.print_title_rows = "1:1"
        wd.auto_filter.ref = f"A1:S{max(2, rr - 1)}"

    # ---------------------------------------------------------------- Weekly
    ww = wb.create_sheet("Weekly OT")
    _head(ww, 1, ["Person", "Company", "Week starts (Mon)", "Work days", "Worked hours (Admin)", "Leave / PH credit (h)",
                  "Total (h)", "Over 51 h", "Week type",
                  "Daily OT 1.5 (HR method, above 8:30/day), reference only",
                  "OT candidate (days, > 30 min after shift end)", "OT candidate total (min)", "OT candidate max (min)"],
          [11, 9, 16, 10, 16, 18, 10, 10, 26, 30, 16, 14, 14])
    daily_ot = defaultdict(float)
    for dr in res["day_rows"]:
        if dr["ot"]:
            daily_ot[(dr["person"], dr["date"] - datetime.timedelta(days=dr["date"].weekday()))] += dr["ot"]
    wr = 2
    weekly_full_over = defaultdict(float)
    for (sid, wk), v in sorted(res["weekly"].items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1])):
        if v["days"] == 0 and v["hours"] == 0:
            continue
        end = wk + datetime.timedelta(days=6)
        full = wk.month == mo and end.month == mo and wk.year == y
        ww.cell(wr, 1, sid); ww.cell(wr, 2, people[sid].company)
        ww.cell(wr, 3, wk).number_format = "yyyy-mm-dd"
        ww.cell(wr, 4, v["days"]); ww.cell(wr, 5, round(v["hours"], 2)); ww.cell(wr, 6, round(v["leave"], 2))
        ww.cell(wr, 7, f"=E{wr}+F{wr}"); ww.cell(wr, 8, f"=MAX(0,G{wr}-{rules.get('weekly_ot_threshold_hours')})")
        ww.cell(wr, 9, "Full week" if full else "Partial week (spans two months): indicative only")
        ww.cell(wr, 10, round(daily_ot.get((sid, wk), 0.0), 2))
        oc = res["otc"].get((sid, wk), [])
        ww.cell(wr, 11, len(oc)); ww.cell(wr, 12, sum(oc)); ww.cell(wr, 13, max(oc) if oc else 0)
        if people[sid].not_assessed and v.get("punches", 0) == 0:     # a week with no data is not a week of zeros
            for col_ in (5, 7, 8, 10, 11, 12, 13):
                ww.cell(wr, col_, NAL)
        if sid in OFFSITE:
            ww.cell(wr, 8, NOT_ASSESSED); ww.cell(wr, 10, NOT_ASSESSED)
        if full and sid not in OFFSITE and not (people[sid].not_assessed and v.get("punches", 0) == 0):
            over = max(0.0, v["hours"] + v["leave"] - rules.get("weekly_ot_threshold_hours"))
            weekly_full_over[sid] += over
        wr += 1
    ww.cell(wr + 3, 1, "OT candidate = punch-out more than 30 min after the shift end (rule ot_candidate_threshold_min). Admin Out stays capped at the shift end, so Working is unchanged. "
                       "Pending approval, never an approval.")
    ww.cell(wr + 2, 1, "The weekly column is the Admin Q18 rule. The daily column mirrors HR's May sheet so the two can be reconciled. Neither is an approval.")
    ww.cell(wr + 1, 1, "Pending approval (Q18). Hours are Admin In/Out working hours; leave and PH days are credited at the leave-day hours (assumed, Q11). "
                       "Partial weeks at the month edges are not counted in the Summary.")
    ww.freeze_panes = "A2"

    # ---------------------------------------------------------------- Leave summary
    wl = wb.create_sheet("Leave summary")
    _head(wl, 1, ["Person", "Company", "AL", "MC", "EL", "UPL", "ABSENT", "PH", "OFF (rest)", "MC dates", "UPL dates", "ABSENT dates"],
          [11, 9, 6, 6, 6, 6, 9, 6, 11, 40, 40, 40])
    lr = 2
    for sid in order:
        lv = res["leave"].get(sid)
        if not lv:
            continue
        fmt = lambda k: ", ".join(d.strftime("%d %b") for d in lv.get(k, []))
        vals = [sid, people[sid].company, len(lv.get("al", [])), len(lv.get("mc", [])), len(lv.get("el", [])),
                len(lv.get("upl", [])), len(lv.get("absent", [])), len(lv.get("ph", [])), len(lv.get("off", [])),
                fmt("mc"), fmt("upl"), fmt("absent")]
        for j, v in enumerate(vals, 1):
            wl.cell(lr, j, v)
        lr += 1
    wl.cell(lr + 1, 1, f"Counts are from the {title} roster codes. MC needs a certificate and receipt (Admin Q18); UPL and ABSENT pay treatment is pending (Q11).")
    wl.freeze_panes = "A2"

    # ---------------------------------------------------------------- No clock file
    wn = wb.create_sheet("No clock file")
    _head(wn, 1, ["Person", "Company", "Home outlet (tab)", "Roster work days", "Reason"], [11, 9, 16, 16, 90])
    nr = 2
    for sid in order:
        P = people[sid]
        if P.source == "none" and P.m["work_days"] > 0:
            wn.cell(nr, 1, sid); wn.cell(nr, 2, P.company); wn.cell(nr, 3, P.home_outlet)
            wn.cell(nr, 4, int(P.m["work_days"]))
            wn.cell(nr, 5, ctx["noclock_reason"](P))
            nr += 1
    wn.cell(nr + 1, 1, "Trial batch: these people have roster days but no punch data. Nothing was inferred or pasted in; Admin in/out and flags are blank for them.")
    wn.freeze_panes = "A2"

    # ---------------------------------------------------------------- Data coverage
    wc = wb.create_sheet("Data coverage")
    r0 = 1
    wc.cell(r0, 1, f"Data coverage: {title}").font = Font(bold=True, size=13)
    r0 += 1
    wc.cell(r0, 1, ctx["excluded_note"]).fill = PatternFill("solid", fgColor=NEUTRAL)
    r0 += 1
    wc.cell(r0, 1, ctx["offsite_note"]).fill = PatternFill("solid", fgColor=NEUTRAL)
    for sid_ in order:
        if people[sid_].partial:
            r0 += 1
            wc.cell(r0, 1, f"{sid_}: {int(people[sid_].m['cov_days'])} of {int(people[sid_].m['cov_sched'])} scheduled days have punches. "
                           "Source data incomplete in this trial.").fill = PatternFill("solid", fgColor=NEUTRAL)
    r0 += 2
    _head(wc, r0, ["Source", "File / scope", "Content", "Note"], [30, 46, 40, 70]); r0 += 1
    for s in ctx["sources"]:
        for j, v in enumerate(s, 1):
            wc.cell(r0, j, v).alignment = Alignment(wrap_text=True, vertical="top")
        r0 += 1
    r0 += 1
    wc.cell(r0, 1, "By outlet (roster block)").font = Font(bold=True); r0 += 1
    for i, h in enumerate(["Outlet", "Company", "Clock data for this outlet", "People on roster", "Scheduled work days", "Days with punches / scheduled"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    for o in ctx["outlet_cov"]:
        # o = (outlet, company, clock_source, people_count, sched_days, with_punches, coverage_pct)
        wc.cell(r0, 1, o[0]); wc.cell(r0, 2, o[1]); wc.cell(r0, 3, o[2]); wc.cell(r0, 4, o[3])
        wc.cell(r0, 5, o[4])
        if isinstance(o[5], int) and isinstance(o[4], int) and o[4]:
            wc.cell(r0, 6, f"{o[5]} of {o[4]}")
        else:
            wc.cell(r0, 6, "n/a")
        r0 += 1
    r0 += 1
    wc.cell(r0, 1, "By person").font = Font(bold=True); r0 += 1
    for i, h in enumerate(["Person", "Company", "Punch source", "Scheduled work days", "Work days with punches", "Work days with no punch", "Days with punches / scheduled"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    for sid in order:
        P = people[sid]
        wd_ = int(P.m["work_days"]); got = wd_ - int(P.m["nopunch_work"])
        wc.cell(r0, 1, sid); wc.cell(r0, 2, P.company); wc.cell(r0, 3, P.source)
        wc.cell(r0, 4, wd_); wc.cell(r0, 5, got if P.source != "none" else 0)
        wc.cell(r0, 6, wd_ - got if P.source != "none" else wd_)
        wc.cell(r0, 7, f"{got} of {wd_}" if (wd_ and P.source != "none") else ("n/a" if not wd_ else f"0 of {wd_}"))
        r0 += 1

    r0 += 1
    wc.cell(r0, 1, "Files needed (derived from the data)").font = Font(bold=True); r0 += 1
    for i, h in enumerate(["File needed", "Needed for", "Why", "Note"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    need = {}
    for o_ in ctx["outlet_cov"]:
        if str(o_[2]).startswith("NO DATA"):
            ppl_ = [x for x in order if people[x].home_outlet == o_[0] and people[x].m["work_days"] > 0]
            need.setdefault(ctx["clock_source"](o_[0]), []).append((ppl_, f"No clock file for {o_[0]} in this batch", "Not provided in this batch."))
    for sid in order:
        P = people[sid]
        if P.partial:
            need.setdefault(ctx["clock_source"](P.home_outlet), []).append(
                ([sid], f"Punches only on {P.punch_dates} ({int(P.m['cov_days'])} of {int(P.m['cov_sched'])} scheduled days)",
                 "Likely held in the outlet exports (inference, not confirmed)."))
    if not need:
        wc.cell(r0, 1, "None: no outlet is missing a clock file and no person is below the partial-data threshold."); r0 += 1
    for f_, lst in need.items():
        names_ = ", ".join(dict.fromkeys(n_ for l_ in lst for n_ in l_[0]))
        why_ = "; ".join(dict.fromkeys(l_[1] for l_ in lst))
        note_ = "; ".join(dict.fromkeys(l_[2] for l_ in lst))
        for j, x in enumerate([f_, names_, why_, note_], 1):
            wc.cell(r0, j, x).alignment = Alignment(wrap_text=True, vertical="top")
        r0 += 1
    r0 += 1
    wc.cell(r0, 1, "Outlet closing time (derived from the roster; reference only)").font = Font(bold=True); r0 += 1
    wc.cell(r0, 1, "Most common shift end per outlet, from roster codes only (never from punches, never guessed). Generic all-day codes (FULL, PM, 12-10PM) do not set it on their own. "
                   "Minority end times are a note only: no flag, no Pending item.")
    r0 += 1
    for i, h in enumerate(["Outlet", "Closing time", "Source", "Shifts supporting it", "Shifts considered", "Minority end times seen"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    for o, v in sorted(res["closing"].items()):
        for j, x in enumerate([o, v["time"] or "none", v["source"], v["support"] or None, v["considered"] or None, v["minority"]], 1):
            wc.cell(r0, j, x)
        r0 += 1
    r0 += 1
    wc.cell(r0, 1, "Unlabelled roster block (CASEY, MORGAN, TAYLOR): roster code and minutes past shift end").font = Font(bold=True); r0 += 1
    for i, h in enumerate(["Person", "Roster code(s), work days", "Days worked (with punches)", "Median min past shift end", "Max min past shift end", "Days with a full punch pair"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    import statistics
    for sid in res["unlabelled"]:
        P = people[sid]
        dl = P.deltas
        codes = ", ".join(f"{c} x{n}" for c, n in sorted(P.codes.items(), key=lambda kv: -kv[1]))
        for j, x in enumerate([sid, codes, int(P.m["work_days"] - P.m["nopunch_work"]),
                               statistics.median(dl) if dl else None, max(dl) if dl else None, len(dl)], 1):
            wc.cell(r0, j, x)
        r0 += 1
    wc.cell(r0, 1, "Minutes past shift end = real punch-out minus the roster shift end, every day with a full punch pair (negative = early). Informational; no flag.")
    r0 += 2
    wc.cell(r0, 1, "Info items moved out of Flags (still counted)").font = Font(bold=True); r0 += 1
    for i, h in enumerate(["Item", "Person", "Company", "Home outlet", "Days", "Detail", "Why"], 1):
        c = wc.cell(r0, i, h); c.fill, c.font = HEAD, HEAD_FONT
    r0 += 1
    tot = defaultdict(lambda: [0, 0])
    for it in sorted(res["moved"], key=lambda x: (x[0], x[2], x[1])):
        for j, x in enumerate(it, 1):
            wc.cell(r0, j, x).alignment = Alignment(wrap_text=True, vertical="top")
        tot[it[0]][0] += 1; tot[it[0]][1] += it[4]
        r0 += 1
    r0 += 1
    for k_, (n_, d_) in sorted(tot.items()):
        wc.cell(r0, 1, f"{k_}: {n_} person rows, {d_} days"); r0 += 1
    r0 += 1
    wc.cell(r0, 1, "Suppressed, merged or moved: counts").font = Font(bold=True); r0 += 1
    for t_ in [f"Out after shift end of 30 min or less: {led.get('overrun_minor_days', 0)} days, Admin Out capped, no count (rule ot_candidate_threshold_min)",
               f"OT candidates (more than 30 min): {led.get('otc_days', 0)} days, per person on Summary and Weekly OT",
               f"Partial-data no-punch days not flagged one by one: {led.get('partial_nopunch_days', 0)}",
               f"Public holiday worked: {led.get('ph_person_days', 0)} person-days merged into {led.get('ph_rows', 0)} rows",
               f"Roster hours differ from the code: {led.get('hours_mismatch_days', 0)} person-days, {led.get('hours_mismatch_people', 0)} person rows",
               f"Possible missing clock-in: {led.get('implausible_late_days', 0)} days, not counted as lates",
               f"Days with roster start missing: " + str(led.get('end_only_days', 0)) + " (end-only roster code; max(10:00, first punch))"]:
        wc.cell(r0, 1, t_); r0 += 1

    # ---------------------------------------------------------------- Aliases
    wa = wb.create_sheet("Aliases")
    wa.cell(1, 1, "Outlet and staff aliases: from {admin}'s Other Information file and the staff map. Status shows how sure each row is.").font = Font(bold=True)
    _head(wa, 2, ["Outlet ID", "Company", "Name", "Code on clock file", "Other names", "Status"], [12, 12, 30, 18, 24, 50])
    ar = 3
    for oid, o in master.outlets.items():
        for j, v in enumerate([oid, o["company"], o["name"], o["clock_code"], o["other_names"], "Per {admin}'s OUTLET LISTING and PLM/PLG column (13 Oct)"], 1):
            wa.cell(ar, j, v)
        wa.cell(ar, 6).fill = PatternFill("solid", fgColor=GREEN)
        ar += 1
    ar += 1
    for i, h in enumerate(["Staff ID", "Full name", "Company", "Company source", "Home outlet", "Clock names (May)", "Note", "Status"], 1):
        c = wa.cell(ar, i, h); c.fill, c.font = HEAD, HEAD_FONT
    ar += 1
    wa.column_dimensions["G"].width = 60; wa.column_dimensions["H"].width = 24
    for sid, st in master.staff.items():
        p = people.get(sid)
        comp = p.company if p else (st["company"] or "")
        csrc = p.company_source if p else ("September transactions" if st["company"] else "")
        status = ("Excluded: shareholder/director" if sid in EXCLUDED else "Off-site, no roster (by design)" if sid in OFFSITE
                  else "Per September transactions" if st["company"]
                  else "Draft: company from home outlet")
        vals = [sid, st["full_name"], comp, csrc, st["home_outlet"], st["may_clock_names"], st["note"], status]
        for j, v in enumerate(vals, 1):
            wa.cell(ar, j, v)
        wa.cell(ar, 8).fill = PatternFill("solid", fgColor=GREEN if status.startswith("Per") else NEUTRAL if sid in EXCLUDED or sid in OFFSITE else AMBER)
        ar += 1

    # ---------------------------------------------------------------- Pending
    wp = wb.create_sheet("Pending")
    wp.cell(1, 1, "Pending questions (amber) and confirmed rules (green)").font = Font(bold=True)
    _head(wp, 2, ["Ref", "Question", "Why it matters", "What this report did meanwhile", "Who can correct"], [8, 80, 50, 60, 16])
    amber_rows = []
    for rule in rules.all_rules():
        if rule.status == "CONFIRMED":
            continue
        why, meanwhile = PENDING.get(rule.rule_id, ("", ""))
        amber_rows.append([rule.question, rule.label, why, meanwhile, WHO.get(rule.rule_id, "Boss / {admin}")])
    for ref, q, why, meanwhile in EXTRA_PENDING:
        amber_rows.append([ref, q, why, meanwhile, "Boss / HR"])
    if res["ledger"].get("end_only_days", 0) or res["ledger"].get("end_only_no_in_days", 0):
        for ref, q, why, meanwhile in EXTRA_PENDING_FIXED:
            amber_rows.append([ref, q, why, meanwhile, "HR / {admin}"])
    pr = 3
    for row_ in _merge_same_ref(amber_rows, " / "):
        for j, v in enumerate(row_, 1):
            wp.cell(pr, j, v).alignment = Alignment(wrap_text=True, vertical="top")
        wp.cell(pr, 1).fill = PatternFill("solid", fgColor=AMBER)
        pr += 1
    pr += 1
    _head(wp, pr, ["Ref", "Confirmed rule", "Source", ""])
    pr += 1
    conf_rows = [[rule.question or "-", rule.label, rule.source] for rule in rules.all_rules() if rule.status == "CONFIRMED"]
    for row_ in _merge_same_ref(conf_rows, "; "):
        for j, v in enumerate(row_, 1):
            wp.cell(pr, j, v).alignment = Alignment(wrap_text=True, vertical="top")
        wp.cell(pr, 1).fill = PatternFill("solid", fgColor=GREEN)
        pr += 1

    # ---------------------------------------------------------------- Summary
    GREY = PatternFill("solid", fgColor=NEUTRAL)
    na_people = [sid for sid in order if people[sid].not_assessed]
    n_people = sum(1 for sid in order if people[sid].m["work_days"] > 0 and sid not in OFFSITE)
    led, mv = res["ledger"], res["moved"]
    ws.cell(1, 1, f"Attendance report: {title}").font = Font(bold=True, size=14)
    ws.cell(2, 1, ctx["scope_line"])
    ws.cell(3, 1, "Read-only trial. Built from the duty roster and punch data only. Nothing was written into any record, roster or time-calculation file. "
                  "Missing data is flagged as no data and never filled.")
    if ctx.get("banner"):
        ws.cell(4, 1, f"Partial trial month: {len(na_people)} of {n_people} people {NAL} (clock exports for "
                      f"{', '.join(ctx['missing_outlets'])} not provided).").font = Font(bold=True)
        ws.cell(4, 1).fill = GREY
    # ---- Data gaps block (above the flag counts)
    ws.cell(5, 1, f"Data gaps: {len(na_people)} of {n_people} people {NAL}").font = Font(bold=True, size=12)
    for i_, h_ in enumerate(["Person / outlet", "Company", "Home outlet", "Coverage (days with punches / scheduled work days)", "Reason"], 1):
        c_ = ws.cell(6, i_, h_); c_.fill, c_.font = HEAD, HEAD_FONT
        c_.alignment = Alignment(wrap_text=True, vertical="center")
    gr = 7
    for o_ in ctx["outlet_cov"]:
        if str(o_[2]).startswith("NO DATA"):
            vals_ = [f"Outlet {o_[0]}", o_[1], o_[0], f"0 of {o_[4]}", f"No clock file for {o_[0]} in this batch ({o_[3]} people on the roster)"]
            for j_, v_ in enumerate(vals_, 1):
                ws.cell(gr, j_, v_).fill = GREY
            gr += 1
    for sid in na_people:
        P = people[sid]
        sched, got = int(P.m["cov_sched"]), int(P.m["cov_days"])
        reason = (ctx["noclock_reason"](P) if P.source == "none"
                  else f"Punches only on {P.punch_dates}; likely held in the outlet exports (inference, not confirmed)")
        for j_, v_ in enumerate([sid, P.company, P.home_outlet, f"{got} of {sched}", reason], 1):
            ws.cell(gr, j_, v_).fill = GREY
        gr += 1
    if gr == 7:
        ws.cell(gr, 1, "None: every person has adequate punch data.")
        gr += 1
    b0 = gr + 1                      # legend header row (was row 5 before the Data gaps block)
    ws.cell(b0, 1, "How to read the colours").font = Font(bold=True)
    for r_, (txt, col) in enumerate([("Red: possible error in the source files. Check it.", RED),
                                      ("Amber: depends on a pending question (see Pending tab). The PLM and PLG tabs have no colour: an OT candidate (punch-out more than 30 minutes after the shift end) and Past closing appear only in the Day remark.", AMBER),
                                      ("Green: a rule you confirmed was applied.", GREEN),
                                      (f"Grey: {NAL}. The roster never fills a gap; the value is left blank and labelled.", NEUTRAL)], b0 + 1):
        ws.cell(r_, 1, txt).fill = PatternFill("solid", fgColor=col)
    fb = b0 + 6                      # "Flag counts" header row
    ws.cell(fb, 1, "Flag counts").font = Font(bold=True)
    items = [("Blocker (do not write that person until fixed)", '=COUNTIF(Flags!B:B,"Blocker")'),
             ("Check (Admin decides)", '=COUNTIF(Flags!B:B,"Check")'),
             ("Info (logged only)", '=COUNTIF(Flags!B:B,"Info")'),
             ("Total flags", "=COUNT(Flags!A:A)"),
             ("Red: possible error", '=COUNTIF(Flags!J:J,"Possible error")'),
             ("Amber: pending question", '=COUNTIF(Flags!J:J,"Pending question")'),
             ("Green: confirmed rule", '=COUNTIF(Flags!J:J,"Confirmed rule")')]
    for i, (a_, b_) in enumerate(items, fb + 1):
        ws.cell(i, 1, a_); ws.cell(i, 4, b_)
    k1, k2, k3, kt, r1, r2, r3 = (fb + 1 + n for n in range(7))
    ws.cell(fb + 8, 1, "Check: Blocker + Check + Info = Total, and red + amber + green = Total")
    ws.cell(fb + 8, 4, f'=IF(AND(D{k1}+D{k2}+D{k3}=D{kt},D{r1}+D{r2}+D{r3}=D{kt}),"OK","MISMATCH")')
    ws.cell(fb, 6, "Not in Flags, still counted (detail on Data coverage)").font = Font(bold=True)
    for i_, t_ in enumerate([
            f"Info rows moved to Data coverage: {len(mv)} items covering {sum(x[4] for x in mv)} days (asterisk, unlabelled block, transfer, duplicate tap)",
            f"Out after shift end: {led.get('overrun_minor_days', 0)} days of 30 min or less (not counted); {led.get('otc_days', 0)} days above 30 min are OT candidates",
            f"Partial-data people: {sum(1 for x in order if people[x].partial)} people, {led.get('partial_nopunch_days', 0)} no-punch days shown as one Flags row per person",
            f"Public holiday worked: {led.get('ph_person_days', 0)} person-days merged into {led.get('ph_rows', 0)} Flags rows (one per date)",
            f"Roster hours differ from the code: {led.get('hours_mismatch_days', 0)} person-days summarised in {led.get('hours_mismatch_people', 0)} person rows (code trusted)",
            f"Possible missing clock-in (first punch more than 4 h after start): {led.get('implausible_late_days', 0)} rows, not counted as lates",
            f"Roster start time missing (end-only roster code): {led.get('end_only_days', 0)} days with max(10:00, first punch); {led.get('end_only_no_in_days', 0)} days with no clock-in"], fb + 1):
        ws.cell(i_, 6, t_)
    ws.cell(fb + 9, 1, "Per person (hours are decimal hours). OT is reference only, pending approval; the system never approves overtime. "
                       f"Net OT 1.5 = daily working above 8:30 minus daily shortfall, not below zero (same month, no carry-forward). Grey rows are {NAL}.").font = Font(bold=True)
    hdr = ["Person", "Company", "Home outlet (tab)", "Punch source", "Days scheduled to work", "Days with punches", "Late in (days)",
           "Early out (days)", "Missing punch (days)", "Transfer (days)", f"OT candidate (days, > {rules.get('ot_candidate_threshold_min')} min after end)",
           "OT candidate total (min)", "Working total (h)", "OT 1.5 gross (h)", "Early 1.5 shortfall (h)", "Net OT 1.5, pending approval (h)",
           "Weekly hours over 51, full weeks (h)", "Flags (count)", "OT candidate max (min)", "Notes"]
    hr = fb + 10
    _head(ws, hr, hdr, [11, 9, 14, 24, 12, 11, 9, 9, 10, 10, 14, 12, 14, 14, 14, 14, 14, 9, 12, 22])
    ws.row_dimensions[hr].height = 62
    r_ = hr + 1
    first = r_
    for sid in order:
        P = people[sid]
        m = P.m
        vals = [sid, P.company, P.home_outlet, P.source, int(m["work_days"]), int(m["punch_days"]), int(m["late_days"]),
                int(m["early_days"]), int(m["missing_days"]), int(m.get("transfer_days", 0)), int(m["otc_days"]),
                int(m["otc_min"]), round(m["working_total"], 2), round(m["ot_total"], 2), round(m["early_total"], 2),
                f"=MAX(0,N{r_}-O{r_})", round(weekly_full_over.get(sid, 0.0), 2), f"=COUNTIF(Flags!E:E,A{r_})",
                int(m["otc_max"]), None]
        if sid in OFFSITE:
            for j in (14, 15, 16, 17):
                vals[j - 1] = NOT_ASSESSED
        if P.not_assessed:
            for j in (11, 12, 13, 14, 15, 16, 17, 19):
                vals[j - 1] = NAL
            if P.source == "none":                     # no day has data: a count of 0 would be a fake zero
                for j in (7, 8, 9):
                    vals[j - 1] = NAL
            vals[19] = "Source data incomplete"
        eo = int(m.get("end_only_days", 0))
        if eo and not P.not_assessed and sid not in OFFSITE:
            vals[19] = f"{eo} day(s) with roster start missing (HR attention needed)"
        for j, v in enumerate(vals, 1):
            c_ = ws.cell(r_, j, v)
            if P.not_assessed:
                c_.fill = GREY
        r_ += 1
    last = r_ - 1
    ws.cell(r_, 1, "Total").font = Font(bold=True)
    for j in range(5, 19):
        ws.cell(r_, j, f"=SUM({L(j)}{first}:{L(j)}{last})")
    ws.cell(r_, 19, f"=MAX(S{first}:S{last})")
    tot_row = r_
    r_ += 1
    for co in ("PLM", "PLG"):
        ws.cell(r_, 1, f"{co} total").font = Font(bold=True)
        for j in range(5, 19):
            ws.cell(r_, j, f'=SUMIFS({L(j)}{first}:{L(j)}{last},$B${first}:$B${last},"{co}",$T${first}:$T${last},"<>Source data incomplete")')
        ws.cell(r_, 19, max([int(people[x].m["otc_max"]) for x in order if people[x].company == co and not people[x].not_assessed] or [0]))
        r_ += 1
    ws.cell(r_, 1, f"PLM total and PLG total exclude {NAL} people (grey rows). The Total row adds every person's counts; {NAL} people add only the counts for days that have data.")
    r_ += 2
    ws.cell(r_, 1, "Check: days with punches in this table should equal rows with punches in the PLM and PLG tabs.")
    ws.cell(r_, 12, f'=IF(F{tot_row}=COUNTA(PLM!I2:I5000)+COUNTA(PLG!I2:I5000),"OK","MISMATCH")')
    ws.cell(r_ + 1, 1, "Assumptions (amber until confirmed): FULL = 10:00-22:00, AM = 10:00-18:00, PM = 14:00-22:00; standard day 8:30; "
                       "breaks in the transactions are ignored; leave and PH days count 8.5 h in the weekly total. See the Pending tab.")
    ws.cell(r_ + 2, 1, "Tabs: PLM and PLG hold the full day-by-day check for each company (the old Day check, split by company). "
                       "Staff are credited to their home company even when they worked at the other group's outlet.")
    ws.freeze_panes = f"B{hr + 1}"

    # ---------------------------------------------------------------- Glossary (reference)
    wgl = wb.create_sheet("Glossary")
    wgl.cell(1, 1, "Glossary of standard comments and codes. The same incident always gets the same comment; details (times, minutes, dates) are in the Details column, never in the comment.").font = Font(bold=True)
    _head(wgl, 2, ["Code", "Standard comment", "Meaning", "Where it appears", "Colour / severity", "Rule or Pending ref"], [7, 48, 70, 28, 14, 10])
    gr = 3
    SEV_FILL = {"Red": RED, "Amber": AMBER, "Green": GREEN, "Info": "FFFFFFFF", "Grey": NEUTRAL}
    for row_g in glossary_rows():
        code, std, meaning, where, sev, ref = row_g
        for j, v in enumerate([code, std, meaning, where, sev, ref], 1):
            c = wgl.cell(gr, j, v); c.alignment = Alignment(wrap_text=True, vertical="top")
        wgl.cell(gr, 5).fill = PatternFill("solid", fgColor=SEV_FILL.get(sev, "FFFFFFFF"))
        gr += 1
    wgl.cell(gr + 1, 1, "Details (times, minutes, dates) are in the Details column, never in the comment.").font = Font(italic=True)
    wgl.freeze_panes = "A3"

    wb.move_sheet("Pending", offset=-(wb.sheetnames.index("Pending") - 1))
    wb.move_sheet("Flags", offset=-(wb.sheetnames.index("Flags") - 2))
    for sn, pos in (("PLM", 3), ("PLG", 4)):
        wb.move_sheet(sn, offset=-(wb.sheetnames.index(sn) - pos))
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return wb.sheetnames
