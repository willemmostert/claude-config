---
name: sync-wurk-trigger
description: "\"Sync Wurk\" is the user's trigger phrase for running the full Notion<->Drive sync in the GotWurk workspace"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 24eabb80-3212-41c2-a1ec-cc2ae565e054
  modified: 2026-08-19T00:12:54.484Z
---

When the user says "Sync Wurk" (any casing), run the full on-demand sync defined in `sops/notion-drive-sync.md` in the GotWurk Drive folder (`g:\My Drive\Claude Brain\GotWurk\sops\notion-drive-sync.md`) — both directions, in full:

- **Direction 1 (Drive → Notion, narrative content, Drive wins):** re-push every file listed in that SOP (positioning, methodology, offers, onboarding questionnaires/call guides) to its corresponding Notion page.
- **Direction 2 (Notion → Drive, transactional data, Notion wins):** full regeneration of `notion-data-snapshot.md` from live Notion (Clients, Pipeline, Projects, Tasks, Meetings, Project Tracker, Invoices).

**Why:** the user set this up 2026-08-19 as a plain memorable phrase for the pre-existing "sync now" on-demand trigger, so they don't have to describe the sync each time. Confirmed by the user directly ("Makes sense?" — yes).

**How to apply:** treat "Sync Wurk" as a standing command, not a request needing clarification — just run it. Do a full sync in both directions rather than guessing which side has pending changes, since the whole point of the on-demand trigger is to catch drift neither side flagged. See [[gotwurk-drive-notion-architecture]] for the broader system this sync sits inside.
