# PHASE_3_INCREMENT_3_4B_REVIEW

## Findings

### Customer Flutter `ProductItem` model (read-only reference)
Fields `brand` and `size` are declared with default `''`:
- `this.brand = ''`
- `this.size = ''`
- Both are `final String`, non-nullable but default to empty string
- `fromJson` reads keys `brand` and `size` directly

### Backend `Product` model (current state)
- Does NOT have `brand` or `size` fields
- Has `unit` (PIECE/KG/GRAM/LITER) which partially overlaps with `size` conceptually but is a different field with different semantics

### Compatibility assessment
- Flutter `brand` and `size` default to `''`, so the parser tolerates missing JSON keys without crashing
- However, the customer app would display empty brand/size values, degrading the customer experience
- Backend `unit` field already exists and serves a related but distinct purpose (selling unit type, not product size/variant)

### Smallest safe schema change (if approved)
Add two optional fields to `Product`:

```python
brand = models.CharField(max_length=100, blank=True, default='')
size = models.CharField(max_length=50, blank=True, default='')
```

Rationale:
- `blank=True, default=''` keeps existing products valid (no data migration needed)
- Backward compatible — no NOT NULL constraint violation
- Public serializer can expose them without exposing internal information
- Product-management APIs (create/update) can accept them naturally

### Migration impact
- One new migration (`makemigrations products`) adding two nullable-with-default columns
- No data migration required; existing rows get `''`
- Safe to apply to the separate Supabase development database

### Test plan (for implementation increment)
- Public product response includes `brand` and `size` when set
- Existing products without brand/size return `''`
- Product create/update accepts brand/size
- Existing 55-test suite still passes

### Fields not addressed in this review
- `emoji`, `confidence`, `inStock` (Flutter-only / derived fields)
- Flutter `id` as String vs backend int (documented in 3.3 review)

## Verification (pre-implementation)
- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: PASS (no pending changes)
- Existing test suite: 55 passed, 0 failed

## Recommendation: APPROVE WITH CHANGES

The schema change is safe and backward compatible. Proceed to implementation increment only if the product team confirms brand/size are needed for customer-facing display. Otherwise, the existing defaults (`''`) are sufficient and no schema change is strictly required.
