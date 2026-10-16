"""De-identification scrub: no PhoneLab-specific value should remain anywhere
in this template, except the provenance note in CHANGELOG.md (explicitly
excluded below).

Matching approach: every forbidden token is matched case-sensitively with
regex word boundaries (\\bTOKEN\\b). This avoids false positives from short
ambiguous tokens that are also ordinary English/code substrings in a
different case or as part of a longer identifier -- e.g. lower-case "op" in
"open"/"operator", "ti" in "time", "sg"/"ww" inside unrelated words, "hq" in
"headquarters"-ish strings. Because matching is exact-case and whole-word,
"TI", "KK", "SG", "WW", "OP", "HQ" only match when they appear as their own
standalone, upper-case word -- which is how they appeared as PhoneLab staff
initials / outlet codes in the source system. Binary files and caches are
skipped; only text files are scanned.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN = [
    "PhoneLab", "PHONELAB", "KK", "TI", "ANGEL", "FARISA", "AIN", "PRITHA",
    "NAEL", "AFIF", "HEMA", "LAI", "ADHA", "SURENDRAN", "SHARVIN", "FAHMIN",
    "ANTHONY", "JULINA", "IYAD", "VISHNU", "IWAN", "MY36", "SC03", "WW",
    "PPM", "SG", "OP", "HQ",
]
PATTERNS = [(tok, re.compile(r"\b" + re.escape(tok) + r"\b")) for tok in FORBIDDEN]

SKIP_DIR_NAMES = {"__pycache__", ".pytest_cache", ".git"}
BINARY_SUFFIXES = {".xlsx", ".xls", ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}
EXCLUDED_FILES = {ROOT / "CHANGELOG.md", Path(__file__)}


def _text_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        if p in EXCLUDED_FILES:
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            continue
        yield p


def test_no_phonelab_values():
    hits = []
    for p in _text_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for tok, pat in PATTERNS:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                hits.append(f"{p.relative_to(ROOT)}:{line_no}: {tok!r}")
    assert not hits, "Forbidden PhoneLab-specific tokens found:\n" + "\n".join(hits)
