# Sci-Core portal — Events, Wholesale, and @mentions (Phases 2–4)

## Context

Phase 1 (In-Store daily numbers, KPI/Deliverables reorg, automated-messaging removal) shipped to `main` and is live. This plan covers the rest of the original department build-out in one pass, per Willem's request: **Phase 2 (Events)**, **Phase 3 (Wholesale, with invoice/shipment tracking)**, and **Phase 4 (@mentions + per-department notification badges)**. Warehouse was never scoped with any specifics and stays out of this pass.

Confirmed with Willem: the In-Store countdown on events only shows events explicitly flagged "Happens in-store" (not every event).

## Key architectural decision: generalize Phase 1's In-Store code, don't fork it

Phase 1 built the daily-log system (`sales-daily-log.ts`, `SalesCalendar.tsx`, `LogDayModal.tsx`, `day-actions.ts`, `eod-actions.ts`, `SalesEodReportPanel.tsx`) hardcoded to `"sales"`. Wholesale needs the identical pattern (log any admin-defined KPI's daily number, weekend/leave-aware EOD, weekend-log combo). Rather than duplicate ~500 lines, **generalize these by department**, matching how `eod-reports.ts` was already generalized in Phase 1 when Marketing→In-Store was added:

- `src/lib/sales-daily-log.ts` → `src/lib/dept-daily-log.ts`: drop the `SALES_DEPARTMENT` constant, every function takes `department: string`; `DAILY_LOG_NOTE` becomes `dailyLogNote(department)`; `salesManualKpis` → `deptManualKpis(department, kpis)`; `getSalesData()` → `getDeptDailyLogData(department)`.
- Server actions move out of the `sales/` route folder into neutral top-level files both departments call: `src/app/portal/(app)/daily-log/day-actions.ts` and `.../daily-log/eod-actions.ts`, each taking `department` as an explicit argument, with `guard()` validating it's one of `["sales", "wholesale"]`.
- `SalesCalendar.tsx` → `src/components/portal/department/DailyLogCalendar.tsx`, taking a `department` prop plus an optional `extraRenderDay?: (ymd) => ReactNode` slot (Wholesale layers its invoice-span bars through this; In-Store passes nothing).
- `LogDayModal.tsx` and `SalesEodReportPanel.tsx` become department-agnostic (take `department` as a prop, call the new shared actions).
- `DeptShell.tsx`'s `department === "sales"` EOD-panel check becomes `["sales", "wholesale"].includes(department)`.
- `sales/page.tsx` shrinks to just pass `department="sales"` into the generalized components; `wholesale/page.tsx` becomes a near-mirror plus its invoice panel.

This means Wholesale gets weekend logging, the Monday "log the weekend" combo, and its own leave-aware EOD report for free — no separate "Phase 4 rollout" work needed.

## Phase 2 — Events

**Data model** (new migration): `events` table — `id, customer_id, event_date, name, stock_needed (text), kpi_id (nullable fk to kpis), in_store (boolean default false), notify_marketing (boolean default false), notes, created_by, created_at`. RLS scoped via `can_access_department('events')`, same shape as `dept_day_logs`.

**Calendar**: reuse `MonthCalendar` directly (it's already fully generic — no changes needed). New `EventsCalendar.tsx`: month/week toggle, `shadeValue` driven by event *count* per day (not a KPI amount) normalized against the max in the visible range, `renderDay` shows event name(s) inline. Click a day → `EventModal` (new): lists existing events that day, "+ Add event" form (name, stock needed, KPI dropdown sourced from Events-department KPIs via the existing `kpis`/`getKpis` system — same "admin defines KPIs, this just tags them" approach as In-Store, no new KPI-logging math), "Happens in-store" checkbox, "Notify marketing" checkbox.

**Notify marketing**: this is a direct, human-triggered action (Rudy ticking a box while creating a real event), not automation — same category as the "New deliverable: X" receipts we deliberately kept when removing automated messages. On submit, if checked, insert one `dept_inbox` message to `marketing` with `from_name` = the real signed-in person's name (mirrors `assignDeliverable`'s pattern in `management/actions.ts`).

**In-Store countdown**: new small `UpcomingEventsCard.tsx` rendered on the In-Store page (between `QuickLinks` and `DailyLogCalendar`), server-fetches events where `in_store = true` and `event_date >= today`, shows the soonest 1–3 as a countdown ("SkiErg Challenge — in 4 days, Thu 2 Oct") linking to `/portal/events`.

**Files**: `src/app/portal/(app)/events/{page.tsx,layout.tsx,event-actions.ts}`, `src/components/portal/events/{EventsCalendar.tsx,EventModal.tsx}`, `src/components/portal/UpcomingEventsCard.tsx`, migration `2026101X_events.sql`.

## Phase 3 — Wholesale

**Reuses the generalized daily-log system** (above) for the day-by-day numbers (stock sold/in stock/to ship/shipped — all just admin-defined KPIs under department "Wholesale", exactly like In-Store's cans/Rand/signups).

**Invoice/shipment tracking — new `wholesale_invoices` table**: `id, customer_id, client_name, amount (numeric), file_path (nullable, storage object path), sent_date, paid (boolean default false), paid_date, follow_up_date, follow_up_deliverable_id (fk mk_deliverables, nullable), ship_date, delivered_date, courier, notes, created_by, created_at, updated_at`. RLS via `can_access_department('wholesale')`.

**Storage**: new private `wholesale-invoices` bucket, RLS policy copied verbatim in shape from `marketing-media`'s (`can_access_department('wholesale')` + tenant-folder check), path `${customerId}/invoices/...`. Upload flow mirrors `KpiUploader.tsx`'s exact pattern (`src/components/portal/management/KpiUploader.tsx`): client uploads via `createClient().storage.from(...).upload(...)`, then a server action records the row.

**Follow-up deliverable**: creating an invoice with a `follow_up_date` creates a real `mk_deliverables` row (department: wholesale, category: Admin, due_date: follow_up_date) via the same insert shape `assignDeliverable` uses, id stored back on the invoice. Marking an invoice paid auto-completes that deliverable if still open. This surfaces naturally on the existing Deliverables board and the KPIs & Deliverables overview — no new UI needed for the reminder itself.

**Calendar visual**: `DailyLogCalendar`'s `extraRenderDay` slot renders two thin spanning bars per day cell for Wholesale — a payment-status bar (sent_date → paid_date/today, blue/amber/red by status) and a shipping bar (ship_date → delivered_date/today, a distinct color), each with a rounded cap only on its true start/end day so adjacent cells read as one continuous bar (the same segmented-bar technique multi-day calendar events commonly use).

**Invoices panel**: new `InvoicesPanel.tsx` below the calendar — list of live invoices with inline "Mark sent/paid" + "+ New invoice" (client name, amount, sent date, follow-up date, optional file upload). Not driven by clicking a calendar day (an invoice has its own dates, unlike a daily log entry).

**Quick links**: new `src/components/portal/wholesale/QuickLinks.tsx` — Lightspeed button not needed here (that's In-Store's system); buttons are: Upload invoice (scrolls to/opens `InvoicesPanel`'s form), Email (`mailto:` placeholder), WhatsApp (`wa.me` placeholder, green) — both placeholders flagged the same way Lightspeed's URL was.

**Files**: `wholesale/page.tsx` rewritten (was generic shell), `wholesale/{invoice-actions.ts}`, `src/components/portal/wholesale/{InvoicesPanel.tsx,QuickLinks.tsx}`, migration `2026101X_wholesale_invoices.sql`.

## Phase 4 — @mentions and per-department notification badges

**Roster lookup problem, resolved**: confirmed via research that `profiles` has no RLS policy letting anyone read another profile at the same business — not even executives (the old own-row policies were dropped in `20260919_harden_profiles_privilege_escalation.sql` and never replaced). Rather than add a new RLS policy (bigger security surface), reuse the existing escape hatch this codebase already uses for the same problem (`src/lib/activity-tracking.ts`, `src/lib/eod-reports.ts`): a server action that resolves `customer_id` server-side from the caller's own session, then queries with `createAdminClient()` — never trusting a client-supplied customer_id. New `getMentionRoster()` in a new `src/app/portal/(app)/mentions/actions.ts`.

**Data model** (new migration): `page_comments` gets `mentioned_profile_ids uuid[] not null default '{}'`. New `profile_mentions` table (per-person notification record, same shape idiom as `portal_patch_reads`): `id, profile_id (fk profiles), customer_id, department, comment_id (fk page_comments), mentioned_by_name, read_at, created_at`; RLS: `profile_id in (select id from profiles where user_id = auth.uid())` (the person can read/update-as-read their own mentions) `or is_service_provider()`.

**Comment box UI**: new `MentionTextarea.tsx` wraps the existing plain `<textarea>` in `PageComments.tsx` — tracks the word at the cursor, and when it starts with `@`, shows a dropdown (fetched once from `getMentionRoster()`, filtered client-side) below the textarea; picking a name replaces `@partial` with `@Full Name ` and records that person's `profile_id` in local state. On submit, `addPageComment` gains a `mentionedProfileIds: string[]` parameter — server re-validates each id actually belongs to the customer (via admin client) before storing, and inserts one `profile_mentions` row per validated id (also via admin client, since the mentioner's own RLS session can't write rows for someone else's `profile_id` — same reasoning as `portal_patch_reads`).

**Sidebar badge**: new `unreadMentionsByDept: Record<string, number>` prop on `Sidebar` (alongside the existing `unreadPatches`, not replacing it), computed in `src/app/portal/(app)/layout.tsx` the same way `unreadPatches` already is (one more admin-scoped query, grouped in JS). Rendered as a numeric pill (`rounded-full bg-accent-blue px-1.5 text-[11px] font-medium text-white`, matching `MessagesPanel.tsx`'s existing unread-count style — not the pulsing dot used for patches) next to whichever department nav link has `unreadMentionsByDept[link.department] > 0`.

**Marking read**: `DeptCommentBox.tsx` (already a per-department server component) additionally updates `profile_mentions` to `read_at = now()` for the signed-in profile + that department where still unread — legal under RLS since it's a person updating their own rows, no admin client needed there.

**Files**: `src/components/portal/department/MentionTextarea.tsx` (or fold into `PageComments.tsx`), `src/app/portal/(app)/mentions/actions.ts`, changes to `PageComments.tsx`, `department/actions.ts`'s `addPageComment`, `Sidebar.tsx`, `layout.tsx`, `DeptCommentBox.tsx`, migration `2026101X_mentions.sql`.

## Verification (all phases)

- `npx tsc --noEmit` and `npx eslint` on every new/changed file after each phase (same as Phase 1), fixing anything that isn't pre-existing noise.
- New branch off current `main` (`instore-daily-log` is already merged) — work happens as separate commits per phase on one branch, pushed and opened as a PR the same way as Phase 1, not committed/pushed until asked.
- Three new migrations (Events, Wholesale, Mentions) handed to Willem the same manual-paste way as every prior one — not run automatically.
- Manual browser check once deployed to preview: create an Events entry flagged "in-store" and confirm it shows on the In-Store countdown; create a Wholesale invoice, mark it sent then paid, confirm the follow-up deliverable appears and auto-completes, and confirm the calendar bar renders across the right days; @mention someone in a comment and confirm their Sidebar badge appears and clears when they open that department.
