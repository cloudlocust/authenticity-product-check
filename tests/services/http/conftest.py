import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from authenticity_product.services.http.entrypoint import app

    yield TestClient(app)
