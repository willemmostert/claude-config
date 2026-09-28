# Sci-Core portal — flexible daily logging, leave visibility, Management daily overview, KPI pagination

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
