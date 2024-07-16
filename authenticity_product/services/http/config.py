"""Config module."""
import os
from typing import Any

from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DbSettingsMixin:
    """Db settings mixin."""

    db_uri: str = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}?application_name={os.getenv('APPLICATION_NAME', 'default_myem_app')}"
    )

    engine = create_engine(
        db_uri,
        connect_args={
            "connect_timeout": 31536000,
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        pool_size=15,
        max_overflow=25,
        pool_pre_ping=True,
        pool_recycle=600,
    )
    session_maker = sessionmaker(bind=engine)

    @classmethod
    def get_db(cls) -> Any:
        """Get database instance."""
        db = cls.session_maker()
        try:
            yield db
        finally:
            db.close()


class Settings(BaseSettings, DbSettingsMixin):
    """Settings."""


settings = Settings()
