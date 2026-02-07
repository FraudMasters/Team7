"""
Token encryption utility using Fernet symmetric encryption.

This module provides secure encryption and decryption for sensitive tokens
like LinkedIn OAuth access tokens and refresh tokens.

Features:
- Fernet symmetric encryption (AES-128-CBC with HMAC)
- Base64-encoded encrypted output
- Key validation and initialization
- Error handling for encryption failures

Security:
- Encryption keys must be 32 bytes, URL-safe base64-encoded
- Keys should be stored in environment variables, not in code
- Never log plaintext tokens
"""
import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from config import get_settings

logger = logging.getLogger(__name__)

# Global Fernet encryptor instance
_fernet: Optional[Fernet] = None


def _get_encryption_key() -> bytes:
    """
    Get or generate the encryption key from environment.

    The encryption key must be:
    - 32 bytes (256 bits)
    - URL-safe base64-encoded

    Returns:
        Fernet encryption key as bytes

    Raises:
        ValueError: If LINKEDIN_TOKEN_ENCRYPTION_KEY is not set or invalid

    Example:
        >>> key = _get_encryption_key()
        >>> len(key)
        44
    """
    settings = get_settings()

    # Try to get key from environment
    encryption_key_str = getattr(settings, "linkedin_token_encryption_key", None)

    if not encryption_key_str:
        # Generate a new key and log warning
        # In production, this should be set via environment variable
        logger.warning(
            "LINKEDIN_TOKEN_ENCRYPTION_KEY not set. "
            "Generating a temporary key. Tokens will not persist across restarts. "
            "Set LINKEDIN_TOKEN_ENCRYPTION_KEY environment variable with a Fernet key."
        )
        encryption_key = Fernet.generate_key()
        logger.warning(
            f"Generated encryption key (save this to environment): {encryption_key.decode()}"
        )
        return encryption_key

    # Validate key format (must be URL-safe base64)
    try:
        # Ensure key is bytes
        if isinstance(encryption_key_str, str):
            encryption_key_bytes = encryption_key_str.encode("utf-8")
        else:
            encryption_key_bytes = encryption_key_str

        # Validate it's a valid Fernet key
        Fernet(encryption_key_bytes)

        return encryption_key_bytes

    except Exception as e:
        raise ValueError(
            f"Invalid LINKEDIN_TOKEN_ENCRYPTION_KEY: {e}. "
            "Encryption key must be a 32-byte URL-safe base64-encoded string. "
            "Generate one with: Fernet.generate_key()"
        ) from e


def _get_fernet() -> Fernet:
    """
    Get or create the global Fernet encryptor instance.

    Returns:
        Fernet encryptor instance

    Raises:
        ValueError: If encryption key is invalid
    """
    global _fernet

    if _fernet is None:
        key = _get_encryption_key()
        _fernet = Fernet(key)
        logger.debug("Fernet encryptor initialized")

    return _fernet


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a plaintext token using Fernet symmetric encryption.

    Args:
        plaintext: Plaintext token to encrypt (e.g., access token, refresh token)

    Returns:
        Encrypted token as URL-safe base64 string

    Raises:
        ValueError: If plaintext is empty or encryption fails

    Example:
        >>> token = "AQXzV3x_8F1G2hI3jK4lM5nO6pQ7rS8tU9vW0xY"
        >>> encrypted = encrypt_token(token)
        >>> print(encrypted)
        'gAAAAABh...'

    Security:
        - Never log the plaintext token
        - Store the encrypted result in the database
        - Token can be decrypted with decrypt_token()
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty token")

    try:
        fernet = _get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode("utf-8"))
        encrypted_str = encrypted_bytes.decode("utf-8")

        logger.debug("Token encrypted successfully")
        return encrypted_str

    except Exception as e:
        logger.error(f"Token encryption failed: {e}")
        raise ValueError(f"Failed to encrypt token: {e}") from e


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt an encrypted token using Fernet symmetric encryption.

    Args:
        encrypted: Encrypted token (URL-safe base64 string from encrypt_token())

    Returns:
        Decrypted plaintext token

    Raises:
        ValueError: If encrypted token is empty, invalid, or decryption fails

    Example:
        >>> encrypted = "gAAAAABh..."
        >>> plaintext = decrypt_token(encrypted)
        >>> print(plaintext)
        'AQXzV3x_8F1G2hI3jK4lM5nO6pQ7rS8tU9vW0xY'

    Security:
        - The decrypted plaintext should never be logged
        - Only decrypt tokens when they are needed for API calls
        - Decrypted tokens should be kept in memory only
    """
    if not encrypted:
        raise ValueError("Cannot decrypt empty token")

    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted.encode("utf-8"))
        decrypted_str = decrypted_bytes.decode("utf-8")

        logger.debug("Token decrypted successfully")
        return decrypted_str

    except InvalidToken as e:
        logger.error("Token decryption failed: Invalid token or wrong key")
        raise ValueError(
            "Failed to decrypt token: Invalid token or encryption key mismatch"
        ) from e

    except Exception as e:
        logger.error(f"Token decryption failed: {e}")
        raise ValueError(f"Failed to decrypt token: {e}") from e


def is_encrypted_token(value: str) -> bool:
    """
    Check if a string appears to be an encrypted token.

    This is a heuristic check - encrypted tokens are typically
    longer than plaintext tokens and start with 'gAAAAA' (Fernet prefix).

    Args:
        value: String to check

    Returns:
        True if value appears to be encrypted, False otherwise

    Example:
        >>> encrypted = encrypt_token("my-token")
        >>> is_encrypted_token(encrypted)
        True
        >>> is_encrypted_token("my-token")
        False
    """
    if not value or len(value) < 10:
        return False

    # Fernet-encrypted tokens start with 'gAAAAA'
    return value.startswith("gAAAAA")


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    This function generates a new random encryption key that can be used
    for token encryption. The key should be stored securely in environment
    variables.

    Returns:
        URL-safe base64-encoded encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> print(f"LINKEDIN_TOKEN_ENCRYPTION_KEY={key}")
        LINKEDIN_TOKEN_ENCRYPTION_KEY=gAAAAABh...

    Note:
        - Save the generated key to your .env file
        - Never share the encryption key
        - If you lose the key, all encrypted tokens cannot be decrypted
        - Generate once and reuse - don't regenerate for existing tokens
    """
    key = Fernet.generate_key()
    key_str = key.decode("utf-8")

    logger.info("Generated new encryption key")
    return key_str
