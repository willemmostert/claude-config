---
name: project-scicore-portal-instore-build
description: Sci-Core client portal — full department build-out plus shared Product/Stock system — shipped to main and live
metadata:
  node_type: memory
  type: project
  originSessionId: b82468e4-4f6a-4ea7-aa6e-2afb96179ac5
  modified: 2026-09-28T11:33:59.397Z
---

The Sci-Core client portal codebase lives at `C:\Users\info\Developer\gotwurkwebsite` (NOT inside this vault — this vault only holds client notes/memos). Repo: `willemmostert/gotwurkwebsite`, deploys to production from `main` via Vercel.

**Status as of 2026-09-28: everything shipped and live on `main` (commit `7af2fc1`).** All migrations run by Willem directly in the Supabase SQL editor (project ref `sklihjowjauhumddslgm`). Built across three sessions:
- Phase 1: In-Store daily numbers log, KPIs & Deliverables page reorganized by department/owner, automated `dept_inbox` messages removed entirely (human-to-human only).
- Phases 2–4: Events department, Wholesale department (invoices/shipping), @mentions with Sidebar badges.
- Phase 5 (this session): shared Product/Stock system, In-Store product-sales logging, Warehouse joining the daily-log system, Events stock requests, KPIs page vertical-column layout.

**Architecture notes for next time:**
- The daily-numbers-calendar system is generalized by department (`DAILY_LOG_DEPARTMENTS` in `src/lib/dept-daily-log.ts` = `["sales", "wholesale", "warehouse"]`). `src/components/portal/department/DailyLogCalendar.tsx` now takes an optional `renderModal` override — In-Store uses this to swap in its own `SalesDayModal` instead of the generic KPI-number `LogDayModal`. If Warehouse or Wholesale ever need their own custom day-entry UI instead of generic KPI numbers, this is the extension point, not a fork.
- **Product/Stock is one shared system**, not three separate ones: a single `products` table with `warehouse_qty`/`wholesale_qty`/`store_qty` columns, one `ProductStockPanel` component mounted at `/portal/{sales,wholesale,warehouse}/stock`. There is no "sync" mechanism because there's only one source of truth — don't build a sync layer if asked to extend this, just read/write the same table.
- In-Store's daily sales (`src/app/portal/(app)/sales/sales-log-actions.ts`) auto-feed whichever KPI is flagged `is_primary_metric` for the sales department — the calendar shading/totals from Phase 1 still work unchanged, they just get a computed number instead of a typed one now.
- The 40% membership discount is one global rate in `store_settings` (one row per customer), not per-product — confirmed explicitly with Willem.
- Events' stock requests and the old free-text "stock needed" field coexist: structured requests reference real catalog products; free text is the fallback for anything not worth a line item (e.g. "extra tables").

**Still open / not yet done:**
1. Real Lightspeed URL, Wholesale's email/WhatsApp numbers — same placeholders as before, still unfilled.
2. The Sci-Core "S" logo for the new Stock quick-link buttons — Willem said he'd look for it; a generic box icon is the placeholder in `QuickLinks.tsx` in `sales/`, `wholesale/`, and `warehouse/`.
3. Real stock quantities — all 42 seeded products start at 0 for every location; someone needs to fill in real numbers via the Stock views.
4. **None of this session's work was clicked through in a real browser before merging** — same as the last two batches, same explicit tradeoff Willem accepted given the urgency each time.
5. Warehouse was never given specifics beyond joining the daily-log system + Stock Management — no other Warehouse-specific features exist.
6. **Security follow-up carried over, still unconfirmed**: Willem pasted a live Supabase publishable + secret key into chat during Phase 1 (2026-09-28) and was told to rotate both. Unconfirmed whether he did.

**Why:** Willem is running Sci-Core's whole team through this one portal. This session turned the freshly-scraped 42-product catalog (built as a one-off Artifact first, see the `sci-core-product-catalog-artifact` reference if it exists) into a real, portal-native shared inventory system, plus finished the remaining pieces from his original department-build brain dump.

**How to apply:** Before touching this portal again, re-verify current git/deploy state directly (`git log`, `git fetch origin`) rather than trusting this snapshot. Before extending the product/stock system, read `src/app/portal/(app)/products/actions.ts` and `ProductStockPanel.tsx` first — it's genuinely shared, not per-department, and the RLS policy on `products`/`product_sales`/`store_settings` grants any of Warehouse/Wholesale/In-Store equal write access by design.
