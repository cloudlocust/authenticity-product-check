"""Database models for the application."""
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped


class Base:
    """Base model class for resources."""

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


DeclarativeBase = declarative_base(cls=Base)


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
