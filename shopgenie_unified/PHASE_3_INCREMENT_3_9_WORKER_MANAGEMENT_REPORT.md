# PHASE_3_INCREMENT_3_9_WORKER_MANAGEMENT_REPORT

## Existing worker-related model structure
The `CustomUser` model already supports workers via:
- `role = SHOP_WORKER`
- `assigned_shop` (FK to Shop, related_name="workers")
- `is_worker_active` (bool)
- `can_view_invoices` (bool)
- `can_confirm_bills` (bool)

No schema changes needed. No migration required.

## Required endpoints and request/response formats

### GET /api/workers/
Returns list of workers assigned to the authenticated owner's shop.

Response (200): Array of worker objects
```json
[
  {
    "id": 1,
    "username": "worker1",
    "email": "w@x.com",
    "first_name": "",
    "last_name": "",
    "is_worker_active": true,
    "can_view_invoices": true,
    "can_confirm_bills": true,
    "date_joined": "2026-10-20T..."
  }
]
```

### POST /api/workers/
Creates a new worker for the owner's shop.

Request:
```json
{
  "username": "newworker",
  "email": "nw@x.com",
  "password": "pass12345",
  "first_name": "New",
  "last_name": "Worker",
  "can_view_invoices": true,
  "can_confirm_bills": false
}
```

Response (201): Worker object (no password hash)

### GET /api/workers/<id>/
Returns a single worker's details (only if belonging to owner's shop).

### PATCH /api/workers/<id>/
Updates worker fields (first_name, last_name, is_worker_active, can_view_invoices, can_confirm_bills).

Response (200): Updated worker object

### DELETE /api/workers/<id>/
Deletes a worker. Response (204).

## Permissions and shop-isolation behaviour
- Only authenticated SHOP_OWNER users can access worker endpoints (IsShopOwner permission)
- Workers are scoped to the owner's shop via `assigned_shop`
- Cross-shop access returns 400 (worker not found in owner's shop)
- Customers and workers cannot manage workers (403)
- Unauthenticated requests return 401
- Password hashes are never exposed in responses

## Files changed
- `workers/` — NEW app (created via startapp)
- `workers/serializers.py` — NEW: WorkerSerializer, WorkerCreateSerializer
- `workers/views.py` — NEW: WorkerViewSet (list, retrieve, create, partial_update, destroy)
- `workers/urls.py` — NEW: URL routing
- `shopgenie/urls.py` — EDITED: added `path("api/workers/", include("workers.urls"))`
- `shopgenie/settings.py` — EDITED: added "workers" to INSTALLED_APPS
- `workers/tests.py` — NEW: 13 tests

## Migration needed
No. The existing `CustomUser` model already has all worker-related fields (`assigned_shop`, `is_worker_active`, `can_view_invoices`, `can_confirm_bills`, `role`). No schema changes required. `makemigrations --check --dry-run` reports no changes.

## Test results
- 13 new worker tests: all PASS
- Full test suite: **104 tests, 104 passed, 0 failed**

## Verification
- `python manage.py check`: PASS
- `python manage.py makemigrations --check --dry-run`: PASS
- Full test suite: 104/104 PASS

## Remaining Flutter compatibility issues
- Owner Flutter `api_service.dart` calls `/workers/` (GET/POST/PATCH) which now maps to `/api/workers/` ✓
- Owner Flutter `Worker.fromJson` expects `id`, `username`, `email`, `first_name`, `last_name`, `is_worker_active`, `can_view_invoices`, `can_confirm_bills`, `date_joined` — all present in serializer ✓
- DELETE endpoint was not in Flutter's ApiService but is implemented for completeness
- No migration needed

## Recommendation
APPROVE — Worker management API implemented and verified. All 104 tests pass. No schema changes required.
