"""Custom strategy."""
from uuid import UUID

import jwt
from fastapi_users import BaseUserManager, exceptions
from fastapi_users.authentication import Strategy
from fastapi_users.authentication.strategy.jwt import (  # type: ignore
    JWTStrategyDestroyNotSupportedError,
)
from fastapi_users.jwt import decode_jwt, generate_jwt, SecretType
from authenticity_product.models import User


class JWTStrategy(Strategy[User, UUID]):
    """Custom JWT strategy."""

    def __init__(
        self,
        secret: SecretType,
        lifetime_seconds: int,
        token_audience: list[str] | None = None,
        algorithm: str = "RS256",
        public_key: SecretType | None = None,
    ):
        self.secret = secret
        self.lifetime_seconds = lifetime_seconds
        self.token_audience = token_audience
        self.algorithm = algorithm
        self.public_key = public_key

    @property
    def encode_key(self) -> SecretType:
        """Return the secret key for encoding JWT tokens."""
        return self.secret

    @property
    def decode_key(self) -> SecretType:
        """Return the secret key for decoding JWT tokens."""
        return self.public_key or self.secret

    async def read_token(
        self, token: str | None, user_manager: BaseUserManager[User, UUID]
    ) -> User | None:
        """Read token."""
        if token is None:
            return None

        try:
            data = decode_jwt(
                token,
                self.decode_key,
                self.token_audience if self.token_audience is not None else ["fastapi-users:auth"],
                algorithms=[self.algorithm],
            )
            if (user_id := data.get("sub")) is None:
                return None
        except jwt.PyJWTError:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID):
            return None

    async def write_token(self, user: User) -> str:
        """Write a token to the response."""
        data = {"id": str(user.id), "aud": self.token_audience, "role": user.role}
        return generate_jwt(data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm)

    async def destroy_token(self, token: str, user: User) -> None:
        """Destroy a token from the response."""
        raise JWTStrategyDestroyNotSupportedError()
