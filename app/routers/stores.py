import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Store
from app.schemas import StoreDetail, StoreSummary

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreSummary])
async def list_stores(
    cuisine_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Store).where(Store.is_active.is_(True))
    if cuisine_id:
        stmt = stmt.where(Store.cuisine_id == cuisine_id)
    rows = await db.scalars(stmt.order_by(Store.rating.desc()))
    return list(rows)


@router.get("/{store_id}", response_model=StoreDetail)
async def get_store(store_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    store = await db.scalar(
        select(Store).where(Store.id == store_id).options(selectinload(Store.products))
    )
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Store not found")
    return store
