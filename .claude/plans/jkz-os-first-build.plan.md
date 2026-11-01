# Plan: JKZ Agentic OS, first build (kernel + revenue path + content engine)

---
**Doc Meta** — Created: 2026-10-28 · Version: v0.4 (market policy, Reeve's spine and reference items added; pain-point and prospect assessment agents marked pending) · Supersedes: v0.3
---

**Source**: Boss's direction of 28 Oct 2026, `JKZ_Agentic_OS_Org_Map_v0.4.html`, `JKZ_MASTER_CONTEXT.md` (sections 8A, 8B, 15), `02_Agents/painpoints-agent.md`
**Selected scope**: Wave 0 (memory kernel) + Wave 1 (first revenue path, shadow mode) + **Content Engine** (promoted into the first build)
**Complexity**: Large
**Status**: PLAN ONLY. Nothing is built. Waiting for Boss's confirmation.

## Summary

Build the smallest JKZ OS that can run itself: a kernel and memory (so nothing is lost), the pain-brief to outreach to quote path, and a **content engine** that plans and posts to the social planner (FB, LinkedIn, IG, Threads) and produces short and long video for TikTok and YouTube. Rationale from Boss: more exposure, more chances, more leads, more revenue. Boss answers **one consolidated direction round**; after that the OS plans, drafts, checks and posts by itself inside the approval levels, with hard kill switches. Everything is built test-first on dummy data and runs a **shadow week** (drafts and a dry-run publish log, nothing live) before any live post.

## Direction recorded (Boss answered the round on 28 Oct)

Full record: `03_Sessions/2026-10-28-direction-round.md`. The plan changes as follows.

| Answer | Effect on the plan |
|---|---|
| Three lanes, plus **constant YouTube** including **GHL-related videos** (HighLevel's monthly affiliate programme rewards video) | Adds a **GHL content lane** on YouTube with plain affiliate disclosure. Content calendar gets a "programme-aware" mode that tracks the month's HighLevel video terms (to verify each month) |
| **TikTok posted locally, solving local problems** | Adds a **local problem-solving lane** on TikTok, built from graded pain briefs |
| English only | Kept. Add a per-lane reach report so Bahasa Malaysia can be added from data |
| **Mix** of faceless and avatar | Faceless ships first. The avatar needs a character brief that does not exist; it becomes its own later task, blocked on Boss |
| **Faceless as an income source** | Each video must have an original script, a specific angle and real information, not a template with swapped nouns (YouTube's "inauthentic content" monetisation rule, 15 Jul 2025). New guardrail and test: **template-similarity check** across a week's videos |
| Step ladder, **text and carousel unattended once a design concept exists** | Adds a task: an approved **Design Concept** artifact (brand template pack plus direction brief). Text and carousels that conform to it go L1 after the shadow week. Video stays L2 for the first 5, then L1 for approved formats |
| ~~$150 a month~~ → **$100 a month, produced with PromptEdit** (revised 29 Oct) | PromptEdit prices in credits (about $0.05 each, to verify), so $100 is about 2,000 credits. Priced read-only: a faceless short is about 40 credits ($2), an avatar short about 75 ($3.75), a long video about 100 to 160 ($5 to $8). A Lean month is about $10 to $38, so the cap holds with room for redos. The budget module asks PromptEdit's **estimator before every generation** and holds the queue at the cap. **PromptEdit balance is currently 0**, so Boss tops up (a purchase only he can make) |
| **Booking calendar** as the destination | Each post's link carries a source tag. The public booking URL must exist and name the service before any live post |
| **YouTube not connected** | Boss action: connect through GHL and say whether he owns the channel or is an invited manager |
| **Market policy (29 Oct): at least 50% of effort on first-tier markets, priced in USD; local work is proof, cashflow and finishing the OS** | Reeve's cold-outreach model targets the USD lane. Price book defaults to USD, RM is display only in the local lane. Sending follows the recipient's business hours (evenings and nights in MYT). Region rules for email (opt-out, postal address, consent) are data, not code. Starting markets suggested: US, UK, Australia, with Canada last because of its stricter consent law (to verify). The OS is still the first priority; outreach and closing is one lane of it |

Phase 0 is therefore **done** except for the token rotation, the repo location, the YouTube connection and the booking URL.

## Added 29 Oct: Reeve's core spine and reference items

Source notes: vault `04_Reference/ai-agency-reference-carousels-2026-10-29.md`. These become test-first tasks (14a to 14h) in the build. Each row says what is built now and what is left for ECC.

| # | Item | Built now (test-first) | Status |
|---|---|---|---|
| 14a | **Daily scoreboard**: Date, Prospects, Outreach, Replies, Mockups, Proposal, Paid, Revenue | Table schema, daily roll-up, weekly summary (5 to 8 numbers) in the chief of staff's brief | Build |
| 14b | **Audit pack template** (Reeve lesson 4): 8-point scorecard (maps and reviews, website, social, WhatsApp/DM, CRM follow-up, automation, SEO/GEO, local channels), top 3 pains, mockup slot, recommended package, price from the price book | Schema and renderer with dummy data | Build the **template**. The agent that fills it is pending (below) |
| 14c | **Facts file and claim check**: a `facts/<brand or client>.md` per source of truth; `/qa` extracts every number, date, time, link and promise from a draft and diffs it against the facts file; voice check against Brand Guide V2.1; kernel rule "if a fact is missing, ask or flag, never guess" | Extractor, diff, flag list. Test fixture: the salon example (price $80 vs $95, "Sunday" vs closed, "free refund anytime" vs 24 hours) | Build |
| 14d | **Follow-up cadence**: first message aims for a reply; follow up every 1 to 2 days, at most 4, stop on any reply | State machine and tests | Build |
| 14e | **Prospect sources and filter**: 6 sources (Maps, social, old websites, creators' commenters, job boards and groups, warm referral) and the filter "has a business, has a problem, has budget"; every prospect carries a source tag | Source enum, filter rule, lead-score input | Build the rules. Finding the prospects is pending (below) |
| 14f | **Mockup-first step**: a mockup or before and after is attached to the outreach draft; image credits come from the PromptEdit budget; Boss approves | Attachment slot, credit gate (fake generator) | Build |
| 14g | **Carousel template library**: 5 fixed formats (how-to, mistakes and fixes, behind-the-build story in studio voice, before and after with consent, checklist) plus an 8-slide skeleton with a keyword call to action; rotated across the week | Format enum, skeletons, rotation and similarity tests | Build |
| 14h | **Market lanes**: foreign (USD, at least 50% of effort) and local (RM display only), per-region sending rules, recipient-time windows | See tasks 13g and 13h | Build |

### PENDING TO BE BUILT (design deferred; to be built with ECC)

Boss, 29 Oct: do not design these now; build them later with the ECC skill. The rest of the build must not wait for them.

- **Pain-point agent (`@painpoints`).** Draft spec exists at vault `02_Agents/painpoints-agent.md` (status: proposed, not approved).
- **Prospect assessment agent.** Fills the audit pack for one prospect from public information; feeds the proposal pack.

**Interface only for now:** the plan defines two small interfaces, `PainBriefProvider` and `ProspectAssessor`, with **fake implementations** for tests. The outreach gate ("no brief, no draft") is tested against the fake. When the real agents are built with ECC, they plug into the same interfaces.

## Requirements restated

1. **Content engine is a must-have, not a later wave.** Social planner posting plus TikTok and YouTube video. TikTok is un-parked.
2. **One question round.** Boss is "grilled" once (an HTML form with recommended defaults pre-selected). Answers become `config/direction.toml`. No further routine questions.
3. **Self-running within the ladder.** L0 and L1 run without Boss; L2 needs an explicit "Approved"; L3 never automated. Boss can widen what posts unattended as trust is earned.
4. **Pain-led content and outreach.** The Intelligence department's `/pain` output feeds every angle. No outreach draft without a graded brief.
5. **Safe by construction.** No live posting until compliance sign-off, accounts connected, a working link destination, and a clean shadow week. Kill switches always on.
6. **Test-first.** The deterministic core is implemented with `/ecc:tdd-workflow` after this plan is approved.

## Pattern grounding (mirror, don't reinvent)

| Category | Source | Pattern to mirror |
|---|---|---|
| Agent shape | `HR-Attendance/v1.3/agents/README.md` | Each agent exposes one `run(ctx)`; scheduler and dashboard call the same function (one code path) |
| Shared helper | `agents/scope_resolver.py` | All date math in one module; `today()` centralised "so tests can patch one place"; frozen dataclasses; `Literal` types |
| Config | `client_config.toml`, `03_MASTER_DATA/rules.toml` | Business rules in data (TOML/CSV), never hard-coded; assumptions marked; secrets only in gitignored `.env` |
| Tests | `tests/test_scope_resolver.py` | pytest, one class per function, a fixed reference date constant, table-style cases |
| Scrub | `tests/test_scrub.py` | Whole-word forbidden-token scan over the repo; excluded provenance note |
| Scheduling | `agents/README.md` | Windows Task Scheduler jobs on the PC |
| Docs | repo rule 11 | Doc Meta on every document |
| OS rules | `jkz-agency-os/.claude/CLAUDE.md` (cloud repo) | Approval matrix L0 to L3, one module per folder, `jkz_` fields, `module:action` tags |
| Naming | ECC `agentic-os` skill | Kernel `CLAUDE.md` under 200 lines, each agent file under 100 lines with a Memory Scope section |

No existing code covers posting, queues, kill switches or budgets. Those are new; they follow the patterns above.

Runtime found on this PC: Python 3.14 (the template targets 3.12, so use 3.12-compatible features only), Node 24, Git.

## Part A: the single direction round

Delivered as one HTML form, [JKZ_Direction_Questionnaire.html](../../JKZ_Direction_Questionnaire.html): 14 multiple-choice questions, recommended default pre-selected, "Other" on each, **Copy answers** and **Download JSON** buttons. Boss fills it once; the answers become `config/direction.toml` and a decision record.

| # | Topic | Recommended default | Why |
|---|---|---|---|
| 1 | Audience lanes | Three lanes as already locked on 10 Sep: Personal (FB, IG, LinkedIn, Threads), Business (FB, IG), Video (TikTok, YouTube) | Already decided, avoids re-opening |
| 2 | Languages | English plus Bahasa Malaysia for the MY lane; English only for video | Matches the home market and the US-first YouTube decision |
| 3 | Pillars and ratios | Keep 35 / 30 / 15 / 15 / 5 (build in public, systems education, proof, POV, offer) | Already locked |
| 4 | Cadence | "Lean" for the first 2 weeks: LinkedIn 4, IG 4, Threads 5, FB 3 per week; 3 shorts per week; 1 long video per month. Then ramp | You have little time; consistency beats volume |
| 5 | On-screen presence | Faceless first (voice, captions, b-roll). AI avatar host in phase 2 | Cheapest, fewest likeness and disclosure issues; Boss never on camera |
| 6 | CTA boundary | Soft bio-link only, never a hard sell in a post | Already decided for credibility content |
| 7 | Channel identity | One handle `jkzentra` everywhere | Decided 10 Sep; fastest |
| 8 | Accounts and access | Per platform: exists and connected / exists, not connected / does not exist. Boss connects through GHL's own sign-in. **The OS never receives a password** | Safe access model |
| 9 | Video budget | Monthly credit cap and per-video cap, hard stop at the cap (Boss picks the numbers; suggested starting point $150 a month, $15 per video, to confirm against actual subscriptions) | Stops cost run-away |
| 10 | Posting windows | Initial windows per platform in MYT with a no-post quiet period overnight; the OS re-tunes from real stats after 2 weeks | Needs a starting point |
| 11 | What may post unattended | Step ladder: (a) nothing for the shadow week, (b) evergreen text posts from approved templates, (c) plus carousels after 2 clean weeks, (d) video only after 10 approved with no edits | Trust is earned in steps |
| 12 | Guardrails | Always label AI-generated video and voice; no outcome claims; no client names without written consent; no competitor naming; no personal financial advice; comment replies only from approved templates, DMs L2 | Brand and platform safety |
| 13 | Kill switches | Global pause file; auto-pause on a platform warning, two QA blocks in 24 hours, spend cap hit, or a spike of negative comments; **dead-man's switch: auto-posting stops if Boss has not opened the queue for 3 days** | Never post blind |
| 14 | Link destination | A GHL discovery-call page on a GHL-hosted address until `jkzentra.com` is fixed | The site returned 404 on 20 Oct, so there is nothing to point to yet |

## Part B: content department design (inside the org map)

| Department | Role in the content engine |
|---|---|
| Intelligence (`@intel`) | `/pain` and `/trend` produce graded angles per industry and per week. Replies and views feed back and re-grade the pains |
| Growth, marketing desk (`@growth`) | `/content`: weekly brief, anchor post, repurpose to carousel, thread, short script, long outline; builds the queue |
| Build Studio (`@planner`, `@coder`, `@tester`, `@release`) | Builds the deterministic core, adapters and tests below |
| Quality (`@qa`) | `/qa` on every draft: price-wall, tool names, brand voice (Brand Guide V2.1), claim grading, AI-disclosure, secrets. Can block. `/compliance` before go-live |
| Knowledge (`@keeper`) | Logs every run, every approval, cost, and the weekly performance note; owns the kill-switch status report |
| Chief of staff | The 08:00 queue shows each draft next to its pain brief; carries the dead-man's-switch clock |

**Weekly rhythm:** Monday brief and angles, Tuesday drafts and QA, Wednesday video production (within credit cap), Thursday repurpose and schedule, Friday spot-check and weekly report. Queue is draft-and-hold; nothing publishes without passing the ladder.

**Video pipeline (per piece):** script from approved angle → asset spec (faceless or avatar) → **credit gate (L2)** → generation request → captions and disclosure label → QA → Boss approval (until trust rule d) → schedule to the platform.

## Part C: phases, exit tests, dependencies

| Phase | What | Exit test | Needs Boss |
|---|---|---|---|
| **0 Direction** | Boss fills the form once. Rotate the exposed GHL token. Decide repo location | `config/direction.toml` exists and validates | Yes, 20 minutes |
| **1 Kernel and memory (Wave 0)** | Scaffold clean repo, kernel `CLAUDE.md`, agent files, `/brief /wrapup /decision`, config loader, health check | Three sessions in a row start with context and end with a wrap-up. Structure tests pass | No |
| **2 Deterministic core** | Library `jkzos`: clock, calendar planner, approval state machine, guardrails, post queue, budget, kill switch, adapter interface and fakes | All unit tests pass, coverage 80% or more, live adapter cannot be created in dry-run | No |
| **3 Intelligence and outreach path (Wave 1)** | `/pain`, pain-library schema and grading, outreach gate "no brief, no draft", `/quote` from the price book, `/qa` | Five dummy prospects go from brief to QA-passed draft to quote, the gate blocks a draft with no brief | No |
| **4 Content engine** | Weekly brief to queue, repurposing, video pipeline with fake generators, performance report from stats | A dummy week is planned, drafted, QA'd, queued and dry-run published to a log with correct windows, caps and ratios | No |
| **5 Shadow week** | Run the whole thing on real drafts, publish to the dry-run log only | Boss compares drafts with what he would have posted; zero guardrail escapes; zero missed runs | Light, 15 min a day |
| **6 Go-live gate** | Compliance checklist signed, accounts connected through GHL, link destination live, kill switches drilled | Each switch tested once on purpose | **Yes** |
| **7 Live, laddered autonomy** | First live posts at L2, then step up the ladder from answer 11 | Two clean weeks per step | Approvals only |

**Dependencies:** direction answers (Phase 0) → config (1) → core (2) → both paths (3, 4) → shadow (5) → go-live (6). Phases 3 and 4 can run in parallel once Phase 2 is done, in separate lanes with separate files.

## Files to change or create (clean repo, location pending Boss)

Assumption: a **new clean repo** `C:\JK Zentra\JKZ OS\` (suggested remote `jkzentra/jkz-os`). If Boss prefers, the same layout goes into the existing Agentic OS repo. Nothing is created until confirmation.

| Path | Action | Why |
|---|---|---|
| `CLAUDE.md` | CREATE | Kernel: identity, rules, routing table, approval matrix (under 200 lines) |
| `agents/{cos,intel,growth,qa,keeper}.md` | CREATE | Wave 0 and 1 seats, each under 100 lines with Memory Scope |
| `.claude/commands/{brief,wrapup,decision,pain,content,qa}.md` | CREATE | Commands |
| `config/direction.toml` | CREATE | The one question round, as data |
| `config/guardrails.toml` | CREATE | Banned words, tool names, price-wall terms, disclosure rules, claim-grade rule |
| `config/channels.toml` | CREATE | Per-platform cadence, windows, daily caps |
| `jkzos/clock.py` | CREATE | One patch point for time (mirrors `scope_resolver.today()`) |
| `jkzos/calendar_plan.py` | CREATE | Weekly plan from direction and ratios |
| `jkzos/approvals.py` | CREATE | L0 to L3 state machine, L1 windows, L2 never times out |
| `jkzos/guardrails.py` | CREATE | Draft checks |
| `jkzos/queue.py` | CREATE | Post queue, idempotency keys, per-day caps, dry-run flag |
| `jkzos/budget.py` | CREATE | Credit and spend caps with a log |
| `jkzos/killswitch.py` | CREATE | Pause file, auto-pause triggers, dead-man's switch |
| `jkzos/adapters/{base,fake,ghl_social,video}.py` | CREATE | `Publisher` interface, fake for tests, GHL adapter, video adapter. Live adapters refuse to construct unless mode is live, compliance is signed and the OS is not paused |
| `tests/…` | CREATE | One test file per module, plus structure, scrub and end-to-end |
| `scripts/{run_scheduled,healthcheck}.ps1` | CREATE | Task Scheduler entry points |
| `data/{inbox,logs,decisions,state,costs}/` | CREATE (gitignored logs) | Machine state; vault stays the knowledge store |
| `.env.example`, `.gitignore` | CREATE | No secrets in files |

## Tasks (each is written test-first in `/ecc:tdd-workflow`)

1. **Scaffold + structure tests.** Mirror the template layout. Tests assert: kernel under 200 lines, every agent file under 100 lines and containing Memory Scope and Constraints, Doc Meta present, no tokens or client names (scrub-style). *Validate:* `py -3 -m pytest tests/test_structure.py tests/test_scrub.py`
2. **Config loader.** Load and validate `direction.toml`, `guardrails.toml`, `channels.toml`; reject missing keys and out-of-range values. *Mirror:* `rules.toml` handling. *Validate:* config tests.
3. **Clock.** One `now()` and `today()`; all other modules import it. *Mirror:* `scope_resolver.today()`.
4. **Calendar planner.** Given a week and the direction, produce slots: ratios within one post of 35/30/15/15/5, per-platform cadence, windows respected, nothing in quiet hours, personal and business split on odd and even days. Golden-file test. *Validate:* calendar tests.
5. **Approval state machine.** Table-driven tests for every level: L1 timeout default (social sends, follow-ups hold), **L2 never auto-sends**, L3 never automated, reject reopens with notes.
6. **Guardrails.** A fixture corpus of good and bad drafts: price-wall breach, tool names, banned words, C-grade pain stated as fact, missing AI label, secret-looking strings, named client. Every bad draft must be blocked with a reason.
7. **Post queue.** Idempotency (replaying the queue never double-posts), per-platform daily cap, dry-run by default, slot collision rejected.
8. **Budget.** Per-video and monthly credit caps, hard stop, spend log; a request over the cap is refused.
9. **Kill switch.** Pause file blocks at the adapter boundary; auto-pause triggers; dead-man's switch at 3 days; status report.
10. **Adapters.** `Publisher` interface, `FakePublisher` records calls. GHL adapter tested against recorded sample payloads with no network. **Invariant test:** a live adapter cannot be constructed in dry-run, unpaused-and-signed is required.
11. **Intelligence path (interfaces only).** `PainBriefProvider` and `ProspectAssessor` interfaces with fakes; pain-brief schema and grading (two independent sources for A), **outreach gate test: no brief, no draft; only A or B pains in a message; one pain per message.** The real `@painpoints` and prospect assessment agents are **PENDING, built later with ECC**.
12. **Quote path.** `/quote` reads the price book and flags any line under the 2x cost floor.
13. **Content engine.** Weekly brief to anchor to repurposed pieces to queue, with the QA gate in between; video pipeline with the credit gate and fake generators; weekly performance report from sample stats.
13a. **Design Concept gate.** A schema for the approved Design Concept (template pack, direction brief, voice, banned patterns). Test: a draft that does not conform cannot take the unattended path; a conforming one can, but only after the shadow week.
13b. **Per-format cost model, in PromptEdit credits.** Monthly cap 2,000 credits ($100), 20% reserve, at most 2 regenerations per piece, ceilings of faceless short 60, avatar short 100, long 250, carousel 15. The budget module calls the **estimate-before-generate** step; a request over a ceiling or the cap is refused. Tests use a fake estimator: a lean month stays under the cap, a piece over its ceiling is refused, a third regeneration is refused, a month over the cap holds the queue.
13g. **Market-aware sending.** Per-region rule set in config (opt-out line, postal address, consent flag, sending hours in the recipient's time zone). Tests: an email to a US prospect without opt-out and postal address is blocked; a send outside the recipient's business hours is held; a region with no rule set is refused.
13h. **USD price book as the default.** Catalog in USD; the local lane shows RM as display only. Test: no RM price can appear in any foreign-lane draft (price-wall), and no unconverted figure in a quote.
13f. **Assembler decision.** PromptEdit makes assets only. Choose and wrap the assembler (captions, timing, cuts) behind the same adapter interface, tested with a fake. Decided by `@planner` in Phase 4.
13c. **Template-similarity check.** Across any week's videos, structure, hook and length must differ; near-identical output is blocked and sent back for a new angle (protects YouTube monetisation under the "inauthentic content" rule).
13d. **Programme-aware calendar.** A small data file of the current month's HighLevel affiliate video terms (per-video payout, minimum length, contest window). The calendar proposes extra YouTube slots inside the budget when a programme is open, and every GHL video carries an affiliate disclosure. Test: no GHL video without the disclosure line.
13e. **Lane reports.** Per-lane reach and lead counts (GHL stats), so Bahasa Malaysia and cadence changes are decided from data.
14. **Scheduler scripts and health check.** Catch-up logic for a missed run; health check reports last run, queue depth, spend, pause state.
15. **End-to-end dry run.** Fake client and a dummy week, start to finish, publish to the log only.
16. **Docs and release.** Doc Meta, changelog, README, decision records for the direction answers; independent code and security review before the shadow week.

## Test strategy for `/ecc:tdd-workflow`

- **Red, green, refactor** for every task above; failing test committed first. Coverage target 80% or more: `py -3 -m pytest --cov=jkzos --cov-fail-under=80`.
- **Dummy data only.** Sample brands, sample prospects, sample stats. No real client, staff or token anywhere in fixtures; the scrub test enforces it.
- **No network in unit tests.** GHL and video adapters tested through recorded payloads and fakes.
- **Properties, not just cases:** never over the daily cap, never inside quiet hours, never two posts in one slot, ratios hold across many generated weeks.
- **Safety invariants as tests:** a paused OS publishes nothing; a live adapter cannot exist without compliance sign-off; an L2 item with no approval never sends, however long it waits.
- **Reviewer independence:** code and security review done by Quality (not the builder) before Phase 5.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Platform enforcement against automated or AI-generated posting (spam rules, synthetic-media labels) on Meta, TikTok, YouTube | High | Official channels only (GHL or platform APIs), no engagement bots, always label AI video and voice, daily caps, human spot-check, check each platform's current policy at build time (not verified here) |
| An unverified claim, client name or SEA price reaches the public | High | Guardrails plus QA on every draft, shadow week, L2 on anything with a claim, claim grading from the pain library |
| `jkzentra.com` is down, so CTAs point nowhere | High | GHL-hosted discovery-call page as the destination; fix DNS separately and only on Boss's yes |
| GHL Social Planner may not publish natively to TikTok or YouTube | Medium | Verify first (earlier notes conflict). Fallbacks: automation scenario, platform API, or a manual-upload package approved at L2 |
| Video credits and token spend run away | Medium | Per-video and monthly caps with a hard stop, spend log, cost shown in the morning queue |
| PC asleep, so scheduled runs miss | Medium | Catch-up logic, health check, optional cloud scheduler later |
| Boss is away, so the OS posts unattended too long | Medium | Dead-man's switch at 3 days |
| Exposed GHL token | High | Rotate before anything is connected; env vars only |
| Low-quality "AI slop" erodes trust | Medium | Pain-led, evidence-backed angles; Boss spot-check; reply and view data feeds back into the pain library |
| Scope creep with little time | Medium | Waves, shadow mode, build only what the exit tests need |
| Platform API access (TikTok publishing) may need developer approval | Medium | Verify early; planned fallback above |
| **YouTube monetisation:** mass-produced or templated AI video is ineligible under "inauthentic content" (15 Jul 2025), and the Partner Programme bar is high (a third-party source gives 1,000 subscribers plus 4,000 watch hours, or 10 million Shorts views in 90 days; to verify) | High | Original script and angle per video from graded evidence, template-similarity check, human gate on video angles, treat monetisation as a later bonus, not the plan |
| **Budget:** $100 a month (about 2,000 credits) against about 13 videos. Estimated at $10 to $38 for a Lean month, so it fits, but real costs reconcile after generation and redos add up | Low | Estimate before every generation, per-format ceilings, 2 regenerations at most, 20% reserve, queue holds at the cap |
| **PromptEdit balance is 0** and credit price ($0.05) is unverified | Medium | Boss tops up in stages (about $20 to $30 first); shadow week uses fake generators and needs almost no credits |
| **PromptEdit does not assemble or publish** | Medium | Pick an assembler in Phase 4 behind the adapter interface; publishing stays with GHL or platform adapters |
| **HighLevel programme terms change monthly** (contest prizes, per-video payouts) | Medium | Programme data file refreshed each month; the OS never promises Boss a payout |
| **English-only local TikTok** may limit reach | Low | Lane reach report after the shadow week; add Bahasa Malaysia if the data supports it |
| **Avatar needs a character brief that does not exist** | Medium | Faceless first; avatar is a separate task blocked on Boss |
| **Booking-link CTA has no context** for the visitor | Low | Source-tagged link, booking page names the service |

## Boss's blockers (only these)

1. ~~The direction form (Part A)~~ **Done 28 Oct.**
2. **Rotate the GHL token**, and **connect YouTube through GHL's sign-in** (say whether you own the channel or are an invited manager).
3. **Repo location** (a clean new repo is recommended; reply "yes" and I will use it).
4. **The public booking-calendar URL** that every post points to, with the service named on the page.
5. **Approve a Design Concept** (template pack and direction brief) before text and carousels can go unattended. I will draft it for you to approve.
6. **A character brief for the AI avatar**, only when you want the avatar half of "Mix".
7. **Top up PromptEdit** (balance is 0), in stages. Only you can make the purchase.
8. **A legal sender identity and a valid postal address** for US and UK cold email (US law requires a postal address in commercial email; to verify). This ties to the open question of how contracts and payment are papered.
9. **A way to collect USD** (GHL with Stripe or another route, availability for Malaysia to verify).
10. **Which first-tier markets first.** Suggested: US, UK, Australia.
11. **Compliance checklist sign-off** before go-live.

## Validation

```bash
py -3 -m pytest -q
py -3 -m pytest --cov=jkzos --cov-fail-under=80
py -3 -m pytest tests/test_structure.py tests/test_scrub.py
```

## Acceptance

- [ ] Direction round answered once; `direction.toml` validates
- [ ] All tasks done test-first; coverage 80% or more
- [ ] Safety invariants proven by tests (pause, dry-run, L2, caps)
- [ ] Dummy week runs end to end in dry-run
- [ ] Independent review passed
- [ ] Shadow week clean
- [ ] Go-live gate signed, kill switches drilled

## Estimate (rough, to tune)

Boss: about 20 minutes for the form, then a few minutes a day. Build: Phases 1 to 4 about 3 to 4 working days of agent work; shadow week 7 days. The sprint ends 8 Nov, so Phases 0 to 4 fit before it; the shadow week finishes just after.

**WAITING FOR CONFIRMATION.** Proceed with this plan? (yes / no / modify: …)
