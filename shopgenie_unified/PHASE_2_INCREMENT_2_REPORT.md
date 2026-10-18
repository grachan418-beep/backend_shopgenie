# PHASE_2_INCREMENT_2_REPORT

## Files changed
- billing/models.py — added Invoice.request_signature field
- billing/migrations/0002_invoice_request_signature.py — new migration (applied)
- billing/serializers.py — InvoiceCreateSerializer (idempotency_key + items validation)
- billing/views.py — InvoiceViewSet (create/list/retrieve) with atomic invoice creation, stock deduction, idempotency
- billing/urls.py — /api/invoices/ and /api/invoices/<int:pk>/
- shopgenie/urls.py — added api/invoices route
- billing/tests.py — 14 billing endpoint tests

## Migration status
- billing.0001_initial and billing.0002_invoice_request_signature APPLIED to confirmed dev DB.
- makemigrations --check: no pending changes.

## Endpoint contract
POST /api/invoices/ — {idempotency_key, items:[{product, quantity}]}
GET /api/invoices/ — scoped to shop
GET /api/invoices/<id>/ — detail with items

## Pricing & stock
- Server pricing from Product.selling_price; client unit_price ignored; snapshots stored
- Atomic transaction; select_for_update consistent lock order; rollback on insufficient stock
- StockAdjustment audit records created

## Idempotency
- (shop, idempotency_key) unique; request_signature compared; different payload => 409

## Tests
- 26 total executed: 26 passed, 0 failed
- Billing: 14 passed
- Concurrency: not tested (documented limitation)

## Recommendation
APPROVE
