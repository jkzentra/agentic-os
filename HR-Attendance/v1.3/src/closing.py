"""Outlet closing times, derived from the ROSTER only (never from punches, never guessed).

Rule closing_time_method (Boss, 16 Oct 2026): closing time = most common shift end in the roster for the outlet.
Order: (1) roster codes carrying an outlet label; (2) codes of staff whose home outlet is that outlet.
Generic all-day codes (rule closing_time_generic_codes) do not set a closing time on their own: a result
from step 1 supported only by generic codes falls through to step 2. Admin is the office: shift end only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

BEGIN = "# >>> DERIVED closing_time (written by the build; do not edit by hand)"
END = "# <<< DERIVED closing_time"


def _unique_top(c: Counter):
    top = c.most_common()
    if top and (len(top) == 1 or top[0][1] > top[1][1]):
        return top[0][0]
    return None


def derive_closing(rows, home_of: dict, generic_shapes: set, skip=("Admin",)) -> dict:
    t1, t1_nongeneric, t2 = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    for r in rows:
        sh = r["shift"]
        if sh.day_type != "WORK" or not sh.end:
            continue
        generic = (sh.start, sh.end) in generic_shapes
        if sh.outlet:
            t1[sh.outlet][sh.end] += 1
            if not generic:
                t1_nongeneric[sh.outlet][sh.end] += 1
        home = home_of.get(r["person"], "")
        if home:
            t2[home][sh.end] += 1
    out = {}
    for o in sorted((set(t1) | set(t2)) - set(skip)):
        pick = None
        top1 = _unique_top(t1[o]) if t1[o] else None
        if top1 and t1_nongeneric[o].get(top1, 0) > 0:
            pick = (top1, "roster codes with an outlet label", t1[o])
        if pick is None and t2[o]:
            top2 = _unique_top(t2[o])
            if top2:
                pick = (top2, "codes of staff whose home outlet is this outlet", t2[o])
        if pick is None and top1:
            pick = (top1, "labelled codes (generic codes only, no better source)", t1[o])
        if pick is None:
            out[o] = {"time": None, "source": "no clear most common shift end", "support": 0, "considered": 0, "minority": ""}
            continue
        end, src, c = pick
        minority = "; ".join(f"{e} x{n}" for e, n in c.most_common() if e != end)
        out[o] = {"time": end, "source": src, "support": c[end], "considered": sum(c.values()), "minority": minority}
    out["Admin"] = {"time": None, "source": "office: shift end only, no closing time", "support": 0, "considered": 0, "minority": ""}
    return out


def write_derived(rules_path: Path, month: str, table: dict) -> None:
    """Rewrite the derived reference block at the end of rules.toml (all months kept). Rule values are not touched."""
    text = Path(rules_path).read_text(encoding="utf-8")
    existing = {}
    if BEGIN in text:
        block = text[text.index(BEGIN):text.index(END) + len(END)]
        raw = tomllib.loads(block).get("derived", {}).get("closing_time", {})
        existing = {mo: {o: {"time": v["closing"] or None, "source": v["source"], "support": v["supporting_shifts"],
                             "considered": v["shifts_considered"], "minority": v["minority_end_times"]}
                         for o, v in outs.items()} for mo, outs in raw.items()}
        text = text[:text.index(BEGIN)].rstrip() + "\n" + text[text.index(END) + len(END):].lstrip("\n")
    existing[month] = table
    lines = ["", BEGIN]
    for mo in sorted(existing):
        for o in sorted(existing[mo]):
            v = existing[mo][o]
            lines.append(f'[derived.closing_time."{mo}".{o}]')
            lines.append(f'closing = "{v["time"] or ""}"')
            lines.append(f'source = "{v["source"]}"')
            lines.append(f'supporting_shifts = {int(v["support"])}')
            lines.append(f'shifts_considered = {int(v["considered"])}')
            lines.append(f'minority_end_times = "{v["minority"]}"')
            lines.append("")
    lines.append(END)
    Path(rules_path).write_text(text.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
