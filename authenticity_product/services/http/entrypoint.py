"""http entrypoint file."""
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy_utils import register_composites
from authenticity_product.models import _conn, async_session_maker, Product, Role
from authenticity_product.schemas import (
    ProductInType,
    ProductOutType,
    UserCreate,
    UserRead,
    UserUpdate,
)
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.users import auth_backend, fastapi_users


app = FastAPI()
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
    if instance := db.query(Product).filter(Product.name == product.name).first():
        if instance.description and instance.name and instance.id:
            return ProductOutType(
                id=instance.id, name=instance.name, description=instance.description
            )
        raise Exception("type mismatch for product name or description")
    db_product = Product(name=product.name, description=product.description)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    if db_product.description and db_product.name and db_product.id:
        return ProductOutType(
            id=db_product.id, name=db_product.name, description=db_product.description
        )
    raise Exception("type mismatch for product name or description")


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
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=db_product.id, name=db_product.name, description=db_product.description
            )
        raise Exception("type mismatch for product name or description")
    raise HTTPException(status_code=404, detail="Product not found")
