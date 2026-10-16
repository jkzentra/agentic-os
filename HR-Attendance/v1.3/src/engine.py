"""Day engine: applies the agreed rules to roster + punches.

Inputs only: roster rows, punches, master data, rules. No HR time-calculation
file is read here. All time maths is plain Python; every rule value comes
from rules.toml via src/rules.py.
"""
from __future__ import annotations


import datetime
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from src.punches import collapse_duplicate_punches, minutes
from src.readers import Master, PunchDay
from src.rules import Rules
from src.comments import canon, JOIN
from src.shifts import Shift, parse_code
from src.closing import derive_closing

# Rule excluded_names (client-configurable, rules.toml): shareholders/directors or other
# non-staff people who get no attendance rows at all. Empty by default in the template;
# Engine.__init__ reads the live set from rules.toml into self.EXCLUDED.
EXCLUDED: set = set()
EXCLUDED_NOTE = "Person is on the excluded_names list (e.g. shareholder/director) and is excluded by rule."
# Rule offsite_names (client-configurable, rules.toml): off-site/WFH people who have no
# roster by design; punches are shown, but there are no shift checks and OT is not assessed.
# Engine.__init__ reads the live set from rules.toml into self.OFFSITE.
OFFSITE: set = set()
OFFSITE_NOTE = "Person is on the offsite_names list: off-site WFH, no roster by design"
OFFSITE_REMARK = "Off-site WFH, no roster"
NOT_ASSESSED = "no roster base, not assessed"

REMARK_ERROR, REMARK_PENDING, REMARK_CONFIRMED = "Possible error", "Pending question", "Confirmed rule"
DAY_TYPE_LABEL = {"WORK": "WORK", "OFF": "OFF", "PH": "PH", "LEAVE_MC": "MC", "LEAVE_AL": "AL",
                  "LEAVE_EL": "EL", "UPL": "UPL", "ABSENT": "ABSENT", "UNKNOWN": "UNKNOWN"}
DAY_REMARK = {"OFF": "REST DAY", "LEAVE_MC": "MC leave", "LEAVE_AL": "AL leave", "LEAVE_EL": "EL leave",
              "UPL": "UPL", "ABSENT": "ABSENT", "PH": "PH"}


@dataclass
class Flag:
    severity: str
    flag: str
    person: str
    home_outlet: str
    date: object
    details: str
    remark: str
    remark_type: str
    ref: str
    company: str = ""


@dataclass
class Person:
    staff_id: str
    company: str
    company_source: str
    home_outlet: str
    source: str            # "clock file", "HRMS transactions PLG", "none"
    full_name: str = ""
    partial: bool = False  # punches on fewer than the threshold share of scheduled work days (trial data)
    not_assessed: bool = False  # no clock file at all, or partial: shown as the not_assessed_label, never as zeros
    punch_dates: str = ""      # 'punches only on <dates>' text for partial people
    deltas: list = field(default_factory=list)   # punch-out minus shift end, every day with a full pair
    codes: dict = field(default_factory=dict)    # roster code -> work days
    m: dict = field(default_factory=lambda: defaultdict(float))


def hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def ceil_to(m: int, step: int) -> int:
    return math.ceil(m / step) * step


def floor_to(m: int, step: int) -> int:
    return (m // step) * step


class Engine:
    def __init__(self, master: Master, rules: Rules):
        self.master, self.rules = master, rules
        self.step_in = rules.get("late_round_step_minutes")
        self.step_out = rules.get("early_out_round_step_minutes")
        self.cap = rules.get("cap_out_at_shift_end")
        self.std = rules.get("standard_day_hours")
        self.weekly_thr = rules.get("weekly_ot_threshold_hours")
        self.leave_h = rules.get("leave_day_hours")
        self.dup_w = rules.get("duplicate_punch_window_minutes")
        self.dup_keep = rules.get("duplicate_punch_keep")
        self.sp_mode = rules.get("single_punch_classification")
        self.sp_tie = rules.get("single_punch_tie_minutes")
        self.ot_thr = rules.get("ot_candidate_threshold_min")
        self.implaus = rules.get("implausible_late_min")
        self.opening = rules.get("opening_time")
        self.gap_remark = rules.get("no_data_day_remark")
        self.large_late = rules.get("large_late_min")
        self.partial_pct = rules.get("partial_data_threshold_pct")
        # Client-configurable name lists (rules.toml: excluded_names / offsite_names).
        # Empty by default in the template; a client fills these in via rules.toml.
        self.EXCLUDED = set(rules.get("excluded_names") or [])
        self.OFFSITE = set(rules.get("offsite_names") or [])

    # remark type from rules
    def rt(self, rule_ids: list[str]) -> tuple[str, str]:
        refs = []
        for r in rule_ids:
            q = self.rules.question(r)
            if q and q not in refs:
                refs.append(q)
        t = REMARK_CONFIRMED if self.rules.is_confirmed(rule_ids) else REMARK_PENDING
        return t, ", ".join(refs)

    # ------------------------------------------------------------ main
    def run(self, month, roster_rows, roster_info, punches: dict, source_of: dict,
            clock_outlets_present: set | None, extra_problems: list):
        y, mo = map(int, month.split("-"))
        roster_rows = [r for r in roster_rows if r["person"] not in self.EXCLUDED]
        punches = {k: v for k, v in punches.items() if k[0] not in self.EXCLUDED}
        flags: list[Flag] = []
        self.moved, self.ledger = [], defaultdict(int)
        self.ph_worked = defaultdict(list)
        self.hours_mismatch = defaultdict(lambda: defaultdict(int))
        self.otc = defaultdict(list)
        self.large_lates = []
        people: dict[str, Person] = {}
        order: list[str] = []
        by_person = defaultdict(list)
        for r in roster_rows:
            by_person[r["person"]].append(r)
            if r["person"] not in people:
                order.append(r["person"])
                people[r["person"]] = None
        for (sid, d) in punches:
            if sid not in people:
                order.append(sid)
                people[sid] = None

        def mkperson(sid, block):
            st = self.master.staff.get(sid, {})
            home = block or st.get("home_outlet", "")
            company, csrc = self.master.company_of(sid, home)
            return Person(sid, company, csrc, home, source_of.get(sid, "none"), st.get("full_name", ""))

        for sid in order:
            blk = by_person[sid][0]["block"] if by_person.get(sid) else ""
            people[sid] = mkperson(sid, blk)
            # coverage of scheduled work days (trial data may be withheld for some people)
            wdays = {r["date"] for r in by_person.get(sid, []) if r["shift"].day_type == "WORK"}
            pdays = {d for (s, d) in punches if s == sid and d in wdays}
            people[sid].m["cov_sched"], people[sid].m["cov_days"] = len(wdays), len(pdays)
            if people[sid].source != "none" and wdays and len(pdays) / len(wdays) * 100 < self.partial_pct:
                people[sid].partial = True
                people[sid].punch_dates = fmt_dates(sorted(d for (s_, d) in punches if s_ == sid))
            if wdays and (people[sid].source == "none" or people[sid].partial):
                people[sid].not_assessed = True   # rule not_assessed_rule
            people[sid].codes = dict(Counter(r["raw"] for r in by_person.get(sid, [])
                                             if r["shift"].day_type == "WORK" or r["shift"].end_only))
        shapes = {(x.start, x.end) for x in (parse_code(c, set(self.master.outlets))
                                            for c in self.rules.get("closing_time_generic_codes")) if x.start}
        self.closing = derive_closing(roster_rows, {sid: people[sid].home_outlet for sid in order}, shapes)

        day_rows = []
        weekly = defaultdict(lambda: {"hours": 0.0, "days": 0, "leave": 0.0, "punches": 0})
        leave = defaultdict(lambda: defaultdict(list))
        asterisk_days = defaultdict(list)
        capped_days = defaultdict(list)
        transfer_days = defaultdict(list)
        dup_days = defaultdict(list)
        punch_outlet_days = defaultdict(lambda: defaultdict(int))

        for sid in order:
            P = people[sid]
            covered = set()
            for r in sorted(by_person.get(sid, []), key=lambda x: x["date"]):
                covered.add(r["date"])
                row = self.process_day(P, r, punches.get((sid, r["date"])), flags, weekly, leave,
                                       asterisk_days, capped_days, transfer_days, dup_days, punch_outlet_days)
                day_rows.append(row)
            # punches on days with no roster row
            extra = sorted(d for (s, d) in punches if s == sid and d not in covered)
            for d in extra:
                pdx = punches[(sid, d)]
                times = pdx.times
                P.m["punch_days"] += 1
                if sid in self.OFFSITE:
                    row = self.blank_row(P, d, "", "OFFSITE", times, pdx)
                    row["remark"] = OFFSITE_REMARK
                    if len(times) > 1:
                        wh = (minutes(times[-1]) - minutes(times[0])) / 60
                        row["working"] = wh
                        P.m["working_total"] += wh
                        wk = d - datetime.timedelta(days=d.weekday())
                        weekly[(sid, wk)]["hours"] += wh
                        weekly[(sid, wk)]["days"] += 1
                    day_rows.append(row)
                    continue
                day_rows.append(self.blank_row(P, d, "", "NO ROSTER", times, pdx))
            if extra and sid not in self.OFFSITE:
                st, ref = self.rt(["no_invented_data"])
                flags.append(Flag("Check", "Punches with no roster row", sid, P.home_outlet, "Month",
                                  f"{len(extra)} day(s) with punches have no roster entry: "
                                  f"{extra[0].isoformat()} to {extra[-1].isoformat()}. No shift to compare, so no Admin times were made.",
                                  "Roster row missing for this person; punches shown as recorded.",
                                  REMARK_ERROR, "", P.company))

        self.person_flags(people, by_person, punches, flags, roster_info, asterisk_days, capped_days,
                          transfer_days, dup_days, punch_outlet_days, extra_problems, clock_outlets_present)
        self.merge_ph(flags)
        self.hours_mismatch_flags(people, flags)
        return {"moved": self.moved, "ledger": dict(self.ledger), "large_lates": self.large_lates, "closing": self.closing, "otc": self.otc,
                "unlabelled": [n for n in roster_info.get("unlabelled", []) if n in people],
                "people": people, "order": order, "day_rows": day_rows, "flags": flags,
                "weekly": weekly, "leave": leave, "asterisk_days": asterisk_days,
                "capped_days": capped_days, "transfer_days": transfer_days}

    # ------------------------------------------------------------ rows
    def blank_row(self, P, d, code, typ, times, pdx=None):
        return {"person": P.staff_id, "company": P.company, "date": d, "day": d.strftime("%a"),
                "code": code, "type": typ, "start": None, "end": None,
                "punches": ", ".join(times) if times else None,
                "outlet": ", ".join(sorted(set(pdx.outlets))) if pdx and pdx.outlets else None,
                "sys_in": times[0] if times else None,
                "sys_out": times[-1] if len(times) > 1 else None,
                "hq_in": None, "hq_out": None, "flags": "", "working": None, "ot": None,
                "early": None, "remark": "", "capped": False, "cap_min": 0, "ot_cand": 0, "closing": None, "late_min": 0}

    def process_day(self, P, r, pdx: PunchDay | None, flags, weekly, leave, asterisk_days,
                    capped_days, transfer_days, dup_days, punch_outlet_days):
        sh, d = r["shift"], r["date"]
        sid = P.staff_id
        if sh.day_type == "UNKNOWN" and sh.end_only:   # rule end_only_assumed_start (ASSUMED, Q19)
            sh = Shift(sh.raw, "WORK", self.opening, sh.end_only, sh.outlet, sh.asterisk, assumed_start=True)
            r = dict(r, shift=sh)
        times = list(pdx.times) if pdx else []
        outlets = list(pdx.outlets) if pdx and pdx.outlets else []
        if times:
            pairs = list(zip(times, outlets or [""] * len(times)))
            kept, dropped = collapse_duplicate_punches(pairs, self.dup_w, self.dup_keep, time_of=lambda p: p[0])
            if dropped:
                dup_days[sid].append(d)
            times = [p[0] for p in kept]
            outlets = [p[1] for p in kept] if outlets else []
        row = self.blank_row(P, d, r["raw"], DAY_TYPE_LABEL[sh.day_type], times, None)
        row["sys_in"] = times[0] if times else None
        row["sys_out"] = times[-1] if len(times) > 1 else None
        row["outlet"] = ", ".join(sorted(set(o for o in outlets if o))) or None
        short, notes = [], []
        has_source = P.source != "none"
        if times:
            P.m["punch_days"] += 1
            for o in set(outlets):
                if o:
                    punch_outlet_days[sid][o] += 1
        if sh.asterisk:
            asterisk_days[sid].append(d)

        def add(sev, name, details, remark, rtype, ref, tag=True):
            flags.append(Flag(sev, name, sid, P.home_outlet, d, details, remark, rtype, ref, P.company))
            if tag:
                short.append(name)

        # public-holiday cross-check against the recognised list
        in_list = d in self.master.holidays
        if sh.day_type == "PH" and not in_list:
            add("Check", "PH code on a date not in the recognised list",
                f"Roster says {r['raw']} but {d.isoformat()} is not in the 2026 recognised public holiday list.",
                "Roster code or holiday list needs checking.", REMARK_ERROR, "")
        elif in_list and sh.day_type not in ("PH",) and False:
            pass

        if sh.day_type == "UNKNOWN":
            add("Check", "Roster code cannot be read",
                f"Roster code {r['raw']!r}: {sh.reason}. No Admin times made; punches shown as recorded.",
                "Not guessed. Confirm the intended shift.", REMARK_ERROR, "")
            row["remark"] = "CODE UNREADABLE"
        elif sh.day_type == "WORK":
            P.m["work_days"] += 1
            row["start"], row["end"] = sh.start, sh.end
            if sh.outlet and sh.outlet != P.home_outlet:
                row["outlet"] = row["outlet"] or f"{sh.outlet} (roster)"
                transfer_days[sid].append((d, sh.outlet))
            rh = r.get("hours")
            if rh is not None and sh.hours is not None and not sh.assumed_start and abs(rh - sh.hours) > 0.01:
                self.hours_mismatch[sid][(r["raw"], sh.hours, rh)] += 1   # one remark per person (decision 9)
            if sh.assumed_start:
                rt_a, ref_a = self.rt(["end_only_start_rule"])
                add("Check", "Roster start time missing",
                    f"Roster code {r['raw']} gives outlet {sh.outlet} and end {sh.end} but no start. Admin In = max(opening time {self.opening}, first real punch); shortfall set to 0.",
                    "End-only roster code. HR to confirm the real shift start.", REMARK_PENDING, ref_a)
                self.ledger["end_only_days"] += 1
                P.m["end_only_days"] = P.m.get("end_only_days", 0) + 1
            if not has_source:
                row["remark"] = self.gap_remark   # no clock file: the month-level Info row covers this person; no day flag
            elif not times:
                if P.partial:
                    row["remark"] = self.gap_remark         # one Flags row per person instead (decision 3)
                    self.ledger["partial_nopunch_days"] += 1
                elif sh.assumed_start:
                    # end-only day with no clock-in: not calculated, flagged for HR (A09)
                    add("Check", "Roster start missing and no clock-in",
                        f"End-only roster code {r['raw']} (outlet {sh.outlet}, end {sh.end}) and no clock-in on {d.isoformat()}; day not calculated.",
                        "End-only roster code and no clock-in. HR to confirm the real shift start.", REMARK_PENDING, ref_a)
                    row["remark"] = "Roster start missing and no clock-in"
                    self.ledger["end_only_no_in_days"] = self.ledger.get("end_only_no_in_days", 0) + 1
                    P.m["end_only_days"] = P.m.get("end_only_days", 0) + 1
                    # don't flow into full/single_punch; day stays blank
                else:
                    add("Check", "No punch on a scheduled work day",
                        f"Scheduled {r['raw']} ({sh.start}-{sh.end}); no punches recorded.",
                        "No punch for a scheduled work day. Absent, leave not in the roster, or a clock miss.",
                        REMARK_ERROR, "")
                if not P.not_assessed:        # a source gap is not a missing punch
                    P.m["missing_days"] += 1
                P.m["nopunch_work"] += 1
            elif len(times) == 1:
                self.single_punch(P, d, r, times[0], row, add, pdx)
                P.m["missing_days"] += 1
            else:
                self.full_day(P, d, r, sh, times, outlets, row, add, capped_days, transfer_days, weekly, pdx)
            if row["hq_in"] and d in self.master.holidays:
                P.m["ot_total"] -= row["ot"]
                P.m["early_total"] -= row["early"]
                row["ot"] = row["early"] = None
                row["remark"] = "Worked on a public holiday"
                short.append("Worked on a public holiday")
                self.ph_worked[d].append((sid, P.company, row["hq_in"], row["hq_out"], row["working"], self.master.holidays[d]))
            ctime = self.closing.get(sh.outlet or P.home_outlet, {}).get("time")
            row["closing"] = ctime
            if row["ot_cand"]:
                notes.append("Clocked out after shift end (OT candidate, pending approval)")
            if ctime and row["sys_out"] and minutes(row["sys_out"]) > minutes(ctime):
                notes.append("Past closing time (reference)")
            if sh.assumed_start:
                notes.append("Roster start time missing")
            if row["late_min"] >= self.large_late:
                notes.append("Large late, check roster shift (Admin)")
            wk = d - datetime.timedelta(days=d.weekday())
            weekly[(sid, wk)]["days"] += 1
            if times:
                weekly[(sid, wk)]["punches"] += 1
        else:
            # not a work day
            row["remark"] = DAY_REMARK.get(sh.day_type, "")
            key = {"LEAVE_MC": "mc", "LEAVE_AL": "al", "LEAVE_EL": "el", "UPL": "upl",
                   "ABSENT": "absent", "PH": "ph", "OFF": "off"}[sh.day_type]
            P.m[f"d_{key}"] += 1
            leave[sid][key].append(d)
            if sh.day_type in ("LEAVE_MC", "LEAVE_AL", "LEAVE_EL", "PH"):
                wk = d - datetime.timedelta(days=d.weekday())
                weekly[(sid, wk)]["leave"] += self.leave_h
            if times:
                ids = ["ot_rate_day_types"] + (["upl_absent_unpaid"] if sh.day_type in ("UPL", "ABSENT", "LEAVE_MC", "LEAVE_AL", "LEAVE_EL") else [])
                rtype, ref = self.rt(ids)
                add("Check", f"Punched on a {DAY_TYPE_LABEL[sh.day_type]} day",
                    f"Roster says {r['raw']}; punches {', '.join(times)}.",
                    "Could be rest-day or holiday work, or a roster not updated. Hours not computed; OT 2.0/3.0 rate pending.",
                    rtype, ref)
                row["remark"] = DAY_REMARK.get(sh.day_type, "") + " (punched)"
        row["flags"] = JOIN.join(dict.fromkeys(short))
        if notes:
            row["remark"] = JOIN.join(x for x in [row["remark"], *notes] if x)
        return row

    def single_punch(self, P, d, r, t, row, add, pdx):
        sh = r["shift"]
        pm, sm, em = minutes(t), minutes(sh.start), minutes(sh.end)
        mid = (sm + em) / 2
        extra = f" HRMS remark: {pdx.remark}." if pdx and pdx.remark else ""
        rtype, ref = self.rt(["single_punch_classification", "single_punch_tie_minutes"])
        if abs(pm - mid) <= self.sp_tie:
            add("Check", "Single punch, cannot tell clock-in from clock-out",
                f"Only {t}. Scheduled {sh.start}-{sh.end}, too close to the midpoint to classify.{extra}",
                "Not guessed.", rtype, ref)
        elif pm < mid:
            add("Check", "Missing clock-out",
                f"Only {t}. Scheduled start {sh.start}; treated as the clock-in.{extra}",
                "Lone punch nearer the shift start.", rtype, ref)
        else:
            add("Check", "Missing clock-in",
                f"Only {t}. Scheduled end {sh.end}; treated as the clock-out.{extra}",
                "Lone punch nearer the shift end.", rtype, ref)
            row["sys_in"], row["sys_out"] = None, t

    def full_day(self, P, d, r, sh, times, outlets, row, add, capped_days, transfer_days, weekly, pdx):
        sm, em = minutes(sh.start), minutes(sh.end)
        im, om = minutes(times[0]), minutes(times[-1])
        expected = sh.outlet or P.home_outlet
        P.deltas.append(om - em)
        # transfer detection from clock outlets (May)
        punched = sorted({o for o in outlets if o})
        if punched and any(o != expected for o in punched):
            transfer_days[P.staff_id].append((d, "/".join(o for o in punched if o != expected)))
        # Admin In
        if sh.assumed_start:
            hq_in = max(sm, im)       # Boss, 16 Oct 2026 (A1 option 3): no rounding, no late check
        elif im <= sm:
            hq_in = sm
        else:
            hq_in = ceil_to(im, self.step_in)
            if im - sm > self.implaus:
                add("Check", "Possible missing clock-in",
                    f"First punch {times[0]} is {im - sm} min after the shift start {sh.start} (more than {self.implaus} min). "
                    "Treated as a possible missing clock-in, not as a late. Admin In still rounds up as usual.",
                    "Not counted as a late. Admin decides what the real start was.", REMARK_PENDING, "")
                self.ledger["implausible_late_days"] += 1
            else:
                rtype, ref = self.rt(["late_round_step_minutes"])
                add("Check", "Clock-in after shift start (late in)",
                    f"Punch {times[0]}, start {sh.start}: {im - sm} min late. System In {times[0]}, Admin In {hhmm(hq_in)}.",
                    f"Real punch kept in System In; Admin In rounds up to the next {self.step_in} min.", rtype, ref)
                P.m["late_days"] += 1
                row["late_min"] = im - sm
                if im - sm >= self.large_late:
                    self.large_lates.append((P.staff_id, d, im - sm))
        # Admin Out
        if om >= em:
            hq_out = em
            if om > em:
                row["capped"] = True
                P.m["capped_days"] += 1
                P.m["capped_min"] += om - em
                capped_days[P.staff_id].append((d, om - em))
                row["cap_min"] = om - em
                if om - em > self.ot_thr:     # OT candidate: pending approval, never an approval
                    row["ot_cand"] = om - em
                    P.m["otc_days"] += 1
                    P.m["otc_min"] += om - em
                    P.m["otc_max"] = max(P.m["otc_max"], om - em)
                    self.otc[(P.staff_id, d - datetime.timedelta(days=d.weekday()))].append(om - em)
                    self.ledger["otc_days"] += 1
                else:
                    self.ledger["overrun_minor_days"] += 1
        else:
            hq_out = floor_to(om, self.step_out)
            rtype, ref = self.rt(["early_out_round_step_minutes"])
            add("Check", "Clock-out before shift end (early)",
                f"Punch {times[-1]}, shift end {sh.end}: {em - om} min early. System Out {times[-1]}, Admin Out {hhmm(hq_out)}.",
                f"Real punch kept in System Out; Admin Out rounds down to the previous {self.step_out} min.", rtype, ref)
            P.m["early_days"] += 1
        row["hq_in"], row["hq_out"] = hhmm(hq_in), hhmm(hq_out)
        if row["capped"]:
            row["flags"] = ""  # set by caller from short; capped is shown by colour
        wh = max(0, hq_out - hq_in) / 60
        row["working"] = wh
        row["ot"] = max(0.0, wh - self.std)
        row["early"] = 0.0 if sh.assumed_start else max(0.0, self.std - wh)   # A3: no Early 1.5 on end-only days
        P.m["working_total"] += wh
        P.m["ot_total"] += row["ot"]
        P.m["early_total"] += row["early"]
        wk = d - datetime.timedelta(days=d.weekday())
        weekly[(P.staff_id, wk)]["hours"] += wh

    # ------------------------------------------------------------ person / month level flags
    def person_flags(self, people, by_person, punches, flags, roster_info, asterisk_days, capped_days,
                     transfer_days, dup_days, punch_outlet_days, extra_problems, clock_outlets_present):
        for sid, P in people.items():
            rows = by_person.get(sid, [])
            work = P.m["work_days"]
            if P.source == "none" and rows and work > 0:
                flags.append(Flag("Info", "No clock file", sid, P.home_outlet, "Month",
                                  f"{int(work)} scheduled work days, but no punch data in this batch. Listed on the 'No clock file' tab. Nothing was inferred.",
                                  "Trial batch: missing data is flagged, never filled.", REMARK_PENDING, "", P.company))
            if P.partial:
                dts = sorted(d for (s_, d) in punches if s_ == sid)
                flags.append(Flag("Check", "Data incomplete in the trial", sid, P.home_outlet, "Month",
                                  f"Data incomplete in the trial: punches only on {fmt_dates(dts)} "
                                  f"({int(P.m['cov_days'])} of {int(P.m['cov_sched'])} scheduled work days).",
                                  "Pattern looks like a partial export, Admin to confirm. No late or no-punch flags are raised for the incomplete days.",
                                  REMARK_PENDING, "Q22", P.company))
            if transfer_days.get(sid):
                dl = sorted({d: o for d, o in transfer_days[sid]}.items())
                where = sorted({o for _, o in dl})
                self.moved.append(("Worked at another outlet (transfer)", sid, P.company, P.home_outlet, len(dl),
                                   f"{len(dl)} day(s) at {', '.join(where)} (home {P.home_outlet or 'n/a'}). Attendance stays with {P.company}. "
                                   "Rule C4: venue exception only; roster shift times still apply.", "Transfers are normal."))
                P.m["transfer_days"] = len(dl)
            if asterisk_days.get(sid):
                a = asterisk_days[sid]
                self.moved.append(("Roster code carries an asterisk", sid, P.company, P.home_outlet, len(a),
                                   f"{len(a)} day(s): {a[0].isoformat()} ... Base code used; asterisk meaning not confirmed (Q13).",
                                   "Asterisk meaning is pending."))
            if dup_days.get(sid):
                dd = dup_days[sid]
                self.moved.append(("Duplicate tap collapsed", sid, P.company, P.home_outlet, len(dd),
                                   f"{len(dd)} day(s) had two punches within {self.dup_w} min; kept the {self.dup_keep} one.",
                                   "Duplicate-tap policy pending."))
            po = punch_outlet_days.get(sid)
            if po and P.home_outlet:
                tot = sum(po.values()); top, n = max(po.items(), key=lambda kv: kv[1])
                if top != P.home_outlet and n / tot >= 0.8:
                    flags.append(Flag("Check", "Roster outlet differs from where the person punches", sid, P.home_outlet, "Month",
                                      f"Roster block {P.home_outlet}, but {n} of {tot} punch days are at {top}.",
                                      "Roster, alias table or a long transfer. Admin decides.", REMARK_PENDING, "Q6", P.company))
        for p in [x for x in extra_problems if str(x.get('name', '')) not in self.EXCLUDED]:
            flags.append(Flag("Check", "Name not matched", str(p.get("name", "")), "", str(p.get("date", "Month")),
                              p.get("detail", ""), "Not guessed; not in the Day tabs.", REMARK_ERROR, "Q6", p.get("company", "")))
        if roster_info.get("dup_people"):
            for n in [x for x in roster_info["dup_people"] if x not in self.EXCLUDED]:
                flags.append(Flag("Info", "Name appears twice on the roster header", n, "", "Month",
                                  f"{n} has two columns on the roster; only the first was read.",
                                  "Roster layout.", REMARK_PENDING, "Q6", people[n].company if n in people else ""))
        for n in roster_info.get("unlabelled", []):
            if n in people:
                self.moved.append(("Roster outlet block has no label", n, people[n].company, people[n].home_outlet,
                                   int(people[n].m["work_days"]),
                                   f"Roster column for {n} sits outside a labelled outlet block; home outlet taken from the staff map "
                                   f"({people[n].home_outlet or 'none'}). Roster codes are read from the roster as written.",
                                   "Alias question (Q6)."))


    # ------------------------------------------------------------ merged rows
    def merge_ph(self, flags):
        """Decision 6: one Flags row per public holiday date."""
        for d, items in sorted(self.ph_worked.items()):
            comps = "/".join(sorted({c for _, c, *_ in items}))
            who = "; ".join(f"{sid} {hi}-{ho} ({w:.2f} h)" for sid, _, hi, ho, w, _n in sorted(items))
            flags.append(Flag("Check", "Worked on a public holiday", f"Several ({len(items)})", "", d,
                              f"{items[0][5]}: {len(items)} people worked. {who}. Not counted in OT 1.5.",
                              "Assumed PL observes it; OT rate pending Q3/Q21.", REMARK_PENDING, "Q3, Q21", comps))
            self.ledger["ph_person_days"] += len(items)
            self.ledger["ph_rows"] += 1

    def hours_mismatch_flags(self, people, flags):
        """Decision 9: roster code trusted; one remark per person quoting the code and the hours column."""
        for sid, dd in self.hours_mismatch.items():
            P = people[sid]
            parts = "; ".join(f"code {c} = {h:g} h vs roster hours column {rh:g} ({n} day(s))" for (c, h, rh), n in sorted(dd.items()))
            flags.append(Flag("Info", "Roster hours differ from the code", sid, P.home_outlet, "Month", parts + ".",
                              "Roster code trusted (Boss, 16 Oct 2026); the hours column is not used.", REMARK_CONFIRMED, "", P.company))
            self.ledger["hours_mismatch_days"] += sum(dd.values())
            self.ledger["hours_mismatch_people"] += 1


def fmt_dates(dts) -> str:
    """[24, 26..30 Sep] -> '24 and 26 to 30 Sep' (consecutive days grouped)."""
    if not dts:
        return "no day"
    groups, cur = [], [dts[0]]
    for d in dts[1:]:
        if (d - cur[-1]).days == 1:
            cur.append(d)
        else:
            groups.append(cur); cur = [d]
    groups.append(cur)
    parts = [f"{g[0].day}" if len(g) == 1 else f"{g[0].day} to {g[-1].day}" for g in groups]
    txt = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"{txt} {dts[-1].strftime('%b')}"
