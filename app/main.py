from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, cuisines, orders, stores


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic now. Run `alembic upgrade head` to create or
    # migrate tables — startup no longer calls create_all, so the two can't
    # disagree about the schema.
    yield


app = FastAPI(title="Bazaar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the Expo dev URL / app origin later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cuisines.router)
app.include_router(stores.router)
app.include_router(orders.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}