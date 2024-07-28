"""http entrypoint file admin."""
import os

import jwt
from fastapi import HTTPException
from sqladmin import ModelView, action
from starlette.responses import FileResponse

from authenticity_product.models import Article, Product, User
from authenticity_product.services.http.config import settings
from authenticity_product.services.http.users import fastapi_users


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
    form_columns =  [User.email, User.phone, User.first_name,User.last_name,User.civility, User.role]
class ArticleAdmin(ModelView, model=Article):  # type: ignore
    """Article admin view."""

    column_list = [Article.id, Article.tag,Article.product]
    column_details_list = [ Article.tag, Article.owner_manufacturer]
    form_columns = [ Article.tag, Article.owner_manufacturer,Article.product]
    @action(
        name="print qr code",
        label="Qr code",
        confirmation_message="Are you sure?",
        add_in_detail=True,
    )
    async def print_qr_code(self,request):
        file_path = "/home/khaldi/Downloads/sssssss.pdf"

        if os.path.exists(file_path):
            return FileResponse(path=file_path, filename="your_file.pdf", media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")





from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request



class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        request.session.update({"token": "..."})
        return True
        import requests
        data = {"username": username, "password": password}
        response = requests.post(f'http://127.0.0.1:8000/auth/jwt/login/', data=data)
        res=response.json()
        if tocken := res.get('access_token'):
            decoded = jwt.decode(
                jwt=tocken,
                audience=["fastapi-users:auth"],
                key=settings.public_key,
                algorithms=["RS256"],
            )
            if decoded["role"] == "admin":
               request.session.update({"token": res['access_token']})
               return True
            else: False
        else:
            return False

    async def logout(self, request: Request) -> bool:
        # Usually you'd want to just clear the session
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        # Check the token in depth
        return True