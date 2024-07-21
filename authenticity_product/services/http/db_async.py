"""DB async file."""
import os
import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from authenticity_product.models import User


DATABASE_URL_ASYNC = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"


engine_async = create_async_engine(DATABASE_URL_ASYNC)
_conn_async = engine_async.connect()
async_session_maker = async_session = sessionmaker(  # type: ignore
    bind=engine_async,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async session generator."""
    async with async_session_maker() as _session:
        yield _session


async def get_user_db_async(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID], None]:
    """Async generator to get the user database."""
    yield SQLAlchemyUserDatabase[User, uuid.UUID](session, User)
