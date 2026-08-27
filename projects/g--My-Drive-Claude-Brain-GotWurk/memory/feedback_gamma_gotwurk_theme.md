---
name: gamma-gotwurk-theme
description: "Always pass themeId for the saved 'GotWurk Theme' custom Gamma theme when generating any Gamma content related to GotWurk"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6bc327db-307a-47e0-ad52-b9da8bce1ed6
  modified: 2026-08-27T23:48:27.140Z
---

For any Gamma generation (`generate`, `generate_from_template`, `generate_multi_page_gamma`, `generate_image`) related to GotWurk — pitch decks, client presentations, internal docs, anything under the GotWurk business — always pass `themeId: "zl2getz46uduoab"` (the "GotWurk Theme" custom theme in the user's Gamma account), rather than omitting themeId or letting Gamma default to whatever theme was last used (e.g. "Catalyst Theme," which is orange/salmon and belongs to a different client/project).

**Why:** The user built this custom theme 2026-08-28 specifically to match gotwurk.com's palette (black background, white/off-white text, wurk blue `#4A79FE` primary accent, mint `#2DD4BF` secondary accent, plus tint/shade variants of both) after an AI-generated attempt at a themed deck defaulted to the wrong existing theme and produced an off-brand result. See [[gotwurk-drive-notion-architecture]] for the broader GotWurk business context this sits inside.

**How to apply:** Before calling any Gamma generation tool for GotWurk work, confirm the theme still exists via `get_themes` (name query "gotwurk") in case it was renamed or deleted, then pass its id as `themeId`. Do not omit `themeId` and hope for a sensible default — that has already caused a wrong-theme generation once. This does not apply to Gamma work for other clients/projects (e.g. Sci-Core) — those should use their own appropriate styling, not the GotWurk theme.
