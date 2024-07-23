"""http entrypoint file admin."""
from sqladmin import ModelView
from authenticity_product.models import Product, User


class ProductAdmin(ModelView, model=Product):  # type: ignore
    """Product admin view."""

    column_list = [Product.id, Product.name, Product.description]


class UserAdmin(ModelView, model=User):  # type: ignore
    """Product admin view."""

    can_create = False
    column_list = [User.email, User.phone, User.first_name, User.role]
    column_details_list = [User.email, User.phone, User.first_name, User.last_name, User.role]
    column_searchable_list = [User.email, User.phone, User.first_name, User.last_name]
