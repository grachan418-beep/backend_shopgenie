# PHASE_3_INCREMENT_3_1_REVIEW

## Existing functionality (verified from source)
- Shop model (`accounts.models.Shop`): fields name, category, description, address, phone, business_hours, status (DRAFT/PUBLISHED/SUSPENDED), rating, owner (OneToOne CustomUser), timestamps.
- Product endpoints exist under `/api/products/` with:
  - `ProductPublicSerializer` exposing id, shop, name, category, description, mrp, selling_price, stock_quantity, unit, image_url, status (cost_price excluded — good).
  - Public list/detail filters to `status=PUBLISHED` only.
  - Owner/worker list filtered to their own shop.
  - Permissions: `IsAuthenticatedOrReadOnly`; write restricted to shop owner/worker.
- `shops` app exists but is an empty placeholder (models.py, views.py stubs only). No shop serializer, views, or URLs exist.
- No shop listing, search, or detail endpoints anywhere.
- `REST_FRAMEWORK` default permission is `IsAuthenticated`; no pagination configured.

## Missing functionality (Phase 3 Increment 3.1)
- Shop public listing endpoint (published shops only).
- Shop public detail endpoint.
- Shop search/filter by name and category.
- Shop public serializer exposing only customer-safe fields.
- Pagination for shop listing.
- Tests for public shop listing/details, inactive shop exclusion, private-data protection, search, and unauthenticated access.

## Proposed endpoints (consistent with existing `/api/` style)
- `GET /api/shops/` — list published shops; query params: `search` (name/category), `category`; paginated.
- `GET /api/shops/<int:pk>/` — detail of a single published shop.

## Proposed response shapes
List item:
```json
{ "id": 1, "name": "...", "category": "...", "description": "...", "address": "...", "phone": "...", "business_hours": "...", "rating": "4.80", "status": "PUBLISHED" }
```
Detail: same fields plus `created_at`, `updated_at`.

Never exposed: owner user details, email, internal shop metrics beyond rating, unpublished status details.

## Required code changes
- `shops/serializers.py`: `ShopPublicSerializer` with public-safe fields only.
- `shops/views.py`: `ShopViewSet` (list, retrieve), queryset `status=PUBLISHED`, permission `AllowAny` for read (overrides default `IsAuthenticated`), pagination.
- `shops/urls.py`: register `/api/shops/` and `/api/shops/<int:pk>/`.
- `shopgenie/urls.py`: include `shops.urls` under `api/shops/`.
- `shopgenie/settings.py`: add default pagination (`PAGE_SIZE`, `DEFAULT_PAGINATION_CLASS`).

## Proposed schema changes
None. Shop model already has all fields needed for public discovery. Status field supports published filtering.

## Test plan
- Public shop listing returns only PUBLISHED shops; DRAFT/SUSPENDED excluded.
- Shop detail returns public fields only; 404 for unpublished/nonexistent shop.
- Search by name and category filters results.
- Unauthenticated access allowed for list/detail.
- Pagination applied to listing.
- Owner cannot expose another owner's unpublished shop via detail.

## Risks & compatibility
- Default `IsAuthenticated` permission must be overridden on shop views or public discovery breaks for unauthenticated Flutter customers.
- No pagination currently configured; add DRF pagination to avoid unbounded lists.
- Product public browsing already exists; no product changes needed for this increment.

## Verification results
- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: PASS (no pending changes)
- Existing test suite: 26 passed, 0 failed
- No schema changes required; migrations not applied.

Recommendation: APPROVE WITH CHANGES — add pagination setting and AllowAny override on shop read views before implementation.
