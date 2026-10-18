# PHASE 1 CODE REVIEW

- System check: PASS
- makemigrations --check --dry-run: PASS (no changes detected; DB connection warnings only)
- manage.py test: BLOCKED (PostgreSQL unavailable at localhost:5432)
- Models/relationships: PASS (Product FK Shop, StockAdjustment FK Product/actor)
- Monetary fields Decimal: PASS
- Cost price privacy in public serializer: PASS (excluded from ProductPublicSerializer)
- Stock adjustment transaction + select_for_update: PASS
- Negative stock validation: PASS
- JWT/roles: PASS (configured)
- Cross-shop isolation: PASS (get_queryset filters by effective_shop for owners/workers)
- Public endpoints exclude unpublished: PASS (status=PUBLISHED filter)

## Endpoints
- /api/products/ (list/detail/create/update/delete)
- /api/inventory/ (stock adjustments)

## Notes
- Tests not executed due to DB unavailability.
- No migrations applied.
