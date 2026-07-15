# Signals — Road Traffic Signs E-commerce

Django + DRF backend for B2C road signage sales.

## Stack

- Python 3.13 / Django 5.x / Django REST Framework
- PostgreSQL 16
- Redis 7 + Celery (wired, no tasks yet)
- uv (package manager)
- Docker + docker-compose (dev)
- Coolify (production deployment)

## Architecture

Domain / Service / Data pattern (HackSoft Django Styleguide):

```
API views → Services → Domain (pure Python rules)
                ↓
            Repositories (ORM ↔ domain entities)
```

## Quick start (local)

```bash
# 1. Copy env
cp .env.example .env

# 2. Install dependencies
uv sync

# 3. Start Postgres + Redis
docker-compose up db redis -d

# 4. Run migrations
uv run python manage.py migrate

# 5. Create superuser
uv run python manage.py createsuperuser

# 6. Start dev server
uv run python manage.py runserver
```

## Run with Docker (full stack)

```bash
docker-compose up --build
```

## Tests

```bash
# All tests
uv run pytest

# Domain tests only (no DB, very fast)
uv run pytest tests/orders/test_domain.py -v

# With coverage
uv run pytest --cov=. --cov-report=term-missing
```

## API endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/register/` | Register customer |
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/auth/me/` | Current customer |
| GET | `/api/categories/` | List categories |
| GET | `/api/products/` | List products (`?category=slug`) |
| GET | `/api/products/<slug>/` | Product detail |
| POST | `/api/orders/` | Create order (auth or guest) |
| GET | `/api/orders/mine/` | My orders (auth) |
| GET | `/api/orders/<id>/` | Order detail (auth) |

## Django Admin

Available at `/admin/` — manage products, categories, orders, customers.
