"""
Configuration encryption utilities for sensitive values.

This module provides encryption and decryption functions for sensitive
configuration values such as API keys, passwords, and secrets.

Encryption uses Fernet (symmetric encryption) with a key derived from
the CONFIG_ENCRYPTION_KEY environment variable. If not set, a development
key is used (not secure for production).
"""
import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Encryption key for sensitive configuration values
# In production, this should be set via environment variable
_DEFAULT_ENCRYPTION_KEY = base64.urlsafe_b64encode(
    b"dev-key-only-change-in-production-32b!"
).decode("utf-8")

_encryption_key: Optional[str] = None
_fernet: Optional[Fernet] = None


def _get_encryption_key() -> str:
    """
    Get the encryption key from environment or use default.

    Returns:
        The encryption key as a string

    Note:
        The default key is NOT secure for production use.
        Always set CONFIG_ENCRYPTION_KEY in production environments.
    """
    global _encryption_key
    if _encryption_key is None:
        _encryption_key = os.environ.get(
            "CONFIG_ENCRYPTION_KEY", _DEFAULT_ENCRYPTION_KEY
        )
        if _encryption_key == _DEFAULT_ENCRYPTION_KEY:
            logger.warning(
                "Using default encryption key. Set CONFIG_ENCRYPTION_KEY "
                "environment variable for production security."
            )
    return _encryption_key


def _get_fernet() -> Fernet:
    """
    Get or create the Fernet cipher instance.

    Returns:
        Fernet cipher instance
    """
    global _fernet
    if _fernet is None:
        key = _get_encryption_key()
        # Ensure key is valid Fernet key (32 bytes, base64-encoded)
        try:
            _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.error(f"Invalid encryption key: {e}")
            raise ValueError(
                "Invalid CONFIG_ENCRYPTION_KEY. Must be a 32-byte URL-safe "
                "base64-encoded string. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            ) from e
    return _fernet


def encrypt_value(value: str) -> str:
    """
    Encrypt a sensitive configuration value.

    Args:
        value: The plaintext value to encrypt

    Returns:
        URL-safe base64-encoded encrypted value

    Raises:
        ValueError: If the value is empty or encryption fails

    Example:
        >>> encrypted = encrypt_value("my_api_key_123")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    if not value:
        raise ValueError("Cannot encrypt empty value")

    try:
        fernet = _get_fernet()
        encrypted_bytes = fernet.encrypt(value.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Failed to encrypt value: {e}") from e


def decrypt_value(encrypted_value: str) -> str:
    """
    Decrypt a sensitive configuration value.

    Args:
        encrypted_value: The encrypted value to decrypt (URL-safe base64-encoded)

    Returns:
        The decrypted plaintext value

    Raises:
        ValueError: If the value is empty or decryption fails
        InvalidToken: If the encryption key is wrong or data is corrupted

    Example:
        >>> decrypted = decrypt_value("gAAAAABh...")
        >>> print(decrypted)
        'my_api_key_123'
    """
    if not encrypted_value:
        raise ValueError("Cannot decrypt empty value")

    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_value.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken as e:
        logger.error("Decryption failed: Invalid token or wrong encryption key")
        raise ValueError(
            "Failed to decrypt value: Invalid token or wrong encryption key. "
            "Ensure CONFIG_ENCRYPTION_KEY matches the key used for encryption."
        ) from e
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Failed to decrypt value: {e}") from e


def is_encrypted_value(value: str) -> bool:
    """
    Check if a value appears to be encrypted.

    Args:
        value: The value to check

    Returns:
        True if the value appears to be encrypted (starts with Fernet prefix)

    Note:
        This is a heuristic check. Fernet-encrypted values start with
        'gAAAAA' (base64-encoded version header).
    """
    if not value:
        return False
    return value.startswith("gAAAAA")


def generate_encryption_key() -> str:
    """
    Generate a new random encryption key.

    Returns:
        URL-safe base64-encoded 32-byte encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> print(key)
        'abcdefghijklmnopqrstuvwxyz123456='
    """
    return Fernet.generate_key().decode("utf-8")
