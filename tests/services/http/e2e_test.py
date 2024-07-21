import pytest
from fastapi import status


@pytest.mark.router
@pytest.mark.asyncio
@pytest.mark.usefixtures("db_dependency")
class TestRegister:
    async def test_valid_body(self, test_app_client):
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
