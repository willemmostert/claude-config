---
name: "catalyst-client-tldr-update"
description: "Use whenever updating a Catalyst Coaching client's Notion page from a Fathom call (TLDR refresh, new training programme, milestone updates). Ensures programs are laid out Monday-Sunday using real Catalyst Workout Library codes, milestones are countdown-friendly, and the page stays clean — no clutter from superseded content."
---

## Catalyst Coaching — Client Notion Update Standard

Apply this whenever pulling a Fathom call for a Catalyst Coaching client and updating their Notion page (in the "Catalyst - All Clients" database) with a new TLDR and/or training programme.

### 0. Always build programmes from the real Catalyst Workout Library — never invent exercises

There is a live Notion database called **"🏋️ Catalyst Workout Library"** (search Notion for "hybrid-workout-library" or "Catalyst Workout Library" to find it; as of this writing its data source is `collection://c5d9537f-5291-4cc3-8c21-250fe4c10146`). This is the same code set synced to Everfit — it is the actual source of truth for what a code like "A1", "B1.b", "E2", "M4", "TRI5" etc. contains. Every client page's "References: hybrid-workout-library.md" line points to this database.

**Before building or rebuilding any Current Programme section:**
1. Query the data source (`notion-query-data-sources`, SQL mode) to pull the relevant Code / Name / Category / Author / Details rows. Category is one of Lift, Run, Conditioning, Abs, Mobility, Tri. Author is Chris or Willem.
2. Select real codes that match the client's needed focus (e.g. chest/shoulder/arm bias, leg maintenance, injury modifications) — do not invent exercise names, set/rep schemes, or made-up codes like "Chest & Shoulders Anchor." Use the actual Code + Name + Details from the library verbatim.
3. Note that several Willem-authored codes (A16, C8, C9, C10, C11, and the TRI-series like TRI5 "Watt Bike Easy Spin" / TRI6 "Watt Bike Intervals") embed cardio/conditioning equipment directly into the code (e.g. A16 opens with "Spin Bike"). When a client's plan calls for pre-lift cardio before every session (e.g. running being phased out in favor of in-gym cardio), prefer these cardio-embedded codes where they fit, and otherwise prepend a TRI-series bike code ahead of a pure Lift code.
4. Keep marquee-lift continuity where possible — if a client has been logging progress on a specific lift (e.g. incline press every Monday), prefer a code that keeps that same marquee lift even if the surrounding accessories change, and note explicitly when a code swap changes the rep scheme (e.g. "swaps A1 4×4-6 for A16 5×5") so the coach can confirm or override.
5. Flag any code selection inline with a bracketed note for the coach to confirm in Everfit, since Details rows don't include rest times — those still need to be set in Everfit as normal.

Do not fabricate set/rep/rest prescriptions from scratch. If a genuinely new movement pattern is needed that isn't in the library, say so explicitly and ask the coach rather than inventing a plausible-sounding exercise.

### 1. Keep the page clean — this is a living doc, not an archive

Every time you issue a brand new TLDR and training programme, **erase the previous full write-ups** rather than stacking them. The page should always read top-to-bottom as:

1. **## TLDR — [current, most recent call/refresh]** — the current narrative recap only. Remove old TLDR write-ups rather than stacking them below with "superseded by" notes.
2. **## Current Programme — [name] (rolls out [date])** — the Monday→Sunday table + day-by-day breakdown for the active programme only, built from real library codes per §0. Remove the previous programme's full breakdown.
3. **## Current Macros** — a short, clean current macro block (training day / rest day targets, protein target, supplements). Not a stacked history of every past macro refresh.
4. **## Previous Phases** — a condensed **2-3 line recap per past phase** (not full exercise write-ups, not full old TLDR prose). One short paragraph per superseded programme: name, dates, and the one-line reason it changed.
5. **## Call History** — the chronological bullet log (one line per call/refresh/bot flag). This is the detailed historical record — keep it complete and append to it, never delete from it.
6. **## [Client] — Client Knowledge Base** — durable personal/training/medical profile info. Not "previous update" clutter — keep it current, edit facts in place rather than duplicating.

**Remove scattered bot check-in callouts** (e.g. "🤖 Reginald · [date]" boxes) once their content is captured in Call History — don't leave them sitting loose in the page body. Call History is the single place for that log.

Do not create sections like "Transition Plan", "Programme Preview", or duplicate "OLD Macros" blocks — fold anything genuinely still-relevant into Current Programme/Current Macros, and drop the rest into the one-line Previous Phases recap or Call History.

### 2. Training programme must always be laid out Monday → Sunday, clearly

- A **summary table** at the top of "Current Programme": Day | Code | Focus | Pre-Lift Cardio (or equivalent columns — adjust for injury-modified programmes, e.g. swap in a "Notes" column for physio constraints).
- Rows ordered **Monday through Sunday**, no exceptions — even REST days get a row (use the relevant Mobility code, e.g. M4, rather than leaving it blank).
- Below the table, a **detailed day-by-day breakdown** (### Day 1 — ... (Monday) through ### Day 7 — ... (Sunday)) naming the library Code + Name and listing its exact Details (sets × reps) per §0.

### 3. Milestone goals (4-Week / 8-Week / 12-Week Milestone properties) must be countdown-friendly

- Lead with a countdown: "X days to go (by [date]): ..." — calculate X as the number of days from today's actual date (get the real current date) to the milestone date.
- Use a distinct emoji per tier: 🔥 for the 4-week (near-term), 🚀 for the 8-week (mid-term), 🏁 for the 12-week (finish-line).
- Keep the substance concrete and specific (weight targets, visible physique changes, habit/consistency proof points, pending confirms) — the fun framing is in addition to the specifics, not instead of them.
- Recalculate milestone dates/day-counts relative to when the new phase actually rolls out (usually the Monday after the call), not from the call date itself.

### 4. General

- Always pull the actual latest Fathom transcript (not just the summary) before writing the TLDR — direct quotes and specifics matter, especially for anything injury/medically related.
- Insert the new TLDR at the top of the page.
- Add a corresponding line to "## Call History" for any live (non-bot) call — this list is append-only, never trimmed.
- Don't invent Client Status changes, blood work numbers, or other verified-data properties without an explicit source — only update fields you have real evidence for (transcript, Reginald bot callouts, or explicit instruction).
- When in doubt about how aggressively to clean up a specific page, or which library codes best fit a client's needs, ask before guessing.

