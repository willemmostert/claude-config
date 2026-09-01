# Portal v1.2: Customizable Grid, Simplified Goals, Real Tasks, Marketing Shells, Department Messaging

## Context

v1.0 and v1.1 shipped to `sci-core-portal-preview` and are live for the real Sci-Core account
(Overview, KPIs, Messages, Integrations, Recommended Apps, per-department integration options, an
add/remove widget menu on Overview). One piece of the approved v1.1 plan was never executed: the
`messages.department` column, blocked twice by the permission classifier pending explicit
go-ahead — it's folded into this plan (item 5) rather than left dangling.

The user's new ask, in their own priority order:
1. **(Top priority, said explicitly)** Clients should be able to **resize and move** the
   information windows on the Overview grid — true free-form layout customization, not just
   add/remove.
2. Tasks need a **traffic-light system** (open / due this week / overdue) plus a **calendar view**,
   eventually synced to Google/Microsoft/Apple Calendar.
3. Marketing needs real insights from **Meta or Metricool** — scheduled posts, boards, timelines,
   calendar view, pulled from a social platform (recommendation wanted).
4. A **feedback/comms window per department**, relayed to/from that department's Slack channel
   (send from portal → Slack channel; replies visible back in the dashboard, not just in Slack).
5. **KPIs & Goals** should be simple to create (a date, or a number target) and visually nicer.

Also: an "Apple design" skill was just installed at `~/.claude/skills/apple-design/` as a standing
guideline for all GotWurk UI work going forward (refine spacing/motion/hierarchy/accessibility,
never touch the brand palette) — applied throughout this round, especially to the KPI visual
redesign (item 5) and the new Tasks/Marketing surfaces.

This is the same production-adjacent codebase the real Sci-Core account uses today — every change
must leave existing pages working, with zero fabricated data anywhere (`kpis`: 4 real rows,
`dashboard_widgets`: 2 real rows, `messages`: 2 real rows — verified via `list_tables` before
planning).

## Scope decisions (what ships now vs. what's a follow-up)

**Ships now** — everything below is buildable with data GotWurk already owns, no external
credentials needed:
- Drag + resize on the Overview grid, with layout persisted per customer.
- A real `tasks` table with a **computed** (not manually set) traffic-light status, plus a native
  calendar-view of tasks. Clients can create tasks.
- Simplified two-mode KPI creation ("hit a number" vs "hit a date") + a visual redesign of KPI rows.
- `messages.department` targeting, with an honest "not yet delivered to Slack" caption.
- Marketing page gets real (empty) UI shells for scheduled posts / boards / timelines / calendar,
  plus **Metricool** added to the integration catalog as the recommended aggregator.

**Explicit follow-ups, not built this round** (each needs a decision or credentials only the user
has):
- The actual Slack relay (bot token + per-department channel mapping) — matches the user's own
  earlier framing that app integrations come "a little bit later."
- Live Metricool/Meta API data pulls — needs an API key/OAuth app the user hasn't created yet.
- Live Google/Microsoft/Apple Calendar sync — needs OAuth app registrations (Google Cloud Console,
  Microsoft Entra); Apple Calendar has no OAuth equivalent (CalDAV + app-specific password), so
  that one may end up out of scope entirely. Surfaced as a Tasks-department integration option
  (honest not-connected state) for now.

**Why split it this way:** every "ships now" item is either pure GotWurk-owned data (tasks, KPIs,
layout, department targeting) or an honest empty state (Marketing shells). Everything in
"follow-up" would otherwise force a choice between fabricating a "connected" state or blocking this
whole round on third-party app approvals — neither is acceptable, so they're named instead.

## Architectural decisions

- **Grid library: `react-grid-layout@2.2.4`** (peer dep `react >= 16.3.0`, confirmed compatible
  with the app's React 19.2.8 / Next 16.3.0). It's the standard React solution for exactly this
  "draggable + resizable dashboard widgets" shape and needs no custom drag/resize math.
- **One new table, `dashboard_layout`**, not more columns on `dashboard_widgets` — because the grid
  now includes two "always-on" panels (KPI summary, Connected Systems) that aren't rows in
  `dashboard_widgets` at all. `dashboard_layout` stores `(customer_id, widget_key, x, y, w, h)` for
  *any* grid item — the 2 built-ins use reserved keys (`_kpis_summary`, `_connected_systems`) plus
  one row per added department widget. Missing rows fall back to sensible defaults computed
  client-side, so an account with no saved layout renders exactly like today.
- **Tasks status is computed, never stored.** `tasks.status` only tracks `open`/`done`; the
  traffic-light color (`green`/`yellow`/`red`) is derived from `due_date` vs. today at render time
  in a small pure function — avoids a background job to keep a stored status in sync.
- **Calendar view is native**, no new date library — Next 16/React 19 project has no `date-fns`
  dependency today and a month grid is simple enough with plain `Date` math, consistent with
  avoiding unnecessary deps.
- **KPI creation stays one form, one server action** (`createKpi` already exists) — "simplify" is a
  UI-only change (a 2-choice toggle switching which fields show), not a new data shape.
- **Metricool joins `integrations-catalog.ts` as a real `IntegrationService` value** (`metricool`),
  same treatment as Xero/Slack/etc. — honest not-connected state until the user supplies an API
  key; Meta Business stays as the secondary option already in the catalog.

## Schema changes (apply via Supabase MCP `apply_migration`, project `sklihjowjauhumddslgm`)

```sql
-- 1. Grid layout positions (Overview drag/resize)
create table public.dashboard_layout (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete cascade,
  widget_key text not null,
  x int not null default 0,
  y int not null default 0,
  w int not null default 2,
  h int not null default 2,
  updated_at timestamptz not null default now(),
  unique (customer_id, widget_key)
);
alter table public.dashboard_layout enable row level security;

create policy "dashboard_layout_select" on public.dashboard_layout for select to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));

create policy "dashboard_layout_upsert" on public.dashboard_layout for insert to authenticated
with check (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));

create policy "dashboard_layout_update" on public.dashboard_layout for update to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()))
with check (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));
```

```sql
-- 2. Real tasks
create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete cascade,
  title text not null,
  department text check (
    department is null or department in
    ('tasks','reports','deliverables','warehouse','marketing','staff','contacts','finance')
  ),
  status text not null default 'open' check (status in ('open','done')),
  due_date date,
  created_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);
alter table public.tasks enable row level security;

create policy "tasks_select" on public.tasks for select to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));

create policy "tasks_client_insert" on public.tasks for insert to authenticated
with check (customer_id = (select public.current_customer_id()));

create policy "tasks_staff_insert" on public.tasks for insert to authenticated
with check ((select public.is_service_provider()));

create policy "tasks_update" on public.tasks for update to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()))
with check (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));
```

```sql
-- 3. Messages: department targeting (the outstanding v1.1 item)
alter table public.messages
  add column department text
  check (department is null or department in
    ('tasks','reports','deliverables','warehouse','marketing','staff','contacts','finance'));
```

After applying: run `get_advisors` (security + performance) to confirm the memoized `(select ...)`
RLS pattern passes lint and both new tables aren't flagged for missing RLS.

## File changes

**New:**
- `src/components/portal/DashboardGrid.tsx` — `"use client"`, wraps `react-grid-layout`
  (`WidthProvider(Responsive)`), receives `{layoutItems, initialLayout}` from the server, calls
  `saveDashboardLayout` (debounced ~600ms) on `onLayoutChange`
- `src/app/portal/(app)/actions.ts` — add `saveDashboardLayout(customerId, layout)` alongside the
  existing `addDashboardWidget`/`removeDashboardWidget`
- `src/lib/portal.ts` — add `getDashboardLayout()` reading `dashboard_layout`
- `src/app/portal/(app)/tasks/actions.ts` — `createTask`, `toggleTaskDone`
- `src/lib/task-status.ts` — pure `getTaskLight(task): "green"|"yellow"|"red"|"done"` (today vs.
  due_date, 7-day window)
- `src/components/portal/CreateTaskForm.tsx`, `TaskRow.tsx`, `TaskCalendar.tsx` (native month grid)
- `src/lib/marketing-shells.ts` — static shell definitions for scheduled posts/boards/timelines,
  rendered as empty states (mirrors `MetricPlaceholderCard`'s honest-empty-state pattern)
- `src/components/portal/GoalTypeToggle.tsx` — the 2-choice ("number" / "date") UI, used inside a
  rewritten `CreateKpiForm`

**Modified:**
- `src/app/portal/(app)/page.tsx` — replace the two hardcoded panels + widgets grid with a single
  `<DashboardGrid>` covering all items (built-ins + added widgets)
- `src/lib/departments-catalog.ts` — no structural change needed (DepartmentKey set is unchanged)
- `src/lib/integrations-catalog.ts`, `integration-options-catalog.ts` — add `metricool`
- `src/app/portal/(app)/marketing/page.tsx` — add the new shell panels above/alongside the existing
  `MetricPlaceholderGrid`
- `src/app/portal/(app)/tasks/page.tsx` — real page: `CreateTaskForm`, `TaskRow` list grouped by
  traffic light, `TaskCalendar`
- `src/components/portal/CreateKpiForm.tsx`, `KpiRow.tsx` — simplified toggle + visual redesign
  (progress ring/cleaner hierarchy, per the apple-design skill's layout/typography/motion guidance)
- `src/app/portal/(app)/messages/actions.ts` — `sendMessage` reads/validates `department`
- `src/components/portal/ComposeMessageForm.tsx` — department `<select>` + "not yet delivered to
  Slack" caption; `MessageThread.tsx` — department badge
- `src/lib/portal.ts` — extend `Message` with `department`, add to `getMessages()` select

## Sequencing

1. Schema migrations (all three DDL blocks) → `get_advisors`.
2. Messages department targeting (smallest slice, closes out the outstanding v1.1 item) — verify
   existing 2 messages render with no badge (`department` is `NULL`, nothing backfilled).
3. KPI simplification + visual redesign — verify against the 4 real Sci-Core KPIs, zero data change.
4. Tasks: table + create/list/calendar + computed traffic light — verify as a client, confirm
   overdue/due-this-week/open buckets compute correctly against real dates.
5. Marketing shells + Metricool catalog entry — verify `/portal/marketing` and
   `/portal/recommended-apps` still render correctly, new shells show honest empty copy.
6. Overview drag/resize grid — highest-risk step since it touches the page real Sci-Core logs into
   daily. Install `react-grid-layout`, build `DashboardGrid`, seed default positions for the 2
   real `dashboard_widgets` rows plus the 2 built-ins, verify layout persists across reload and a
   fresh account (no saved layout) renders the same default arrangement as today.
7. Full regression pass as the real Egmar account: Overview (drag, resize, reload), KPIs (create
   both goal types), Tasks (create, see traffic light, calendar), Messages (send with a
   department), Marketing, Recommended Apps. Final `get_advisors`, `next build` clean.
8. Commit to `sci-core-portal-preview` (never `main`). Report results and the follow-up list above,
   and wait for explicit confirmation before merging to `main`.

## Critical files
- `src/app/portal/(app)/page.tsx`, new `DashboardGrid.tsx`
- `src/lib/portal.ts`
- `src/app/portal/(app)/tasks/` (new actions + page)
- `src/components/portal/CreateKpiForm.tsx`, `KpiRow.tsx`
- `src/app/portal/(app)/messages/actions.ts`
- `src/lib/integrations-catalog.ts`, `integration-options-catalog.ts`

## Verification
- `next build` clean after each numbered step, not just at the end.
- Supabase `get_advisors` after migrations and again before the final push.
- Manual click-through as `egmar@sci-core.co.za` covering every item in step 7.
- No step may alter/delete existing real rows in `kpis`, `dashboard_widgets`, or `messages` — only
  additive columns/tables and new rows the user (or Egmar) creates through the new UI.
