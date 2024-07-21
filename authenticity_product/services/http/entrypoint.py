"""http entrypoint file."""
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy_utils import register_composites
from authenticity_product.models import Role
from authenticity_product.schemas import UserCreate, UserRead
from authenticity_product.services.http.db_async import _conn_async, async_session_maker
from authenticity_product.services.http.users import auth_backend, fastapi_users


app = FastAPI()
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # type: ignore
    prefix="/auth",
    tags=["auth"],
)


@app.on_event("startup")
async def startup() -> None:
    """Connect to database at app startup required for fastapi_users, and create roles."""
    async with async_session_maker() as session:
        for role_name in ("admin", "user"):
            statement = select(Role).where(Role.name == role_name.lower())
            if not ((await session.execute(statement)).first()):
                session.add(Role(name=role_name.lower()))
                await session.commit()
    register_composites(_conn_async)
