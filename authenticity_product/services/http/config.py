"""Config module."""
import json
import os
from http.client import HTTPException
from typing import Any
from urllib.request import urlopen

from fastapi.security import OAuth2PasswordBearer
from jwcrypto.jwk import JWK
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from authenticity_product.services.http import private_key, rsa_key


public_key_web_content = None

if public_key_url := os.environ["PUBLIC_KEY_URL"] if os.getenv("PUBLIC_KEY_URL") else None:
    with urlopen(os.environ["PUBLIC_KEY_URL"]) as f:
        public_key_web_content = json.loads(f.read())["keys"]


class FastApiSettingsMixin:
    """FastApi settings mixin."""

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    public_key_web_content = public_key_web_content

    @classmethod
    def get_public_key(cls, index: int = 0) -> str:
        """Returns a public key from a url contains a decoded header and a token."""
        # we used urllib rather than requests because it's has an incompabilities with
        # fast api or other you can check the same error in this link
        # https://stackoverflow.com/questions/49820173/requests-recursionerror-maximum-recursion-depth-exceeded
        try:
            header_key = cls.public_key_web_content[index]
            return JWK(**header_key).export_to_pem()
        except Exception:
            raise HTTPException(detail="Invalid Key", status_code=400) from Exception

    @classmethod
    def get_private_key(cls, index: int = 0) -> str:
        """Returns a private key from a url contains a decoded header and a token."""
        try:
            header_key = cls.public_key_web_content[index]
            return JWK(**header_key).export_to_pem(private_key=True, password=None)
        except Exception:
            raise HTTPException(detail="unauthorized", status_code=401) from Exception


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


class Settings(DbSettingsMixin, FastApiSettingsMixin):
    """Settings."""

    private_key: str = private_key
    public_key: str = rsa_key.export_to_pem()
    token_expiration_in_seconds = int(os.environ["TOKEN_EXPIRATION_IN_SECONDS"])


settings = Settings()
