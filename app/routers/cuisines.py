from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Cuisine
from app.schemas import CuisineOut

router = APIRouter(prefix="/cuisines", tags=["cuisines"])


@router.get("", response_model=list[CuisineOut])
async def list_cuisines(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Cuisine).order_by(Cuisine.label))
    return list(rows)
