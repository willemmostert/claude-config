---
name: project_gotwurk_page_structure_standard
description: "GotWurk marketing pages must follow a fixed 7-part section order (Hero, Problem, Solution, How it works, Social proof, FAQ, CTA)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7a597fe1-c056-40ff-bc85-37fdcac0e5f1
  modified: 2026-09-07T00:13:04.508Z
---

GotWurk's marketing/landing pages (starting with the homepage, gotwurk.com) must follow a fixed section order: Hero → Problem → Solution → How it works → Social proof → FAQ → Call to action.

**Why:** Willem asked (2026-09-07) to cement this as a standing rule modeled on GotWurk's own reference-quality landing pages, not a one-off homepage tweak.

**How to apply:** When building or restructuring any GotWurk landing-style page, follow this order. The rule is documented in the codebase itself at `website-code/PAGE-STRUCTURE.md` (referenced from `website-code/AGENTS.md`) — read that file for the current mapping of each section to homepage content fields. Notably: the "Social proof" slot is deliberately left empty until GotWurk has real client logos/case studies (per [[feedback_no_liquid_glass]]-style honesty about being a startup — don't fabricate placeholder logos to fill it). See also [[project_gotwurk_drive_notion_architecture]] for where the underlying content actually lives (Drive `website/content/`, synced into the `website-code` repo).
