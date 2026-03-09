"""
Criptografia AES-256 para credenciais de corretora.
"""
import base64
import json
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Deriva chave Fernet a partir de BROKER_CREDENTIALS_KEY."""
    key_bytes = settings.BROKER_CREDENTIALS_KEY.encode() if isinstance(settings.BROKER_CREDENTIALS_KEY, str) else settings.BROKER_CREDENTIALS_KEY
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"gpfx_broker_salt", iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
    return Fernet(key)


def encrypt_credentials(data: dict[str, Any]) -> str:
    """Criptografa payload JSON de credenciais."""
    fernet = _get_fernet()
    payload = json.dumps(data).encode()
    return fernet.encrypt(payload).decode()


def decrypt_credentials(encrypted: str) -> dict[str, Any]:
    """Descriptografa payload de credenciais."""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted.encode())
    return json.loads(decrypted.decode())
