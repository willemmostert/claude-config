---
name: project-gotwurk-client-folder-simplification
description: "Drive /clients folders were flattened 2026-09-09 — no more status/category nesting, just /clients/<client-slug>/"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4f41025c-fb55-41ce-9f08-a888b3ae3e3a
  modified: 2026-09-09T11:01:00.055Z
---

Willem had `/clients` flattened on 2026-09-09: it used to nest `<status>/<category>/<client-slug>/` (status: leads/incubator/active-clients/closed, mirroring Notion Stage; category: full-package-clients/social-media-clients, mirroring Notion Client Category). Now it's just `/clients/<client-slug>/` — currently `clients/BLU/` and `clients/sci-core/`.

**Why:** Willem's own words: "the whole client folder thing... is completely all over the place... someone's either a client or they're not." The taxonomy was built ahead of any real client and never paid for its own overhead (a folder move + relative-link recompute on every Stage change) across just two clients ever having existed in it.

**How to apply:**
- Don't recreate the old status/category folders. New clients get `/clients/<client-slug>/` directly — see [sops/client-folder-structure.md](../../../../sops/client-folder-structure.md) (path relative to this memory file, i.e. the vault root's `sops/`) for the current checklist.
- A client's Stage/Category changing in Notion is now a Notion-only edit — the Drive folder never moves.
- Notion's Stage and Client Category fields themselves were deliberately **not** touched or removed — only their mirroring into the Drive folder path was dropped. Changing the actual Notion schema would be a separate, bigger decision Willem hasn't made.
- `ventures/cowboy-cafe/` was explicitly kept out of `/clients/` despite Willem floating it as a "maybe" — it's his own in-house venture, not a client engagement; flagged back to him rather than moved.
- Older memories/history (decision log entries before 2026-09-09, old meeting notes, possibly [[project_sci_core_lead]]) may still reference the retired `clients/leads/full-package-clients/sci-core/`-style paths — that's accurate history from when it was true, not a live path. Don't treat a path like that as current without checking.
- `notion-data-snapshot.md` wasn't hand-edited (per its own read-only convention) — if it still shows old-style Drive Folder path text, a "Sync Wurk" pass regenerates it correctly rather than needing a manual fix.
