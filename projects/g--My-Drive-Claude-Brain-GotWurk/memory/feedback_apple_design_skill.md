---
name: apple-design-skill
description: "Always apply the installed apple-design Claude Code skill to GotWurk visual/UI work, refining not replacing brand colors"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2a983932-285b-45e2-81ec-1ed1624b7da9
  modified: 2026-09-01T15:39:56.106Z
---

Use the `apple-design` skill (installed at `~/.claude/skills/apple-design/`, from
https://github.com/dickwu/apple-design-skill) as the default guideline for anything visual built
for GotWurk — website, client portal, dashboards, mockups. It's an Apple HIG-derived design-review
skill (53 reference docs under `references/hig/`, routed via `references/hig-lookup.md`) covering
layout, typography, motion, accessibility, materials, and drag/resize conventions.

**Why:** User wants an "Apple feel and effect" in the finer UX/UI details (spacing, motion,
hierarchy, feedback states, accessibility) without changing GotWurk's brand.

**How to apply:** Keep GotWurk's existing color palette, dark theme, and brand marks exactly as-is
— never propose swapping to Apple's own palette or literal iOS/macOS chrome. Pull only the
underlying principles (spacing rhythm, type scale, motion/feedback quality, accessibility rigor,
elevation/materials for cards and modals). A GotWurk-specific usage note is already appended at the
top of the skill's `SKILL.md` reinforcing this scope. Relevant to [[project_sci_core_lead]] and any
future portal UI work (see [[project_gotwurk_drive_notion_architecture]] for where else GotWurk
work is tracked).
