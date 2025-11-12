# backend/apps/users/utils/security.py
import base64
import logging
import os
import binascii
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """
    Get encryption key with proper fallbacks and validation.
    
    Returns:
        bytes: Encryption key suitable for Fernet
        
    Raises:
        ImproperlyConfigured: If no key is found in production
    """
    # Try to get from Django settings first
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if not key:
        # Try environment variable
        key = os.environ.get('ENCRYPTION_KEY')
    
    if not key:
        if getattr(settings, 'DEBUG', False):
            # Generate temporary key for development
            logger.warning("ENCRYPTION_KEY not set — generated temporary key for DEBUG mode")
            temporary_key = Fernet.generate_key()
            
            # Store it for consistency during this session
            if not hasattr(settings, '_TEMPORARY_ENCRYPTION_KEY'):
                settings._TEMPORARY_ENCRYPTION_KEY = temporary_key
            return temporary_key
        else:
            raise ImproperlyConfigured(
                "ENCRYPTION_KEY must be set in production. "
                "Set it in your environment variables or Django settings. "
                "You can generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
    
    # Ensure key is bytes and properly formatted
    if isinstance(key, str):
        key = key.encode()
    
    # Validate key format (Fernet keys are 32 url-safe base64-encoded bytes)
    try:
        # Try to decode as base64 to validate format
        decoded_key = base64.urlsafe_b64decode(key)
        if len(decoded_key) != 32:
            raise ValueError("Encryption key must be 32 bytes when decoded")
    except (ValueError, binascii.Error) as e:
        raise ImproperlyConfigured(
            f"Invalid ENCRYPTION_KEY format: {e}. "
            "Key must be 32 url-safe base64-encoded bytes."
        )
    
    return key


def _get_fernet() -> Fernet:
    """Get Fernet instance with validated key."""
    return Fernet(get_encryption_key())


def encrypt_data(value: str) -> str:
    """
    Encrypt a UTF-8 string and return a token string.
    
    Args:
        value: Plaintext string to encrypt
        
    Returns:
        str: Encrypted token string
        
    Raises:
        ValueError: If value is None or encryption fails
    """
    if value is None:
        raise ValueError("Cannot encrypt None value")
    
    if not value:
        return ""
    
    try:
        token = _get_fernet().encrypt(value.encode()).decode()
        logger.debug("✅ Data encrypted successfully")
        return token
    except Exception as e:
        logger.error(f"❌ Encryption failed: {e}")
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_data(token: str, handle_legacy_prefix: bool = True) -> str:
    """
    Decrypt a token produced by encrypt_data.
    
    Args:
        token: Encrypted token string
        handle_legacy_prefix: Whether to handle legacy 'encrypted:' prefix
        
    Returns:
        str: Decrypted plaintext string
        
    Raises:
        ValueError: If token is invalid or decryption fails
    """
    if token is None:
        raise ValueError("Cannot decrypt None token")
    
    if not token:
        return ""
    
    try:
        # Handle legacy prefix if present and requested
        if handle_legacy_prefix and token.startswith("encrypted:"):
            token = token[len("encrypted:"):]
            logger.debug("🔍 Handled legacy encryption prefix")
        
        decrypted_value = _get_fernet().decrypt(token.encode()).decode()
        logger.debug("✅ Data decrypted successfully")
        return decrypted_value
        
    except InvalidToken as e:
        logger.error(f"❌ Invalid token during decryption: {e}")
        raise ValueError("Invalid encryption token - data may be corrupted or key may have changed")
    except Exception as e:
        logger.error(f"❌ Decryption failed: {e}")
        raise ValueError(f"Decryption failed: {str(e)}")


def safe_encrypt_data(value: str, fallback_to_plaintext: bool = False) -> str:
    """
    Encrypt data with safety fallbacks for non-critical operations.
    
    Args:
        value: Plaintext string to encrypt
        fallback_to_plaintext: Whether to return plaintext on failure
        
    Returns:
        str: Encrypted token or plaintext if fallback enabled
        
    Raises:
        ValueError: If encryption fails and fallback is disabled
    """
    if value is None:
        return ""
    
    try:
        return encrypt_data(value)
    except Exception as e:
        logger.error(f"❌ Safe encryption failed: {e}")
        
        if fallback_to_plaintext:
            logger.warning("⚠️ Falling back to plaintext storage (DEBUG/lenient mode)")
            return value
        else:
            raise ValueError(f"Encryption failed and fallback disabled: {str(e)}")


def safe_decrypt_data(
    token: str, 
    fallback_to_token: bool = False, 
    handle_legacy_prefix: bool = True
) -> str:
    """
    Decrypt data safely with configurable fallback behavior.
    
    Args:
        token: Encrypted token string
        fallback_to_token: Whether to return original token on failure
        handle_legacy_prefix: Whether to handle legacy 'encrypted:' prefix
        
    Returns:
        str: Decrypted plaintext or original token if fallback enabled
        
    Raises:
        ValueError: If decryption fails and fallback is disabled
    """
    if token is None:
        return ""
    
    if not token:
        return ""
    
    try:
        return decrypt_data(token, handle_legacy_prefix=handle_legacy_prefix)
    except Exception as e:
        logger.error(f"❌ Safe decryption failed: {e}")
        
        if fallback_to_token:
            logger.warning("⚠️ Returning raw token due to decryption failure (fallback enabled)")
            return token
        else:
            raise ValueError(f"Decryption failed and fallback disabled: {str(e)}")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted.
    
    Args:
        value: String to check
        
    Returns:
        bool: True if value appears to be encrypted
    """
    if not value:
        return False
    
    # Check for legacy prefix
    if value.startswith("encrypted:"):
        return True
    
    # Check if it looks like a Fernet token
    # Fernet tokens are URL-safe base64, typically 100+ characters
    if len(value) >= 100:
        try:
            # Try to decode as base64 to validate format
            import binascii
            base64.urlsafe_b64decode(value)
            return True
        except (ValueError, binascii.Error):
            pass
    
    return False


def rotate_encryption_key(old_key: bytes, new_key: bytes) -> Dict[str, Any]:
    """
    Rotate encryption key for all encrypted data.
    
    Args:
        old_key: The current encryption key
        new_key: The new encryption key to use
        
    Returns:
        Dict with rotation results
    """
    # This would typically be used in a migration script
    # Implementation depends on your data model
    
    logger.info("🔄 Starting encryption key rotation")
    
    # Example implementation - you would adapt this to your models
    try:
        from ..models import APIKey
        import base64
        
        old_fernet = Fernet(old_key)
        new_fernet = Fernet(new_key)
        
        rotated_count = 0
        failed_count = 0
        
        # Rotate API keys
        api_keys = APIKey.objects.filter(is_encrypted=True)
        for api_key in api_keys:
            try:
                # Decrypt with old key
                if api_key.api_key and is_encrypted(api_key.api_key):
                    decrypted = old_fernet.decrypt(api_key.api_key.encode()).decode()
                    api_key.api_key = new_fernet.encrypt(decrypted.encode()).decode()
                
                if api_key.secret_key and is_encrypted(api_key.secret_key):
                    decrypted = old_fernet.decrypt(api_key.secret_key.encode()).decode()
                    api_key.secret_key = new_fernet.encrypt(decrypted.encode()).decode()
                
                if api_key.passphrase and is_encrypted(api_key.passphrase):
                    decrypted = old_fernet.decrypt(api_key.passphrase.encode()).decode()
                    api_key.passphrase = new_fernet.encrypt(decrypted.encode()).decode()
                
                api_key.save()
                rotated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to rotate API key {api_key.id}: {e}")
                failed_count += 1
        
        return {
            "success": True,
            "rotated_count": rotated_count,
            "failed_count": failed_count,
            "message": f"Rotated {rotated_count} records, {failed_count} failures"
        }
        
    except Exception as e:
        logger.error(f"Key rotation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_secure_key() -> str:
    """
    Generate a secure encryption key.
    
    Returns:
        str: Base64-encoded encryption key
    """
    key = Fernet.generate_key()
    return key.decode()


def health_check() -> Dict[str, Any]:
    """
    Comprehensive security health check.
    
    Returns:
        Dict with health check results
    """
    try:
        # Test 1: Basic encrypt/decrypt roundtrip
        sample_data = "security-health-check-2024"
        encrypted = encrypt_data(sample_data)
        decrypted = decrypt_data(encrypted)
        
        roundtrip_ok = decrypted == sample_data
        
        # Test 2: Legacy prefix handling
        legacy_encrypted = f"encrypted:{encrypted}"
        legacy_decrypted = decrypt_data(legacy_encrypted, handle_legacy_prefix=True)
        legacy_ok = legacy_decrypted == sample_data
        
        # Test 3: Safe encryption fallback
        safe_encrypted = safe_encrypt_data(sample_data, fallback_to_plaintext=False)
        safe_decrypted = safe_decrypt_data(safe_encrypted, fallback_to_token=False)
        safe_ok = safe_decrypted == sample_data
        
        # Test 4: Encryption detection
        detection_ok = is_encrypted(encrypted) and not is_encrypted(sample_data)
        
        all_tests_passed = all([roundtrip_ok, legacy_ok, safe_ok, detection_ok])
        
        return {
            "ok": all_tests_passed,
            "tests": {
                "basic_roundtrip": roundtrip_ok,
                "legacy_prefix": legacy_ok,
                "safe_operations": safe_ok,
                "encryption_detection": detection_ok
            },
            "message": "All security checks passed" if all_tests_passed else "Some security checks failed",
            "key_source": "configured" if hasattr(settings, 'ENCRYPTION_KEY') or os.environ.get('ENCRYPTION_KEY') else "temporary"
        }
        
    except Exception as e:
        logger.error(f"❌ Security health check failed: {e}")
        return {
            "ok": False,
            "error": str(e),
            "message": "Security health check failed",
            "key_source": "unknown"
        }


def get_security_status() -> Dict[str, Any]:
    """
    Get comprehensive security status information.
    
    Returns:
        Dict with security status details
    """
    health = health_check()
    
    return {
        "encryption_configured": bool(getattr(settings, 'ENCRYPTION_KEY', None) or os.environ.get('ENCRYPTION_KEY')),
        "using_temporary_key": getattr(settings, 'DEBUG', False) and not bool(getattr(settings, 'ENCRYPTION_KEY', None)),
        "health_check": health,
        "key_length": len(get_encryption_key()) if health.get('ok') else 0,
        "fernet_available": True,
        "recommendations": [
            "Use a strong ENCRYPTION_KEY in production",
            "Rotate encryption keys periodically",
            "Store keys in environment variables, not code",
            "Use different keys for different environments"
        ] if not health.get('ok') or getattr(settings, 'DEBUG', False) else []
    }


# Legacy function aliases for backward compatibility
_get_encryption_key = get_encryption_key