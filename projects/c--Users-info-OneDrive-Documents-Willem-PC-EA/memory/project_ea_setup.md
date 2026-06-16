---
name: project-ea-setup
description: "Willem's cross-platform EA setup — vault location, structure, skills, and session rules"
metadata: 
  node_type: memory
  type: project
  originSessionId: 141fde09-212e-454b-8b2d-7e8984cf0e08
---

Willem's EA system is an Obsidian vault ("Willem's Vault") synced via Google Drive for Desktop, working identically on Mac and PC.

**Vault path on PC:** `G:\My Drive\Willem's Vault\Willem's Vault\`
**Google Drive drive letter on PC:** `G:`
**Vault path on Mac:** `~/Library/CloudStorage/GoogleDrive-info@willemmostert.com/My Drive/Willem's Vault/Willem's Vault/`

**Session rules (apply every session):**
1. At session start, read vault `CLAUDE.md` and `context/current-priorities.md`
2. Save all created files to the vault (client files → `01 Clients\<Name>\`)
3. Log decisions to `decisions/log.md` in format `[YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...`
4. Close every session with a summary saved to `99 Archive/sessions/YYYY-MM-DD-[topic].md`
5. Never delete — archive instead

**Vault structure:**
- `00 Inbox/` — fast captures
- `01 Clients/` — one folder per client (_Client.md, Meetings/, WhatsApp/, Files/, Game Plan)
- `02 Meetings/` — standalone meeting notes
- `03 Notion Mirror/` — pages pulled from Notion
- `04 Knowledge/` — reference notes
- `05 Projects/` — active projects
- `99 Archive/sessions/` — session summaries
- `context/` — me.md, work.md, team.md, current-priorities.md, goals.md
- `Commands/` — command specs (training game plan, etc.)
- `.claude/rules/` — client-management.md, communication-style.md
- `.claude/skills/` — client-onboarding, fathom-to-execution-plan, monthly-partner-invoice, new-client
- `decisions/log.md` — append-only decision log

**Skills available:** `/client-onboarding`, `/fathom-to-execution-plan`, `/monthly-partner-invoice`, `/new-client`

**PC EA folder** (`C:\Users\info\OneDrive\Documents\Willem PC EA\`) is the Claude Code project anchor — its CLAUDE.md routes every session to the vault.

**How to apply:** Always read vault CLAUDE.md and current-priorities.md at the start of a substantive session before doing any work.
