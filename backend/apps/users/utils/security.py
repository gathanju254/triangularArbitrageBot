# backend/apps/users/utils/security.py
import base64
import logging
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_encryption_key() -> str:
    """Get ENCRYPTION_KEY from Django settings or generate a dev key (safe for DEBUG only)."""
    key = getattr(settings, "ENCRYPTION_KEY", None)
    if key:
        return key
    # Fallback for development only
    if getattr(settings, "DEBUG", False):
        gen = Fernet.generate_key().decode()
        logger.warning("ENCRYPTION_KEY not set — generated temporary key for DEBUG mode")
        return gen
    raise RuntimeError("ENCRYPTION_KEY not configured in settings")


def _get_fernet() -> Fernet:
    return Fernet(_get_encryption_key().encode())


def encrypt_data(value: str) -> str:
    """Encrypt a UTF-8 string and return a token string."""
    if not value:
        return ""
    token = _get_fernet().encrypt(value.encode()).decode()
    return token


def decrypt_data(token: str, handle_legacy_prefix: bool = True) -> str:
    """Decrypt a token produced by encrypt_data. Handle legacy 'encrypted:' prefix if requested."""
    if not token:
        return ""
    try:
        if handle_legacy_prefix and token.startswith("encrypted:"):
            token = token.split(":", 1)[1]
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        logger.error(f"Invalid token during decryption: {e}")
        raise


def safe_encrypt_data(value: str, fallback_to_plaintext: bool = False) -> str:
    """Encrypt but never raise in non-strict flows if fallback_to_plaintext=True."""
    try:
        return encrypt_data(value)
    except Exception as e:
        logger.exception(f"Encryption failed: {e}")
        if fallback_to_plaintext:
            logger.warning("Falling back to plaintext storage (DEBUG/lenient mode)")
            return value
        raise


def safe_decrypt_data(token: str, fallback_to_plaintext: bool = False, handle_legacy_prefix: bool = True) -> str:
    """Decrypt safely: on failure return token (or original) when fallback enabled."""
    try:
        return decrypt_data(token, handle_legacy_prefix=handle_legacy_prefix)
    except Exception as e:
        logger.exception(f"Decryption failed: {e}")
        if fallback_to_plaintext:
            logger.warning("Returning raw token due to decryption failure (fallback enabled)")
            return token or ""
        raise


def health_check() -> Dict[str, Any]:
    """Simple encrypt/decrypt roundtrip to verify configuration."""
    try:
        sample = "health-check"
        token = safe_encrypt_data(sample, fallback_to_plaintext=False)
        result = safe_decrypt_data(token, fallback_to_plaintext=False)
        ok = result == sample
        return {"ok": ok, "message": "roundtrip ok" if ok else "mismatch"}
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {"ok": False, "message": str(e)}