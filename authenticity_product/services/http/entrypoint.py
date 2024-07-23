"""http entrypoint file."""
from fastapi import Depends, FastAPI, HTTPException, status
from sqladmin import Admin
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy_utils import register_composites
from authenticity_product.models import Product, Role
from authenticity_product.schemas import (
    ListProductsOutType,
    ProductInType,
    ProductOutType,
    UserCreate,
    UserRead,
)
from authenticity_product.services.http.admin import ProductAdmin, UserAdmin
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.db_async import _conn_async, async_session_maker
from authenticity_product.services.http.users import auth_backend, fastapi_users


app = FastAPI()
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # type: ignore
    prefix="/auth",
    tags=["auth"],
)

# create product endpoint
@app.post(
    "/products/create-product",
    response_model=ProductOutType,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductInType,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Create a new product."""
    if instance := db.query(Product).filter(Product.name == product.name).first():
        if instance.description and instance.name and instance.id:
            return ProductOutType(
                id=instance.id, name=instance.name, description=instance.description
            )
        raise HTTPException(status_code=404)
    db_product = Product(name=product.name, description=product.description)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    if db_product.description and db_product.name and db_product.id:
        return ProductOutType(
            id=db_product.id, name=db_product.name, description=db_product.description
        )
    raise HTTPException(status_code=404)


@app.put(
    "/products/{product_id}",
    response_model=ProductOutType,
)
def update_product(
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
        raise HTTPException(status_code=404)
    raise HTTPException(status_code=404, detail=f"Product not found whith id {product_id}")


@app.delete(
    "/products/{product_id}",
    response_model=ProductOutType,
)
def delete_product(
    product_id: int,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Delete a product."""
    if db_product := db.query(Product).filter(Product.id == product_id).first():
        db.delete(db_product)
        db.commit()
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=product_id, name=db_product.name, description=db_product.description
            )
    raise HTTPException(status_code=404, detail=f"Product not found whith id {product_id}")


@app.get(
    "/products",
    response_model=ListProductsOutType,
)
def get_products(
    db: Session = Depends(settings.get_db),
) -> ListProductsOutType:
    """Get all products."""
    return ListProductsOutType(
        products=[
            ProductOutType(id=product.id, name=product.name, description=product.description)
            for product in db.query(Product).all()
            if product.name and product.description and product.id
        ]
    )


@app.get("/products/{product_id}", response_model=ProductOutType)
def get_product(
    product_id: int,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Get a single product."""
    if db_product := db.query(Product).filter(Product.id == product_id).first():
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=db_product.id, name=db_product.name, description=db_product.description
            )
    raise HTTPException(status_code=404, detail=f"Product not found whith id {product_id}")


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


admin = Admin(app, settings.engine)
admin.add_view(ProductAdmin)
admin.add_view(UserAdmin)
