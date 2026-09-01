# Portal v1.1: Customizable Overview, Client-Created KPIs, Department Messaging, Recommended Apps

## Context

v1.0 (department pages, first-party Messages, honest empty states) already shipped to the `sci-core-portal-preview` branch and is live for the real Sci-Core account. The user now wants four additions on top of it, confirmed via clarifying questions:

1. Clients should be able to customize their Overview page — add/remove which department "windows" show there, via a "+" button.
2. Clients should be able to create their own KPIs/goals from the portal (confirmed: goes live immediately, no staff approval step).
3. Messages should support targeting a specific department, as groundwork for an eventual Slack relay ("if the owner sends a message to a department, it should go to that department's Slack channel") — but the actual Slack integration is explicitly deferred by the user ("we are going to do the app integrations a little bit later"), so this ships as real storage/display of the target department with an honest "not live yet" caption, never a fabricated "delivered to Slack" state.
4. A new "Recommended Apps" tab, plus a reusable "Integration option" affordance under Marketing/Finance/Staff/Contacts/Integrations/Recommended Apps.
5. Session cookies currently persist ~1 year (an `@supabase/ssr` default, never overridden). Confirmed via clarifying question: don't do a hard sign-out-on-navigation (would break the portal's own "Back to gotwurk.com" link and any multi-tab use) — instead make sessions expire on browser close.

This is a real production-adjacent codebase (the live Sci-Core account uses this portal already) — every change must leave the existing Overview/KPIs/Messages/Integrations pages working exactly as they do today for that account, with zero fabricated data anywhere.

## Architectural decisions

- **Dashboard widgets: new table (`dashboard_widgets`), not a jsonb column on `customers`.** Matches every other per-customer mutable concept in this schema (its own table + `customer_id` + the memoized `(select current_customer_id())`/`(select is_service_provider())` RLS pattern already used by `kpis`/`integrations`/`messages`). Avoids broadening `customers` UPDATE RLS (that table also holds staff-only-sensitive columns like `stripe_customer_id`).
- **KPI and Integrations summary panels on Overview stay always-on**, not removable widgets — they're the only two panels backed by real queries today; with an empty `dashboard_widgets` table (true for Sci-Core on ship day) the Overview page renders identically to today, zero risk to the live account.
- **Messages `department` reuses the existing `DepartmentKey` closed union** (the same 8 values already driving nav/pages), nullable — a message's target is one of the fixed department destinations, not free text like `Kpi.department` already is.
- **Client KPI creation is an additive RLS policy**, not a replacement — Postgres ORs multiple permissive policies for the same command, so the existing staff-only insert path is untouched.
- **"Integration option" reuses `IntegrationCard`, generalized** to accept plain `{mark, label, description, integration?}` instead of being hard-wired to the real `IntegrationService` union — lets department pages show integration-style cards (some mapping to a real DB-backed integration, e.g. Finance→Xero; others purely aspirational, e.g. Staff/Contacts) through one honest-empty-state component, without inventing fake values in the `integrations.service` CHECK enum.
- **"Recommended Apps" is a new standalone route**, not a 9th `DepartmentKey` — it has no metrics and would otherwise leak into the widget-add menu with a nonsensical placeholder grid.

## Schema changes (apply via Supabase MCP `apply_migration` against project `sklihjowjauhumddslgm`)

```sql
-- 1. Dashboard widgets (Overview customization)
create table public.dashboard_widgets (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete cascade,
  widget_key text not null check (
    widget_key in ('tasks','reports','deliverables','warehouse','marketing','staff','contacts','finance')
  ),
  created_at timestamptz not null default now(),
  unique (customer_id, widget_key)
);
alter table public.dashboard_widgets enable row level security;

create policy "dashboard_widgets_select" on public.dashboard_widgets for select to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));

create policy "dashboard_widgets_insert" on public.dashboard_widgets for insert to authenticated
with check (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));

create policy "dashboard_widgets_delete" on public.dashboard_widgets for delete to authenticated
using (customer_id = (select public.current_customer_id()) or (select public.is_service_provider()));
```

```sql
-- 2. Client-created KPIs (additive -- ORs with the existing kpis_staff_insert policy)
create policy "kpis_client_insert" on public.kpis for insert to authenticated
with check (customer_id = (select public.current_customer_id()));
```

```sql
-- 3. Messages: target-department groundwork (nullable, closed set, no RLS change needed)
alter table public.messages
  add column department text
  check (department is null or department in
    ('tasks','reports','deliverables','warehouse','marketing','staff','contacts','finance'));
```

After applying: run `get_advisors` (security + performance) on the project to confirm the new policies pass the same memoized-`(select ...)` lint the existing `messages_*` policies already satisfy, and `dashboard_widgets` isn't flagged for missing RLS.

## File changes

**New:**
- `src/app/portal/(app)/actions.ts` — `addDashboardWidget`, `removeDashboardWidget` (`"use server"`, sibling to Overview's `page.tsx`, matching the `messages/actions.ts` convention)
- `src/app/portal/(app)/kpis/actions.ts` — `createKpi`
- `src/app/portal/(app)/recommended-apps/page.tsx`
- `src/components/portal/DashboardWidgetPanel.tsx` — renders one department's `MetricPlaceholderGrid` plus a small "Remove" form
- `src/components/portal/AddWidgetMenu.tsx` — Server Component, native `<details>/<summary>` dropdown listing not-yet-added departments, each a one-button form calling `addDashboardWidget` (no client JS needed)
- `src/components/portal/CreateKpiForm.tsx` — `"use client"`, `useActionState(createKpi, undefined)`, tucked behind a `<details>` on the KPIs page
- `src/components/portal/IntegrationOptionsSection.tsx` — renders a department's `integrationOptions` via the generalized `IntegrationCard`
- `src/lib/integration-options-catalog.ts` — `IntegrationOption` type + `RECOMMENDED_APPS` list

**Modified:**
- `src/lib/portal.ts` — add `DashboardWidget` type + `getDashboardWidgets()`; extend `Message` with `department: DepartmentKey | null` and add it to `getMessages()`'s select list
- `src/lib/departments-catalog.ts` — add `DEPARTMENTS_ORDER: DepartmentKey[]`; extend `DepartmentConfig` with optional `integrationOptions?: IntegrationOption[]`, populated for `marketing`/`finance`/`staff`/`contacts`
- `src/app/portal/(app)/page.tsx` — keep the two real panels as-is; add a widget render loop (`getDashboardWidgets()` → `DashboardWidgetPanel` per row) + `AddWidgetMenu`
- `src/app/portal/(app)/kpis/page.tsx` — add the `CreateKpiForm` behind a toggle
- `src/app/portal/(app)/messages/actions.ts` — `sendMessage` reads/validates `department` against the 8-value set (else `null`), includes it in the insert
- `src/components/portal/ComposeMessageForm.tsx` — add a department `<select>` (including a "General" / no-department option) + a caption noting Slack delivery isn't live yet
- `src/components/portal/MessageThread.tsx` — small department badge per message when present
- `src/components/portal/IntegrationCard.tsx` — decouple from `IntegrationService`; accept `{mark, label, description, integration?}`
- `src/app/portal/(app)/integrations/page.tsx` — pass `INTEGRATIONS_CATALOG[service]` fields explicitly into the now-generic `IntegrationCard` (must render pixel-identical to today)
- `src/app/portal/(app)/marketing/page.tsx`, `finance/page.tsx`, `staff/page.tsx`, `contacts/page.tsx` — render `IntegrationOptionsSection` when `dept.integrationOptions` is non-empty
- `src/components/portal/Sidebar.tsx` — add "Recommended Apps" nav link
- `src/lib/supabase/middleware.ts`, `src/lib/supabase/server.ts` — in each `setAll`, override cookies to `{ ...options, maxAge: undefined, expires: undefined }` so auth cookies become session-only instead of the current ~1-year default

## Sequencing

1. **Session cookie fix** — isolated, zero DB dependency. Verify by signing in and checking the `Set-Cookie` response header has no `Max-Age`/`Expires`.
2. **Schema migrations** — apply all three DDL blocks, then `get_advisors` before any app code depends on them.
3. **Data layer** — `portal.ts` additions (`DashboardWidget`/`getDashboardWidgets`, `Message.department`). No UI yet.
4. **Messages department routing** — smallest self-contained slice, touches a table with real rows for Sci-Core. Verify: existing messages render with no badge (their `department` is `NULL` — honest, nothing backfilled/fabricated); new messages can carry one; the "not live yet" caption is visible and nothing ever implies Slack delivery happened.
5. **Client-created KPIs** — verify as a regression check first (staff-only insert still works unchanged), then verify the new client path (client can only insert their own `customer_id`; the client branch of `createKpi` never reads a client-supplied `customerId` at all, matching `sendMessage`'s existing precedent).
6. **Overview dashboard widgets** — verify Sci-Core's Overview renders identically to pre-change (empty `dashboard_widgets` row set) before adding a widget; then add/remove one and confirm `revalidatePath` reflects it without a full reload.
7. **Integration options / Recommended Apps** — last, since it refactors a component already live (`IntegrationCard`). Verify `/portal/integrations` is pixel-identical after the refactor before wiring the new department affordances and the new route + Sidebar link.
8. **Full regression pass** against the real Sci-Core account (`egmar@sci-core.co.za`): Overview, KPIs, Messages, Integrations all match pre-change appearance with zero new fabricated data; final `get_advisors` check; `next build` clean.
9. **Stop before pushing** — commit to the same `sci-core-portal-preview` branch (not `main`) so the existing preview link updates in place; report results and wait for explicit confirmation before ever merging to `main`.

## Critical files
- `src/lib/portal.ts`
- `src/lib/departments-catalog.ts`
- `src/app/portal/(app)/page.tsx`
- `src/components/portal/IntegrationCard.tsx`
- `src/app/portal/(app)/messages/actions.ts`
- `src/lib/supabase/middleware.ts`, `src/lib/supabase/server.ts`
