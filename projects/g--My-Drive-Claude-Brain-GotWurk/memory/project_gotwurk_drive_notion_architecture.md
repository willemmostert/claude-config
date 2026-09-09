---
name: gotwurk-drive-notion-architecture
description: "GotWurk's business runs on a two-system architecture (Drive markdown + Notion HQ) with defined sync ownership — check this before creating anything new in either system"
metadata: 
  node_type: memory
  type: project
  originSessionId: 24eabb80-3212-41c2-a1ec-cc2ae565e054
  modified: 2026-09-09T11:00:44.650Z
---

GotWurk (Willem's business — "Fractional Operations & Business Systems," Systems + AI led, methodology Audit → Architect → Implement → Operate → Optimise) already has a full operating system built across two places, not a blank slate:

- **Google Drive**, locally synced at `g:\My Drive\Claude Brain\GotWurk\` (readable/editable directly with filesystem tools, not just the Drive MCP connector, which only supports create + metadata-update, not content edits). Root index: `GOTWURK_OS.md`. Markdown here is the source of truth for narrative content: positioning, methodology, offers, ICP, onboarding questionnaires/call guides, and per-client working folders under `/clients/`.
- **Notion HQ**, page `https://app.notion.com/p/3b71ef07d0fb8187bb64caaccdcd1f8a` ("GotWurk™"). Source of truth for transactional/live data: Clients, Pipeline, Projects, Tasks, Meetings, Project Tracker, Invoices databases.

**Why:** the two-system split with defined per-direction ownership (Drive wins for narrative, Notion wins for transactional) was a deliberate decision (see Drive `decisions/log.md`) specifically so neither side silently overwrites real edits on the other. See [[sync-wurk-trigger]] for how syncing between them is invoked.

**How to apply:**
- Before creating any new page/database/folder for GotWurk, search both systems first — there is very likely already a matching page, database, or SOP (this has happened twice: a duplicate "GotWurk" Notion page created before the real one was linked, and nearly duplicating the Meetings database before finding the existing one).
- Client folders live at `/clients/<client-slug>/` in Drive — flat, one folder per client (e.g. `/clients/BLU/`, `/clients/sci-core/`), no status/category nesting. **Retired 2026-09-09**: it used to nest `<status>/<category>/<client-slug>/` mirroring Notion's Stage and Client Category fields; Willem had it flattened ("someone's either a client or they're not") — see [[project_gotwurk_client_folder_simplification]] and `decisions/log.md` (2026-09-09). Notion's Stage/Category fields themselves were deliberately left untouched, just no longer mirrored into the Drive path. See `sops/client-folder-structure.md` for the current convention, including required files per client and the always-present `meeting-notes/` subfolder.
- Full package clients = the core 90-Day Business Operating Transformation / retainer offer (business systems build). Social media management was originally positioned as an in-account upsell only, but as of 2026-08-19 GotWurk also pitches it standalone (e.g. to Airbnb hosts) — the Drive/Notion category taxonomy was extended to reflect that.
- SOPs live in `sops/` in Drive — read the relevant one before changing structure (e.g. `client-folder-structure.md`, `notion-drive-sync.md`, `monthly-retainer-billing.md`).
- **2026-09-09: the Notion HQ page ID above may not resolve.** In one session, `notion-search` for "GotWurk" returned zero results, the page ID `3b71ef07d0fb8187bb64caaccdcd1f8a` 404'd, and other searches surfaced pages from an apparently unrelated business ("Catalyst Curves," "Coach Productivity Suite") — meaning the Notion account connected to Claude at that time was not the GotWurk workspace. Don't trust this memory's page ID blindly: search first, and if "GotWurk" truly returns nothing, flag the workspace-connection mismatch to Willem (claude.ai connector settings) rather than create pages in whatever workspace happens to be connected.
