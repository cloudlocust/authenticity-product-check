"""Authenticity product schemas."""
import uuid

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserUpdate(schemas.BaseUserUpdate):
    pass


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User read schema."""

    pass  # pylint: disable=unnecessary-pass


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


class ProductOutType(BaseModel):
    """Product schema."""

    id: int
    name: str
    description: str

    class Config:
        """Orm config."""

        orm_mode = True


class ListProductsOutType(BaseModel):
    """List of products schema."""

    products: list[ProductOutType]

    class Config:
        """Orm config."""

        orm_mode = True


class ProductInType(BaseModel):
    """Product schema."""

    name: str
    description: str

    class Config:
        """Orm config."""

        orm_mode = True


class ArticleCreate(BaseModel):
    """Article schema."""

    tag: str
    owner_manufacturer_email: str
    product_id: int


class ArticleRead(BaseModel):
    """Article read schema."""

    id: str
    tag: str
    owner_manufacturer_id: str | None
    product_id: int

    class Config:
        orm_mode = True


class ListArticlesOutType(BaseModel):
    """List of products schema."""

    articles: list[ArticleRead]

    class Config:
        """Orm config."""

        orm_mode = True

class GenerateListArticleQuery(BaseModel):
    """List of products schema."""
    product_id: int
    created_by_email: str
    nbr_unites: int
    status: str = None