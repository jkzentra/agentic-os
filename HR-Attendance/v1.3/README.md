# HR-Attendance v1.3

A reusable attendance/payroll-adjacent engine template: it turns a duty
roster and clock/HRMS punch exports into a monthly attendance report
workbook (flags, OT candidates, data-coverage gaps, a glossary). It is
derived from a real production build and is now fully client-agnostic — no
real staff, outlet or company names remain anywhere in this template.

## 30-minute onboarding

1. **Edit `client_config.toml`** at the project root: set `client_name`,
   `companies`, `outlet_company_map`, and `data_paths.roster` /
   `data_paths.punches` / `data_paths.output_dir`.
2. **Drop the client's own data** into `03_MASTER_DATA/`: fill in
   `staff_map.csv`, `outlets.csv`, `public_holidays.csv` and
   `roster_text_labels.csv` (each currently has only its header row), and
   point `client_config.toml`'s `data_paths` at the client's roster and
   punch-export workbooks.
3. **Confirm or override every rule** in `03_MASTER_DATA/rules.toml`. Every
   rule ships as `status = "ASSUMED"` with a working default value and a
   `question` field asking the client to confirm it. Change `value`, set
   `status = "CONFIRMED"`, and fill in `source` once the client has signed
   off. Run `py -m src.rules check` to see a status summary and catch any
   validation error.
4. **Run it**: `py -m src.run <YYYY-MM>` (e.g. `py -m src.run 2026-11`).
5. **Open the result**: `06_REPORTS\<YYYY-MM>\Attendance report <YYYY-MM>.xlsx`.

## One-click demo

`py -m src.demo` (optionally `py -m src.demo 2026-09`) rebuilds the bundled
`sample_data/` — two fake months for six fake staff across two fake
companies/three fake outlets, with September deliberately missing most
punches for one person to exercise the "Not assessed, missing data" path —
and writes the result into `06_REPORTS/`. Compare it against
`sample_data/expected_output/` to see the known-good baseline.

## Tests

`py -m pytest -q tests` runs the full suite, including:
- `test_demo_rebuild_matches_fixture` — rebuilds the sample_data demo and
  checks every sheet's cell values against the saved baseline in
  `sample_data/expected_output/`. This is the regression fixture: if a code
  change alters any computed value, this test catches it.
- `test_no_phonelab_values` — scans every text file in this template and
  fails if any client-specific name, initials or outlet code from the
  original source system has leaked back in (CHANGELOG.md's provenance note
  is the one explicit exception).

## Layout

```
client_config.toml       the one file a new client edits first
03_MASTER_DATA/           rules.toml + staff/outlet/holiday CSVs (header-only until filled in)
src/                      engine, readers, report writer, CLI (py -m src.run / py -m src.demo)
tests/                    full test suite, pointed at sample_data/
sample_data/              fake two-month dataset + saved baseline output
PROMPTS/                  one dated Markdown file per change made to a client's build
_backup/                  dated backup folders (created automatically before an edit)
06_REPORTS/               empty; filled in on first run
```

## Versioning

v1.3 is independent of the live production build it was derived from (see
CHANGELOG.md for provenance); changes to one do not affect the other.
