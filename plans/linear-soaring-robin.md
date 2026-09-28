# Sci-Core portal — shared Product/Stock system, In-Store sales logging, Events stock requests, KPI page layout

## Context

Willem wants the 42-product catalog we just scraped from sci-core.co.za turned into a real, shared inventory system inside the portal — not just a one-off reference page. It needs to live in Wholesale (as "the main wholesale database"), In-Store, and Warehouse, staying in sync across all three, plus: a new product-based daily sales flow for In-Store (replacing manual KPI number entry), structured stock requests on Events, and a vertical-column layout for the KPIs & Goals page. Confirmed with Willem: "the membership tab" meant Warehouse; In-Store's product-sales logging **replaces** its KPI number-entry (any KPI that should track it gets computed automatically); the 40% membership discount is one global rate, not per-product.

## Data model (three new migrations)

**`products`** — the single shared catalog, one row per product, with a quantity per physical location so each department's stock view stays separate but always reads the same numbers:
```
id, customer_id, name, info (text), image_url, shopify_handle, shopify_url,
retail_price numeric, status text check in ('in_development','coming_soon','new','active','old_stock','discontinued') default 'active',
new_until date (status='new' auto-reads as expired once past this date — computed in the UI, not enforced by a job),
warehouse_qty int default 0, wholesale_qty int default 0, store_qty int default 0,
low_stock_threshold int default 10,
created_by, created_at, updated_at
```
RLS: any of `can_access_department('warehouse'|'wholesale'|'sales')`, matching the "separate tabs, same data" requirement — there's no single owning department.

**`product_sales`** — In-Store's per-sale log (and reusable by Wholesale later if it ever needs the same pattern): `id, customer_id, product_id, department, sale_date, quantity, price_tier ('membership'|'retail'), unit_price (snapshot at sale time), total, logged_by, logged_by_name, created_at`. Same multi-department RLS shape as `dept_day_logs`.

**`store_settings`** — one row per business: `customer_id (pk), membership_discount_pct numeric default 40`. The single global discount rate, editable from the Stock view.

**Events**: `alter table events add column stock_requests jsonb not null default '[]'` — an array of `{product_id, quantity, source: 'warehouse'|'wholesale'|'store'}`, same jsonb-array-for-a-variable-length-list pattern already used by `mk_calendar_rows.links`.

**Seed migration**: the 42 real products (name, price, image URL, availability → status) as plain `insert` statements generated from the scrape — real portal pages aren't sandboxed like the Artifact tool, so `image_url` just points straight at the existing Shopify CDN URLs (`cdn.shopify.com/...`), no re-hosting needed.

## Shared Product/Stock UI

One component, three mount points — same pattern as `DailyLogCalendar` being shared by In-Store/Wholesale:

- `src/components/portal/products/ProductStockPanel.tsx` — takes `primaryLocation: "warehouse" | "wholesale" | "store"`. Shows every product as a card/row: photo, name, status badge (Coming Soon / New / Old Stock / In Development, "New" auto-hides once `new_until` passes), retail price, this location's quantity (editable, prominent) plus the other two locations' quantities (read-only, for the cross-department overview), a stock-health dot (out of stock / low / healthy, from `low_stock_threshold`). "+ Add product" and "Delete" (with confirm). A "Membership discount" field at the top (reads/writes `store_settings`, one global number).
- `src/components/portal/products/ProductPicker.tsx` — a searchable dropdown showing each product's thumbnail + name (a native `<select>` can't show images). Reused by the In-Store sales modal and the Events stock-request rows.
- `src/app/portal/(app)/products/actions.ts` — `getProducts()`, `addProduct()`, `updateProduct()` (name/info/price/status/new_until/the three quantities), `deleteProduct()`, `getDiscountRate()`, `setDiscountRate()`.
- New routes, each a thin wrapper: `sales/stock/page.tsx`, `wholesale/stock/page.tsx`, `warehouse/stock/page.tsx` rendering `<ProductStockPanel primaryLocation="..." />`.
- Quick-link buttons: Wholesale's `QuickLinks.tsx` gains a "Stock" button (next to Invoices/Email/WhatsApp) linking to `/portal/wholesale/stock`. In-Store's `QuickLinks.tsx` gains an "In-Store Stock" button (next to Lightspeed) linking to `/portal/sales/stock`. Both use the Sci-Core "S" logo if Willem finds one; a generic package icon otherwise (flagged the same way the other placeholder buttons were).

## In-Store: product-sales logging replaces KPI entry

Reuses everything from the daily-log system except the modal:
- New `src/components/portal/sales/SalesDayModal.tsx` — for the selected date(s): a list of line items (`ProductPicker` + quantity + a Membership 40% off / Full retail toggle — no manual price typing), add/remove rows, save.
- New `src/app/portal/(app)/sales/sales-log-actions.ts`: `submitProductSales(dates, lineItems)` — inserts `product_sales` rows (unit price computed server-side from the product's `retail_price` and the current `store_settings` discount, never trusted from the client), decrements each sold product's `store_qty`, and — this is the "gets computed automatically" part — upserts `dept_day_logs` plus a `kpi_logs` row for whichever KPI is flagged `is_primary_metric` on In-Store, with the day's total Rand value, tagged with the existing `dailyLogNote("sales")`. This means the calendar shading/weekly/monthly totals from the last build keep working unchanged — they just get their number from real sales instead of a typed-in figure.
- `DailyLogCalendar.tsx` gains an optional `renderModal?: (dates, onClose) => ReactNode` prop; when provided it's used instead of the default `LogDayModal`. In-Store's page passes `SalesDayModal`; Wholesale and Warehouse pass nothing and keep today's generic KPI-number modal.

## Warehouse joins the daily-log system

`DAILY_LOG_DEPARTMENTS` in `src/lib/dept-daily-log.ts` gains `"warehouse"` — since every daily-log function, the EOD report, and `DeptShell`'s panel logic already key off this one array, this alone gives Warehouse the click-a-day popup, weekend logging, and its own leave-aware end-of-day report, matching In-Store and Wholesale. `warehouse/page.tsx` and a new `warehouse/layout.tsx` go from the generic `DepartmentPage` shell to a bespoke page (mirroring `sales/page.tsx`): comment box, a "Stock Management" quick-link, `DailyLogCalendar`, deliverables.

## Events: structured stock requests

`EventModal.tsx`'s form gains a repeatable "Products needed" section: `ProductPicker` + quantity + a source select (Warehouse / Wholesale / In-Store), add/remove rows, stored as `stock_requests` on the event. Replaces the current free-text "stock needed" field (kept as a fallback note for anything not worth a structured line, e.g. "extra tables").

## KPIs & Goals: vertical department columns

`KpiManager.tsx`'s department sections currently stack full-width, top to bottom. Restructure the wrapping container to a horizontally-scrolling row of fixed-width columns (one per department — In-Store, Wholesale, Marketing, Events, Warehouse side by side), each column keeping its own existing internal layout (owner sub-groups, KPI cards) stacked vertically inside it. `DeliverablesOverview` below is left as it is — only the KPI section was asked for.

## Verification

- `npx tsc --noEmit` / `npx eslint` on every new/changed file, same as every prior phase.
- New branch off current `main`, work as separate commits (foundation → In-Store sales → Warehouse → Events → KPI layout), pushed and merged the same way as the last two batches — confirm with Willem before merging, same as always.
- New migrations (schema + seed) handed over the same manual-paste way, run before merge.
- Manual browser check once deployed: add a product, log an In-Store sale against it and confirm `store_qty` drops and the calendar's primary-KPI number updates, open Wholesale's and Warehouse's Stock views and confirm the same product/quantities show up, create an event with a stock request, check the KPIs page's new column layout.
