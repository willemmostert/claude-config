---
name: project-scicore-portal-instore-build
description: "Sci-Core client portal — In-Store daily-numbers feature build, in progress on a pushed-not-merged branch"
metadata:
  node_type: memory
  type: project
  originSessionId: b82468e4-4f6a-4ea7-aa6e-2afb96179ac5
  modified: 2026-09-28T00:22:27.088Z
---

The Sci-Core client portal codebase lives at `/c/Users/info/Developer/gotwurkwebsite` (or `C:\Users\info\Developer\gotwurkwebsite` on Windows), NOT inside this vault — this vault (`G:\My Drive\Claude Brain\Sci-Core`) only holds client notes/memos. Repo: `willemmostert/gotwurkwebsite`, deploys to production from `main`.

**Standing architecture facts** (confirmed by reading the code directly, not by trusting vault notes — the vault's `_overview.md` was stale/wrong about what departments existed):
- Marketing is the only department with a real calendar/EOD report historically. In-Store (folder `sales`), Wholesale, Events, Warehouse existed only as generic shells (comment box + shared deliverables + messages + KPI display) before this build.
- Shared pieces already generic and safe to reuse as-is: `DepartmentPage`/`DeptShell` (department page frame), `page_comments` + `PageComments` (comment box), `mk_deliverables` + `DeliverablesBoard`/`Board.tsx` (Kanban), `dept_inbox` + `MessagesPanel` (messaging), `kpis`/`kpi_logs` + `KpiManager`/`KpiPanel` (admin-defined, ad-hoc, department-scoped KPIs — no fixed catalog).
- Marketing's Weekly Content Calendar (`CalendarWeek.tsx`) is deeply coupled to Metricool — not reusable for other departments without a rewrite.

**What's been built (Phase 1 of a 4-phase plan — see [[feedback-portal-department-build-order]]):** In-Store daily numbers log. Branch `instore-daily-log`, commit `7432bc3`, **pushed to GitHub but not yet merged or PR-opened** as of 2026-09-28. Full plan was saved to `C:\Users\info\.claude\plans\linear-soaring-robin.md` in that session (plan files are session-scoped/ephemeral — may not persist across machines/sessions, so treat this memory as the durable record instead).

Built: a new generic `MonthCalendar` component (month/week toggle, meant to be reused for Events next); `SalesCalendar` (log any admin-defined In-Store KPI's daily number, shaded by whichever KPI is flagged `is_primary_metric`, using the exact color-mix heatmap formula Marketing already uses for follower-activity); a Monday-only "Log the weekend" combo entry for Sat+Sun; In-Store's own end-of-day report (reads back the day's numbers for a one-tap confirm, separate code path from Marketing's post-attribution EOD); `eod-reports.ts` generalized to take a `department` param (was hardcoded to `"marketing"` via a since-removed `EOD_DEPARTMENT` constant); self-service leave days on the Profile page (new `profile_leave_days` table) that suppress a department's EOD report only when everyone assigned to that department is on leave; a Lightspeed quick-link button (placeholder `href="#"` URL). New migration: `supabase/migrations/20261011_instore_daily_log.sql` (adds `kpis.is_primary_metric`, `dept_day_logs`, `profile_leave_days`) — **not yet run in Supabase**.

**Still blocking before this ships:**
1. Real Lightspeed login/deep-link URL from Willem — `src/components/portal/sales/QuickLinks.tsx`.
2. The actual In-Store metrics (cans sold, Rand sales, signups, etc.) from Rudi — created via `/portal/kpis` once known, no code change needed since KPIs are admin-defined.
3. Run the migration in the Supabase SQL editor (same manual-paste workflow as every prior migration in this project).
4. Open the PR (link: `https://github.com/willemmostert/gotwurkwebsite/pull/new/instore-daily-log`) and confirm the Vercel preview deployment before merging.
5. `gh` CLI and an authenticated `vercel` CLI are NOT available on this machine — PR creation and preview-link lookup had to be handed to Willem to do manually.

**Why:** Willem is expanding the Sci-Core portal beyond Marketing into In-Store, Wholesale, and Events (a large voice-dictated feature dump on 2026-09-28). Agreed build order: In-Store → Events → Wholesale → cross-cutting (@mentions/notifications, leave-day rollout to other departments). This In-Store phase is meant to establish reusable patterns (`MonthCalendar`, the day-log anchor table, the leave-day EOD gate) that Events and Wholesale build on next, not a one-off.

**How to apply:** Before starting Phase 2 (Events) or touching this portal again, re-read this memory and re-verify current git/PR/migration state directly (`git log`, `gh pr list` if available, Supabase dashboard) rather than trusting this snapshot — portal state has previously drifted from what memory/notes claimed (see the vault's own `_overview.md` history of "Ben" being built-and-documented but never actually deployed). Do not assume the migration has been run or the PR has been merged without checking.
