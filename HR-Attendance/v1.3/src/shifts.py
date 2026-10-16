"""Parse a roster cell into a day type, shift times and an optional outlet marker.

Pure functions, no I/O. A code that cannot be read safely returns day_type
"UNKNOWN" with a reason: it is flagged, never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

NAMED_SHIFTS = {  # ASSUMED until {client} confirms (Q11 area), same as the live build
    "FULL": ("10:00", "22:00"),
    "AM": ("10:00", "18:00"),
    "PM": ("14:00", "22:00"),
}
LEAVE_TYPES = {"AL": "LEAVE_AL", "EL": "LEAVE_EL", "UPL": "UPL", "ABSENT": "ABSENT"}
RANGE_RE = re.compile(
    r"^(\d{1,2})(?:[:.](\d{2}))?\s*(AM|PM)?\s*-+\s*(\d{1,2})(?:[:.](\d{2}))?\s*(AM|PM)?$")


@dataclass
class Shift:
    raw: str
    day_type: str            # WORK, OFF, PH, LEAVE_AL, LEAVE_EL, LEAVE_MC, UPL, ABSENT, UNKNOWN
    start: str | None = None
    end: str | None = None
    outlet: str | None = None   # outlet marker inside the code (transfer / stationed)
    asterisk: bool = False
    reason: str = ""
    named: bool = False         # FULL/AM/PM (times assumed)
    end_only: str | None = None  # roster gives an end time but no start (e.g. OUT1/6.30PM)
    assumed_start: bool = False  # start filled by an ASSUMED rule (end_only_assumed_start)

    @property
    def hours(self) -> float | None:
        if self.start and self.end:
            return (_m(self.end) - _m(self.start)) / 60
        return None


def _m(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_range(text: str) -> tuple[str, str] | None:
    m = RANGE_RE.match(text.strip().upper())
    if not m:
        return None
    sh, sm, ssuf, eh, em, esuf = m.groups()
    sh, eh = int(sh), int(eh)
    sm, em = int(sm or 0), int(em or 0)
    if sh > 23 or eh > 23 or sm > 59 or em > 59:
        return None
    if esuf == "PM" and eh < 12:
        eh += 12
    if esuf == "AM" and eh == 12:
        eh = 0
    if ssuf == "PM" and sh < 12:
        sh += 12
    if not ssuf and sh < 8:      # nobody opens before 8: "2-8PM" means 14:00
        sh += 12
    if not esuf and eh * 60 + em <= sh * 60 + sm and eh < 12:
        eh += 12                  # "10-8" and "12-10" mean 20:00 and 22:00
    start, end = sh * 60 + sm, eh * 60 + em
    if end <= start:
        return None
    return _hhmm(start), _hhmm(end)


def parse_code(raw: str, outlet_ids: set[str], fallback: dict[str, str] | None = None) -> Shift:
    """fallback: lower-cased exact text -> day type, for free-text holiday labels."""
    text = (raw or "").strip()
    star = text.endswith("*")
    body = text.rstrip("*").strip()
    parts = [p.strip() for p in re.split(r"\s*/\s*", body) if p.strip()]
    outlet = None
    rest = []
    for p in parts:
        if p.upper() in outlet_ids and outlet is None:
            outlet = p.upper()
        else:
            rest.append(p)
    if len(rest) != 1:
        low = body.lower()
        if fallback and low in fallback:
            return Shift(text, fallback[low], asterisk=star)
        return Shift(text, "UNKNOWN", outlet=outlet, asterisk=star,
                     reason=("half-day or combined code" if len(rest) > 1 else "no shift in code"))
    code = rest[0].upper()
    if code == "OFF":
        return Shift(text, "OFF", outlet=outlet, asterisk=star)
    if code == "PH":
        return Shift(text, "PH", outlet=outlet, asterisk=star)
    if re.fullmatch(r"MC\s*\d*", code):
        return Shift(text, "LEAVE_MC", outlet=outlet, asterisk=star)
    if code in LEAVE_TYPES:
        return Shift(text, LEAVE_TYPES[code], outlet=outlet, asterisk=star)
    if code in NAMED_SHIFTS:
        s, e = NAMED_SHIFTS[code]
        return Shift(text, "WORK", s, e, outlet, star, named=True)
    rng = parse_range(code)
    if rng:
        return Shift(text, "WORK", rng[0], rng[1], outlet, star)
    low = body.lower()
    if fallback and low in fallback:
        return Shift(text, fallback[low], outlet=outlet, asterisk=star)
    mo = re.fullmatch(r"(\d{1,2})[:.](\d{2})\s*(AM|PM)", code)
    if mo:
        h, mi = int(mo.group(1)), int(mo.group(2))
        if mo.group(3) == "PM" and h < 12:
            h += 12
        if h <= 23 and mi <= 59:
            return Shift(text, "UNKNOWN", outlet=outlet, asterisk=star, reason="end time only, no start", end_only=f"{h:02d}:{mi:02d}")
    return Shift(text, "UNKNOWN", outlet=outlet, asterisk=star, reason=f"cannot read shift '{rest[0]}'")
