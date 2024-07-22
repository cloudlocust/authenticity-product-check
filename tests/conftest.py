import asyncio
import os
import uuid
from typing import AsyncGenerator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from authenticity_product.models import DeclarativeBase, User
from authenticity_product.schemas import UserCreate
from authenticity_product.services.http.db_async import async_session_maker
from authenticity_product.services.http.entrypoint import app
from authenticity_product.services.http.users import UserManager


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def db_dependency_factory(request):
    """Create a database dependency for sqlalchemy tests."""

    from sqlalchemy import create_engine

    # Do not import testing at the top, otherwise it will create problems with request lib
    # https://github.com/nameko/nameko/issues/693
    # https://github.com/gevent/gevent/issues/1016#issuecomment-328529454
    sqlalchemy_testing_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

    engine = create_engine(sqlalchemy_testing_url)

    def make_db_dependency(DeclarativeBase):
        DeclarativeBase.metadata.drop_all(bind=engine)
        DeclarativeBase.metadata.create_all(bind=engine)
        # service = ServiceContainer(Service)
        # provider = get_extension(service, DatabaseSession)
        # # simulate db uris with the first existing one from yml file.
        # provider.setup()

        def clean():
            DeclarativeBase.metadata.drop_all(bind=engine)

        request.addfinalizer(clean)
        return engine

    yield make_db_dependency


@pytest.fixture(scope="module")
def db_dependency(db_dependency_factory):
    engine = db_dependency_factory(DeclarativeBase)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session_db = session()
    yield session_db
    session_db.close_all()


@pytest.fixture(scope="module")
@pytest.mark.asyncio
def get_test_client(db_dependency):
    async def _get_test_client(app: FastAPI):
        async with LifespanManager(app):
            async with httpx.AsyncClient(app=app, base_url="http://app.io") as test_client:
                yield test_client

    return _get_test_client


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def test_app_client(get_test_client) -> AsyncGenerator[httpx.AsyncClient, None]:
    async for client in get_test_client(app):
        yield client


from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def user_manager():
    async with async_session_maker() as session:
        yield UserManager(SQLAlchemyUserDatabase[User, uuid.UUID](session, User))


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def fake_user(db_dependency, user_manager, test_app_client):
    user = await user_manager.create(
        UserCreate(
            **{
                "email": "king.arthur@camelot.bt",
                "first_name": "lake",
                "last_name": "lady",
                "civility": "Mrs",
                "phone": "0101010101",
                "password": "guinevere",
                "role": "admin",
            }
        )
    )
    yield user
    db_dependency.query(User).filter(User.email == "king.arthur@camelot.bt").delete()
    db_dependency.commit()


@pytest.fixture(scope="module")
def client():
    from authenticity_product.services.http.entrypoint import app

    yield TestClient(app)
