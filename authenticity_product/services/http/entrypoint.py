"""http entrypoint file."""
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy_utils import register_composites
from authenticity_product.models import _conn, async_session_maker, Product, Role, User
from authenticity_product.schemas import (
    ProductInType,
    ProductOutType,
    UserCreate,
    UserRead,
    UserUpdate,
)
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.users import (
    auth_backend,
    current_active_user,
    fastapi_users,
)


app = FastAPI()
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
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


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    """Authenticated route."""
    return {"message": f"Hello {user.email}!"}


@app.get("/health")
def read_root() -> Any:
    """Read root."""
    return {"Hello": "World"}


@app.on_event("startup")
async def startup() -> None:
    """Connect to database at app startup required for fastapi_users, and create roles."""
    async with async_session_maker() as session:
        for role_name in ("admin", "user"):
            statement = select(Role).where(Role.name == role_name.lower())
            if not ((await session.execute(statement)).first()):
                session.add(Role(name=role_name.lower()))
                await session.commit()
    register_composites(_conn)


# create product endpoint
@app.post(
    "/products/create-product",
    response_model=ProductOutType,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product: ProductInType,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Create a new product."""
    db_product = Product(name=product.name, description=product.description)
    if instance := db.query(Product).filter(Product.name == product.name).first():
        return instance
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# update product endpoint
@app.put(
    "/products/{product_id}",
    response_model=ProductOutType,
)
async def update_product(
    product_id: int,
    product: ProductInType,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Update a product."""
    if db_product := db.query(Product).filter(Product.id == product_id).first():
        db_product.name = product.name
        db_product.description = product.description
        db.commit()
        db.refresh(db_product)
        return db_product
    raise HTTPException(status_code=404, detail="Product not found")
