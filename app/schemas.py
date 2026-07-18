import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Cuisine ----
class CuisineOut(ORMModel):
    id: str
    label: str
    flag: str


# ---- Product ----
class ProductOut(ORMModel):
    id: uuid.UUID
    name: str
    price: float
    unit: str | None
    emoji: str | None
    category: str | None
    description: str | None
    in_stock: bool


# ---- Store ----
class StoreSummary(ORMModel):
    id: uuid.UUID
    name: str
    origin: str
    emoji: str | None
    cuisine_id: str | None
    cuisine_label: str | None
    flag: str | None
    rating: float
    review_count: int
    delivery_fee: float
    min_order: float
    delivery_time: str | None
    tags: list[str]
    header_bg: list[str]
    categories: list[str]


class StoreDetail(StoreSummary):
    products: list[ProductOut]


# ---- Auth ----
class RegisterIn(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=6)
    name: str | None = None
    email: str | None = None


class LoginIn(BaseModel):
    phone: str
    password: str


class GoogleAuthIn(BaseModel):
    # The Google ID token (a JWT) obtained by the app from the Google sign-in
    # flow. The server verifies it against Google's public keys.
    id_token: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: uuid.UUID
    phone: str | None
    email: str | None
    name: str | None
    auth_provider: str


# ---- Orders ----
class OrderItemIn(BaseModel):
    product_id: uuid.UUID
    qty: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(ORMModel):
    product_id: uuid.UUID
    name: str
    price: float
    qty: int


class OrderOut(ORMModel):
    id: uuid.UUID
    store_id: uuid.UUID
    status: str
    subtotal: float
    delivery_fee: float
    tax: float
    total: float
    created_at: datetime
    items: list[OrderItemOut]