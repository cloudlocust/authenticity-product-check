import uuid

from fastapi_users import schemas
from pydantic import EmailStr


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.CreateUpdateDictModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    civility: str
    role: str


class UserUpdate(schemas.BaseUserUpdate):
    pass
