"""Module contains the user service for the FastAPI application."""
import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from authenticity_product.models import User
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.db_async import get_user_db_async
from authenticity_product.services.http.strategy import JWTStrategy


SECRET = "SECRET"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager."""

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        """After register."""
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        """After forgot password."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        """After request verify function, send verification email."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db_async),
) -> AsyncGenerator[UserManager, None]:
    """Async generator to get the user manager."""
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """Jwt strategy function."""
    return JWTStrategy(
        token_audience=["fastapi-users:auth"],
        algorithm="RS256",
        secret=settings.private_key,
        public_key=settings.public_key,
        lifetime_seconds=settings.token_expiration_in_seconds,
    )


auth_backend = AuthenticationBackend(
    name="application_backend",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
