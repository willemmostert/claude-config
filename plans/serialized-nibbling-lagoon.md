# Client Portal: Department Dashboards + First-Party Messaging

## Context

Sci-Core is being presented the GotWurk client portal this Friday (2026-09-05... actually 2026-09-04, this Friday from 2026-09-01). The portal currently only has Overview/KPIs/Integrations/Settings. The user wants the full department structure visible in the sidebar (Tasks, Reports, Deliverables, Warehouse, Marketing, Staff, Contacts, Finance), a mail/inbox summary, and a first-party GotWurk↔client messaging feature — using the inspiration dashboards (Brightside HR, Ironwood Warehouse, Bluebird Fleet, Fairview CRM) as visual/structural reference.

Critically: **no live data source exists yet** for Warehouse, Marketing, Finance, or mail aggregation (no WMS, ad platform, accounting system, or connected inbox is authorized in this environment). Per the user's explicit answer to my clarifying question, these ship as **real UI with honest "not connected" empty states** — the same pattern already used for Integrations — never fabricated numbers, even for a client-facing demo. The one exception is the messaging feature: it's first-party (fully within GotWurk's control, no external dependency), so it gets built as a real, working, database-backed feature.

This also requires a real Supabase auth account for the client contact (confirmed: **egmar@sci-core.co.za**), and touches the live `gotwurk-website` repo, which auto-deploys to gotwurk.com on push to `main` — so a production push only happens after explicit separate confirmation.

## Scope confirmed with user
- Real UI + honest empty states for anything without a live source (not demo/fake numbers).
- Client login: `egmar@sci-core.co.za` (not the typo'd address from the original message).
- GotWurk OS1 (staff cross-client admin view) is a **future** recommendation only, not built this week.

## What's being built

### 1. Prep: port the already-built floating-label input (`FloatingField`)
This was fully designed, built, and verified earlier this session but only landed in the Drive `website-code/` snapshot, not the real repo. Port it into `C:\Users\info\Developer\gotwurk-website`:
- `src/components/FloatingField.tsx`, the `.wave-*` CSS block in `src/app/globals.css`, and the `ApplyForm.tsx` / `LoginForm.tsx` wiring — copy over as already-verified (re-run the same dev-server + Playwright check after copying, since this is a different repo checkout than where it was last verified).
- Not used for the new messages compose box (see below) — that's a plain chat-style textarea, not a labeled form field.

### 2. Data model (Supabase project `sklihjowjauhumddslgm`)

**First, verify before writing anything** (read-only): `select * from customers` and `select * from profiles` to see what the existing single row in each actually is (may or may not already be Sci-Core), and read the literal RLS policy SQL on `kpis`/`integrations` to confirm `current_customer_id()` / `is_service_provider()` signatures before reusing them.

**New `messages` table:**
```sql
create table public.messages (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id),
  sender_profile_id uuid not null references public.profiles(id),
  sender_role text not null check (sender_role in ('client', 'service_provider')),
  body text not null check (char_length(body) between 1 and 4000),
  created_at timestamptz not null default now(),
  read_at timestamptz
);
create index messages_customer_id_created_at_idx on public.messages (customer_id, created_at desc);
alter table public.messages enable row level security;

create policy messages_select on public.messages for select
  using (customer_id = (select current_customer_id()) or (select is_service_provider()));

create policy messages_insert on public.messages for insert
  with check (
    (customer_id = (select current_customer_id()) or (select is_service_provider()))
    and sender_profile_id = (select id from public.profiles where user_id = (select auth.uid()))
  );
-- no update/delete policy -- append-only for now.
```
Note the `(select auth.<fn>())` wrapping — the existing `profiles` policies re-evaluate per-row (an advisory-flagged anti-pattern); don't copy that into new policies. Apply via Supabase MCP `apply_migration`, then immediately `get_advisors` to confirm no new issues.

**Real accounts** (via `execute_sql` using `pgcrypto`/`crypt()` against `auth.users`, the same method already validated in the 2026-08-28 session — no service-role key is available in this environment):
- Confirm/create the `customers` row for Sci-Core (name, slug `sci-core`, industry) if the existing single row isn't already it.
- Create `profiles` + `auth.users` for `egmar@sci-core.co.za`, `user_type = 'client'`, linked to the Sci-Core `customer_id`. Generate a strong random password — given to the user directly in chat (never emailed by me), clearly flagged as sensitive, for them to relay to Egmar.
- Also confirm/create a `service_provider` account for Willem (`info@willemmostert.com`) if one doesn't exist, so the messaging feature can be demoed as a real round-trip (client sends → GotWurk account receives/replies) — at single-client scale this works fine through the same `/portal/messages` page; a proper multi-client inbox is what OS1 (below) is for later.

### 3. Shared "honest empty state" components
- `src/components/portal/MetricPlaceholderCard.tsx` — thin wrapper on the existing `StatCard` (`value="—"`, `hint="Not connected yet"`, `hintTone="muted"`), no new visual system.
- `src/components/portal/MetricPlaceholderGrid.tsx` — maps a `string[]` of metric labels into a `MetricPlaceholderCard` grid (matches the existing `grid-cols-2 lg:grid-cols-4` pattern from the Overview page).
- `src/lib/departments-catalog.ts` — static config per department (`title`, `description`, `metrics: string[]`), mirroring `integrations-catalog.ts`'s existing pattern. Warehouse's metrics list is exactly: Orders to pick, Shipped today, Inventory, Shipping, Picking, Low stock, Pallet wrap, Boxes (12x12), Label rolls, Tape rolls. Other departments get a small reasonable placeholder set (e.g. Marketing: Ad spend, Reach, Engagement) — easy to edit later once a real source is picked per department.

### 4. Department pages
One `page.tsx` per department under `src/app/portal/(app)/`, each a thin Server Component rendering a heading + `MetricPlaceholderGrid` from the catalog: `tasks/`, `reports/`, `deliverables/`, `marketing/`, `finance/`, `staff/`, `contacts/`. `warehouse/page.tsx` additionally renders a second `rounded-2xl` card below the main grid for "Warehouse team" (its own small metric set: On shift now, Pickers, Packers) — kept as a section within the one page rather than a new nested route, since no dynamic/nested routes exist anywhere in this codebase yet.

### 5. Messages feature (real)
- `src/lib/portal.ts`: add `Message` type + `getMessages()` (same shape as `getKpis`/`getIntegrations`).
- `src/app/portal/(app)/messages/actions.ts`: `sendMessage` server action (`useActionState` shape, matching `signIn` in `login/actions.ts`) — looks up the caller's own profile, inserts with their real `customer_id`/`sender_role`, `revalidatePath`.
- `src/components/portal/MessageThread.tsx` (server, pure render) + `src/components/portal/ComposeMessageForm.tsx` (`"use client"`, the only client piece — plain styled `<textarea>` + Send button, same input styling already used in `LoginForm`, not `FloatingField`).
- `src/app/portal/(app)/messages/page.tsx`: fetch + render list + compose form.

### 6. Sidebar
Convert `Sidebar.tsx` to `"use client"` (safe — already receives plain serializable props, server actions still callable from client components), add the full 13-item `navLinks` array (Overview, KPIs & Goals, Messages, Tasks, Reports, Deliverables, Warehouse, Marketing, Finance, Staff, Contacts, Integrations, Settings), and add `usePathname`-based active-route highlighting — not scope creep at 13 items, a real usability need once the list gets this long.

### 7. GotWurk OS1 — recommendation only, not built now
Separate app/repo on its own subdomain (e.g. `os.gotwurk.com`), sharing the same Supabase project and RLS model (`is_service_provider()` already distinguishes staff from client rows — the right primitive). Reason: OS1's security boundary (sees every customer) and growth path (cross-tenant queries/exports) are different enough from the public marketing site + single-tenant client portal that bundling them into one deploy needlessly widens blast radius in both directions. This is a one-paragraph note for the user, no code touched this week.

## Sequencing
1. Verify `customers`/`profiles` real contents + read literal existing RLS policy SQL (read-only).
2. Apply `messages` migration, re-check `get_advisors`.
3. Create/confirm Sci-Core `customers` row, Egmar's real auth+profile account, Willem's service_provider account.
4. Port `FloatingField` into this repo (prep item 1).
5. Build shared components + `departments-catalog.ts`, verify against one page (Marketing) before repeating.
6. Build the remaining simple department pages, then Warehouse.
7. Build the messages feature end-to-end.
8. Update Sidebar last (every route depends on it — touch it once everything it links to actually exists).
9. **Verification**: run the local dev server, sign in as the real `egmar@sci-core.co.za` account (not a synthetic test user), click through all 13 sidebar links confirming honest empty states render (no fabricated numbers), send a test message and confirm it's visible from both the client and Willem's service_provider account (RLS working both directions). Screenshot key pages.
10. Run `next build` (not just `dev`) to catch type errors across the new Server/Client boundary, and a final `get_advisors` pass on Supabase.
11. **Stop before pushing.** Report what was built + verification results, and get explicit confirmation before `git push` to `main` (auto-deploys to the live gotwurk.com).

## Critical files
- `src/components/portal/Sidebar.tsx`
- `src/lib/portal.ts`
- `src/lib/departments-catalog.ts` (new)
- `src/components/portal/MetricPlaceholderGrid.tsx`, `MetricPlaceholderCard.tsx` (new)
- `src/app/portal/(app)/warehouse/page.tsx`, `messages/page.tsx`, `messages/actions.ts` (new)
- `src/components/portal/MessageThread.tsx`, `ComposeMessageForm.tsx` (new)
