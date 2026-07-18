"""Seed the database with the data currently hard-coded in the app's src/data/stores.js.

Run once after the tables exist:  python -m app.seed
Idempotent: it skips seeding if stores already exist.
"""
import asyncio

from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models import Cuisine, Product, Store

CUISINES = [
    {"id": "ethiopian", "label": "Ethiopian", "flag": "🇪🇹"},
    {"id": "indian", "label": "Indian", "flag": "🇮🇳"},
    {"id": "nigerian", "label": "Nigerian", "flag": "🇳🇬"},
    {"id": "jamaican", "label": "Jamaican", "flag": "🇯🇲"},
    {"id": "mexican", "label": "Mexican", "flag": "🇲🇽"},
    {"id": "korean", "label": "Korean", "flag": "🇰🇷"},
]

STORES = [
    {
        "name": "Lalibela Ethiopian Market",
        "cuisine_id": "ethiopian",
        "origin": "Ethiopia",
        "emoji": "🍲",
        "rating": 4.8,
        "review_count": 312,
        "delivery_fee": 1.99,
        "min_order": 15,
        "delivery_time": "25-35 min",
        "tags": ["Injera", "Berbere", "Teff Flour", "Coffee"],
        "header_bg": ["#2D1A0E", "#5C3317", "#8B4513"],
        "categories": ["Grains & Flours", "Spices & Sauces", "Beverages", "Fresh Produce", "Dairy & Eggs"],
        "products": [
            {"name": "Teff Flour", "price": 8.99, "unit": "2 lb bag", "emoji": "🌾", "category": "Grains & Flours", "description": "Stone-ground whole grain teff flour, the base for authentic injera bread."},
            {"name": "Injera (Fresh)", "price": 6.49, "unit": "Pack of 5", "emoji": "🫓", "category": "Grains & Flours", "description": "Freshly made sourdough flatbread, ready to serve."},
            {"name": "Berbere Spice Blend", "price": 7.29, "unit": "4 oz", "emoji": "🌶️", "category": "Spices & Sauces", "description": "Traditional Ethiopian spice blend with chili, fenugreek, and warming spices."},
            {"name": "Niter Kibbeh", "price": 9.99, "unit": "8 oz jar", "emoji": "🧈", "category": "Dairy & Eggs", "description": "Spiced clarified butter infused with onion, garlic, and cardamom."},
            {"name": "Ethiopian Coffee", "price": 14.99, "unit": "12 oz whole bean", "emoji": "☕", "category": "Beverages", "description": "Single-origin Yirgacheffe beans, medium roast. Bright and fruity."},
            {"name": "Mitmita Powder", "price": 6.49, "unit": "2 oz", "emoji": "🌶️", "category": "Spices & Sauces", "description": "Bird's eye chili blended with cardamom, cloves, and cinnamon. Fiery and aromatic."},
            {"name": "Lentils (Red & Green)", "price": 4.99, "unit": "2 lb bag", "emoji": "🫘", "category": "Grains & Flours", "description": "Essential for misir wot and other Ethiopian stews."},
            {"name": "Tej (Honey Wine)", "price": 11.99, "unit": "750 ml", "emoji": "🍯", "category": "Beverages", "description": "Traditional Ethiopian honey wine with a gentle, sweet flavor."},
        ],
    },
    {
        "name": "Spice Route Indian Grocers",
        "cuisine_id": "indian",
        "origin": "India",
        "emoji": "🌶️",
        "rating": 4.6,
        "review_count": 248,
        "delivery_fee": 2.49,
        "min_order": 20,
        "delivery_time": "30-40 min",
        "tags": ["Basmati Rice", "Ghee", "Masalas", "Paneer"],
        "header_bg": ["#0D2B1A", "#1A5C30", "#2E8B57"],
        "categories": ["Rice & Grains", "Spices & Masalas", "Dairy", "Lentils & Legumes", "Snacks & Sweets"],
        "products": [
            {"name": "Basmati Rice", "price": 12.99, "unit": "5 lb bag", "emoji": "🍚", "category": "Rice & Grains", "description": "Aged long-grain basmati rice from the Himalayan foothills. Fragrant and fluffy."},
            {"name": "Pure Desi Ghee", "price": 16.99, "unit": "32 oz jar", "emoji": "🧈", "category": "Dairy", "description": "Slow-cooked clarified butter from grass-fed cows. Rich and nutty."},
            {"name": "Garam Masala", "price": 5.99, "unit": "3 oz", "emoji": "🫙", "category": "Spices & Masalas", "description": "House-ground whole spice blend: cardamom, cinnamon, cloves, cumin, and more."},
            {"name": "Fresh Paneer", "price": 8.49, "unit": "14 oz block", "emoji": "🧀", "category": "Dairy", "description": "House-made fresh Indian cheese. Firm and perfect for curries or grilling."},
            {"name": "Chana Dal", "price": 4.49, "unit": "2 lb bag", "emoji": "🫘", "category": "Lentils & Legumes", "description": "Split Bengal gram, perfect for dal and halwa."},
            {"name": "Tamarind Paste", "price": 3.99, "unit": "14 oz", "emoji": "🍬", "category": "Spices & Masalas", "description": "Concentrated tamarind for chutneys, curries, and marinades."},
            {"name": "Chakki Atta (Wheat Flour)", "price": 9.99, "unit": "10 lb bag", "emoji": "🌾", "category": "Rice & Grains", "description": "Stone-milled whole wheat flour for soft rotis and chapatis."},
            {"name": "Gulab Jamun Mix", "price": 4.29, "unit": "7 oz box", "emoji": "🟤", "category": "Snacks & Sweets", "description": "Ready-mix for the classic Indian milk-solid dessert. Just fry and soak."},
        ],
    },
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        existing = await db.scalar(select(func.count()).select_from(Store))
        if existing:
            print(f"Stores already present ({existing}); skipping seed.")
            return

        for c in CUISINES:
            db.add(Cuisine(**c))

        for s in STORES:
            products = s.pop("products")
            store = Store(**s, products=[Product(**p) for p in products])
            db.add(store)

        await db.commit()
        print(f"Seeded {len(CUISINES)} cuisines and {len(STORES)} stores.")


if __name__ == "__main__":
    asyncio.run(seed())