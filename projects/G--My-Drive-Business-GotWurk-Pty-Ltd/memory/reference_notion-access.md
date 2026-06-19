---
name: notion-access
description: "How to access Willem's Notion -- two workspaces, API token required for personal one"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d0d6e7b0-468a-4388-9f3a-d37994a85879
---

Willem has two separate Notion workspaces:

1. **Willem's Workspace** (info@willemmostert.com) -- contains the Wurk App page with all GotWurk business and development docs. The Claude.ai MCP Notion integration does NOT connect to this workspace. Access it via direct API calls using the token in `GotWurk EA/.env` (NOTION_TOKEN).

2. **Catalyst Coaching workspace** -- this is the workspace the Claude.ai MCP Notion tools connect to. It's for coaching work, unrelated to GotWurk.

**How to apply:** When fetching GotWurk Notion content, use `Invoke-RestMethod` (PowerShell) or `curl` (Bash) with the token from `.env`, not the MCP Notion tools. The MCP tools will return "object_not_found" for GotWurk pages.

**Wurk App page ID:** 1a41ef07-d0fb-806d-acc6-d7bb0f6e9408
