# PHASE_3_INCREMENT_3_2_REVIEW

## A. Existing product APIs (verified from source)

**Model** (`products.models.Product`):
- Fields: id, shop (FK), name, category, description, mrp, selling_price, cost_price, stock_quantity, unit, image_url, status (DRAFT/PUBLISHED/ARCHIVED), timestamps
- No `brand`, `size`, or `store_name` fields

**Endpoints** (`/api/products/`):
- List and detail via `ProductViewSet` (ModelViewSet)
- Permission: `IsAuthenticatedOrReadOnly` (public read allowed)
- Public queryset: `status=PUBLISHED` only
- Owner/worker queryset: own shop only
- `ProductPublicSerializer` exposes: id, shop, name, category, description, mrp, selling_price, stock_quantity, unit, image_url, status (cost_price excluded ✓)
- `ProductOwnerSerializer` also exposes cost_price (owner only)

**Existing tests**: `products.tests.ProductApiTests` — covers create, price validation, public cost-price privacy, owner write, customer write block, unauth list, cross-shop isolation

## B. Customer Flutter app expectations (read-only reference)

**`ProductItem` model** (`flutter_shopgenie/lib/models/product_item.dart`):
- id (string), storeId (string), storeName (string), name, brand, category, size, price, mrp, emoji, stock (int), description, inStock (bool), confidence

**`Product` model** (recognition):
- id, name, brand, category, size, price, image, emoji, confidence, storeId, storeName

**Key expectations:**
- `price` = selling price (not mrp)
- `storeId` / `storeName` — shop identity as string, not bare integer FK
- `brand`, `size` — not present on backend Product model
- `stock` + `inStock` — derived from stock_quantity
- `confidence` — recognition-related (not a backend product field)

## C. Public product visibility — GAPS IDENTIFIED

1. **Product list does NOT filter by shop publication status.** A `PUBLISHED` product belonging to a `DRAFT` or `SUSPENDED` shop would still appear in public results. Must add `shop__status=Shop.Status.PUBLISHED` to public queryset.
2. **Product detail has the same gap** — `get_queryset` for public returns only `status=PUBLISHED` products, but doesn't verify the shop is published.
3. **No search/filter backends** declared on `ProductViewSet`. Despite global `DEFAULT_FILTER_BACKENDS`, the viewset has no `filterset_fields`/`search_fields`, so `?search=` and `?shop=`/`?category=` won't work.
4. **No `store_name` field** in public response. Flutter expects `storeName` (string) and `storeId` (string); API returns bare integer `shop` FK.
5. **`status` field exposed publicly** — internal field, harmless but not customer-facing.
6. **No `brand` or `size` fields** on the model; Flutter `ProductItem` expects both.

## D. Safe product fields

**Safe to expose (public):** id, name, category, description, mrp, selling_price (as `price`), stock_quantity (as `stock` + derived `inStock`), unit, image_url, shop id + store_name

**Must NOT expose:** cost_price (already excluded ✓), owner email/account details, internal audit fields, `status` (recommend removing from public serializer)

## E. Search and filtering — proposed (no new schema)

- `?search=` — search by `name` and `category`
- `?shop=<id>` — filter by shop (must still enforce shop published status)
- `?category=<value>` — filter by category
- Pagination: already configured globally (`PAGE_SIZE=20`)

## F. Proposed API contract (reuse existing routes)

**`GET /api/products/`** — paginated list
- Query: `search`, `shop`, `category`, `ordering`, `page`
- Response: `{ count, next, previous, results: [...] }`
- Only products where `status=PUBLISHED` AND `shop.status=PUBLISHED`
- Public fields only (no cost_price)

**`GET /api/products/<id>/`** — detail
- Only if product AND shop are PUBLISHED
- 404 otherwise

## G. Required code changes

1. `products/views.py` — Update `ProductViewSet.get_queryset()`:
   - Public: `qs.filter(status=PUBLISHED, shop__status=Shop.Status.PUBLISHED)`
   - Add `filter_backends`, `filterset_fields = ["shop", "category"]`, `search_fields = ["name", "category"]`, `ordering_fields`
2. `products/serializers.py` — `ProductPublicSerializer`:
   - Add read-only `store_name` (source: `shop.name`)
   - Remove `status` from public fields
   - Keep cost_price excluded
3. `products/urls.py` — No change needed (reuse `/api/products/`)

## H. Proposed schema changes (require separate review — NOT implemented here)

- Add `brand` (CharField) and `size` (CharField) to Product model — Flutter `ProductItem` expects both. This is a genuine compatibility need, not convenience. Would require a migration.

## I. Test plan

- Public listing excludes DRAFT/ARCHIVED products
- Products from unpublished (DRAFT/SUSPENDED) shops hidden in list and detail
- Search by name and category works
- Filter by shop ID works
- Pagination works (count, next, previous, results)
- cost_price never in public response
- store_name present in public response
- Cross-shop owner isolation preserved
- Regression: existing 36 tests still pass

## J. Risks & compatibility

- Changing public field set (`status` removal, `store_name` addition) could affect Flutter clients expecting old shape — but Flutter currently uses mock data, so risk is low
- Adding `brand`/`size` requires migration — flagged for separate review
- Default `IsAuthenticated` permission must not be tightened on product read views

## Verification (pre-implementation)
- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: PASS (no pending changes)
- Existing test suite: 36 passed, 0 failed (from prior run)

Recommendation: **APPROVE WITH CHANGES** — proceed to implement visibility fix, `store_name`, search/filter, and pagination; brand/size schema change requires separate review before implementation.
