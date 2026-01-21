import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload (dict with 'sub', 'exp', etc.)

    Raises:
        jwt.PyJWTError: If token is invalid, expired, or malformed
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# =============================================================================
# API Key Encryption (for user LLM provider keys)
# =============================================================================

def _get_fernet() -> Fernet:
    """
    Get Fernet instance using a key derived from SECRET_KEY.

    Fernet requires a 32-byte base64-encoded key. We derive this
    deterministically from the application's SECRET_KEY using SHA256.
    """
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_api_key(plain_key: str) -> str:
    """
    Encrypt an API key for secure storage.

    Args:
        plain_key: The plain text API key

    Returns:
        Encrypted key as a string (safe for database storage)
    """
    f = _get_fernet()
    return f.encrypt(plain_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key for use.

    Args:
        encrypted_key: The encrypted API key from database

    Returns:
        Decrypted plain text API key

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails
    """
    f = _get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()
