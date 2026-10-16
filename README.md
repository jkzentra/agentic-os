# JK Zentra Agentic OS

Private template library for JK Zentra client builds. Each template is a
self-contained, client-agnostic engine that gets instantiated per client
and then driven by that client's own master data.

## Repo layout

```
Agentic OS/
  HR-Attendance/
    v1.3/              Current HR attendance template (see its own README)
  (future templates land here as sibling folders)
```

## Current templates

- **HR-Attendance v1.3** — see
  [HR-Attendance/v1.3/README.md](HR-Attendance/v1.3/README.md) for the
  30-minute onboarding, demo script, and versioning note.

## Conventions

- Each template is independently versioned (e.g. `v1.3`, `v1.4`); a bump
  in one template does not force a bump in any client's live build.
- Templates ship with `sample_data/` under invented names only — no real
  client identifiers live in this repo. The scrub test enforces this.
- Per-client runtime artifacts (`06_REPORTS/`, `_backup/`, filled master
  data) are gitignored and never pushed here.

## License

Proprietary. See [LICENSE](LICENSE).
