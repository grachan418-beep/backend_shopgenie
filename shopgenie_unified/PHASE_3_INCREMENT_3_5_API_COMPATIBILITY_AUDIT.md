# PHASE_3_INCREMENT_3_5_API_COMPATIBILITY_AUDIT

## Audit Scope
- Customer Flutter app (`Shopgenie-customer-\flutter_shopgenie`)
- Shop Owner Flutter app (`shopGenie-owner-app\flutter_app`)
- New unified Django backend (`R:\shopgenie backend\shopgenie_unified\`)

This is an audit only. No code, schema, or database changes were made.

---

## 1. Customer Flutter App — Expected API Format

### Customer ProductItem model (`lib/models/product_item.dart`)
| Flutter field | Expected type | Default | JSON key | Backend equivalent |
|---|---|---|---|---|
| id | String | — | id | Product.id (int) — TYPE MISMATCH |
| storeId | String | — | storeId | Product.shop (int FK) — KEY + TYPE MISMATCH |
| storeName | String | — | storeName | Product.store_name (str) — KEY MISMATCH (has store_name) |
| name | String | — | name | Product.name ✓ |
| brand | String | '' | brand | Product.brand ✓ (added in 3.4B) |
| category | String | — | category | Product.category ✓ |
| size | String | '' | size | Product.size ✓ (added in 3.4B) |
| price | double | — | price | Product.selling_price — KEY MISMATCH (has price via serializer) |
| mrp | double | — | mrp | Product.mrp ✓ |
| emoji | String | — | emoji | NOT in backend — MISSING FIELD |
| stock | int | 10 | stock | Product.stock_quantity (Decimal) — KEY + TYPE MISMATCH |
| description | String | — | description | Product.description ✓ |
| inStock | bool | true | inStock | NOT in backend — MISSING FIELD (derivable) |
| confidence | double | 0.95 | confidence | NOT in backend — MISSING FIELD |

### Customer StoreItem model (`lib/models/store_item.dart`)
| Flutter field | Expected type | Default | JSON key | Backend equivalent |
|---|---|---|---|---|
| id | String | — | id | Shop.id (int) — TYPE MISMATCH |
| name | String | — | name | Shop.name ✓ |
| category | String | — | category | Shop.category ✓ |
| distance | String | — | distance | NOT in backend — MISSING FIELD |
| rating | String | — | rating | Shop.rating (Decimal) — TYPE MISMATCH |
| address | String | — | address | Shop.address ✓ |
| emoji | String | — | emoji | NOT in backend — MISSING FIELD |
| selfCheckout | bool | false | selfCheckout | NOT in backend — MISSING FIELD |
| offer | String? | null | offer | NOT in backend — MISSING FIELD |
| description | String? | null | description | Shop.description ✓ |
| lat | double | 12.9250 | lat | NOT in backend — MISSING FIELD |
| lng | double | 77.5220 | lng | NOT in backend — MISSING FIELD |
| hours | String | '8:00 AM - 10:00 PM' | hours | Shop.business_hours — KEY MISMATCH (has hours alias now) |
| phone | String | '+91...' | phone | Shop.phone ✓ |
| followers | int | 384 | followers | NOT in backend — MISSING FIELD |
| isFollowing | bool | false | isFollowing | NOT in backend — MISSING FIELD |

### Customer API usage
- `shop_service.dart`: Uses mock data only (sampleStores, sampleProducts) — NO live API calls
- `product_recognition_service.dart`: baseUrl `http://10.0.2.2:8000`, endpoint `/api/products/recognize/` — AI recognition endpoint NOT implemented (later phase)
- Customer app does NOT currently call `/api/shops/` or `/api/products/`

---

## 2. Shop Owner Flutter App — Expected API Format

### Owner `api_service.dart` (`lib/api_service.dart`)
baseUrl: `http://10.0.2.2:8000/api`

| Flutter call | Endpoint | Method | Request body | Expected response |
|---|---|---|---|---|
| login | /auth/login/ | POST | {username, password} | {access, ...} token |
| getMyShop | /shops/my_shop/ | GET | — | Shop object |
| updateMyShop | /shops/my_shop/ | PATCH | shop fields | Shop object |
| getWorkers | /workers/ | GET | — | [Worker] |
| createWorker | /workers/ | POST | worker fields | Worker object |
| updateWorker | /workers/{id}/ | PATCH | worker fields | Worker object |
| getProducts | /products/ | GET | — | [Product] |
| confirmBill | /billing/invoices/ | POST | {payment_mode, customer_name, customer_phone, items:[{product_id, quantity, unit_price}]} | invoice JSON |

### Owner `models.dart` — InvoiceItem
| Field | Type | JSON key (toJson) |
|---|---|---|
| product | Product | product_id |
| quantity | double | quantity |
| price | double | unit_price |

InvoiceItem.toJson(): `{'product_id': product.id, 'quantity': quantity, 'unit_price': price}`

---

## 3. Comparison Against New Django API

### 3.1 Accounts and Authentication

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| POST /auth/login/ {username, password} → {access} | No /auth/login/ endpoint implemented | HIGH | Implement JWT login endpoint (Simple JWT TokenObtainPair) | No |
| JWT Bearer token in Authorization header | Backend configured for JWT auth ✓ | NONE | N/A | No |

### 3.2 Shop Discovery and Detail

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| GET /shops/my_shop/ | No my_shop endpoint | HIGH | Implement shop detail by authenticated user's shop | No |
| GET /shops/<id>/ | GET /api/shops/<int:pk>/ ✓ | NONE | N/A | No |
| GET /shops/ (published only) | GET /api/shops/ ✓ | NONE | N/A | No |
| Flutter id as String | Backend id as int | MEDIUM | Flutter parser or serializer alias | No |
| rating as String "4.8 ★" | Backend rating as Decimal | MEDIUM | Format on Flutter side or serializer | No |
| hours key | Backend business_hours → hours alias added ✓ | NONE | N/A | No |
| distance, emoji, selfCheckout, offer, lat, lng, followers, isFollowing | NOT in backend | LOW | Add fields or leave as Flutter defaults | Possible |

### 3.3 Product Discovery and Detail

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| GET /products/ | GET /api/products/ ✓ | NONE | N/A | No |
| GET /products/<id>/ | GET /api/products/<int:pk>/ ✓ | NONE | N/A | No |
| search, shop, category filters | search, shop, category ✓ | NONE | N/A | No |
| price key | selling_price → price alias added ✓ | NONE | N/A | No |
| store_id key (String) | shop.id → store_id alias added ✓ | NONE | N/A | No |
| storeName key | shop.name → store_name alias added ✓ | NONE | N/A | No |
| stock (int) key | stock_quantity (Decimal) | MEDIUM | Add stock alias or change Flutter | No |
| inStock (bool) | NOT in backend | LOW | Add computed field or Flutter derives | No |
| brand, size | Added in 3.4B ✓ | NONE | N/A | Yes (applied) |
| emoji, confidence | NOT in backend | LOW | Add fields or Flutter defaults | Possible |

### 3.4 Product Creation and Updates (Owner)

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| POST /products/ | POST /api/products/ ✓ | NONE | N/A | No |
| PATCH /products/<id>/ | PATCH /api/products/<int:pk>/ ✓ | NONE | N/A | No |
| brand, size writable | Added to write serializer ✓ | NONE | N/A | Yes (applied) |
| cost_price excluded from public | cost_price excluded ✓ | NONE | N/A | No |

### 3.5 Inventory Adjustments

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| No explicit inventory API in owner api_service.dart | POST /api/inventory/ {product, delta, reason} | NONE | Backend has endpoint, Flutter may not use it yet | No |
| decimal stock_quantity | Backend stock_quantity Decimal ✓ | NONE | N/A | No |

### 3.6 Billing and Invoices

| Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|
| POST /billing/invoices/ | POST /api/invoices/ | HIGH | Align URL path or add billing alias | No |
| {payment_mode, customer_name, customer_phone, items:[{product_id, quantity, unit_price}]} | {idempotency_key, items:[{product, quantity}]} | HIGH | Align fields: accept payment_mode, customer_name, customer_phone; accept product_id; ignore/never use unit_price | No |
| Server computes totals from selling_price | Backend computes server-side ✓ | NONE | N/A | No |
| Invoice list/detail | GET /api/invoices/, GET /api/invoices/<id>/ ✓ | NONE | N/A | No |
| Idempotency key | idempotency_key ✓ | NONE | N/A | No |

---

## 4. Mismatch Summary

### Critical mismatches (require backend changes before Flutter integration)

| # | Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|---|
| 1 | POST /auth/login/ | No endpoint | HIGH | Implement JWT login | No |
| 2 | GET/PATCH /shops/my_shop/ | No endpoint | HIGH | Implement authenticated shop detail | No |
| 3 | POST /billing/invoices/ | POST /api/invoices/ | HIGH | Add billing URL alias or align path | No |
| 4 | Invoice items {product_id, quantity, unit_price} | {product, quantity} | HIGH | Accept product_id, ignore unit_price for calc | No |
| 5 | Invoice body {payment_mode, customer_name, customer_phone} | {idempotency_key, items} | HIGH | Add optional billing fields | No |

### Moderate mismatches

| # | Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|---|
| 6 | stock (int) | stock_quantity (Decimal) | MEDIUM | Add stock alias or Flutter cast | No |
| 7 | id as String | id as int | MEDIUM | Flutter-side or serializer | No |
| 8 | rating as String | rating as Decimal | MEDIUM | Flutter-side formatting | No |

### Low mismatches (Flutter defaults handle absence)

| # | Flutter expects | Backend actual | Severity | Fix | Migration? |
|---|---|---|---|---|---|
| 9 | emoji, confidence, inStock | NOT in backend | LOW | Add fields or Flutter defaults | Possible |
| 10 | distance, selfCheckout, offer, lat, lng, followers, isFollowing | NOT in backend | LOW | Add fields or Flutter defaults | Possible |

---

## 5. Key Field Mapping Corrections

| Concern | Flutter expects | Backend actual | Status |
|---|---|---|---|
| stock vs stock_quantity | stock (int) | stock_quantity (Decimal) | Alias needed or Flutter cast |
| integer vs decimal | stock int | Decimal | Alias or Flutter cast |
| store_id vs shop | store_id (String) | shop (int FK) | Alias added ✓ |
| price vs selling_price | price (double) | selling_price (Decimal) | Alias added ✓ |
| hours vs business_hours | hours | business_hours | Alias added ✓ |
| brand and size | brand, size | Added in 3.4B ✓ | Applied |
| auth tokens | Bearer JWT | JWT configured ✓ | Endpoint missing |
| server-authoritative pricing | unit_price from client | selling_price from server ✓ | Correct |

---

## 6. Existing Tests and Django Checks

- `python manage.py check`: PASS — no issues (0 silenced)
- `python manage.py makemigrations --check --dry-run`: PASS — no pending changes
- `python manage.py test --noinput`: 62 passed, 0 failed
- No migrations applied during this audit
- No database changes made

---

## 7. Recommended Next Steps (not implemented in this audit)

1. Implement JWT auth login endpoint (`/auth/login/`) to match Flutter `ApiService.login()`
2. Implement `/shops/my_shop/` GET/PATCH for owner shop detail
3. Implement `/workers/` GET/POST/PATCH for worker management
4. Align billing invoice endpoint path and request body with Flutter `confirmBill()`
5. Consider adding `stock` alias to product public serializer
6. Consider adding missing Flutter-only fields (emoji, confidence, inStock, distance, offer, lat/lng) if customer app integrates live API
7. Customer app currently uses mock data only — no live API integration yet

---

## 8. Rules Compliance

- No application code edited ✓
- No Flutter apps modified ✓
- No old backend modified ✓
- No migrations applied during audit ✓
- No database changes made ✓
- No credentials exposed ✓
- No implementation begun ✓
