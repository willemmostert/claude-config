# Sci-Core portal — EOD report detail, no-activity report cleanup, remove filler images, calendar dimming

## Context

Five smaller fixes/changes requested after the last release: (1) Management's end-of-day report detail is too thin for anything other than Marketing — sales/wholesale/warehouse reports only show manual KPI numbers, missing notes, ad hoc metrics and In-Store's sale lines even though that data already exists (built last session for the Daily Overview calendar). (2) Empty end-of-day reports get created for sales/wholesale/warehouse even on days nothing was logged, because report creation only checks "is this a weekday" not "did anything happen" — Willem wants no report at all when a department had zero activity that day. (3) The "filler image" auto-fallback (a Drive folder of stock images pushed to Metricool when a post has no real media) is being removed entirely — no more silent filler substitution, ever. (4) Manually-logged calendar posts should render faint (~30% opacity) in the grid until opened, to visually discourage the habit of logging by hand instead of pushing through Metricool. (5) Marketing's EOD report should keep real Metricool-confirmed posts as the primary path and make the "log something manually" section feel like a genuine last resort, not an equally-weighted option.

## 1. Management EOD: full report detail for every department

`getEodReportDetail()` in `src/lib/eod-reports.ts` only queries `mk_calendar_rows` (Marketing's posts) and `kpi_logs` by `eod_report_id` — so a sales/wholesale/warehouse report's detail popup shows almost nothing. The exact data that's missing (day's notes, ad hoc metrics, In-Store sale lines) is already fetched by `getDailyOverviewDetail()` in `src/lib/management-daily-overview.ts` (built for the Daily Overview calendar) — reuse it instead of writing new queries.

- `getEodReportDetail(db, customerId, reportId)`: select `department` alongside `report_date` on the report lookup. Call `getDailyOverviewDetail(customerId, report_date)` and pick the entry matching `report.department`, merging `notes`, `metrics`, and `saleLines` into the returned `EodReportDetail`. Keep the existing marketing-only queries as-is (they naturally return empty for non-marketing departments).
- Extend `EodReportDetail` type (`src/lib/eod-reports.ts`) with `notes: string | null`, `metrics: { label: string; amount: number }[]`, `saleLines?: { name: string; quantity: number; total: number }[]`.
- `src/components/portal/management/EodReportsAdmin.tsx`'s `Detail` component: add sections for notes/metrics/saleLines (same visual pattern already used in `DailyOverviewCalendar.tsx`'s day-detail popup — small heading + list), and update the "nothing was credited" empty-state check to also account for them.
- No change to the interaction model — it's still the existing inline expand/collapse, just with real content for every department now.

## 2. Stop creating EOD reports when nothing happened

`getOrCreateTodayReport()` (`src/lib/eod-reports.ts`) creates a `portal_eod_reports` row whenever it's called and `isReportableDay()` passes (weekday, not everyone on leave) — with no check for actual activity. It's called from three places: the hourly cron (`marketing-processor.ts` → `ensureTodayReport(..., "sales", ...)`, proactive, before anyone may have logged anything), and lazily on page visit for sales/wholesale/warehouse (`getDeptEodReportView`) and marketing.

- New `hasActivityToday(db, customerId, department, date)` helper (in `src/lib/eod-reports.ts` or `src/lib/dept-daily-log.ts`): true if any `dept_day_logs` row, any `dept_day_metrics` row, (for `sales`) any `product_sales` row, or any `kpi_logs` row tagged `note = dailyLogNote(department)` exists for that customer/department/date.
- `getOrCreateTodayReport()`: for `DAILY_LOG_DEPARTMENTS` (sales, wholesale, warehouse) only, also require `hasActivityToday` before inserting — marketing keeps today's unconditional creation (its whole job is the content calendar, activity is effectively guaranteed). This single choke point fixes both the cron path and the lazy on-visit path automatically.
- Effect: nobody sees an EOD panel for a daily-log department until they've logged something via that department's calendar that day; once they log something, the next render creates the report and the confirm panel appears — matches "you can only create a report once activity happens."
- `lockOverdueReports` needs no change — a report that exists and reaches its lock time while still pending now genuinely means "logged something, never confirmed," which is worth flagging as missed.
- **Historical cleanup**: a one-time SQL delete for existing empty reports from before today, scoped to `department in ('sales','wholesale','warehouse')` and `status != 'completed'` (never touch a completed submission) and `report_date < current_date`, where no matching row exists in `dept_day_logs`, `dept_day_metrics`, `product_sales` (sales only), or `kpi_logs` for that customer/department/date. Given this repo's history of the auto-mode classifier blocking migration files that contain a `DELETE` statement, this will be handed to Willem as a SQL snippet to run directly in the Supabase SQL editor, not written as a migration file.

## 3. Remove the filler-image feature entirely

Filler images are an automatic fallback in the Metricool push pipeline (`src/lib/marketing-processor.ts`'s `resolveMedia()`): when a post has no attached media and nothing matches in the real Drive media folders, it silently pulls a random image from a separate "filler folder" (configured per-business in Management → Automation) and stamps the row `media_status = "Filler (Auto)"`. This is being removed outright — a post with no real media should just be blocked ("needs media"), never silently filled.

- `resolveMedia()`: delete the filler branch (currently right after the real-media-match branch); update the "missing" message for a Reel/non-Reel to drop the filler mention. Remove `driveCache.filler` from the `Ctx` type.
- `src/lib/automation-settings.ts`: remove `driveFillerFolderId` from `AutomationSettings`, `DEFAULT_SETTINGS`, `getSettings`, `saveSettings`.
- `src/components/portal/management/AutomationPanel.tsx`: remove the "Filler image folder" input and its state.
- `src/app/portal/(app)/management/automation/actions.ts` (`saveAutomation`) and `.../automation/page.tsx`: remove the `fillerFolder` plumbing.
- `src/lib/marketing-types.ts`: remove `"Filler (Auto)"` from `MEDIA_STATUSES`.
- New migration: backfill any `mk_calendar_rows`/`mk_content_ideas` rows currently stamped `media_status = 'Filler (Auto)'` to `'Sourced from Drive'` (closest honest label — it did come from Drive, just auto-picked), then drop and re-add both tables' `media_status` check constraints without `'Filler (Auto)'` (both declared in `supabase/migrations/20260919_marketing_workspace.sql`).
- `src/lib/credential-defs.ts`: reword the Google Drive integration blurb/steps to drop "filler images"/"filler folders" mentions (keep the real-media-folder wording).
- **Out of scope for me**: the actual Google Drive folder of filler images is a real folder in Willem's Drive, not something this session has API access to delete — he said he'd do that himself if needed, so I'll leave that to him and just confirm the code no longer references or needs it.

## 4. Faint manually-logged posts on the calendar

`src/components/portal/marketing/CalendarWeek.tsx`'s `Chip` component (the grid-cell card) already derives a distinct purple "Logged manually" style from `statusOf(row)` when `row.logged_manually` is true, but at full opacity like every other card. `IdeaChip` in the same file already uses `opacity-80 hover:opacity-100` as a "this is lesser" visual device — same pattern, stronger value.

- Add `row.logged_manually ? "opacity-30 hover:opacity-100" : ""` to `Chip`'s card `className` (the div at the role="button" level), and widen the existing `transition-[filter]` to `transition-[filter,opacity]` so the hover-brighten stays smooth.
- `PostModal` (the detail view opened on click) is a separate component that doesn't reuse `Chip`'s className, so it's unaffected — already renders at full opacity, satisfying "full opacity once opened."

## 5. Marketing EOD: make manual logging feel like a last resort

`src/components/portal/marketing/EodReportPanel.tsx` already orders things posts-first: real Metricool-confirmed posts to attribute, then "Anything else today?" (manual KPI amounts), then "Additional content posted" (add a post that never touched Metricool, capped at 10, quietly). The order is already correct — the gap is that the manual "add a post" section is just as open and inviting as the real one.

- Collapse "Additional content posted" behind a disclosure toggle, default closed: a plain-text button like "Something went out but never touched Metricool? Log it here" instead of the section being open by default with an "+ Add another post" button sitting right there.
- Sharpen the copy once expanded to frame it as a fallback, not routine (e.g. "Last resort — Kyla shouldn't need this if everything's scheduled through Metricool").
- Leave the "Anything else today?" manual-KPI-amount section as-is — those are KPIs that are inherently manually tracked (not a Metricool-avoidance shortcut), so no framing change needed there.

## Verification

- `npx tsc --noEmit` / `npx eslint` on every changed file.
- New branch off current `main`; the media_status migration and the historical EOD-report cleanup SQL get handed to Willem to run (cleanup as a pasted snippet, not a migration file, per the classifier precedent) before merging.
- Manual checks once deployed: open a completed sales/wholesale/warehouse EOD report in Management and confirm notes/metrics/sales show up; visit Warehouse on a day nothing was logged and confirm no EOD panel appears, then log something and confirm it appears; try pushing a post with no media to Metricool and confirm it's blocked with a clear message and no filler option anywhere in Automation settings; check a manually-logged post on the calendar renders faint and opens at full opacity; open Marketing's EOD report and confirm the manual "add a post" section stays collapsed until clicked.


## Context

Three rounds of feedback on the daily-log system built over the last two sessions converge on one real problem: logging was too rigid. It either required a pre-existing KPI to type a number into (blocking Wholesale/Warehouse/Events entirely until Willem sets KPIs up, and blocking even a plain note), or — for In-Store specifically — was replaced entirely by product-sales-only logging, losing the ability to log things like membership signups or cans handed out that aren't a product sale. Willem also wants leave-day marking surfaced on every department (not just buried on Profile) with visibility for Management, a new Management-wide daily overview calendar combining every department's day into one shaded view, and the KPI page's vertical columns capped with a "show more" since they've gotten long.

Confirmed with Willem: Rudi can type a brand-new ad hoc metric label himself on the spot (no need to wait for a KPI to be pre-created) — the daily-log entry system becomes genuinely free-form. The end-of-day report stays a single overall confirm (edit a quantity, submit) — no per-item "what does this count toward" picking; that's simpler and matches "don't want them to fill in a lot of work."

**Separately, still outstanding**: the products-seed migration silently inserted 0 rows (confirmed: `select count(*) from products` returned 0) — the `where slug ilike 'sci-core%' or name ilike 'sci-core%'` match found nothing. Still need Willem to run `select id, slug, name from public.customers;` and share the result before a corrected re-seed can be written — not part of this plan's file changes, handled separately once that comes back.

## Free-form daily logging (In-Store, Wholesale, Warehouse)

**New table `dept_day_metrics`** — ad hoc "label: number" entries, no KPI required at all:
```
id, customer_id, department, log_date, label text, amount numeric,
logged_by, logged_by_name, created_at, updated_at
unique (customer_id, department, log_date, label)
```
RLS: `can_access_department(department)`, same shape as `dept_day_logs`. These are a record of what happened, not wired into `kpi_logs` — no per-item attribution step, matching the "one overall confirm" decision. If Willem wants a metric to show up in the official KPI/shading system, he still creates it as a real KPI the way he always could (unchanged).

**`LogDayModal.tsx`** (used today by Wholesale and Warehouse) currently refuses to render *anything* — not even the notes field — when the department has zero KPIs (`kpis.length === 0` gates the entire per-date block). Rebuilt so every date section always shows, regardless of KPI count:
- The existing per-KPI number inputs, if any KPIs exist (unchanged behavior when they do).
- A new always-present "Add anything else" list: repeatable rows of free-typed label + number, add/remove, no KPI needed. Saved to `dept_day_metrics`.
- The existing notes textarea, always present.

**`SalesDayModal.tsx`** (In-Store) gains the same "Add anything else" section beneath its product-sales lines, so Rudi can log membership signups, cans handed out, etc. alongside actual product sales in the same popup. The primary-metric Rand figure still auto-computes from product sales exactly as built — ad hoc metrics don't feed it, they're just logged.

**Custom one-off products** ("ice cream", "a slushy" at a special event): `product_sales.product_id` becomes nullable, gains `custom_name text`, with `check (product_id is not null or custom_name is not null)`. `SalesDayModal`'s product-sales row gets a "Custom item" toggle: instead of `ProductPicker`, a free-text name + typed price, still with the membership/retail choice applied to that typed price. `submitProductSales` skips the stock-decrement step for custom rows (nothing in the catalog to decrement) but still counts toward the day's Rand total.

**Shared day-actions** (`src/app/portal/(app)/daily-log/day-actions.ts`) gains `getDayMetrics(department)`/`submitDayMetrics(department, entries)` — mirroring `submitDayLogs`'s replace-the-day pattern (delete this day's rows for the department, re-insert). `getDeptDailyLogData` in `src/lib/dept-daily-log.ts` also returns the day's existing metrics so the modal can prefill them when reopening a logged day.

**End-of-day report** (`DailyEodReportPanel`/`getDeptEodReportView`/`submitDeptEod`) reads back and displays the day's full picture for a one-tap confirm: the primary-metric figure (if any), the list of ad hoc metrics logged, and (for In-Store) the product-sales lines — editable inline, no per-item KPI picker, matching the original "are these numbers accurate?" design intent from the first build.

## Leave days on every department + Management visibility

- New compact `LeaveQuickLink` in `DeptShell.tsx`'s right column (visible on every department page, not just Profile): a small "Mark leave" control using the existing `addLeaveDay`/`getMyLeaveDays` actions from `src/app/portal/(app)/profile/leave-actions.ts` — no new leave-tracking logic, just a second, more visible entry point to what Phase 1 already built.
- New `getTeamLeaveDays()` in `profile/leave-actions.ts`, executive-gated, using the admin client to read every profile's leave for the business — `profile_leave_days`' RLS only lets a person see their own rows, so this mirrors the same admin-client escape hatch already used for `activity-tracking.ts` and the @mention roster.
- New small "Who's out" panel on Management's Departments tab (`src/components/portal/TeamOverview.tsx`'s `DepartmentsGrid`) listing anyone currently or soon on leave.

## Management: combined daily overview calendar

New tab on Management (`ManagementTabs.tsx` gains "Daily Overview", new route `src/app/portal/(app)/management/daily/page.tsx`):
- Reuses `MonthCalendar` again (its third reuse, after Events and the daily-log departments) — month/week view, each day shaded by how many (department, metric) facts were logged that day across the whole business (EOD reports completed, primary-metric amounts, ad hoc metrics, product sales) — same `color-mix` shading formula, normalized per visible range.
- Clicking a day opens a detail view: per department, its EOD status, primary-metric number, ad hoc metrics, notes, and (for In-Store) the day's product sales — pulled from `portal_eod_reports`, `dept_day_logs`, `kpi_logs`, `dept_day_metrics`, `product_sales`, read via the admin client (executive-only route, same pattern as everywhere else admin needs cross-department visibility).

## KPIs & Goals: cap columns at 5, expand

`KpiManager.tsx`'s per-department column currently renders every KPI across every owner group, which has gotten long. Flatten each column's KPIs into one ordered list (owner grouping stays for display, just capped), show the first 5, with a "Show all (N)" toggle per column to reveal the rest — a small `useState` per section, no data changes needed.

## Verification

- `npx tsc --noEmit` / `npx eslint` on every changed file, same as every prior phase.
- New branch off current `main`, commits per sub-feature, pushed for Willem to run the two new migrations (`dept_day_metrics` table; `product_sales.product_id` nullable + `custom_name`) before merging — same manual process as always.
- Manual check once deployed: log a day for Wholesale with zero KPIs defined and confirm it's no longer blocked; add an ad hoc "Cans handed out: 12" entry for In-Store; log a custom "Ice cream" sale; mark a leave day from the Wholesale page and confirm it shows on Management's "Who's out"; open Management's new Daily Overview calendar and click into a day; confirm the KPI page's "Show all" expand works.
