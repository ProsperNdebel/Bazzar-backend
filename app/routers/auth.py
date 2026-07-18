from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import GoogleAuthIn, LoginIn, RegisterIn, TokenOut, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.google_auth import GoogleAuthError, verify_google_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    user = User(
        phone=body.phone,
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Phone or email already registered")
    await db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.phone == body.phone))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/google", response_model=TokenOut)
async def google_auth(body: GoogleAuthIn, db: AsyncSession = Depends(get_db)):
    try:
        identity = verify_google_token(body.id_token)
    except GoogleAuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))

    # Only ever trust a Google-*verified* email. An unverified one could be
    # attacker-controlled, so we neither link on it nor store it — that both
    # prevents account hijacking and avoids colliding with the unique email of
    # a real account.
    trusted_email = identity.email if identity.email_verified else None

    # 1. Returning Google user — matched by the stable google_id.
    user = await db.scalar(select(User).where(User.google_id == identity.google_id))

    if user is None and trusted_email:
        # 2. Verified email matches an existing (e.g. phone) account -> link.
        existing = await db.scalar(select(User).where(User.email == trusted_email))
        if existing is not None:
            existing.google_id = identity.google_id
            if not existing.name and identity.name:
                existing.name = identity.name
            user = existing

    if user is None:
        # 3. Brand new Google account.
        user = User(
            email=trusted_email,
            name=identity.name,
            google_id=identity.google_id,
            auth_provider="google",
        )
        db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        # Rare race: two requests creating the same account at once.
        await db.rollback()
        user = await db.scalar(select(User).where(User.google_id == identity.google_id))
        if user is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Could not link Google account")

    await db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user