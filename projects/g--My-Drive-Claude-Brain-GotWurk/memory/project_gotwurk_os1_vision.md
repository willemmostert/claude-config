---
name: gotwurk-os1-vision
description: "Willem's vision for a standalone \"GotWurk OS1\" business-hub portal aggregating all clients, staff, and custom agents"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2a983932-285b-45e2-81ec-1ed1624b7da9
  modified: 2026-09-01T16:21:25.127Z
---

Willem wants a second, separate portal (distinct from the per-client portal in the
`gotwurk-website` repo) that acts as his own internal business OS: a few department tabs for his
own team, plus a "Clients" tab that aggregates everything about every client in one place —
payments, revenue, KPIs/goals, messages. If a client does something in their own portal (e.g.
Egmar at Sci-Core sends a message or adds a KPI), it should surface automatically in Willem's
Clients tab, not require him to log into their portal. He also wants each client's Slack connected
into this hub. He plans to run custom agents inside/alongside it (referred to it as "Open Claw" —
exact tool/product name unconfirmed, worth clarifying with him before assuming what it is) that
operate the business and report back to him; he'll set this up on a separate PC "later this month"
(relative to 2026-09-01). He asked whether it needs its own domain, and separately asked about an
hourly GitHub push of the repo plus Google Drive sync as a backup cadence — undecided, not yet
requested as a real task.

**Why:** First floated as a "recommendation only, future work" item during the v1.0 client-portal
build; as of 2026-09-01 he has a much more concrete spec for it (client-data aggregation, own
dashboard, Slack-wide visibility, agent orchestration).

**How to apply:** This is explicitly deferred — Willem said "this isn't for now, let's just focus
on the website" (2026-09-01). Don't start building it. When it resumes, recommend a subdomain (e.g.
`os.gotwurk.com`) on the same GotWurk infra rather than a fully separate domain, since it's an
internal staff tool, not a separately-branded product — revisit only if he later wants to
white-label or sell it independently. Cross-reference [[project_sci_core_lead]] and the portal
architecture already built (multi-tenant Supabase + RLS, `dashboard_widgets`/`dashboard_layout`
customization pattern) as the likely foundation to extend rather than rebuild.
