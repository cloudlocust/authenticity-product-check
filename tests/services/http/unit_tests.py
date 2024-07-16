import os

from sqlalchemy import text
from authenticity_product.models import Role, User


def test_db(db_dependency):
    users = [
        Role(name="John,n,Doe"),
        Role(name="JanekjDoe"),
        Role(name="AlicembnmbSmith"),
    ]
    db_dependency.bulk_save_objects(users)
    db_dependency.commit()

    # Query all users
    all_users = db_dependency.query(Role).all()
    print(all_users)
