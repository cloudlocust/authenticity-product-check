"""Database models for the application."""
import os
from datetime import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import Mapped, relationship, sessionmaker


class Base:
    """Base model class for resources."""

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


DeclarativeBase: DeclarativeMeta = declarative_base(cls=Base)


class Role(DeclarativeBase):
    """Role model."""

    __tablename__ = "role"
    id = Column(Integer(), primary_key=True)
    name = Column(String(), unique=True, nullable=False)
    description = Column(String())


class User(DeclarativeBase, SQLAlchemyBaseUserTableUUID):
    """User model."""

    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    phone = Column(String(), nullable=False)
    civility = Column(String(), nullable=True)
    role: Mapped[str] = Column(String, ForeignKey("role.name"), nullable=False)


DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"


engine = create_async_engine(DATABASE_URL)
_conn = engine.connect()
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async session."""
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Get user database."""
    yield SQLAlchemyUserDatabase(session, User)


class Product(DeclarativeBase):
    """Product class representing a product in the database.

    This class creates a product table with columns for id, name, and description.
    It also defines a representation method to easily view product details.

    Attributes:
        __tablename__ (str): Table name for the product.
        id (Column): Primary key column.
        name (Column): Name of the product, nullable=False.
        description (Column): Description of the product.
        __repr__ (method): Method to display product details in string format.

    """

    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String)

    def __repr__(self) -> str:
        """Return a string representation of the product."""
        return f"<Product(name={self.name})>"


# class Article(Base):
#     __tablename__ = 'articles'
#     id = Column(Integer, unique=True,nullable=False, autoincrement=True)
#     title = Column(String(200), nullable=False)
#     content = Column(String, nullable=False)
#     product_id = Column(Integer, ForeignKey('products.id'))
#     product = relationship("Product", back_populates="articles")
#     def __repr__(self):
#         return f"<Article(title={self.title})>"
#
# Product.articles = relationship("Article", order_by=Article.id, back_populates="product")
