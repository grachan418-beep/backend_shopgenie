# PHASE 2 PLAN REVIEW

Decision: APPROVE WITH CHANGES

## Required plan corrections
- Accept legacy `unit_price` in request but ignore its value for calculations.
- Store authoritative server-derived unit_price and line_total snapshots in InvoiceItem.
- Preserve product name snapshot.
- Use idempotency_key (UUID/char) unique per shop.
- Atomic transaction with select_for_update on products; reject negative stock; rollback all.
- Worker authorization: require can_confirm_bills for invoice creation; can_view_invoices for list/detail.
- Decimal quantities for weight-based products (DecimalField, max_digits 12, decimal_places 3).

## Model changes proposed
- Invoice: shop FK, created_by FK, idempotency_key (unique with shop), total_amount Decimal, status, created_at.
- InvoiceItem: invoice FK, product FK (nullable), product_name snapshot, quantity Decimal, unit_price Decimal, line_total Decimal.

## Endpoint changes
- POST /api/invoices/ accepts {idempotency_key, items:[{product_id, quantity, unit_price?}]}
- GET /api/invoices/, GET /api/invoices/<id>/

## Migration risks
- New tables only; no alteration of existing Phase 1 tables. Low risk.
- Idempotency unique constraint (shop, idempotency_key).

## Required tests
- Successful billing totals.
- Invalid quantities rejected.
- Insufficient stock rollback.
- Duplicate idempotency returns same invoice.
- Cross-shop access denied.
- unit_price manipulation cannot alter total.
- Worker permission enforcement.

## Unresolved decisions
- Invoice status values (DRAFT/COMPLETED) — confirm whether all invoices are immediately completed.
- Whether to expose cost price in invoice detail to owners — recommend no.
