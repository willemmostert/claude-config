# GotWurk Supabase Schema Recon (for multi-tenant feature planning)

## Status
Plan mode is active. Steps 1, 2, and 5 (below) are complete using read-only enumeration
tools (`list_projects`, `list_tables`, `get_advisors`). Steps 3 and 4 — pulling actual
row data from `customers` and `profiles` via `execute_sql` — were **not run**. Even
though the intended queries are plain `SELECT`s, `execute_sql` is a generic
raw-SQL-execution tool (capable of INSERT/UPDATE/DELETE/DDL), so it is classified as a
non-read-only tool and blocked under the current plan-mode restriction, which
supersedes the task instructions. These two SELECTs are ready to run the moment plan
mode is exited/approved:

```sql
select * from public.customers;
select * from public.profiles;
```

## 1. Project confirmed
- id/ref: `sklihjowjauhumddslgm`
- name: "GotWurk"
- status: `ACTIVE_HEALTHY`
- region: eu-west-2, Postgres 17.4.1.074
- (sibling project on same org, not relevant: `fzhvwmerxbbienczncyu` "Frik Fridge App", INACTIVE)

## 2. Public schema — tables, columns, FKs (verbatim from list_tables)

### public.customers (RLS enabled, 1 row)
- id uuid, default gen_random_uuid(), PK
- stripe_customer_id text, unique
- name text
- email text, unique
- notion_client_id text, nullable
- created_at timestamptz, default now()
- slug text, nullable, unique
- logo_url text, nullable
- industry text, nullable
- Referenced by: integrations.customer_id, profiles.customer_id, subscriptions.customer_id, kpis.customer_id (all -> customers.id)

### public.profiles (RLS enabled, 1 row)
- id uuid, default gen_random_uuid(), PK
- user_id uuid, unique -> FK to auth.users.id (profiles_user_id_fkey)
- first_name text
- last_name text
- email text
- phone text, nullable
- user_type text, nullable, default 'client', CHECK IN ('client','service_provider')
- created_at timestamptz, default now()
- updated_at timestamptz, default now()
- customer_id uuid, nullable -> FK to customers.id (profiles_customer_id_fkey)
- No `first/last` split issue, no `role` column beyond user_type — note only two user_type values exist (client / service_provider); no explicit "staff"/"admin" distinct from service_provider.

### public.kpis (RLS enabled, 4 rows)
- id uuid PK default gen_random_uuid()
- customer_id uuid -> FK customers.id (kpis_customer_id_fkey) — **NOT INDEXED** (perf advisory)
- name text
- department text, default 'General'
- target_value numeric, nullable
- current_value numeric, default 0
- unit text, nullable
- status text, default 'on_track', CHECK IN ('on_track','at_risk','off_track','complete')
- due_date date, nullable
- slack_channel text, nullable
- notes text, nullable
- created_at timestamptz default now()
- updated_at timestamptz default now()

### public.kpi_history (RLS enabled, 0 rows)
- id uuid PK default gen_random_uuid()
- kpi_id uuid -> FK kpis.id (kpi_history_kpi_id_fkey) — **NOT INDEXED** (perf advisory)
- value numeric
- recorded_at timestamptz default now()

### public.integrations (RLS enabled, 6 rows)
- id uuid PK default gen_random_uuid()
- customer_id uuid -> FK customers.id (integrations_customer_id_fkey)
- service text, CHECK IN ('slack','notion','xero','meta_business','email','google_calendar')
- status text, default 'not_connected', CHECK IN ('not_connected','connected','error')
- external_account_name text, nullable
- connected_at timestamptz, nullable
- last_synced_at timestamptz, nullable
- meta jsonb, default '{}'

### public.subscriptions (RLS enabled, 0 rows, no policies — advisory flagged)
- id uuid PK default gen_random_uuid()
- customer_id uuid -> FK customers.id (subscriptions_customer_id_fkey)
- stripe_subscription_id text, unique
- stripe_price_id text, nullable
- monthly_amount numeric
- currency text, default 'usd'
- status text, default 'incomplete'
- current_period_end timestamptz, nullable
- created_at timestamptz default now()
- updated_at timestamptz default now()

### public.invoices (RLS enabled, 0 rows, no policies — advisory flagged)
- id uuid PK default gen_random_uuid()
- subscription_id uuid -> FK subscriptions.id (invoices_subscription_id_fkey)
- stripe_invoice_id text, unique
- amount_paid numeric
- currency text
- status text
- invoice_date timestamptz
- created_at timestamptz default now()

### Not present at all (confirmed absent from public schema)
No tables named/related to: messages, comments, notes, tasks, reports, deliverables,
warehouse, marketing, staff, contacts, finance (beyond subscriptions/invoices above).
If the new feature needs any of these, they must be created from scratch.

### Helper functions found (from advisories, not from list_tables)
- public.current_customer_id() — SQL, SECURITY DEFINER, exposed to anon+authenticated via RPC
- public.handle_new_user() — plpgsql, SECURITY DEFINER, exposed to anon+authenticated via RPC (likely the auth.users -> profiles trigger function)
- public.is_service_provider() — SQL, SECURITY DEFINER, exposed to anon+authenticated via RPC

## 3 & 4. customers / profiles row data
**Not retrieved** — blocked by plan mode (see Status above). `list_tables` shows
`customers` has exactly 1 row and `profiles` has exactly 1 row, so there is at most one
customer and one profile in the entire system today — meaning either a Sci-Core row
already exists as the *only* customer, or it's some other single seed/test row. Cannot
confirm which, or whether it matches egmar@sci-core.co.za, without running the SELECTs.

## 5. Advisories (informational)

Security:
- `subscriptions` and `invoices` have RLS enabled but **no policies at all** (so effectively locked to everyone except service_role) — will need policies before the feature can use them.
- `customers`, `integrations`, `invoices`, `kpi_history`, `kpis`, `profiles`, `subscriptions` are all exposed to anon+authenticated in the GraphQL schema (SELECT grants present) — worth revisiting when scoping the new multi-tenant feature by customer_id.
- `current_customer_id()`, `handle_new_user()`, `is_service_provider()` are SECURITY DEFINER and directly callable via RPC by anon — should confirm each is safe to expose that way (handle_new_user especially, being a trigger-style function).
- Auth: OTP expiry >1hr, leaked-password protection disabled, Postgres has pending security patches — general hygiene items, unrelated to this feature but worth flagging.

Performance:
- Unindexed FKs: `kpi_history.kpi_id`, `kpis.customer_id`, `profiles.customer_id` — will matter once this multi-tenant feature adds query volume filtered by customer_id.
- `profiles` and `integrations` both have multiple overlapping permissive RLS policies for the same role/action (e.g., profiles has both "Users can view their own profile" and `profiles_self_select` doing the same job) — worth consolidating before adding more policies for the new feature.
- RLS policies on `profiles` re-evaluate `auth.<function>()` per-row instead of `(select auth.<function>())` — a known perf footgun, will replicate into any new customer_id-scoped policies if copy-pasted as-is.

## Open items before proposing the multi-tenant feature design
- [ ] Run the two SELECTs above (needs plan-mode exit / user approval) to confirm real Sci-Core customer id/slug and whether egmar@sci-core.co.za has a profile/auth user.
- [ ] Decide whether new feature tables (messages/tasks/reports/etc.) get created fresh, and whether they follow the same customer_id FK + RLS pattern as kpis/integrations.
- [ ] Decide whether to fix the existing RLS/index advisories opportunistically while adding new tables, or track separately.
