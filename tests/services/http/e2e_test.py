from typing import Any, cast

import jwt
import pytest
from fastapi import status
from fastapi_users.router import ErrorCode
from authenticity_product.models import User
from authenticity_product.services.http.config import settings


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
    async def test_valid_credentials_unverified_with_email(self, fake_user, email, test_app_client):
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

    @pytest.mark.parametrize("phane", ["0664302870", "0664302870"])
    async def test_valid_credentials_unverified_with_phane(self, fake_user, phane, test_app_client):
        data = {
            "username": phane,
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
