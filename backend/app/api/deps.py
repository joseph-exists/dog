from collections.abc import AsyncGenerator, Generator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.db import async_session_maker, engine, get_async_session
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def get_async_session_with_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session generator with automatic transaction management.

    Provides a session with an active transaction that:
    - Commits automatically on successful completion
    - Rolls back automatically on exceptions
    - Ensures atomic operations across CRUD functions

    Use this dependency for all write operations (POST, PATCH, DELETE).
    For read-only operations (GET), use AsyncSessionDep instead.

    Example:
        @router.post("/rooms/")
        async def create_room(
            session: AsyncSessionTransactionDep,
            current_user: CurrentUser,
            room_in: RoomCreate,
        ):
            # Transaction active throughout handler
            room = await create_room(session=session, ...)
            # Transaction commits here (on successful return)
            # or rolls back (on exception)
            return room
    """
    async with async_session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                # Transaction automatically rolls back via context manager
                # Re-raise exception for FastAPI error handling
                raise


AsyncSessionTransactionDep = Annotated[
    AsyncSession,
    Depends(get_async_session_with_transaction)
]

TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# Optional OAuth2 - doesn't raise error when no token provided
optional_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def get_optional_current_user(
    session: SessionDep,
    token: str | None = Depends(optional_oauth2),
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        return None
    user = session.get(User, token_data.sub)
    if not user or not user.is_active:
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]


async def get_current_user_from_token(token: str) -> User:
    """
    Validate JWT token and return user.

    Used for WebSocket authentication (can't use Depends() in WebSocket routes).
    """
    from app.core.security import verify_token

    payload = verify_token(token)
    user_id = UUID(payload.get("sub"))

    # Get user from database using async session
    async with async_session_maker() as session:
        result = await session.exec(
            select(User).where(User.id == user_id)
        )
        user = result.one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return user

def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
