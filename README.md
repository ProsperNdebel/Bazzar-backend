# Bazaar API

FastAPI backend for the Bazaar app. Runs on **SQLite in development** (zero setup)
and **Postgres in production**, from one codebase.

## Stack
- FastAPI (async)
- SQLAlchemy 2.0 (async)
- SQLite (dev, via aiosqlite) / Postgres (prod, via asyncpg)
- JWT auth (phone + password)

## Run (development, SQLite)

No database server needed. SQLite is a local file.

```bash
python -m venv .venv && source .venv/bin/activate   # use Python 3.13
pip install -r requirements.txt

cp .env.example .env        # edit JWT_SECRET; leave DATABASE_URL unset for SQLite

python -m app.seed          # creates ./bazaar.db and loads the starter stores
uvicorn app.main:app --reload
```

Interactive docs at http://localhost:8000/docs

To start over, delete the file: `rm bazaar.db && python -m app.seed`.

## Run (production, Postgres)

Set `DATABASE_URL` to a Postgres URL and everything else is identical:

```bash
export DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/DBNAME
python -m app.seed
uvicorn app.main:app
```

Managed Postgres (Neon, Supabase, Railway, Render) all give you a URL like this.
Keep the `+asyncpg` in the scheme.

## How one schema runs on both engines
The models use portable column types so nothing is Postgres-only:
- `Uuid` -> native `uuid` on Postgres, `CHAR(32)` on SQLite
- `JSON` (for `tags`, `categories`, `header_bg`) -> JSON on both, instead of a
  Postgres-only `ARRAY`

That avoids the classic "SQLite doesn't support UUID" crash you get when a
Postgres-shaped schema is pointed at SQLite. On SQLite, foreign keys are enabled
per connection so `ON DELETE CASCADE` behaves like it does on Postgres.

One caveat to know: SQLite is a single-writer file, so it will not surface
concurrency issues (lock contention, race conditions) that Postgres would. Dev
on SQLite is fine; load-test and stage on Postgres before trusting behavior under
real traffic.

## Endpoints
| Method | Path              | Auth | Purpose                                  |
|--------|-------------------|------|------------------------------------------|
| GET    | /health           | no   | Liveness check                           |
| GET    | /cuisines         | no   | Cuisine / origin filter list             |
| GET    | /stores           | no   | List active stores (`?cuisine_id=`)      |
| GET    | /stores/{id}      | no   | Store detail with products               |
| POST   | /auth/register    | no   | Create account, returns JWT              |
| POST   | /auth/login       | no   | Log in, returns JWT                      |
| GET    | /auth/me          | yes  | Current user                             |
| POST   | /orders           | yes  | Place order (totals recomputed server-side) |
| GET    | /orders           | yes  | Order history                            |

## Why checkout is server-authoritative
`POST /orders` accepts only `{product_id, qty}` pairs. Prices, delivery fee,
tax (TAX_RATE), and the store minimum are all read from the database and
recomputed on the server. The client's idea of the total is never trusted.

## Wiring the app to this
In `src/data/stores.js`, replace the static `STORES` export with a fetch to
`GET /stores`. The response shape matches the fields the screens already read.

## Next steps
- Alembic migrations (drop `create_all` on startup once you have real data).
  Note: with two backends, generate migrations against Postgres, since that is
  what production runs.
- Phone OTP instead of password (Twilio / Africa's Talking)
- Stripe (or local rail) payment intent tied to order creation
- Store admin auth + product CRUD
