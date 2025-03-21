"""Authenticity product schemas."""
import re
import uuid

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


# Define regex patterns
dz_phone_regex = re.compile(r"^(\+213|0)([567])[0-9]{8}$")  # Algerian phone format
email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserEmailOrPhone(str):
    """Custom type to validate either an Algerian phone number or an email."""

    @classmethod
    def validate(cls, value: str) -> str:
        """Validate whether the input is a valid Algerian phone number or email."""
        if dz_phone_regex.match(value) or email_regex.match(value):
            return cls(value)  # Return an instance of the class
        raise ValueError("Must be a valid Algerian phone number or email address")

    def is_phone(self) -> bool:
        """Check if the stored value is an Algerian phone number."""
        return bool(dz_phone_regex.match(self))

    def is_email(self) -> bool:
        """Check if the stored value is an email address."""
        return bool(email_regex.match(self))


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User read schema."""

    first_name: str
    last_name: str
    phone: str
    civility: str
    role: str


class UserCreate(schemas.CreateUpdateDictModel):
    """User create schema."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    civility: str | None = None
    role: str


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""

    pass  # pylint: disable=unnecessary-pass


class PhoneNumberRequest(BaseModel):
    """Phone number request."""

    phone_number: str
