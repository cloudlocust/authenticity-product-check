"""Authenticity product schemas."""
import uuid

from fastapi_users import schemas
from pydantic import EmailStr


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User read schema."""

    pass


class UserCreate(schemas.CreateUpdateDictModel):
    """User create schema."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    civility: str
    role: str


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""

    pass
