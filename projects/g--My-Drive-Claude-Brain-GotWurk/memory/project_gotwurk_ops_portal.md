---
name: project-gotwurk-ops-portal
description: "GotWurk Operations Portal (/ops) is a new staff-only internal dashboard scaffolded 2026-09-09, separate from the client-facing /portal — not yet live"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4f41025c-fb55-41ce-9f08-a888b3ae3e3a
  modified: 2026-09-09T00:59:38.226Z
---

Willem asked (2026-09-09, overnight, while asleep — a "get as far as possible, report back at 7:30am" instruction) for an internal "business OS" dashboard: a staff-only view listing all clients in a sidebar, with per-client messages/tasks/deliverables/KPIs/invoices, plus cross-client Overview/Tasks/Finance pages, and a hook for his own agents to delegate tasks into department queues. He explicitly wants it visually identical to the [[project_gotwurk_web_design_system]] redesign, and wants it live on its own domain/subdomain eventually (leaning towards a `gotwurk.com` subdomain via Vercel, not a new domain purchase).

**Built that night** (`website-code/src/app/ops/*`, `src/components/ops/*`, `src/lib/ops.ts`): full route tree gated on `profiles.user_type = 'service_provider'` (redirects clients to `/portal`, staff default-land on `/ops` after login), client list sidebar with search, Overview/Tasks/Finance/Clients pages, a per-client detail page with all requested sections, manual create-forms for tasks/deliverables/invoices, and `POST /api/ops/tasks` (shared-secret `OPS_AGENT_API_KEY` auth) as the first real "agent delegates a task" hook. Schema lives in `supabase/migrations/20260909120000_ops_portal.sql` — new tables `ops_messages`, `ops_tasks`, `ops_deliverables`, `invoices`, plus a `status` column on `customers`.

**Why it isn't live yet:** the GotWurk Supabase project (`sklihjowjauhumddslgm`) was paused, and restoring it was blocked by Claude Code's auto-mode classifier (production DB, also backs Stripe webhooks + the real client portal) — needs Willem's explicit go-ahead, not something to do unattended. There's also no Vercel or GoDaddy credential available in this environment at all (confirmed via `env | grep -i vercel/godaddy` — empty), so deployment and DNS are hard blockers, not just caution. Full checklist is in `website-code/DEPLOYMENT.md`.

**How to apply:** Before assuming `/ops` is usable, check whether the Supabase project has since been restored and the migration applied (ask, or check `git log` / the live site) — as of 2026-09-09 it was schema-ready but rendering empty states everywhere. If asked to keep building this out, read `DEPLOYMENT.md` first for exactly what's outstanding, and `src/lib/ops.ts` for the data layer shape before adding new tables/queries.
