# Test valid Algerian phone numbers
import pytest
from authenticity_product.schemas import UserEmailOrPhone


@pytest.mark.parametrize(
    "phone",
    ["+213555555555", "+213666666666", "+213777777777", "0555555555", "0666666666", "0777777777"],
)
def test_valid_algerian_phone_numbers(phone):
    user_input = UserEmailOrPhone.validate(phone)
    assert user_input.is_phone() is True
    assert user_input.is_email() is False


# Test invalid Algerian phone numbers
@pytest.mark.parametrize(
    "phone",
    [
        "+21355555555",  # Too short
        "+2135555555555",  # Too long
        "+213455555555",  # Invalid prefix (4)
        "+213855555555",  # Invalid prefix (8)
        "055555555",  # Too short
        "05555555555",  # Too long
        "0455555555",  # Invalid prefix (4)
        "0855555555",  # Invalid prefix (8)
        "+213 55 555 555",  # Contains spaces
        "+213-555-555-55",  # Contains hyphens
        "ABCDEFGHIJ",  # Not a number
    ],
)
def test_invalid_algerian_phone_numbers(phone):
    with pytest.raises(ValueError):
        UserEmailOrPhone.validate(phone)


# Test valid email addresses
@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user123@example.co.uk",
        "user_name@example-domain.com",
        "1234567890@example.com",
        "user@subdomain.example.com",
    ],
)
def test_valid_emails(email):
    user_input = UserEmailOrPhone.validate(email)
    assert user_input.is_email() is True
    assert user_input.is_phone() is False


# Test invalid email addresses
@pytest.mark.parametrize(
    "email",
    [
        "user@example",  # Missing top-level domain
        "user@.com",  # Missing domain name
        "@example.com",  # Missing username
        "user@",  # Missing domain
        "user name@example.com",  # Contains space
    ],
)
def test_invalid_emails(email):
    with pytest.raises(ValueError):
        UserEmailOrPhone.validate(email)
