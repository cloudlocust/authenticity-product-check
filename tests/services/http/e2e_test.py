from typing import Any, cast

import jwt
import pytest
from fastapi import status
from fastapi_users.router import ErrorCode
from authenticity_product.models import Product, User
from authenticity_product.schemas import ProductInType, ProductOutType
from authenticity_product.services.http.config import settings


class TestProduct:
    def test_create_product_if_not_exist(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        json = {"name": "Test Product", "description": "This is a test product"}
        response = client.post("/products/create-product", json=json)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == "Test Product"
        assert data["description"] == "This is a test product"
        row = db_dependency.query(Product).filter_by(id=data["id"]).first()
        assert row is not None
        assert row.name == "Test Product"
        assert row.description == "This is a test product"

    def test_create_product_if_exist(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        db_dependency.add(Product(name="Test Product", description="This is a test product"))
        db_dependency.commit()
        json = {"name": "Test Product", "description": "This is a test product"}
        response = client.post("/products/create-product", json=json)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == data["id"]
        assert data["name"] == "Test Product"
        assert data["description"] == "This is a test product"
        assert db_dependency.query(Product).count() == 1

    def test_update_product(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)

        db_dependency.add(Product(name="Test Product", description="This is a test product"))
        db_dependency.commit()

        product_id = db_dependency.query(Product).first().id
        json = {"name": "Updated Test Product", "description": "This is an updated test product"}
        response = client.put(f"/products/{product_id}", json=json)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Updated Test Product"
        assert data["description"] == "This is an updated test product"
        row = db_dependency.query(Product).filter_by(id=product_id).first()
        assert row is not None
        assert row.name == "Updated Test Product"
        assert row.description == "This is an updated test product"

    def test_update_product_not_found(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        json = {"name": "Updated Test Product", "description": "This is an updated test product"}
        response = client.put(f"/products/5", json=json)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Product not found"

    def test_delete_product(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        product = Product(name="Test Product", description="This is a test product")
        db_dependency.add(product)
        db_dependency.commit()
        product_id = db_dependency.query(Product).filter(Product.name == "Test Product").first().id
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": product.id,
            "name": "Test Product",
            "description": "This is a test product",
        }
        assert db_dependency.query(Product).count() == 0

    @pytest.mark.parametrize("product_id", [2, 3, 4])
    def test_product_not_found(self, client, product_id, db_dependency):
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 404

    def test_get_products(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        db_dependency.add(Product(name="Test Product 1", description="This is a test product 1"))
        db_dependency.add(Product(name="Test Product 2", description="This is a test product 2"))
        db_dependency.commit()
        response = client.get("/products")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["products"][0]["name"] == "Test Product 1"
        assert response.json()["products"][1]["name"] == "Test Product 2"
        assert len(response.json()["products"]) == 2

    def test_get_products_empty(self, client, db_dependency, request):
        response = client.get("/products")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["products"] == []

    def test_get_product(self, client, db_dependency, request):
        def clean():
            db_dependency.query(Product).delete()
            db_dependency.commit()

        request.addfinalizer(clean)
        product = Product(name="Test Product", description="This is a test product")
        db_dependency.add(product)
        db_dependency.commit()
        product_id = db_dependency.query(Product).filter(Product.name == "Test Product").first().id
        response = client.get(f"/products/{product_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Test Product"
        assert response.json()["description"] == "This is a test product"
        assert "id" in response.json()

    def test_get_product_not_found(self, client, db_dependency, request):
        response = client.get(f"/products/5")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Product not found"


@pytest.mark.router
@pytest.mark.asyncio
@pytest.mark.usefixtures("db_dependency")
class TestRegister:
    async def test_valid_body(self, test_app_client, db_dependency):
        json = {
            "email": "user@example.com",
            "password": "string",
            "first_name": "string",
            "last_name": "string",
            "phone": "string",
            "civility": "string",
            "role": "admin",
        }
        response = await test_app_client.post("/auth/register", json=json)
        assert response.status_code == status.HTTP_201_CREATED
        res_db = db_dependency.query(User).filter_by(email="user@example.com").first() is not None
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data
        assert data["id"] is not None

    async def test_empty_body(self, test_app_client):
        response = await test_app_client.post("/auth/register", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_email(self, test_app_client):
        json = {
            "password": "string",
            "first_name": "string",
            "last_name": "string",
            "phone": "string",
            "role": "admin",
        }
        response = await test_app_client.post("/auth/register", json=json)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_password(self, test_app_client):
        json = {
            "email": "king.arthur@camelot.bt",
            "first_name": "string",
            "last_name": "string",
            "phone": "string",
            "role": "admin",
        }
        response = await test_app_client.post("/auth/register", json=json)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_wrong_email(self, test_app_client):
        json = {
            "email": "king.arthur",
            "first_name": "string",
            "last_name": "string",
            "phone": "string",
            "role": "admin",
        }
        response = await test_app_client.post("/auth/register", json=json)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("email", ["king.arthur@camelot.bt", "King.Arthur@camelot.bt"])
    async def test_existing_user(self, fake_user, email, test_app_client):
        json = {
            "email": email,
            "first_name": "king",
            "last_name": "arthur",
            "civility": "Mr",
            "phone": "0101010101",
            "password": "guinevere",
            "role": "admin",
        }
        response = await test_app_client.post("/auth/register", json=json)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == ErrorCode.REGISTER_USER_ALREADY_EXISTS


@pytest.mark.router
@pytest.mark.asyncio
class TestLogin:
    async def test_empty_body(self, test_app_client):
        response = await test_app_client.post("/auth/jwt/login", data={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_username(self, test_app_client):
        data = {"password": "guinevere"}
        response = await test_app_client.post("/auth/jwt/login", data=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_password(self, test_app_client):
        data = {"username": "king.arthur@camelot.bt"}
        response = await test_app_client.post("/auth/jwt/login", data=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_not_existing_user(self, test_app_client):
        data = {"username": "lancelot@camelot.bt", "password": "guinevere"}
        response = await test_app_client.post("/auth/jwt/login", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = cast(dict[str, Any], response.json())
        assert data["detail"] == ErrorCode.LOGIN_BAD_CREDENTIALS

    async def test_wrong_password(self, test_app_client, fake_user):
        data = {"username": "king.arthur@camelot.bt", "password": "percival"}
        response = await test_app_client.post("/auth/jwt/login", data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = cast(dict[str, Any], response.json())
        assert data["detail"] == ErrorCode.LOGIN_BAD_CREDENTIALS

    @pytest.mark.parametrize("email", ["king.arthur@camelot.bt", "King.Arthur@camelot.bt"])
    async def test_valid_credentials_unverified(self, fake_user, email, test_app_client):
        data = {
            "username": email,
            "password": "guinevere",
        }
        response = await test_app_client.post("/auth/jwt/login", data=data)
        assert response.status_code == status.HTTP_200_OK
        decoded = jwt.decode(
            jwt=response.json()["access_token"],
            audience=["fastapi-users:auth"],
            key=settings.public_key,
            algorithms=["RS256"],
        )
        assert decoded["role"] == "admin"
        assert decoded["id"] == str(fake_user.id)
        assert decoded["aud"] == ["fastapi-users:auth"]
