"""http entrypoint file admin."""
import os

import jwt
import requests
from fastapi import HTTPException
from sqladmin import action, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import FileResponse
from authenticity_product.models import Article, Product, User
from authenticity_product.services.http.config import settings


class ProductAdmin(ModelView, model=Product):  # type: ignore
    """Product admin view."""

    column_list = [Product.id, Product.name, Product.description]
    form_columns = [Product.name, Product.description]


class UserAdmin(ModelView, model=User):  # type: ignore
    """Product admin view."""

    can_create = False
    column_list = [User.email, User.phone, User.first_name, User.role]
    column_details_list = [
        User.email,
        User.phone,
        User.first_name,
        User.last_name,
        User.role,
    ]
    column_searchable_list = [User.email, User.phone, User.first_name, User.last_name]
    form_columns = [
        User.email,
        User.phone,
        User.first_name,
        User.last_name,
        User.civility,
        User.role,
    ]


class ArticleAdmin(ModelView, model=Article):  # type: ignore
    """Article admin view."""
    name_plural="Unites"
    column_list = [Article.id, Article.tag, Article.product]
    column_details_list = [Article.tag, Article.owner_manufacturer]
    form_columns = [Article.tag, Article.owner_manufacturer, Article.product]

    @action(
        name="print qr code",
        label="Qr code",
        confirmation_message="Are you sure?",
        add_in_detail=True,
    )
    async def print_qr_code(self, request):
        """Print qr code for the article."""
        file_path = "/home/khaldi/Downloads/sssssss.pdf"

        if os.path.exists(file_path):
            return FileResponse(
                path=file_path, filename="your_file.pdf", media_type="application/pdf"
            )
        raise HTTPException(status_code=404, detail="File not found")


class AdminAuth(AuthenticationBackend):
    """Admin authentication backend."""

    async def login(self, request: Request) -> bool:
        """Login user."""
        form = await request.form()
        username, password = form["username"], form["password"]
        data = {"username": username, "password": password}
        response = requests.post(
            f'https://{os.environ["DNS_DOMAIN"]}/auth/jwt/login/', data=data, timeout=10
        )
        res = response.json()
        if tocken := res.get("access_token"):
            decoded = jwt.decode(
                jwt=tocken,
                audience=["fastapi-users:auth"],
                key=settings.public_key,
                algorithms=["RS256"],
            )
            if decoded["role"] == "admin":
                request.session.update({"token": res["access_token"]})
                return True
            return False
        return False

    async def logout(self, request: Request) -> bool:
        """Logout user."""
        # Usually you'd want to just clear the session
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Authenticate user."""

        if request.session.get("token"):
            return False
        # Check the token in depth
        return True
