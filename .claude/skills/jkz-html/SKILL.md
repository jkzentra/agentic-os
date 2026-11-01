---
name: jkz-html
description: "Use when the user asks to wrap up, recap, summarize, or deliver back a session, its context, decisions, or ideas discussed, or says 'wrap up', 'deliver this back', 'summarize what we covered', or 'give me the recap' — produces a colourful, visual HTML report with diagrams and comparison tables"
metadata:
  version: "1.0.0"
  source: user-preference
---

# JKZ HTML - Session Wrap-Up (HTML, Visual, Colourful)

Deliver the wrap-up of a session, its context, or ideas discussed as a single self-contained HTML file. The user does not want to repeat these preferences each time.

## Output requirements (non-negotiable)

1. **HTML** - one self-contained `.html` file (inline CSS/JS/SVG, no build step). Include a `<title>`, viewport meta, and a light/dark friendly palette.
2. **Visualised** - imagery and diagrams: inline SVG flow/architecture diagrams, timelines, simple charts, icons/emoji as visual anchors. A wall of text is a failure.
3. **Tables preferred** - use tables for comparison and reference (options vs. trade-offs, decisions, status, files touched, next steps). Prefer a table over bullets whenever items share attributes.
4. **Colourful** - a distinct accent colour per section/status (e.g. green = done, amber = pending, red = blocked, blue = info, purple = ideas). Use colour consistently and keep text contrast readable.

## Workflow

1. **Gather** - review the conversation: goals, decisions made, ideas raised, work done (files changed), open questions, next steps. Pull from git status/diff if the session involved code.
2. **Structure** the page in this order (drop sections that don't apply):
   - Header: title, date, one-sentence TL;DR
   - At a glance: coloured stat cards (done / open / decisions / ideas)
   - Context & goal (short)
   - Diagram: how the pieces fit, or the session timeline
   - Decisions table: decision | why | alternatives | status
   - Ideas / options comparison table: option | pros | cons | effort | verdict
   - Work done / files touched reference table
   - Open questions & blockers
   - Next steps checklist with owner and priority
3. **Write** the file to the session's working folder as `JKZ_<Topic>_Wrapup_<YYYY-MM-DD>.html` (match the existing `JKZ_*.html` naming in the repo; otherwise `<Topic>_Wrapup_<date>.html`). Never overwrite an existing file; add a version suffix instead.
4. **Verify** - open or screenshot it in the browser pane if available; confirm diagrams render and there is no horizontal scroll at phone width.
5. **Reply in chat briefly** - 2-4 lines plus the file path/link. Do not repeat the report in chat; deliver via `SendUserFile` when the user may be on another device.

## Style defaults

- Card layout, rounded corners, generous spacing, one accent colour per section, sticky mini table-of-contents for long reports.
- Diagrams: SVG with labelled boxes and arrows; keep to one idea per diagram.
- Keep prose tight; the tables and visuals carry the content.
- Use only facts from the session; mark anything uncertain as "assumed" rather than inventing it.
