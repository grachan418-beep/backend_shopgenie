# PHASE 2 INCREMENT 1 REVIEW (UPDATED)

Original finding: InvoiceItem could reference a Product from a different Shop.

Files changed:
- billing/models.py (Invoice, InvoiceItem) — unchanged fields
- billing/serializers.py — added InvoiceSerializer with cross-shop validation
- billing/tests.py — added CrossShopValidationTests

Validation logic implemented:
- InvoiceSerializer.validate rejects shop ID not owned by authenticated user's effective shop.
- Every item product must belong to invoice shop; cross-shop rejected with DRF error.
- All items validated, including multi-product invoices.

Test results: 4/4 passed.

Migration consistency check: PASS (no changes detected).
System check: PASS.
Migrations: not applied.

Remaining limitations: no create logic, idempotency, stock deduction, or endpoints yet (Increment 2).

Recommendation: APPROVE
