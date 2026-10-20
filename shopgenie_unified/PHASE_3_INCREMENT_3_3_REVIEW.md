# PHASE_3_INCREMENT_3_3_REVIEW

## A. Flutter-to-API field mapping — Customer ProductItem

Backend `GET /api/products/<id>/` public response (`ProductPublicSerializer`):
- `id` (int) → Flutter `id` expects String — TYPE MISMATCH
- `shop` (int FK) → Flutter `storeId` expects String, reads key `store_id` — KEY + TYPE MISMATCH
- `store_name` (string) → Flutter `storeName` reads key `store_name` — MATCH
- `name` → MATCH
- `category` → MATCH
- `description` → MATCH
- `selling_price` (decimal) → Flutter `price` expects double, reads key `price` — KEY MISMATCH
- `mrp` → Flutter `mrp` reads key `mrp` — MATCH
- `stock_quantity` (decimal) → Flutter `stock` expects int, reads key `stock` — KEY + TYPE MISMATCH
- `unit` → Flutter `size` expects string, reads key `size` — KEY MISMATCH
- `image_url` → Flutter `image` reads key `image` — KEY MISMATCH
- `brand` — NOT in backend — MISSING FIELD
- `size` — NOT in backend — MISSING FIELD
- `emoji` — NOT in backend — MISSING FIELD
- `confidence` — NOT in backend — MISSING FIELD
- `inStock` — NOT in backend — MISSING FIELD (derivable from stock_quantity > 0)
- `cost_price` — correctly EXCLUDED from public ✓
- `status` — removed from public serializer ✓

## B. Flutter-to-API field mapping — Customer ShopItem

Backend `GET /api/shops/<id>/` public response (`ShopPublicSerializer`):
- `id` (int) → Flutter `id` expects String — TYPE MISMATCH
- `name` → MATCH
- `category` → MATCH
- `description` → MATCH
- `address` → MATCH
- `phone` → MATCH
- `business_hours` → Flutter `hours` reads key `hours` — KEY MISMATCH
- `rating` (decimal) → Flutter `rating` expects String like "4.8 ★" — KEY + TYPE MISMATCH
- `distance` — NOT in backend — MISSING FIELD
- `emoji` — NOT in backend — MISSING FIELD
- `selfCheckout` — NOT in backend — MISSING FIELD
- `offer` — NOT in backend — MISSING FIELD
- `lat`/`lng` — NOT in backend — MISSING FIELD
- `followers` — NOT in backend — MISSING FIELD
- `isFollowing` — NOT in backend — MISSING FIELD

## C. Security findings (verified from source + tests)

1. Public product queryset: `status=PUBLISHED AND shop__status=PUBLISHED` — PASS
2. Public product detail cannot bypass via direct ID — PASS (404 for unpublished shop products)
3. `cost_price` excluded from public — PASS
4. Owner email/private data not exposed — PASS
5. Owner/worker operations scoped to own shop — PASS (tested)
6. Public filters (`?shop=`, `?category=`, `?search=`) cannot bypass shop visibility — PASS (applied to already-filtered queryset)
7. Unauthenticated read allowed for products and shops — PASS
8. Writes require authentication — PASS

## D. Brand and size schema decision

Flutter `ProductItem` expects `brand` and `size` fields. Backend `Product` model does NOT have them.

Recommendation: This is a genuine compatibility need (Flutter `ProductItem.brand` and `.size` are required fields with default `''`, so the parser tolerates absence, but data would be empty).

Smallest safe change:
- Add `brand = models.CharField(max_length=100, blank=True, default='')` to Product
- Add `size = models.CharField(max_length=50, blank=True, default='')` to Product
- Both nullable-with-default, backward compatible, no data loss
- Requires one migration (`makemigrations products`)

Do NOT implement in this review (per constraints).

## E. Regression verification

- `python manage.py test --noinput`: 48 passed, 0 failed
- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: PASS (no pending changes)
- No migrations applied during this review

## F. Required fixes (for next increment, not implemented here)

1. Add `store_id` alias or adjust serializer to output `store_id` as string (Flutter reads `store_id`)
2. Add `price` alias or map `selling_price` → `price` (Flutter reads `price`)
3. Add `stock` alias or map `stock_quantity` → `stock` (Flutter reads `stock`)
4. Add `size` and `brand` fields to Product model (migration required)
5. Shop: add `hours` alias for `business_hours`, consider `distance`/`rating` formatting
6. Consider `inStock` computed field

## G. Proposed next increment

Increment 3.4: Customer API compatibility layer — serializer aliases (`store_id`, `price`, `stock`, `hours`), optional `brand`/`size` model fields + migration, and Flutter-facing response shape alignment.

Recommendation: **APPROVE WITH CHANGES** — security and visibility are sound; compatibility aliases and brand/size schema need a follow-up increment before Flutter can consume the API directly.
