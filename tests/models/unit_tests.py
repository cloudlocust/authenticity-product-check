from unittest.mock import Mock

from pytest import fixture
from authenticity_product.models import Product


@fixture
def product():
    return Product(name="Laptop", description="Electronics")


def test_product_repr(product):
    # Test 1: Check if the __repr__ method returns a string
    assert isinstance(product.__repr__(), str)

    # Test 2: Ensure the string contains the product name
    assert "Laptop" == product.__repr__().split("(")[0].strip()


def test_product_init():
    # Test 3: Check if product is initialized correctly
    product = Product(name="Phone", description="Device")
    assert product.name == "Phone"
    assert product.description == "Device"


def test_product_name_validation():
    # Test 4: Validate name attribute
    product = Product(name="", description="test")
    assert product.name is None

    product = Product(name="   valid   ", description="test")
    assert product.name == "valid"


def test_product_description_validation():
    # Test 5: Validate description attribute
    product = Product(name="Name", description="")
    assert product.description is None

    product = Product(name="Name", description="  valid  ")
    assert product.description == "valid"
