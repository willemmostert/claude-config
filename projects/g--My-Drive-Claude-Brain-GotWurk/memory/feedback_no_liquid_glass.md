---
name: no-liquid-glass
description: Willem rejected a liquid-glass/glassmorphism reskin for the GotWurk site and portal
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2a983932-285b-45e2-81ec-1ed1624b7da9
  modified: 2026-09-09T00:43:15.183Z
---

Don't pursue a liquid-glass or glassmorphism visual direction (blurred/refractive frosted panels,
SVG-displacement edge warp, specular mouse-follow highlights) for the GotWurk marketing site or
client portal. Built a full interactive prototype (via `liquid-glass-react`-inspired CSS/SVG
technique, with a live on/off toggle) so he could compare it directly against the current flat
dark-card look; he looked at it and said "I don't like the glass stuff, so we can just scrap that
idea" (2026-09-01). Nothing in the real `gotwurk-website` repo was touched — the prototype was a
standalone artifact only, so there was nothing to revert.

**Why:** Direct rejection after seeing a real, working comparison — not a hypothetical he talked
himself out of. Keep this in mind before proposing glass/blur-heavy visual directions again.

**How to apply:** The rule is "no blur/frosted/refractive surfaces," not "never change the visual
style" — the site/portal were later fully rebuilt (2026-09-09) into the numbered-module "Systems +
AI" language in [[project_gotwurk_web_design_system]], which is now the standard. That rebuild
still avoids `backdrop-blur`/glassmorphism entirely (the portal login page's glass card was
explicitly flattened as part of it), so this rejection stays in force — just don't read "flat
dark-card look" below as freezing the pre-2026-09-09 visual design specifically. Relates to
[[feedback_apple_design_skill]] — the "Apple feel" refinement should come from spacing, motion,
typography, and accessibility polish, not from adding glass/blur surfaces.
