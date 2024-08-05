"""http entrypoint file."""

from io import BytesIO

import qrcode
from fastapi import Depends, FastAPI, HTTPException, status
from PIL import Image
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from sqladmin import Admin
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy_utils import register_composites
from starlette.responses import StreamingResponse
from authenticity_product.models import Article, Product, Role
from authenticity_product.schemas import (
    ListProductsOutType,
    ProductInType,
    ProductOutType,
    UserCreate,
    UserRead,
    UserUpdate,
)
from authenticity_product.services.http.admin import (
    AdminAuth,
    ArticleAdmin,
    ProductAdmin,
    UserAdmin,
)
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.db_async import _conn_async, async_session_maker
from authenticity_product.services.http.entrypoint_unites import articles_router
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

# create product endpoint
@app.post(
    "/produits/",
    response_model=ProductOutType,
    status_code=status.HTTP_201_CREATED,
    tags=["produits"],
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
    "/produits/{produit_id}",
    response_model=ProductOutType,
    tags=["produits"],
)
def update_product(
    produit_id: int,
    product: ProductInType,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Update a product."""
    if db_product := db.query(Product).filter(Product.id == produit_id).first():
        db_product.name = product.name
        db_product.description = product.description
        db.commit()
        db.refresh(db_product)
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=db_product.id, name=db_product.name, description=db_product.description
            )
        raise HTTPException(status_code=404)
    raise HTTPException(status_code=404, detail=f"Product not found whith id {produit_id}")


@app.delete(
    "/produits/{produit_id}",
    response_model=ProductOutType,
    tags=["produits"],
)
def delete_product(
    produit_id: int,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Delete a product."""
    if db_product := db.query(Product).filter(Product.id == produit_id).first():
        db.delete(db_product)
        db.commit()
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=produit_id, name=db_product.name, description=db_product.description
            )
    raise HTTPException(status_code=404, detail=f"Product not found whith id {produit_id}")


@app.get(
    "/produits",
    response_model=ListProductsOutType,
    tags=["produits"],
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


@app.get("/produits/{produit_id}", response_model=ProductOutType, tags=["produits"])
def get_product(
    produit_id: int,
    db: Session = Depends(settings.get_db),
) -> ProductOutType:
    """Get a single product."""
    if db_product := db.query(Product).filter(Product.id == produit_id).first():
        if db_product.description and db_product.name and db_product.id:
            return ProductOutType(
                id=db_product.id, name=db_product.name, description=db_product.description
            )
    raise HTTPException(status_code=404, detail=f"Product not found whith id {produit_id}")


@app.get("/get-etiquettes-thermiques/{unite_id}", tags=["unites"])
def generate_pdf(
    unite_id: str,
    db: Session = Depends(settings.get_db),
) -> StreamingResponse:
    article = db.query(Article).filter(Article.id == unite_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    buffer = BytesIO()
    width_mm = 20
    height_mm = 20

    # Convert dimensions to pixels (1 inch = 25.4 mm, 1 inch = 72 points)
    width_px = int(width_mm * 72 / 25.4)
    height_px = int(height_mm * 72 / 25.4)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,  # Adjust this if necessary
        border=4,
    )
    qr.add_data(unite_id)  # Replace with your URL or data
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill="black", back_color="white")

    # Resize the image to the desired size
    img = img.resize((width_px, height_px), Image.Resampling.LANCZOS)

    # Save the QR code image as a PNG file
    img.save("qr_code.png")

    # Save the QR code image to a temporary file
    img_path = "qr_code.png"
    img.save(img_path)

    width_mm = 40
    height_mm = 20

    # Convert dimensions to points (1 point = 1/72 inch; 1 inch = 25.4mm)
    width_pts = width_mm * mm
    height_pts = height_mm * mm
    # Create a PDF and draw the QR code

    c = canvas.Canvas(buffer, pagesize=(width_pts, height_pts))
    c.drawImage(
        img_path, 0, 0, width=height_pts, height=height_pts
    )  # Adjust position and size as needed

    c.setFont("Helvetica", 12)
    c.drawString(height_pts, height_pts / 8, article.product.name.upper())

    c.setFont("Helvetica", 20)
    c.drawString(height_pts, height_pts * 3 / 8, "17 DA")

    c.save()

    # Clean up the temporary file

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=example.pdf"},
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
admin.add_view(ProductAdmin)
admin.add_view(UserAdmin)
admin.add_view(ArticleAdmin)
authentication_backend = AdminAuth(secret_key="secret_key")
admin = Admin(app, settings.engine, authentication_backend=authentication_backend)

app.include_router(articles_router, prefix="/unites", tags=["unites"])
