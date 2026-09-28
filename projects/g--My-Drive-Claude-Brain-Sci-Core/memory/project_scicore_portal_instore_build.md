---
name: project-scicore-portal-instore-build
description: "Sci-Core client portal — full department build-out (In-Store, Events, Wholesale, @mentions) — shipped to main and live"
metadata:
  node_type: memory
  type: project
  originSessionId: b82468e4-4f6a-4ea7-aa6e-2afb96179ac5
  modified: 2026-09-28T10:36:10.686Z
---

The Sci-Core client portal codebase lives at `C:\Users\info\Developer\gotwurkwebsite` (NOT inside this vault — this vault only holds client notes/memos). Repo: `willemmostert/gotwurkwebsite`, deploys to production from `main` via Vercel.

**Status as of 2026-09-28: all four phases shipped and live on `main` (commit `611eb7a`).** All migrations run by Willem directly in the Supabase SQL editor (project ref `sklihjowjauhumddslgm`). This was a large batch built across two sessions:
- Phase 1 (earlier session): In-Store daily numbers log, KPIs & Deliverables page reorganized by department/owner, automated `dept_inbox` messages removed entirely (human-to-human only from here on).
- Phases 2–4 (this session, built and merged in one pass at Willem's request): Events department, Wholesale department, @mentions.

**Architecture note for next time:** the daily-numbers-calendar system (month/week calendar, click-a-day logging, KPI shading, weekend logging, leave-aware end-of-day report) is now **generalized by department**, not In-Store-specific. Shared code: `src/lib/dept-daily-log.ts`, `src/app/portal/(app)/daily-log/{day,eod}-actions.ts`, `src/components/portal/department/{DailyLogCalendar,LogDayModal,DailyEodReportPanel}.tsx`. Currently used by `sales` (In-Store) and `wholesale`. `src/components/portal/calendar/MonthCalendar.tsx` is the underlying generic month/week grid — already reused by Events too (`EventsCalendar.tsx`, shaded by event count instead of a KPI amount). If Warehouse ever gets a daily-numbers calendar, reuse this same system rather than forking it again.

**What shipped this session (Phases 2–4):**
1. **Events** — `events` table (name, stock needed, KPI tag, "happens in-store" flag, "notify marketing" flag). Calendar at `/portal/events`. "Notify marketing" sends one direct `dept_inbox` message signed by whoever created the event — a human-action receipt, not automation (matches the same category kept when automated messaging was removed in Phase 1). A new `UpcomingEventsCard` on the In-Store page shows a countdown to the soonest events flagged "in-store."
2. **Wholesale** — reuses the generalized daily-log system for its own numbers (stock sold/in stock/to ship/shipped, all admin-defined KPIs like In-Store's). New `wholesale_invoices` table covers both payment (sent/paid/follow-up) and shipping (ship/delivered/courier) on one row per client order. A follow-up date auto-creates a real `mk_deliverables` reminder; marking paid auto-completes it. New private `wholesale-invoices` storage bucket (department-scoped RLS, same shape as `marketing-media`). Two thin status bars render on the calendar days an invoice spans (`src/components/portal/wholesale/InvoiceCalendarBars.tsx`).
3. **@mentions** — `page_comments.mentioned_profile_ids` + new per-person `profile_mentions` table (same shape idiom as `portal_patch_reads`). New `MentionTextarea.tsx` wraps the comment box; typing "@" opens a roster picker. Roster is resolved via `getMentionRoster()` (`src/app/portal/(app)/mentions/actions.ts`) using the **admin client**, because `profiles` has no RLS letting anyone read another profile at the same business — not even executives (confirmed by reading `20260919_harden_profiles_privilege_escalation.sql`: the old own-row policies were dropped and never replaced). Sidebar shows a numeric pill next to a department nav link when the signed-in person has an unread mention there; opening that department's comment box clears it.

**Still open / not yet done:**
1. Real Lightspeed URL for In-Store's quick-link button (`src/components/portal/sales/QuickLinks.tsx`).
2. Real email address and WhatsApp number for Wholesale's quick-links (`src/components/portal/wholesale/QuickLinks.tsx` — both are empty-string placeholders, `href="#"` until filled in).
3. The actual In-Store/Wholesale metrics from Rudi — create via `/portal/kpis` (department: Sales/Wholesale) once confirmed, no code change needed since KPIs are fully admin-defined.
4. **None of this was clicked through in a real browser before merging** — only `tsc --noEmit` and `eslint` were run. This was Willem's explicit call given the urgency ("get everything pushed to the live site now") — he was told this tradeoff directly before merging. Worth a real walkthrough of Events and Wholesale on the live site.
5. Warehouse was explicitly never scoped (no specifics given) and stays untouched.
6. **Security follow-up carried over from Phase 1, still unconfirmed**: Willem pasted a live Supabase publishable key and secret key directly into chat on 2026-09-28 during Phase 1. He was told to rotate both in Supabase → Project Settings → API Keys. Whether he actually did this is unconfirmed — check before assuming those keys are still safe to treat as private.

**Why:** Willem is running Sci-Core's whole team (In-Store/Marketing/Wholesale/Events/Warehouse) through this one portal. This session finished the department build-out he originally scoped in one voice-dictated brain dump, after Phase 1 (In-Store) had already validated the pattern.

**How to apply:** Before touching this portal again, re-verify current git/deploy state directly (`git log`, `git fetch origin`) rather than trusting this snapshot. If a future request touches the daily-log calendar, KPI shading, or end-of-day reports for ANY department, check `src/lib/dept-daily-log.ts` and `DAILY_LOG_DEPARTMENTS` first — it's shared code now, not per-department.
