---
name: feedback-campaigns-separate-from-marketing
description: "Campaigns (Willem's work) must never feed into the Marketing department/calendar — Marketing and Kyla only run the Members Club, a side branch of Sci-Core"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 934cfdc2-4d78-46c8-bda2-e60513a23fa3
  modified: 2026-10-05T21:11:15.072Z
---

Never send, push or link anything from the Campaigns department into Marketing (no content pushed to Kyla's `mk_calendar_rows` calendar, no marketing notifications, no shared KPIs).

**Why:** Willem (2026-10-05): the Marketing department and Kyla only run the Members Club, a side branch of the main Sci-Core brand. Campaigns is for Willem operating the main Sci-Core brand, so mixing them would pollute the Members Club calendar and KPI counts.

**How to apply:** When building or extending Campaigns, keep its tables self-contained (`campaigns`, `campaign_talent`, `campaign_content`, `campaign_budget_lines`). Drop the earlier "push content into the Marketing calendar" idea. `campaign_content.calendar_row_id` exists in the live DB but is unused and must stay unused. Campaigns publishing and performance need their own path, not Marketing's. See [[project-scicore-portal-restricted-depts-mentions]] for the access model.
