import asyncio
import os
from typing import AsyncGenerator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker
from authenticity_product.models import DeclarativeBase
from authenticity_product.services.http.entrypoint import app


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
