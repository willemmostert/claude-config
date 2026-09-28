# Sci-Core portal — department build-out (Phase 1: In-Store)

## Context

Marketing is the only fully-built department in the Sci-Core client portal (`gotwurkwebsite`, deploys from `main`). In-Store, Wholesale, Events, and Warehouse exist only as empty generic shells (comment box + shared deliverables + messages + KPI display) — confirmed by reading the actual code, not the vault notes (which were stale/wrong in places). Willem wants to build these out into real working departments, plus two cross-cutting features (@mention notifications, weekend/leave-aware end-of-day reporting).

Given the size of the full ask, we agreed to build **one department fully, end-to-end, before starting the next**, in this order: **In-Store → Events → Wholesale → cross-cutting (@mentions, weekend/leave EOD)**. This plan covers **Phase 1: In-Store** in full implementation detail. Later phases are sketched at the end as a roadmap so scope stays visible, but will get their own detailed plan when we get there.

In-Store's job (Rudi): every day, log the day's numbers (cans sold, sales in Rand, membership signups — exact metrics TBD, Willem will confirm with Rudi) on a calendar. The calendar shades days by sales intensity (like Marketing's activity heatmap, but by Rand value instead of follower activity), shows weekly/monthly totals, and feeds an end-of-day report that reads back what was logged for a one-tap confirm ("are these numbers accurate?").

## Key architectural decisions (from codebase research)

1. **Reuse the existing KPI system entirely for "the numbers."** `kpis`/`kpi_logs` already support: admin-defined ad-hoc KPIs per department (no fixed catalog), department scoping via `KpiManager` (`src/components/portal/KpiManager.tsx`, `src/app/portal/(app)/kpis/actions.ts`), and a `kpi_logs` insert path with no department or same-day restriction (`src/lib/kpi-tracking.ts`'s `recomputeKpis` already re-derives `current_value` from all logs in-period). Willem/Rudi don't yet know the exact metric names — that's fine, since KPIs are admin-defined at any time with zero code changes. **No exact-metrics blocker for this build.**
2. **New table `dept_day_logs`** is the "this day was logged" anchor (customer_id, department, log_date, notes, submitted, submitted_at, logged_by, logged_by_name) — generic by department so Events/Wholesale can reuse it in later phases. Actual numeric values still live in `kpi_logs` (tagged so we can identify/replace them on edit — see below); `dept_day_logs` just marks a day as logged and carries free-text notes.
3. **New reusable presentational component `MonthCalendar`** (`src/components/portal/calendar/MonthCalendar.tsx`) — a from-scratch month grid + week-view toggle, not an extension of `CalendarWeek.tsx` (that component is deeply coupled to Metricool/marketing per research — reusing it would mean a rewrite anyway). Grid math (month offset/day-cell generation) is lifted from the existing `DatePicker.tsx` popover, which already has exactly this logic. Pure props: `{ month, year, view: "month"|"week", weekAnchor, onSelectDate, renderDay(date) => node, shadeValue?(date) => number 0..1 }` — no business logic, no department awareness. Events (Phase 2) will reuse this same component; this is not speculative — it's the very next phase already scoped with the user.
4. **Calendar shading** copies the exact formula from `CalendarWeek.tsx`'s `useActivityLookup`/`HourRow`: normalize a day's value against the max value in the visible month, then `color-mix(in srgb, var(--accent-blue) round(normalized*45)%, transparent)` (matching Marketing's existing look-and-feel). To know *which* KPI drives shading without hardcoding "Sales in Rand," add one nullable boolean column `kpis.is_primary_metric` (admin checks it once per department in `KpiManager`, enforced client-side to allow only one true per department). Shading and the weekly/monthly totals footer both read this KPI's `kpi_logs`.
5. **EOD reports generalized to accept a department.** `EOD_DEPARTMENT` today is a hardcoded module constant in `src/lib/eod-reports.ts`; `getOrCreateTodayReport`/`ensureAndLockEodReports` close over it directly. Add a `department: string` parameter to both functions (mechanical change — the `portal_eod_reports` table and the "missed" sweep are already department-agnostic). Add a second job entry in `src/lib/marketing-processor.ts`'s job list for `sales`. Build a **new, separate** submit/detail flow for In-Store (`src/app/portal/(app)/sales/eod-actions.ts`, `SalesEodReportPanel.tsx`) — do not touch Marketing's post-attribution flow, since In-Store's report content (confirm logged numbers) is structurally different from Marketing's (attribute posts to KPIs).
6. **Weekends**: nothing needs to change to allow logging on Saturday/Sunday — `kpi_logs`/`dept_day_logs` writes aren't gated by weekday at all, only *EOD report creation* is (`isWeekday()`), and that's already correct per Willem's ask (no EOD prompt on weekends). Add one small affordance: a "Log the weekend" button that appears only on Monday, opening the same Log Day modal in a two-day mode (Saturday + Sunday stacked in one form, submitted together).
7. **Leave days**: new `profile_leave_days` table (`profile_id`, `customer_id`, `start_date`, `end_date`), self-service — a person adds/removes their own leave dates from their own Profile page (`src/app/portal/(app)/profile/page.tsx`), RLS-scoped to their own `profile_id`. Extend the EOD creation gate: skip creating a department's report for a day only if **every** profile whose `departments` includes that department is on leave that day (handles the common single-owner case — Rudi for In-Store — without a deeper per-person-report redesign, which `portal_eod_reports`'s schema doesn't support today anyway).
8. **Quick-link buttons**: follow the existing convention exactly (Marketing's Drive/Metricool buttons in `CalendarTable.tsx` are hardcoded URL constants in the component, not admin-configurable). Add a small `QuickLinks.tsx` row (pill buttons, brand color + icon) rendered between the calendar and the comment box on the In-Store page, for a Lightspeed button. **Real Lightspeed URL is unknown — use a clearly-labeled placeholder `href="#"` and flag to Willem to supply the real login/deep-link URL before shipping.**

## Data model changes (new migration `supabase/migrations/2026XXXX_instore_daily_log.sql`)

```sql
alter table public.kpis add column if not exists is_primary_metric boolean not null default false;

create table if not exists public.dept_day_logs (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete cascade,
  department text not null,
  log_date date not null,
  notes text,
  submitted boolean not null default false,
  submitted_at timestamptz,
  logged_by uuid references public.profiles(id) on delete set null,
  logged_by_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (customer_id, department, log_date)
);
-- RLS: select/insert/update scoped to customer_id + can_access_department(department), mirroring page_comments' policy shape.

create table if not exists public.profile_leave_days (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  customer_id uuid not null references public.customers(id) on delete cascade,
  start_date date not null,
  end_date date not null check (end_date >= start_date),
  created_at timestamptz not null default now()
);
-- RLS: a profile can select/insert/delete only rows where profile_id = their own profile id.
```

`kpi_logs` rows written by the daily-log form are tagged `note = 'In-Store daily log'` so the replace-on-edit logic (below) only ever touches rows it owns, never Marketing's EOD-attributed rows.

## New/changed files

**New:**
- `src/components/portal/calendar/MonthCalendar.tsx` — generic month/week grid (see decision #3).
- `src/components/portal/sales/SalesCalendar.tsx` — wraps `MonthCalendar`, fetches the month's `dept_day_logs` + primary-KPI `kpi_logs`, computes shading, renders weekly/monthly total footers, opens `LogDayModal`.
- `src/components/portal/sales/LogDayModal.tsx` — lists this department's manual KPIs with number inputs (prefilled from today's/this-day's `kpi_logs`), a notes field, single-day or two-day (weekend) mode.
- `src/app/portal/(app)/sales/day-actions.ts` — `getDayLog(date)`, `submitDayLog(date | {from,to}, values, notes)`: upserts `dept_day_logs`, replaces (delete-then-insert, tagged by note) that day's manual `kpi_logs` rows, calls `recomputeKpis()`.
- `src/components/portal/sales/QuickLinks.tsx` — Lightspeed button (placeholder URL, flagged).
- `src/app/portal/(app)/sales/eod-actions.ts` — `getSalesEodReportView()`, `submitSalesEod()`: reads today's `dept_day_logs`/`kpi_logs` for confirm-or-edit.
- `src/components/portal/sales/SalesEodReportPanel.tsx` — mirrors `EodReportPanel.tsx`'s shell/timing UI, different body (numbers confirm, not post attribution).
- Profile page addition: a small "Leave days" card (reuse two `DatePicker`s as a from/to pair — no new range-picker component needed) + list/remove of upcoming leave, server actions in a new `src/app/portal/(app)/profile/leave-actions.ts`.

**Changed:**
- `src/app/portal/(app)/sales/page.tsx` — becomes bespoke (like `marketing/page.tsx`) instead of the 9-line generic wrapper: renders `SalesCalendar` + `QuickLinks` above the existing `DepartmentPage` pieces (or composes `DeptShell` directly the way Marketing does).
- `src/lib/eod-reports.ts` — `getOrCreateTodayReport`/`ensureAndLockEodReports` gain a `department: string` param; `isWeekday` gains the leave-day check (rename conceptually to `isReportableDay`); `EOD_DEPARTMENT` constant removed once both call sites (marketing, sales) pass their department explicitly.
- `src/lib/marketing-processor.ts` — job list gets a second `["eod-sales", () => ensureAndLockEodReports(db, customerId, now, "sales")]`-style entry (exact wiring TBD when implementing — may warrant renaming the file/route since it's no longer marketing-only, but that's a larger rename best left alone for this phase to limit blast radius).
- `src/components/portal/KpiManager.tsx` — add the "Use for calendar shading" checkbox wired to `is_primary_metric`, with client-side enforcement of one-per-department.
- `supabase/migrations/` — new migration file per above.

## Verification

- `npm run build` / `tsc --noEmit` in `/c/Users/info/Developer/gotwurkwebsite` before any commit (existing project convention per commit history).
- Run the new migration against the real Supabase project via the SQL editor (same manual-paste workflow used for every prior migration in this project — confirmed from vault notes, no automated migration runner exists).
- Manually exercise in a browser once deployed to a preview branch: create 2-3 In-Store KPIs via `/portal/kpis`, mark one "primary," log a day's numbers via the new calendar, confirm shading appears and intensifies with higher values, confirm the EOD report at 16:30 SAST shows the logged numbers for confirm/edit, confirm weekend logging works with no EOD prompt, confirm the Monday "Log the weekend" flow, confirm a self-added leave day suppresses the next day's EOD report.
- This plan does not commit/push/merge or run migrations automatically — implementation will happen on a new branch (matching existing workflow: `departments-events-wholesale`-style feature branch → PR → Willem merges), migrations get handed to Willem to paste into Supabase like every prior one.

## Roadmap after Phase 1 (not detailed yet)

- **Phase 2 — Events**: month calendar (reusing `MonthCalendar`) for Rudi to create events (name, stock needed, KPI contribution or none, "notify marketing" flag), shaded by proximity/density rather than a numeric KPI.
- **Phase 3 — Wholesale**: same day-log pattern as In-Store (stock sold/in-stock/to-ship) plus a new invoice system — real file upload into portal storage (Supabase Storage bucket, mirroring the existing avatar-upload pattern), sent/paid tracking, auto-created follow-up reminders, and a shipment-duration visual spanning multiple calendar days.
- **Phase 4 — Cross-cutting**: @mention parsing in `page_comments` (needs a real profile-id-based person picker — `portal_access`/name-string assignees aren't sufficient, per research), a per-person unread-mentions badge on the Sidebar (modeled on the existing `unreadPatches` pattern, `portal_patch_reads`-shaped), and rolling the leave-day EOD suppression + weekend-log pattern out to Wholesale/Events once they have their own day-logs.
