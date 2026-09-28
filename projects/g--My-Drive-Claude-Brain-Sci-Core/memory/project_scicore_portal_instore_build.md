---
name: project-scicore-portal-instore-build
description: "Sci-Core client portal — In-Store daily-numbers feature, KPI/Deliverables reorg, and automated-messaging removal — shipped to main"
metadata:
  node_type: memory
  type: project
  originSessionId: b82468e4-4f6a-4ea7-aa6e-2afb96179ac5
  modified: 2026-09-28T09:42:59.692Z
---

The Sci-Core client portal codebase lives at `C:\Users\info\Developer\gotwurkwebsite` (NOT inside this vault — this vault only holds client notes/memos). Repo: `willemmostert/gotwurkwebsite`, deploys to production from `main` via Vercel.

**Status as of 2026-09-28: shipped and live.** PR #11 (`instore-daily-log` → `main`, merge commit `6486563`) merged. Both pending Supabase SQL pieces were run successfully by Willem directly in the SQL editor (project ref `sklihjowjauhumddslgm`): the `20261011_instore_daily_log.sql` migration, and a one-off `delete from dept_inbox where from_name in (...)` cleanup. Local checkout fast-forwarded to match.

**What shipped (three commits, one PR):**
1. **In-Store daily numbers log** — new generic `MonthCalendar` component (month/week toggle, meant for reuse on Events next); `SalesCalendar` logs any admin-defined In-Store KPI's daily number, shaded by whichever KPI is flagged `is_primary_metric` (reuses Marketing's exact color-mix heatmap formula); Monday-only "Log the weekend" combo entry for Sat+Sun; In-Store's own end-of-day report (separate code path from Marketing's); `eod-reports.ts` generalized to take a `department` param; self-service leave days on the Profile page (new `profile_leave_days` table) suppress a department's EOD only when everyone assigned to it is on leave; a Lightspeed quick-link button with a **placeholder `href="#"` URL — still needs the real link from Willem**.
2. **KPIs & Deliverables reorg** (`/portal/kpis`, now titled "KPIs & Deliverables") — KPIs and live deliverables both grouped by canonical department (not raw department text) then by owner. New "Assigned to" dropdown on the KPI form, backed by the previously-unused `kpis.assignee_name` column. New read-only `DeliverablesOverview` component.
3. **Automated messaging removed** — `dept_inbox` (the portal's Messages/Inbox) is now for human-to-human/human-to-management messages only. Removed: EOD "opens soon"/"missed" notices, marketing automation's `notify()` (missing-info nudges, filming heads-up, overdue-with-no-calendar-row flags) and its dead call sites/helpers, and the monthly performance-report notification. The underlying state changes (report creation, status flips, deliverable/report creation) are untouched — only message-sending was cut. Human-sent messages (Send & assign, replies, deliverable-assigned/approved receipts tied to a real person's name) are unaffected.

**Still open / not yet done:**
1. Real Lightspeed URL for the In-Store quick-link button (`src/components/portal/sales/QuickLinks.tsx`).
2. The actual In-Store metrics (cans sold, Rand sales, signups, etc.) from Rudi — create them via `/portal/kpis` (department: Sales) once confirmed, no code change needed.
3. **Security follow-up**: Willem pasted a live Supabase publishable key AND secret key directly into this chat on 2026-09-28 to try to get direct DB access. Declined to use them (the secret key can't run DDL anyway — it's a project API key, not a DB connection string or Management API token — and using it for the pending `dept_inbox` DELETE would have routed around an existing auto-mode permission denial on that same action). Told Willem to rotate both keys in Supabase → Project Settings → API Keys. **Unconfirmed whether he actually rotated them** — check before assuming those keys are safe to treat as still-valid/private.

**Why:** Willem is expanding the Sci-Core portal beyond Marketing into In-Store, Wholesale, and Events (see [[feedback-portal-department-build-order]] if that memory exists — agreed order: In-Store → Events → Wholesale → cross-cutting @mentions/notifications). This phase also picked up two adjacent asks that came up mid-build: a better KPI/Deliverables management view, and killing automated Messages-panel noise so it only ever shows real human conversation.

**How to apply:** Before starting Phase 2 (Events) or touching this portal again, re-verify current git/deploy state directly (`git log`, `git fetch origin`) rather than trusting this snapshot — this project's portal state has drifted from documentation before (see the vault's own history of automation that was documented as built but never actually deployed). Do not assume the Lightspeed URL or real In-Store KPIs exist without checking `/portal/kpis` and the QuickLinks file directly.
