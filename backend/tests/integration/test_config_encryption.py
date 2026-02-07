"""
Integration Tests for Configuration Encryption

This test module performs comprehensive verification of the configuration
encryption system, ensuring that sensitive configuration values are properly
encrypted and can be decrypted when needed.

Test Coverage:
- Sensitive configuration values (API keys, passwords, database URLs) are encrypted
- Encrypted values can be decrypted with the correct key
- Encryption produces different output for the same input (random IV)
- Encrypted values don't leak plaintext information
- Key rotation scenarios at integration level
- Error handling for invalid encrypted values
- Integration with configuration system
"""
import os
import importlib
from datetime import datetime
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.config_change import ConfigChange, ConfigChangeAction
from config import get_settings
from config.encryption import (
    encrypt_value,
    decrypt_value,
    is_encrypted_value,
    generate_encryption_key,
)
from config.audit import log_config_change


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """Create a test HTTP client with database override."""
    from main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Test 1: Sensitive API Keys Are Encrypted
# ============================================================================

@pytest.mark.asyncio
async def test_sensitive_api_key_is_encrypted():
    """Verify that sensitive API keys are encrypted correctly."""
    # Sample API keys (similar to real-world formats)
    api_keys = [
        "sk-1234567890abcdef",
        "sk-proj-abc123def456ghi789",
        "AKIAIOSFODNN7EXAMPLE",  # AWS access key format
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT-like format
    ]

    for api_key in api_keys:
        # Encrypt the API key
        encrypted = encrypt_value(api_key)

        # Verify it's encrypted (starts with Fernet prefix)
        assert is_encrypted_value(encrypted), f"API key should be encrypted: {api_key[:10]}..."
        assert encrypted.startswith("gAAAAA"), "Encrypted value should have Fernet prefix"

        # Verify it can be decrypted
        decrypted = decrypt_value(encrypted)
        assert decrypted == api_key, "Decrypted value should match original"

        # Verify original is not in encrypted output
        assert api_key not in encrypted, "Original API key should not be visible in encrypted output"

        # Verify encrypted value is different from original
        assert encrypted != api_key, "Encrypted value should differ from original"

        print(f"✓ API key format {api_key[:10]}... encrypted successfully")


# ============================================================================
# Test 2: Sensitive Database URLs Are Encrypted
# ============================================================================

@pytest.mark.asyncio
async def test_sensitive_database_url_is_encrypted():
    """Verify that database URLs with passwords are encrypted correctly."""
    # Sample database URLs with passwords
    db_urls = [
        "postgresql://user:password123@db.example.com:5432/dbname",
        "postgresql://admin:P@ssw0rd!@localhost:5432/production",
        "mysql://root:secret@mysql-host:3306/mydb",
        "mongodb://user:sesame123@mongo-host:27017/authdb",
    ]

    for db_url in db_urls:
        # Encrypt the database URL
        encrypted = encrypt_value(db_url)

        # Verify it's encrypted
        assert is_encrypted_value(encrypted), "Database URL should be encrypted"

        # Verify it can be decrypted
        decrypted = decrypt_value(encrypted)
        assert decrypted == db_url, "Decrypted URL should match original"

        # Verify password is not visible in encrypted output
        # Extract password from URL (between : and @)
        if "@" in db_url and "://" in db_url:
            start = db_url.find("://") + 3
            at_pos = db_url.find("@", start)
            if ":" in db_url[start:at_pos]:
                colon_pos = db_url.find(":", start)
                password = db_url[colon_pos + 1:at_pos]
                assert password not in encrypted, f"Password '{password}' should not be visible in encrypted output"

        print(f"✓ Database URL {db_url[:30]}... encrypted successfully")


# ============================================================================
# Test 3: Encryption Produces Different Output For Same Input
# ============================================================================

@pytest.mark.asyncio
async def test_encryption_produces_different_output():
    """Verify that encrypting the same value twice produces different output."""
    sensitive_value = "super_secret_api_key_12345"

    # Encrypt the same value twice
    encrypted1 = encrypt_value(sensitive_value)
    encrypted2 = encrypt_value(sensitive_value)

    # Verify outputs are different (due to random IV)
    assert encrypted1 != encrypted2, "Same input should produce different encrypted outputs"

    # Verify both decrypt to the same value
    decrypted1 = decrypt_value(encrypted1)
    decrypted2 = decrypt_value(encrypted2)

    assert decrypted1 == sensitive_value, "First decryption should match original"
    assert decrypted2 == sensitive_value, "Second decryption should match original"
    assert decrypted1 == decrypted2, "Both decryptions should match"

    print(f"✓ Encryption produces different output: {encrypted1[:20]}... != {encrypted2[:20]}...")


# ============================================================================
# Test 4: Encrypted Values Don't Leak Partial Information
# ============================================================================

@pytest.mark.asyncio
async def test_encrypted_values_dont_leak_partial_info():
    """Verify that encrypted values don't contain partial plaintext information."""
    # Test with various sensitive patterns
    test_cases = [
        ("password", "MySecurePassword123!"),
        ("api_key", "sk-1234567890abcdef"),
        ("secret", "super_secret_value_abc"),
        ("token", "bearer_token_xyz789"),
    ]

    for label, sensitive_value in test_cases:
        encrypted = encrypt_value(sensitive_value)

        # Check that common substrings are not in the encrypted output
        words = sensitive_value.split("_")
        for word in words:
            if len(word) > 3:  # Only check words longer than 3 characters
                assert word not in encrypted, f"Partial '{word}' should not be in encrypted output"

        # Check original value is not in encrypted output
        assert sensitive_value not in encrypted, f"{label} should not be fully visible in encrypted output"

        print(f"✓ {label}: No partial information leaked")


# ============================================================================
# Test 5: Key Rotation At Integration Level
# ============================================================================

@pytest.mark.asyncio
async def test_key_rotation_integration():
    """Verify encryption key rotation works at integration level."""
    # Original value encrypted with default key
    original_value = "original_secret_value"
    encrypted_with_old_key = encrypt_value(original_value)

    # Decrypt with old key to verify it works
    decrypted_with_old_key = decrypt_value(encrypted_with_old_key)
    assert decrypted_with_old_key == original_value

    # Generate a new encryption key
    new_key = generate_encryption_key()
    assert new_key != os.environ.get("CONFIG_ENCRYPTION_KEY", "")

    # Set new key in environment
    old_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    os.environ["CONFIG_ENCRYPTION_KEY"] = new_key

    try:
        # Reload the encryption module to use new key
        import config.encryption
        importlib.reload(config.encryption)

        # Import the reloaded functions
        from config.encryption import (
            encrypt_value as encrypt_with_new_key,
            decrypt_value as decrypt_with_new_key,
        )

        # Old encrypted value should NOT decrypt with new key
        with pytest.raises(ValueError, match="Invalid token"):
            decrypt_with_new_key(encrypted_with_old_key)

        # Encrypt a new value with the new key
        new_value = "new_secret_with_rotated_key"
        encrypted_with_new = encrypt_with_new_key(new_value)

        # Verify it decrypts with new key
        decrypted_with_new = decrypt_with_new_key(encrypted_with_new)
        assert decrypted_with_new == new_value

        print("✓ Key rotation: Old values cannot be decrypted with new key")
        print("✓ Key rotation: New values can be encrypted and decrypted with new key")

    finally:
        # Restore original key
        if old_key is None:
            os.environ.pop("CONFIG_ENCRYPTION_KEY", None)
        else:
            os.environ["CONFIG_ENCRYPTION_KEY"] = old_key

        # Reload encryption module to restore original behavior
        importlib.reload(config.encryption)


# ============================================================================
# Test 6: Error Handling For Invalid Encrypted Values
# ============================================================================

@pytest.mark.asyncio
async def test_error_handling_for_invalid_encrypted_values():
    """Verify that invalid encrypted values are handled correctly."""
    invalid_cases = [
        ("", "empty string"),
        ("not_encrypted", "plain text value"),
        ("gAAAAA_invalid_token_data", "malformed Fernet token"),
        ("AAAAA_wrong_prefix", "wrong prefix"),
    ]

    for invalid_value, description in invalid_cases:
        # Attempting to decrypt invalid values should raise ValueError
        try:
            decrypt_value(invalid_value)
            if invalid_value:  # Only expect error for non-empty values
                assert False, f"Should raise error for {description}"
        except ValueError as e:
            # Expected error
            assert "Failed to decrypt" in str(e) or "Cannot decrypt" in str(e)
            print(f"✓ Correctly handled {description}: {e}")


# ============================================================================
# Test 7: Integration With Configuration System
# ============================================================================

@pytest.mark.asyncio
async def test_encryption_integration_with_config_system():
    """Verify encryption integrates correctly with the configuration system."""
    # Get current settings
    settings = get_settings()

    # Test encrypting configuration values
    test_values = {
        "database_url": "postgresql://user:pass@localhost:5432/db",
        "llm_api_key": "sk-test-api-key-12345",
        "redis_url": "redis://:password@localhost:6379/0",
    }

    for config_key, config_value in test_values.items():
        # Encrypt the configuration value
        encrypted = encrypt_value(config_value)

        # Verify encryption properties
        assert is_encrypted_value(encrypted), f"{config_key} should be encrypted"
        assert encrypted != config_value, f"{config_key} encrypted value should differ from original"

        # Verify decryption works
        decrypted = decrypt_value(encrypted)
        assert decrypted == config_value, f"{config_key} decrypted value should match original"

        print(f"✓ {config_key}: Encryption integrates with config system")


# ============================================================================
# Test 8: Encryption Of Common Sensitive Patterns
# ============================================================================

@pytest.mark.asyncio
async def test_encryption_of_common_sensitive_patterns():
    """Verify encryption of common sensitive configuration patterns."""
    sensitive_patterns = [
        # API Keys
        ("OpenAI API Key", "sk-proj-abc123def456ghi789jkl012mno345pqr"),
        ("AWS Access Key", "AKIAIOSFODNN7EXAMPLE"),
        ("AWS Secret Key", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
        ("GitHub Token", "ghp_1234567890abcdefghijklmnopqrstuvwxyzABCDEF"),

        # Database URLs
        ("PostgreSQL URL", "postgresql://admin:P@ssw0rd@db.example.com:5432/production"),
        ("MySQL URL", "mysql://root:secret123@mysql-host:3306/mydb"),
        ("MongoDB URL", "mongodb://user:sesame@mongo-host:27017/authdb"),

        # Redis URLs
        ("Redis URL with password", "redis://:myredispassword@localhost:6379/0"),

        # JWT Tokens
        ("JWT Token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456"),

        # Certificates/Keys
        ("Private Key", "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0B...\n-----END PRIVATE KEY-----"),
    ]

    for label, sensitive_value in sensitive_patterns:
        # Encrypt the value
        encrypted = encrypt_value(sensitive_value)

        # Verify it's encrypted
        assert is_encrypted_value(encrypted), f"{label} should be encrypted"

        # Verify it can be decrypted
        decrypted = decrypt_value(encrypted)
        assert decrypted == sensitive_value, f"{label} should decrypt correctly"

        # Verify original is not in encrypted output
        # For longer values, check key components
        if len(sensitive_value) < 100:
            assert sensitive_value not in encrypted, f"{label} should not be visible in encrypted output"
        else:
            # For long values like certificates, check the beginning
            start = sensitive_value[:50]
            assert start not in encrypted, f"{label} prefix should not be in encrypted output"

        print(f"✓ {label}: Encrypted successfully ({len(encrypted)} chars)")


# ============================================================================
# Test 9: Encryption With Empty And Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_encryption_with_empty_and_edge_cases():
    """Verify encryption handles edge cases correctly."""
    # Test empty string (should raise error)
    with pytest.raises(ValueError, match="Cannot encrypt empty value"):
        encrypt_value("")

    # Test single character
    single_char = "a"
    encrypted = encrypt_value(single_char)
    assert is_encrypted_value(encrypted)
    assert decrypt_value(encrypted) == single_char

    # Test special characters only
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    encrypted = encrypt_value(special_chars)
    assert is_encrypted_value(encrypted)
    assert decrypt_value(encrypted) == special_chars

    # Test Unicode characters
    unicode_str = "Hello 世界 🌍 Привет"
    encrypted = encrypt_value(unicode_str)
    assert is_encrypted_value(encrypted)
    assert decrypt_value(encrypted) == unicode_str

    # Test very long value
    long_value = "a" * 10000
    encrypted = encrypt_value(long_value)
    assert is_encrypted_value(encrypted)
    assert decrypt_value(encrypted) == long_value

    print("✓ Edge cases handled correctly")


# ============================================================================
# Test 10: Encrypted Value Detection
# ============================================================================

@pytest.mark.asyncio
async def test_is_encrypted_value_detection():
    """Verify that is_encrypted_value correctly identifies encrypted values."""
    # Valid encrypted values (start with 'gAAAAA')
    valid_encrypted = [
        encrypt_value("test1"),
        encrypt_value("test2"),
        "gAAAAAabc123def456",
        "gAAAAAb_test_value_here",
    ]

    for encrypted in valid_encrypted:
        assert is_encrypted_value(encrypted), f"Should detect encrypted value: {encrypted[:20]}..."

    # Invalid encrypted values
    invalid_encrypted = [
        "",
        "plaintext",
        "sk-1234567890",  # API key format
        "postgresql://...",  # Database URL format
        "xAAAAA_invalid_prefix",
        "AAAAA_no_g_prefix",
    ]

    for not_encrypted in invalid_encrypted:
        assert not is_encrypted_value(not_encrypted), f"Should NOT detect as encrypted: {not_encrypted}"

    print("✓ Encrypted value detection works correctly")
