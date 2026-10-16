"""Standard comments: one text per incident, codes grouped by severity.

Boss, 16 Oct 2026 (merged change C): the same incident always gets the same comment.
Variable facts (times, minutes, dates, counts, names) go in the Details column, never
in the comment. The Flag column, PLM/PLG Day remark column, Summary notes, Pending
'What this report did meanwhile' and Data coverage notes all draw from this list.
"""
from __future__ import annotations

# (severity, code, standard, meaning, where, ref)
CODES: list[tuple[str, str, str, str, str, str]] = [
    # ---- Red (Possible error)
    ("Red",   "R01", "Possible missing clock-in",
                     "First punch is implausibly late (over the implausible-late cutoff after shift start); treated as a possible missing clock-in, not a late.",
                     "Flags", "Q6"),
    ("Red",   "R02", "Roster code cannot be read",
                     "The roster code is not in the recognised list; no Admin times made, punches shown as recorded.",
                     "Flags, PLM, PLG", "Q22"),
    # ---- Amber (Pending question)
    ("Amber", "A01", "Clocked out after shift end (OT candidate, pending approval)",
                     "Punch-out is more than 30 min after the shift end; Admin Out stays capped at the shift end and the minutes go to OT candidate.",
                     "PLM, PLG, Weekly OT, Summary", "Q2"),
    ("Amber", "A02", "Data incomplete in the trial",
                     "Fewer than half of this person's scheduled work days have punches; the trial batch did not cover them.",
                     "Flags", "Q22"),
    ("Amber", "A03", "No clock file",
                     "This person has no clock export in the batch at all; not assessed.",
                     "Flags", "Q22"),
    ("Amber", "A04", "No punch on a scheduled work day",
                     "A scheduled work day has no punches at all; not a partial-data person.",
                     "Flags, PLM, PLG", "Q6"),
    ("Amber", "A05", "PH code on a date not in the recognised list",
                     "The roster uses a PH code on a date not on the 2026 public-holiday list.",
                     "Flags", "Q5"),
    ("Amber", "A06", "Punched on an UPL day",
                     "The roster is UPL for the day but there are real punches.",
                     "Flags, PLM, PLG", "C6"),
    ("Amber", "A07", "Roster hours differ from the code",
                     "The roster hours column disagrees with the shift code; the code is trusted.",
                     "Flags", "Q11"),
    ("Amber", "A08", "Roster outlet differs from where the person punches",
                     "The roster outlet and the clocked outlet are not the same.",
                     "Flags", "Q6"),
    ("Amber", "A09", "Roster start missing and no clock-in",
                     "End-only roster code (e.g. OUT1/6.30PM) and no clock-in punch on the day; not calculated, flagged for HR.",
                     "Flags, PLM, PLG", "Q19"),
    ("Amber", "A10", "Roster start time missing",
                     "Roster code has an end but no start; Admin In taken as max(opening time 10:00, first real punch); no late check; Early 1.5 shortfall set to 0.",
                     "Flags, PLM, PLG", "Q19"),
    ("Amber", "A11", "Worked on a public holiday",
                     "A real punch exists on a recognised public holiday; OT rate pending.",
                     "Flags, PLM, PLG", "Q3"),
    ("Amber", "A12", "Punched on a REST DAY",
                     "The roster is a rest day but there are real punches.",
                     "Flags, PLM, PLG", "C6"),
    ("Amber", "A13", "Punched on a PH day",
                     "The roster is PH but there are real punches; OT rate pending.",
                     "Flags, PLM, PLG", "Q3"),
    ("Amber", "A14", "Single punch, cannot tell clock-in from clock-out",
                     "Only one punch recorded for the day and it falls near the shift midpoint; not guessed.",
                     "Flags, PLM, PLG", "Q22"),
    # ---- Green (Confirmed rule)
    ("Green", "G01", "Clock-in after shift start (late in)",
                     "Late in: System In keeps the real punch; Admin In rounds up to the next 30 min.",
                     "Flags, PLM, PLG", "Q1"),
    ("Green", "G02", "Clock-out before shift end (early)",
                     "Early clock-out: System Out keeps the real punch; Admin Out rounds down to the previous 30 min.",
                     "Flags, PLM, PLG", "Q5"),
    ("Green", "G03", "Duplicate tap collapsed",
                     "Two punches within the duplicate window were counted as one tap; the first was kept.",
                     "Data coverage", "Q15"),
    ("Green", "G04", "Large late, check roster shift (Admin)",
                     "A late of 90 min or more (and under the implausible-late cutoff); HR to review the roster shift.",
                     "PLM, PLG", "Q22"),
    ("Green", "G05", "Missing clock-in",
                     "A day has a clock-out but no clock-in.",
                     "Flags, PLM, PLG", "Q22"),
    ("Green", "G06", "Missing clock-out",
                     "A day has a clock-in but no clock-out.",
                     "Flags, PLM, PLG", "Q22"),
    ("Green", "G07", "Off-site WFH, no roster",
                     "Off-site work from home with no roster; working computed from the real punches only.",
                     "PLM, PLG", "Q20"),
    ("Green", "G08", "Past closing time (reference)",
                     "The real punch-out is later than the outlet closing time (reference only, no flag).",
                     "PLM, PLG, Data coverage", "Q11"),
    ("Green", "G09", "Roster code carries an asterisk",
                     "The roster code ends with a trailing asterisk; the base code is used, meaning pending.",
                     "Data coverage", "Q13"),
    ("Green", "G10", "Unlabelled roster block",
                     "CASEY, MORGAN and TAYLOR sit in a roster block with no company header; code read as-is.",
                     "Data coverage", "Q6"),
    ("Green", "G11", "Worked at another outlet (transfer)",
                     "The person punched at an outlet other than their home or rostered outlet; venue exception only.",
                     "Data coverage", "C4"),
    # ---- Info (counted but not Check)
    ("Info",  "I01", "Name appears twice on the roster header",
                     "A person's name has two columns on the roster header; only the first was read.",
                     "Flags", "Q6"),
    # ---- Grey (Not assessed / data gap)
    ("Grey",  "X01", "No data (source gap)",
                     "A scheduled work day with no punch for a Not-assessed person; no day flag raised.",
                     "PLM, PLG", "Q22"),
    ("Grey",  "X02", "Not assessed, missing data",
                     "Cell label for a person with no clock file or with fewer than half of scheduled work days with punches.",
                     "Summary, Weekly OT", "Q22"),
    ("Grey",  "X03", "Source data incomplete",
                     "Summary Notes column marker for a Not-assessed person's row.",
                     "Summary", "Q22"),
]

CODE_FOR_TEXT: dict[str, str] = {c[2]: c[1] for c in CODES}

SEVERITY_ORDER = ["Red", "Amber", "Green", "Info", "Grey"]

# Old text -> new standard. Used by engine and (via Flag.flag) by the Flags writer.
CANON: dict[str, str] = {
    # Flag column
    "Possible missing clock-in, Admin to decide": "Possible missing clock-in",
    "Missing clock-in": "Missing clock-in",
    "Missing clock-out": "Missing clock-out",
    "No punch on a scheduled work day": "No punch on a scheduled work day",
    "Late in, Admin In rounded up": "Clock-in after shift start (late in)",
    "Early clock-out, Admin Out rounded down": "Clock-out before shift end (early)",
    "Roster start time missing, {admin}/Admin to confirm": "Roster start time missing",
    "Roster start missing and no clock-in": "Roster start missing and no clock-in",
    "Worked on a public holiday": "Worked on a public holiday",
    "No data for this person": "No clock file",
    "Data incomplete in the trial": "Data incomplete in the trial",
    "Roster hours differ from the code (code trusted)": "Roster hours differ from the code",
    "Roster hours differ from the code": "Roster hours differ from the code",
    "Punched on a UPL day": "Punched on a UPL day",
    "PH code on a date not in the recognised list": "PH code on a date not in the recognised list",
    "Roster outlet differs from where the person punches": "Roster outlet differs from where the person punches",
    "Name appears twice on the roster header": "Name appears twice on the roster header",
    "Punched on a UPL day": "Punched on an UPL day",
    "Punched on a REST DAY day": "Punched on a REST DAY",
    "Punched on a PH day": "Punched on a PH day",
    "Punched on a ABSENT day": "Punched on an ABSENT day",
    "Punched on a MC leave day": "Punched on an MC leave day",
    "Punched on a AL leave day": "Punched on an AL leave day",
    "Punched on a EL leave day": "Punched on an EL leave day",
    "Single punch, cannot tell clock-in from clock-out": "Single punch, cannot tell clock-in from clock-out",
    "Roster code cannot be read": "Roster code cannot be read",
    "CODE UNREADABLE": "Roster code cannot be read",
    # Day remark fragments
    "Past closing: Yes": "Past closing time (reference)",
    "PH worked (OT rate pending)": "Worked on a public holiday",
    "Large late, check roster shift (Admin)": "Large late, check roster shift (Admin)",
    "No data (source gap)": "No data (source gap)",
    "Off-site WFH, no roster": "Off-site WFH, no roster",
}

JOIN = " | "


def canon(text: str) -> str:
    return CANON.get(text, text)


def code_for(text: str) -> str:
    return CODE_FOR_TEXT.get(canon(text), "")


def glossary_rows() -> list[tuple[str, str, str, str, str, str]]:
    out = []
    by_sev = {s: [] for s in SEVERITY_ORDER}
    for sev, code, std, meaning, where, ref in CODES:
        by_sev[sev].append((code, std, meaning, where, sev, ref))
    for s in SEVERITY_ORDER:
        for row in sorted(by_sev[s], key=lambda r: r[1].lower()):
            out.append(row)
    return out
