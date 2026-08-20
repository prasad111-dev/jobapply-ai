import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def _get_fernet() -> Fernet:
    key_material = settings.SECRET_KEY.encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return Fernet(key)


def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt a platform password / token before storing in DB."""
    if not plaintext:
        return None
    try:
        return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encrypt secret: {e}")
        return None


def decrypt_secret(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt a stored platform password / token for use in automation."""
    if not ciphertext:
        return None
    try:
        return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error("Credential decryption failed - refusing to treat as plaintext")
        return None
    except Exception as e:
        logger.error(f"Failed to decrypt secret: {e}")
        return None