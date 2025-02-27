"""http entrypoint file."""
from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import select
from sqlalchemy_utils import register_composites
from authenticity_product.models import Role
from authenticity_product.schemas import UserCreate, UserRead, UserUpdate
from authenticity_product.services.http.admin import AdminAuth, UserAdmin
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.db_async import _conn_async, async_session_maker
from authenticity_product.services.http.users import auth_backend, fastapi_users


app = FastAPI(
    title="Product Authenticity",
)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # type: ignore
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
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


settings.init_app(app)
admin = Admin(app, settings.engine)
admin.add_view(UserAdmin)
authentication_backend = AdminAuth(secret_key="secret_key")
admin = Admin(app, settings.engine, authentication_backend=authentication_backend)
