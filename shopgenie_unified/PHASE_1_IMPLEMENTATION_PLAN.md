# PHASE 1 IMPLEMENTATION PLAN — ShopGenie Unified Backend

## Proposed project structure
- shopgenie_unified/
  - shopgenie/ (settings, urls, wsgi, asgi)
  - accounts/ (CustomUser, Shop, auth, permissions)
  - shops/ (shop views/serializers — may merge into accounts)
  - products/ (Product model)
  - inventory/ (StockAdjustment)
  - requirements.txt, .env.example, .gitignore, README.md

## Dependencies
Django 5.2, djangorestframework, djangorestframework-simplejwt, django-filter, psycopg[binary], python-dotenv, django-cors-headers.

## Models & relationships
- CustomUser (AbstractBaseUser+PermissionsMixin), roles CUSTOMER/SHOP_OWNER/SHOP_WORKER, email unique normalized.
- Shop (OneToOne owner, publication status, timestamps).
- Product (FK shop, MRP/selling/cost Decimal, stock, unit, availability).
- StockAdjustment (FK product, actor, delta, reason, timestamp).

## API routes
- /api/auth/register/, /api/auth/login/, /api/auth/refresh/, /api/auth/me/
- /api/shops/, /api/shops/<id>/
- /api/products/, /api/products/<id>/
- /api/inventory/adjustments/

## Env vars
DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DATABASE_URL (or DB_*), CORS_ALLOWED_ORIGINS.

## Migration & testing
Create migrations only after user model configured. Run against Supabase dev DB. Tests per Step 9.

## Risks/assumptions
- One shop per owner (confirmed).
- Customer auth email+password (confirmed).
- MRP field added (confirmed).
- DB is separate dev project (must verify before migrate).
