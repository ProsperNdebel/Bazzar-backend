# Bazaar API

FastAPI + Postgres backend for the Bazaar app.

## Stack
- FastAPI (async)
- SQLAlchemy 2.0 (async) + asyncpg
- Postgres 16
- JWT auth (phone + password)

## Prerequisites: Postgres running locally

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
# create the role + database that .env.example expects
psql -d template1 -c "CREATE ROLE bazaar LOGIN PASSWORD 'bazaar';" \
                   -c "CREATE DATABASE bazaar OWNER bazaar;"
```

**Ubuntu / Debian:**
```bash
sudo apt install postgresql
sudo -u postgres psql -c "CREATE USER bazaar WITH PASSWORD 'bazaar';" \
                      -c "CREATE DATABASE bazaar OWNER bazaar;"
```

No local Postgres at all? Point `DATABASE_URL` at a free hosted instance
(Neon, Supabase, Railway) instead. Keep the `+asyncpg` in the scheme.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # edit JWT_SECRET

python -m app.seed          # loads the two stores from src/data/stores.js
uvicorn app.main:app --reload
```

Interactive docs at http://localhost:8000/docs

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
- Alembic migrations (drop `create_all` on startup once you have real data)
- Phone OTP instead of password (Twilio / Africa's Talking)
- Stripe (or local rail) payment intent tied to order creation
- Store admin auth + product CRUD
- expo-location driven distance, computed per request
