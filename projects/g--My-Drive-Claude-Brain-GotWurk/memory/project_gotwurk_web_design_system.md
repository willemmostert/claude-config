---
name: project-gotwurk-web-design-system
description: "GotWurk's website + client portal were rebuilt 2026-09-09 into a \"Systems + AI\" black/mono/blue-signal design language, now the standing standard for all GotWurk web properties"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4f41025c-fb55-41ce-9f08-a888b3ae3e3a
  modified: 2026-09-09T00:42:58.181Z
---

GotWurk's marketing site (`website-code/src/app/(marketing)/*`) and client portal (`website-code/src/app/portal/*`) were both rebuilt on 2026-09-09 into one coherent visual system: near-black background, restrained GotWurk blue (`#4a79fe`) used only as a "signal" (index numbers, hairlines, status dots), Geist Mono for uppercase eyebrow/nav/metadata text, numbered bordered "module" rows instead of rounded card grids, no glassmorphism, no blob gradients. Visual grammar was inspired by Hermes Agent (hermes-agent.nousresearch.com) — principles only, not copied assets.

Full spec of the request lives in `GOTWURK_OS.md` at the vault root. The resulting standard is documented in `website-code/DESIGN-SYSTEM.md` — read that file before any future GotWurk web/portal work.

**Why:** Willem explicitly directed this to be "the new way of moving forward" for GotWurk's own websites and portals — not a one-off homepage reskin. Also ties into [[feedback_no_liquid_glass]] (glassmorphism was already rejected once) and [[feedback_apple_design_skill]] (brand color refinement, not replacement).

**How to apply:** Any new GotWurk-owned page, dashboard, or portal should extend `website-code/DESIGN-SYSTEM.md`'s tokens/components (`Eyebrow`, `Module`, `Section`, `.label-mono`, `.index-number`, flat hairline borders) rather than reintroducing rounded cards, filled pill badges, or backdrop-blur surfaces. As of 2026-09-09 the changes were made locally in the working tree — check `git log` in `website-code/` for whether/when they were committed and deployed before assuming they're live.
