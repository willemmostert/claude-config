---
name: gotwurk-legal-docs
description: "GotWurk now has a /legal folder in Drive with a reusable Mutual NDA template, separate from the client-facing data-security disclosure template"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5137aabc-9146-44d1-91a5-103bfc70496c
  modified: 2026-09-02T13:57:31.063Z
---

GotWurk's Drive OS (see [[project_gotwurk_drive_notion_architecture]]) has a `/legal` folder as of 2026-09-02 — previously listed as deferred in `GOTWURK_OS.md`'s folder map, activated once a real need (a reusable NDA) existed.

**What's there**: `legal/GotWurk-Mutual-NDA-Template.docx` — a general, reusable mutual non-disclosure agreement for use with any new client, not tied to one engagement. Source/editable content at `templates/nda-template.md`. Mutual (not one-way): protects both GotWurk's confidential material (methodology, pricing, internal processes) and the client's (business/financial/customer data), since GotWurk consulting engagements expose both directions.

**Distinct from** `templates/sensitive-information-disclosure-template.md` (see [[project_blu_horizon]] for the first use of that one) — that's a plain-language trust document about day-to-day handling of logins/API keys, not a signed legal contract. The NDA is the actual binding confidentiality agreement.

**Not lawyer-reviewed** — drafted from general mutual-NDA convention (South Africa governing law, 3-year confidentiality survival term, standard exclusions/remedies/boilerplate). Flagged in both the template source and a footer note on the document itself that cross-border enforceability (GotWurk is South Africa-based; real clients so far include Germany-based Blu Horizon and US-based Sci-Core) hasn't been legally verified — recommend real legal review before relying on it for a high-value or higher-risk engagement.

**Still a placeholder**: GotWurk's own registered entity address (`[GOTWURK REGISTERED ADDRESS]`) — the WURK app's own docs reference "GotWurk (Pty) Ltd" as the legal entity but no physical/registered address was found anywhere in the Drive to pre-fill. Confirm with Willem before sending a real signable copy to a client.

**How to apply**: When any client engagement needs a signed confidentiality agreement (not just the data-disclosure trust doc), start from this NDA template, fill in `[CLIENT LEGAL NAME]`, `[CLIENT ADDRESS]`, `[EFFECTIVE DATE]`, `[BRIEF DESCRIPTION OF ENGAGEMENT]`, and flag the missing GotWurk address/lawyer-review gap rather than silently treating it as final/binding-ready.
