"""
Tests for configuration encryption module.

Tests cover encryption, decryption, key generation,
edge cases, and error handling.
"""
import os

import pytest
from cryptography.fernet import Fernet

from config.encryption import (
    decrypt_value,
    encrypt_value,
    generate_encryption_key,
    is_encrypted_value,
)


class TestEncryptDecrypt:
    """Tests for encrypt_value and decrypt_value functions."""

    def test_encrypt_and_decrypt_simple_string(self):
        """Test basic encryption and decryption."""
        original = "test_secret"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_and_decrypt_api_key(self):
        """Test encrypting and decrypting an API key."""
        api_key = "sk-1234567890abcdef"
        encrypted = encrypt_value(api_key)
        decrypted = decrypt_value(encrypted)
        assert decrypted == api_key

    def test_encrypt_and_decrypt_password(self):
        """Test encrypting and decrypting a password."""
        password = "MySecureP@ssw0rd!123"
        encrypted = encrypt_value(password)
        decrypted = decrypt_value(encrypted)
        assert decrypted == password

    def test_encrypt_and_decrypt_database_url(self):
        """Test encrypting and decrypting a database URL."""
        db_url = "postgresql://user:password@db.example.com:5432/dbname"
        encrypted = encrypt_value(db_url)
        decrypted = decrypt_value(encrypted)
        assert decrypted == db_url

    def test_encryption_produces_different_output(self):
        """Test that encrypting the same value twice produces different output."""
        value = "same_value"
        encrypted1 = encrypt_value(value)
        encrypted2 = encrypt_value(value)
        # Fernet uses a random IV, so encrypted values should differ
        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert decrypt_value(encrypted1) == value
        assert decrypt_value(encrypted2) == value

    def test_encrypted_value_looks_like_fernet(self):
        """Test that encrypted values have Fernet format."""
        value = "test_value"
        encrypted = encrypt_value(value)
        # Fernet-encrypted values start with 'gAAAAA' (base64-encoded version header)
        assert encrypted.startswith("gAAAAA")
        # Should be longer than original due to base64 encoding and auth tag
        assert len(encrypted) > len(value)


class TestIsEncryptedValue:
    """Tests for is_encrypted_value function."""

    def test_detects_fernet_encrypted_value(self):
        """Test that Fernet-encrypted values are detected."""
        encrypted = encrypt_value("test")
        assert is_encrypted_value(encrypted) is True

    def test_false_for_plaintext(self):
        """Test that plaintext values return False."""
        assert is_encrypted_value("plaintext") is False
        assert is_encrypted_value("test_api_key") is False
        assert is_encrypted_value("postgresql://...") is False

    def test_false_for_empty_string(self):
        """Test that empty string returns False."""
        assert is_encrypted_value("") is False

    def test_detects_fernet_prefix(self):
        """Test that values starting with Fernet prefix are detected."""
        assert is_encrypted_value("gAAAAAtest") is True
        assert is_encrypted_value("gAAAAAb ") is True
        assert is_encrypted_value("not-gAAAAA") is False


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key function."""

    def test_generates_valid_fernet_key(self):
        """Test that generated key is valid for Fernet."""
        key = generate_encryption_key()
        # Should not raise an exception
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_generates_different_keys(self):
        """Test that each generated key is unique."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2

    def test_key_is_url_safe(self):
        """Test that generated key is URL-safe base64 encoded."""
        key = generate_encryption_key()
        # URL-safe base64 only contains A-Z, a-z, 0-9, -, _, =
        valid_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_="
        )
        assert all(c in valid_chars for c in key)


class TestErrorHandling:
    """Tests for error handling in encryption functions."""

    def test_encrypt_empty_string_raises_error(self):
        """Test that encrypting empty string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot encrypt empty value"):
            encrypt_value("")

    def test_decrypt_empty_string_raises_error(self):
        """Test that decrypting empty string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot decrypt empty value"):
            decrypt_value("")

    def test_decrypt_invalid_token_raises_error(self):
        """Test that decrypting invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Failed to decrypt value"):
            decrypt_value("invalid_token_value")

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decrypting with wrong key fails."""
        original = "test_value"
        encrypted = encrypt_value(original)

        # Change the encryption key by setting a new one
        new_key = generate_encryption_key()
        os.environ["CONFIG_ENCRYPTION_KEY"] = new_key

        # Reload the Fernet instance with new key
        import importlib

        import config.encryption

        importlib.reload(config.encryption)

        # Attempting to decrypt with the new key should fail
        from config.encryption import decrypt_value as decrypt_with_new_key

        with pytest.raises(ValueError, match="Invalid token"):
            decrypt_with_new_key(encrypted)

        # Restore original behavior for other tests
        if "CONFIG_ENCRYPTION_KEY" in os.environ:
            del os.environ["CONFIG_ENCRYPTION_KEY"]
        importlib.reload(config.encryption)


class TestEncryptedValueProperties:
    """Tests for properties of encrypted values."""

    def test_encrypted_value_is_string(self):
        """Test that encrypted value is returned as string."""
        encrypted = encrypt_value("test")
        assert isinstance(encrypted, str)

    def test_decrypted_value_is_string(self):
        """Test that decrypted value is returned as string."""
        decrypted = decrypt_value(encrypt_value("test"))
        assert isinstance(decrypted, str)

    def test_encrypted_value_not_contain_original(self):
        """Test that original value is not visible in encrypted output."""
        original = "secret_password_123"
        encrypted = encrypt_value(original)
        assert original not in encrypted
        # Also check that partial strings aren't there
        assert "secret" not in encrypted
        assert "password" not in encrypted
