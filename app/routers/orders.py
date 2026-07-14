from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Order, OrderItem, Product, Store, User
from app.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])
settings = get_settings()


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Collapse duplicate product lines into a single qty per product.
    wanted: dict = {}
    for line in body.items:
        wanted[line.product_id] = wanted.get(line.product_id, 0) + line.qty

    products = (
        await db.scalars(select(Product).where(Product.id.in_(list(wanted.keys()))))
    ).all()
    found = {p.id: p for p in products}

    missing = set(wanted) - set(found)
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown product(s): {sorted(map(str, missing))}")

    # Every item must belong to the same store. The cart is single-store by design.
    store_ids = {found[pid].store_id for pid in wanted}
    if len(store_ids) != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "All items must be from the same store")
    store_id = store_ids.pop()

    out_of_stock = [str(pid) for pid in wanted if not found[pid].in_stock]
    if out_of_stock:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Out of stock: {out_of_stock}")

    store = await db.get(Store, store_id)

    # Prices come from the DB, never from the client.
    subtotal = sum((Decimal(str(found[pid].price)) * qty for pid, qty in wanted.items()), Decimal("0"))

    if subtotal < Decimal(str(store.min_order)):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Order below store minimum of {store.min_order}",
        )

    delivery_fee = Decimal(str(store.delivery_fee))
    tax = _money(subtotal * Decimal(str(settings.tax_rate)))
    total = _money(subtotal + delivery_fee + tax)

    order = Order(
        user_id=user.id,
        store_id=store_id,
        status="pending",
        subtotal=_money(subtotal),
        delivery_fee=_money(delivery_fee),
        tax=tax,
        total=total,
        items=[
            OrderItem(
                product_id=pid,
                name=found[pid].name,
                price=_money(Decimal(str(found[pid].price))),
                qty=qty,
            )
            for pid, qty in wanted.items()
        ],
    )
    db.add(order)
    await db.commit()

    order = await db.scalar(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    return order


@router.get("", response_model=list[OrderOut])
async def list_my_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.scalars(
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return list(rows)
