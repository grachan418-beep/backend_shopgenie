# PHASE 2 IMPLEMENTATION PLAN — Billing and Invoices

## Inspection findings
- Owner Flutter InvoiceItem sends product_id, quantity, unit_price (see models.dart toJson).
- Owner app expects invoice creation with multiple products.
- Existing role policy: SHOP_OWNER full; SHOP_WORKER gated by can_view_invoices and can_confirm_bills.

## Proposed models
- Invoice: shop FK, created_by FK user, idempotency_key (unique), total_amount Decimal, status, created_at.
- InvoiceItem: invoice FK, product FK (nullable for historical), product_name (snapshot), quantity Decimal, unit_price Decimal (snapshot), line_total Decimal.

## API routes
- POST /api/invoices/ (create with items array)
- GET /api/invoices/ (list, scoped by shop + can_view_invoices)
- GET /api/invoices/<id>/ (detail)

## Consistency rules
- Server-side price from Product.selling_price; ignore client prices.
- Atomic transaction with select_for_update on products.
- Reject insufficient stock; rollback all.
- Idempotency key header/body; duplicate returns existing invoice.

## Conflicts
- Flutter sends unit_price; backend will ignore and use selling_price (API compatibility conflict: document).
- No customer checkout/payment in this phase.

## Next
Awaiting approval to implement.

## Review-required additions (APPROVE WITH CHANGES)
- Accept legacy unit_price but ignore for calculation.
- Snapshot product name, unit_price, line_total in InvoiceItem.
- Idempotency key unique per shop.
- Atomic transaction + select_for_update; reject negative stock; rollback.
- Worker permissions: can_confirm_bills for create; can_view_invoices for read.
- Decimal quantities.
- No cost price in invoice responses.
