# PHASE_3_INCREMENT_3_8_IDEMPOTENCY_REPORT

## Root cause
The Flutter-compatible invoice endpoint (`POST /api/billing/invoices/`) derived a deterministic idempotency key from shop + items when the client didn't supply one. This caused two separate legitimate purchases of identical items to produce the same key and be treated as a retry of the first purchase, preventing the second invoice from being created.

## Final idempotency design
- **Client-provided key required**: `idempotency_key` is now required in `FlutterInvoiceSerializer`. No server-side deterministic fallback.
- **Retries of same attempt**: Same `idempotency_key` + same payload → existing invoice returned with status 200 (no duplicate stock deduction).
- **Payload mismatch**: Same `idempotency_key` + different payload → HTTP 409 Conflict with `detail` explaining mismatch.
- **Separate purchases**: Different `idempotency_key` values → new invoices even if items are identical. Stock is deducted for each purchase.
- **Shop-scoped**: Uniqueness is `(shop, idempotency_key)` at the model level.
- **Atomic protection**: Nested atomic savepoints handle IntegrityError on concurrent duplicate inserts. The unique constraint prevents race conditions.
- **Payload fingerprinting**: `request_signature` (SHA-256 of sorted canonical items) is stored for comparison on duplicate key hits.

## Files changed
- `billing/flutter_serializers.py` — Made `idempotency_key` required (was optional with default)
- `billing/flutter_views.py` — Removed `_derive_idempotency_key()` method and fallback key generation; `key = validated["idempotency_key"]` directly
- `billing/tests.py` — Added 3 new tests; fixed 2 existing tests to provide `idempotency_key`

## Tests added
1. `test_flutter_missing_idempotency_key_rejected` — Missing key returns 400 with `idempotency_key` error; no invoice created
2. `test_flutter_different_key_same_items_creates_separate_invoice` — Different keys + identical items create separate invoices with different IDs; stock deducted for both
3. `test_flutter_retry_does_not_deduct_stock_twice` — Same key retry returns 200 with same invoice ID; stock only deducted once

## Existing tests preserved
All existing billing tests updated to provide explicit `idempotency_key` where needed. All 91 tests pass.

## Migration status
No schema changes made. `python manage.py makemigrations --check --dry-run` reports no changes. No migrations applied.

## Verification results
- `python manage.py check`: PASS
- `python manage.py makemigrations --check --dry-run`: PASS
- Full test suite: **91 tests, 91 passed, 0 failed**

## Remaining Flutter requirements
The Flutter owner app must be updated to generate and persist a unique `idempotency_key` for each new billing attempt (e.g., UUID) and reuse the same key only when retrying the exact same failed attempt. Without this change, legitimate separate purchases of identical items would be rejected. The backend now correctly enforces this requirement.

## Recommendation
APPROVE — Idempotency corrected. Legitimate separate purchases of identical items now create separate invoices when using different keys. Retry protection and conflict detection preserved.
