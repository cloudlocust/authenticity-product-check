import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from authenticity_product.models import DeclarativeBase, Role


@pytest.mark.parametrize("name, description", [("mod", "Moderator"), ("admin", "Admin")])
def test_create_role_with_name_and_description(db_dependency, name, description, request):
    def clean():
        db_dependency.execute(delete(Role))
        db_dependency.commit()

    request.addfinalizer(clean)
    role = Role(name=name, description=description)
    db_dependency.add(role)
    db_dependency.commit()
    fetched_role = db_dependency.query(Role).filter_by(name=name).first()

    assert fetched_role.name == name
    assert fetched_role.description == description


def test_update_role_name_and_description(db_dependency, request):
    def clean():
        db_dependency.execute(delete(Role))
        db_dependency.commit()

    request.addfinalizer(clean)
    role = Role(name="old_name", description=" desc")
    db_dependency.add(role)
    db_dependency.commit()

    role_id = role.id
    role.name = "new_name"
    role.description = "new desc"
    db_dependency.commit()

    updated_role = db_dependency.query(Role).filter_by(id=role_id).first()
    assert updated_role.name == "new_name"
    assert updated_role.description == "new desc"


def test_create_role_name_is_none(db_dependency_factory):
    engine = db_dependency_factory(DeclarativeBase)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session_db = session()
    with pytest.raises(IntegrityError) as e:
        role = Role(name=None, description="Admin")
        session_db.add(role)
        session_db.commit()
    assert (
        str(e.value.args[0].split("\n")[0])
        == '(psycopg2.errors.NotNullViolation) null value in column "name" of relation '
        '"role" violates not-null constraint'
    )


def test_create_role_with_name_exsting(db_dependency_factory):
    engine = db_dependency_factory(DeclarativeBase)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session_db = session()
    role = Role(name="admin", description="Admin")
    session_db.add(role)
    session_db.commit()

    with pytest.raises(IntegrityError) as e:
        role = Role(name="admin", description="Admin")
        session_db.add(role)
        session_db.commit()
    assert (
        str(e.value.args[0])
        == "(psycopg2.errors.UniqueViolation) duplicate key value violates unique "
        'constraint "role_name_key"\n'
        "DETAIL:  Key (name)=(admin) already exists.\n"
    )
