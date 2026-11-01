---
name: jkz-html
description: "Use when the user asks to wrap up, recap, summarize, or deliver back a session, its context, decisions, or ideas discussed, or says 'wrap up', 'deliver this back', 'summarize what we covered', or 'give me the recap' — produces a colourful, visual poster-slide HTML report with diagrams and comparison tables"
metadata:
  version: "2.0.0"
---

# JKZ HTML - Session Wrap-Up (Poster-Slide Style)

Deliver the wrap-up of a session, its context, or ideas discussed as a single self-contained HTML deck. The user finds visual, colour-coded pages far easier to read and kinder on the eyes than text. Reference look: `PhoneLab_Ecosystem_Blueprint_v3.html` (PL-DELIVERY_121026). Start from `template.html` in this skill folder.

## Output requirements (non-negotiable)

1. **One self-contained `.html`** - inline CSS/JS/SVG, no build step. Only external asset allowed: the Google Fonts link (with system fallbacks). Include `<title>`, viewport meta (`viewport-fit=cover`).
2. **Poster-slide layout** - a stack of white "slides" on a light grey table, one idea per slide, each with a kicker, a short heading and a lede line. Not a wall of text.
3. **Visualised** - an inline SVG diagram or flow on every slide that can carry one; stat tiles, flow steps, cards, heat bars. Prose stays tight.
4. **Tables preferred** over bullets whenever items share attributes (decision, option, status, files, next steps).
5. **Colour is a code, not decoration** - declare a legend on the first slide and use each colour for one meaning only.

## Design system (copy these, do not improvise)

| Token | Value | Notes |
|---|---|---|
| Page bg / paper / ink | `#F5F5F5` / `#FFFFFF` / `#15151F` (ink-2 `#464656`) | Single **light** theme by choice. Dark backgrounds render unreadably in the viewer. Set `color-scheme:light`. |
| Fills | coral `#FF6B5A`, sun `#FFC93C`, mint `#3DDBB0`, sky `#4CC9F0`, violet `#B79CFF`, lime `#B8F060` | Each has a pale tint (`-t`) for slide/panel backgrounds: `#FFE1DC #FFF1C2 #D6F7EC #D8F2FB #EAE2FF #ECFAD0` |
| Borders | `2.5px solid ink` on every box; dashed = assumed / proposed | Hard offset shadow `7px 7px 0 ink` on slides, `6px 6px 0` on menus |
| Fonts | Display: Bricolage Grotesque 800. Body: Instrument Sans. Labels: DM Mono uppercase, letter-spaced | Fallbacks: Arial Black / system-ui / ui-monospace |
| Status marks | `.m` pill: filled ink = built/done, lime = recommended, coral tint = on hold/blocked, violet tint = beta, dashed = assumed | Never rely on colour alone; always include the word |
| Lime | Reserved for **the recommended pick only** | Highlight that row/card in lime, nothing else |

Default colour code (state it in the legend; remap only if the topic demands it): sky = Claude / tools, violet = agents / ideas, mint = data / done, sun = dashboards / info / pending, coral = humans, guardrails, blockers.

## Chrome

- **Sticky top bar**: brand left; right side has prev / next buttons, a `n / total` counter, and a `<details>` menu listing every slide (grouped with small mono headings). Border-bottom `2px ink`.
- **Keyboard**: ArrowRight / PageDown next, ArrowLeft / PageUp previous. Respect `prefers-reduced-motion`.
- Slides use `scroll-margin-top` so the sticky bar never covers a heading.
- On desktop (>=1000px) slides have `min-height:560px`; the title slide may use 16:9.

## Workflow

1. **Gather** - goals, decisions, ideas, work done (files changed), open questions, next steps. Pull from git status/diff if code was touched.
2. **Slides, in order** (drop what does not apply):
   1. Title: kicker, huge H1, one-sentence TL;DR, stat tiles, legend
   2. At a glance: stat tiles (done / open / decisions / ideas)
   3. Context and goal (short) with a diagram of how the pieces fit, or a timeline
   4. Decisions table: decision | why | alternatives | status
   5. Options comparison: option | pros | cons | effort | verdict (lime row = recommended)
   6. Work done / files touched table
   7. Risks, open questions and blockers (coral)
   8. Next steps: owner, priority, status marks
   9. "Decisions I need from you" panel (always last, short)
3. **Write** to the session's working folder as `JKZ_<Topic>_Wrapup_<YYYY-MM-DD>.html` (match existing `JKZ_*.html` names). Never overwrite; add a version suffix.
4. **Verify** in the browser pane: diagrams render, no console errors, no horizontal page scroll at 375px (tables scroll inside `.tablewrap`), menu and arrow keys work.
5. **Reply in chat in 2-4 lines** plus the file link. Deliver with `SendUserFile` (`display: "render"`). Do not repeat the report in chat.

## Rules

- Use only facts from the session. Mark anything uncertain as **assumed** (dashed `.m.as` mark) rather than inventing it.
- Placeholder or sample numbers must be labelled dummy data.
- Contrast: body text is ink on white or a pale tint, never on a saturated fill smaller than 14px bold.
- Keep each diagram to one idea; label every box and arrow.
