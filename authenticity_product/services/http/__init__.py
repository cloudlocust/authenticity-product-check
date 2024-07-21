"""Init file for http services."""
import os

import requests
from jwcrypto.jwk import JWK


rsa_key = JWK(**requests.get(os.environ["FASTAPI_USERS_RSA_KEY_URL"], timeout=10).json()["keys"][0])
private_key: str = rsa_key.export_to_pem(private_key=True, password=None)
