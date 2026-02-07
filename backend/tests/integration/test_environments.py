"""
Integration Tests for Environment-Specific Configuration

This test module verifies that environment-specific configurations (dev, staging, production)
are loaded correctly and have the expected overrides and values for each environment.

Test Coverage:
- Development configuration loads with correct values
- Staging configuration loads with correct values
- Production configuration loads with correct values
- Environment-specific overrides are applied correctly
- Configuration values match expected defaults for each environment
"""
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.environments import (
    load_config_file,
    get_environment_config,
    DevelopmentConfig,
    StagingConfig,
    ProductionConfig,
)
from config.base import BaseConfig


# ============================================================================
# Test 1: Development Environment Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_load_development_config_from_yaml():
    """Verify that development config loads correctly from YAML file."""
    # Set environment to dev
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "dev"

    try:
        # Load config from YAML file
        config = load_config_file()

        # Verify environment
        assert config.environment == "dev", f"Expected 'dev', got '{config.environment}'"

        # Verify log level (DEBUG for development)
        assert config.log_level == "DEBUG", f"Expected DEBUG, got {config.log_level}"

        # Verify server configuration
        assert config.backend_host == "127.0.0.1", f"Expected 127.0.0.1, got {config.backend_host}"
        assert config.backend_port == 8000, f"Expected 8000, got {config.backend_port}"
        assert config.frontend_url == "http://localhost:5173", f"Expected http://localhost:5173, got {config.frontend_url}"

        # Verify upload settings (more permissive in dev)
        assert config.max_upload_size_mb == 20, f"Expected 20MB, got {config.max_upload_size_mb}"
        assert config.analysis_timeout_seconds == 600, f"Expected 600s, got {config.analysis_timeout_seconds}"

        # Verify backup is disabled in development
        assert config.backup_enabled is False, "Expected backup_enabled to be False in dev"
        assert config.backup_retention_days == 7, f"Expected 7 days, got {config.backup_retention_days}"

        # Verify audit log retention (shorter in dev)
        assert config.audit_log_retention_days == 7, f"Expected 7 days, got {config.audit_log_retention_days}"

        # Verify LLM settings
        assert config.llm_provider == "zai", f"Expected 'zai', got {config.llm_provider}"
        assert config.llm_model == "glm-4.7", f"Expected 'glm-4.7', got {config.llm_model}"
        assert config.llm_temperature == 0.1, f"Expected 0.1, got {config.llm_temperature}"

        # Verify S3 backup is disabled
        assert config.backup_s3_enabled is False, "Expected S3 backup to be disabled in dev"
        assert config.backup_incremental_enabled is False, "Expected incremental backup to be disabled in dev"
        assert config.backup_compression_enabled is False, "Expected compression to be disabled in dev"

        print(f"✓ Development config loaded correctly: environment={config.environment}, log_level={config.log_level}")

    finally:
        # Restore original environment
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_development_config_class():
    """Verify that DevelopmentConfig class has correct defaults."""
    config = DevelopmentConfig()

    # Verify environment name
    assert config.environment == "development"

    # Verify log level is DEBUG
    assert config.log_level == "DEBUG"

    # Verify backup is disabled by default
    assert config.backup_enabled is False

    # Verify larger upload size for development
    assert config.max_upload_size_mb == 20

    print(f"✓ DevelopmentConfig class has correct defaults")


# ============================================================================
# Test 2: Staging Environment Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_load_staging_config_from_yaml():
    """Verify that staging config loads correctly from YAML file."""
    # Set environment to staging
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "staging"

    try:
        # Load config from YAML file
        config = load_config_file()

        # Verify environment
        assert config.environment == "staging", f"Expected 'staging', got '{config.environment}'"

        # Verify log level (INFO for staging)
        assert config.log_level == "INFO", f"Expected INFO, got {config.log_level}"

        # Verify server configuration
        assert config.backend_host == "0.0.0.0", f"Expected 0.0.0.0, got {config.backend_host}"
        assert config.backend_port == 8000, f"Expected 8000, got {config.backend_port}"
        assert config.frontend_url == "https://staging.example.com", f"Expected staging URL, got {config.frontend_url}"

        # Verify upload settings (moderate in staging)
        assert config.max_upload_size_mb == 10, f"Expected 10MB, got {config.max_upload_size_mb}"
        assert config.analysis_timeout_seconds == 300, f"Expected 300s, got {config.analysis_timeout_seconds}"

        # Verify backup is enabled with shorter retention
        assert config.backup_enabled is True, "Expected backup_enabled to be True in staging"
        assert config.backup_retention_days == 7, f"Expected 7 days, got {config.backup_retention_days}"

        # Verify audit log retention (moderate in staging)
        assert config.audit_log_retention_days == 30, f"Expected 30 days, got {config.audit_log_retention_days}"

        # Verify LLM settings
        assert config.llm_provider == "zai", f"Expected 'zai', got {config.llm_provider}"
        assert config.llm_model == "glm-4.7", f"Expected 'glm-4.7', got {config.llm_model}"

        # Verify S3 backup settings (can be enabled in staging but defaults to false)
        assert config.backup_s3_enabled is False, "Expected S3 backup to be disabled by default in staging"
        assert config.backup_s3_bucket == "staging-resume-backups", f"Expected staging bucket, got {config.backup_s3_bucket}"

        # Verify backup features
        assert config.backup_incremental_enabled is True, "Expected incremental backup to be enabled"
        assert config.backup_compression_enabled is True, "Expected compression to be enabled"

        print(f"✓ Staging config loaded correctly: environment={config.environment}, log_level={config.log_level}")

    finally:
        # Restore original environment
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_staging_config_class():
    """Verify that StagingConfig class has correct defaults."""
    config = StagingConfig()

    # Verify environment name
    assert config.environment == "staging"

    # Verify log level is INFO
    assert config.log_level == "INFO"

    # Verify backup is enabled with shorter retention
    assert config.backup_enabled is True
    assert config.backup_retention_days == 7
    assert config.audit_log_retention_days == 30

    # Verify moderate upload size
    assert config.max_upload_size_mb == 10

    # Verify staging URL is set
    assert "staging" in config.frontend_url.lower()

    print(f"✓ StagingConfig class has correct defaults")


# ============================================================================
# Test 3: Production Environment Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_load_production_config_from_yaml():
    """Verify that production config loads correctly from YAML file."""
    # Set environment to production
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"

    try:
        # Load config from YAML file
        config = load_config_file()

        # Verify environment
        assert config.environment == "production", f"Expected 'production', got '{config.environment}'"

        # Verify log level (WARNING for production - less verbose)
        assert config.log_level == "WARNING", f"Expected WARNING, got {config.log_level}"

        # Verify server configuration
        assert config.backend_host == "0.0.0.0", f"Expected 0.0.0.0, got {config.backend_host}"
        assert config.backend_port == 8000, f"Expected 8000, got {config.backend_port}"
        assert config.frontend_url == "https://app.example.com", f"Expected production URL, got {config.frontend_url}"

        # Verify upload settings (standard in production)
        assert config.max_upload_size_mb == 10, f"Expected 10MB, got {config.max_upload_size_mb}"
        assert config.analysis_timeout_seconds == 300, f"Expected 300s, got {config.analysis_timeout_seconds}"

        # Verify backup is enabled with full retention
        assert config.backup_enabled is True, "Expected backup_enabled to be True in production"
        assert config.backup_retention_days == 30, f"Expected 30 days, got {config.backup_retention_days}"

        # Verify audit log retention (full in production)
        assert config.audit_log_retention_days == 90, f"Expected 90 days, got {config.audit_log_retention_days}"

        # Verify LLM settings
        assert config.llm_provider == "zai", f"Expected 'zai', got {config.llm_provider}"
        assert config.llm_model == "glm-4.7", f"Expected 'glm-4.7', got {config.llm_model}"

        # Verify S3 backup is enabled in production
        assert config.backup_s3_enabled is True, "Expected S3 backup to be enabled in production"
        assert config.backup_s3_bucket == "prod-resume-backups", f"Expected prod bucket, got {config.backup_s3_bucket}"
        assert config.backup_s3_endpoint == "https://s3.amazonaws.com", f"Expected S3 endpoint, got {config.backup_s3_endpoint}"
        assert config.backup_s3_region == "us-east-1", f"Expected us-east-1, got {config.backup_s3_region}"

        # Verify backup notification email
        assert config.backup_notification_email == "ops@example.com", f"Expected notification email, got {config.backup_notification_email}"

        # Verify backup features
        assert config.backup_incremental_enabled is True, "Expected incremental backup to be enabled"
        assert config.backup_compression_enabled is True, "Expected compression to be enabled"

        print(f"✓ Production config loaded correctly: environment={config.environment}, log_level={config.log_level}")

    finally:
        # Restore original environment
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_production_config_class():
    """Verify that ProductionConfig class has correct defaults."""
    config = ProductionConfig()

    # Verify environment name
    assert config.environment == "production"

    # Verify log level is WARNING
    assert config.log_level == "WARNING"

    # Verify backup is enabled with full retention
    assert config.backup_enabled is True
    assert config.backup_retention_days == 30
    assert config.audit_log_retention_days == 90

    # Verify standard upload size
    assert config.max_upload_size_mb == 10

    print(f"✓ ProductionConfig class has correct defaults")


# ============================================================================
# Test 4: Environment-Specific Overrides
# ============================================================================

@pytest.mark.asyncio
async def test_environment_overrides_log_level():
    """Verify that each environment has the correct log level override."""
    configs = {
        "dev": ("dev", "DEBUG"),
        "staging": ("staging", "INFO"),
        "production": ("production", "WARNING"),
    }

    original_env = os.environ.get("ENVIRONMENT")

    try:
        for env_name, (env_param, expected_log_level) in configs.items():
            os.environ["ENVIRONMENT"] = env_name
            config = load_config_file()

            assert config.log_level == expected_log_level, (
                f"Environment {env_name}: Expected log_level={expected_log_level}, "
                f"got {config.log_level}"
            )

            print(f"✓ {env_name}: log_level={config.log_level}")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_environment_overrides_backup_settings():
    """Verify that backup settings are correctly overridden per environment."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Dev: backup disabled
        os.environ["ENVIRONMENT"] = "dev"
        dev_config = load_config_file()
        assert dev_config.backup_enabled is False, "Dev should have backup disabled"
        assert dev_config.backup_retention_days == 7, "Dev should have 7-day retention"

        # Staging: backup enabled with shorter retention
        os.environ["ENVIRONMENT"] = "staging"
        staging_config = load_config_file()
        assert staging_config.backup_enabled is True, "Staging should have backup enabled"
        assert staging_config.backup_retention_days == 7, "Staging should have 7-day retention"
        assert staging_config.audit_log_retention_days == 30, "Staging should have 30-day audit retention"

        # Production: backup enabled with full retention
        os.environ["ENVIRONMENT"] = "production"
        prod_config = load_config_file()
        assert prod_config.backup_enabled is True, "Production should have backup enabled"
        assert prod_config.backup_retention_days == 30, "Production should have 30-day retention"
        assert prod_config.audit_log_retention_days == 90, "Production should have 90-day audit retention"

        print(f"✓ Backup settings correctly override per environment")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_environment_overrides_upload_settings():
    """Verify that upload settings are correctly overridden per environment."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Dev: larger upload size and longer timeout
        os.environ["ENVIRONMENT"] = "dev"
        dev_config = load_config_file()
        assert dev_config.max_upload_size_mb == 20, f"Dev should have 20MB upload limit, got {dev_config.max_upload_size_mb}"
        assert dev_config.analysis_timeout_seconds == 600, f"Dev should have 600s timeout, got {dev_config.analysis_timeout_seconds}"

        # Staging: standard upload size and timeout
        os.environ["ENVIRONMENT"] = "staging"
        staging_config = load_config_file()
        assert staging_config.max_upload_size_mb == 10, f"Staging should have 10MB upload limit, got {staging_config.max_upload_size_mb}"
        assert staging_config.analysis_timeout_seconds == 300, f"Staging should have 300s timeout, got {staging_config.analysis_timeout_seconds}"

        # Production: standard upload size and timeout
        os.environ["ENVIRONMENT"] = "production"
        prod_config = load_config_file()
        assert prod_config.max_upload_size_mb == 10, f"Production should have 10MB upload limit, got {prod_config.max_upload_size_mb}"
        assert prod_config.analysis_timeout_seconds == 300, f"Production should have 300s timeout, got {prod_config.analysis_timeout_seconds}"

        print(f"✓ Upload settings correctly override per environment")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_environment_overrides_frontend_url():
    """Verify that frontend URL is correctly set per environment."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Dev: localhost
        os.environ["ENVIRONMENT"] = "dev"
        dev_config = load_config_file()
        assert dev_config.frontend_url == "http://localhost:5173", f"Dev frontend URL incorrect: {dev_config.frontend_url}"

        # Staging: staging URL
        os.environ["ENVIRONMENT"] = "staging"
        staging_config = load_config_file()
        assert staging_config.frontend_url == "https://staging.example.com", f"Staging frontend URL incorrect: {staging_config.frontend_url}"

        # Production: production URL
        os.environ["ENVIRONMENT"] = "production"
        prod_config = load_config_file()
        assert prod_config.frontend_url == "https://app.example.com", f"Production frontend URL incorrect: {prod_config.frontend_url}"

        print(f"✓ Frontend URL correctly set per environment")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_environment_overrides_s3_backup():
    """Verify that S3 backup settings are correctly configured per environment."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Dev: S3 disabled
        os.environ["ENVIRONMENT"] = "dev"
        dev_config = load_config_file()
        assert dev_config.backup_s3_enabled is False, "Dev should have S3 backup disabled"

        # Staging: S3 can be enabled but defaults to false
        os.environ["ENVIRONMENT"] = "staging"
        staging_config = load_config_file()
        assert staging_config.backup_s3_enabled is False, "Staging should have S3 backup disabled by default"
        assert staging_config.backup_s3_bucket == "staging-resume-backups", f"Staging bucket incorrect: {staging_config.backup_s3_bucket}"

        # Production: S3 enabled
        os.environ["ENVIRONMENT"] = "production"
        prod_config = load_config_file()
        assert prod_config.backup_s3_enabled is True, "Production should have S3 backup enabled"
        assert prod_config.backup_s3_bucket == "prod-resume-backups", f"Production bucket incorrect: {prod_config.backup_s3_bucket}"

        print(f"✓ S3 backup settings correctly configured per environment")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


# ============================================================================
# Test 5: Config Loading Functions
# ============================================================================

@pytest.mark.asyncio
async def test_get_environment_config_function():
    """Verify the get_environment_config function works correctly."""
    # Test getting config for each environment
    environments = ["development", "staging", "production"]

    for env in environments:
        config = get_environment_config(env)
        assert config is not None, f"Failed to get config for {env}"
        assert config.environment == env, f"Expected {env}, got {config.environment}"
        print(f"✓ get_environment_config('{env}') returns {config.environment} config")


@pytest.mark.asyncio
async def test_load_config_file_with_short_names():
    """Verify that load_config_file accepts both short and full environment names."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Test short names
        short_names = ["dev", "staging", "production"]

        for short_name in short_names:
            config = load_config_file(short_name)
            assert config is not None, f"Failed to load config for short name '{short_name}'"
            print(f"✓ load_config_file('{short_name}') works")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_load_config_file_with_full_names():
    """Verify that load_config_file accepts full environment names."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Test full names (development -> dev)
        config = load_config_file("development")
        assert config.environment == "dev", f"Expected 'dev', got {config.environment}"
        print(f"✓ load_config_file('development') maps to dev config")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


@pytest.mark.asyncio
async def test_load_config_file_invalid_environment():
    """Verify that load_config_file raises error for invalid environment."""
    import pytest

    with pytest.raises(ValueError) as exc_info:
        load_config_file("invalid_environment")

    assert "Invalid environment" in str(exc_info.value)
    print(f"✓ load_config_file raises ValueError for invalid environment")


# ============================================================================
# Test 6: Config File Existence
# ============================================================================

@pytest.mark.asyncio
async def test_environment_config_files_exist():
    """Verify that all environment config files exist."""
    config_dir = Path(__file__).parent.parent.parent / "config"

    required_files = [
        config_dir / "config.dev.yml",
        config_dir / "config.staging.yml",
        config_dir / "config.production.yml",
    ]

    for config_file in required_files:
        assert config_file.exists(), f"Config file not found: {config_file}"
        print(f"✓ Config file exists: {config_file.name}")


# ============================================================================
# Test 7: Environment-Specific ATS Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_ats_configuration_same_across_environments():
    """Verify that ATS simulation settings are consistent across environments."""
    original_env = os.environ.get("ENVIRONMENT")

    try:
        ats_settings = {}

        for env in ["dev", "staging", "production"]:
            os.environ["ENVIRONMENT"] = env
            config = load_config_file()

            ats_settings[env] = {
                "threshold": config.ats_threshold,
                "visual_check": config.ats_visual_check_enabled,
                "keyword_weight": config.ats_keyword_weight,
                "experience_weight": config.ats_experience_weight,
                "education_weight": config.ats_education_weight,
                "fit_weight": config.ats_fit_weight,
            }

        # Verify all environments have the same ATS settings
        dev_ats = ats_settings["dev"]
        staging_ats = ats_settings["staging"]
        prod_ats = ats_settings["production"]

        assert dev_ats == staging_ats, "Dev and staging ATS settings should match"
        assert staging_ats == prod_ats, "Staging and production ATS settings should match"

        print(f"✓ ATS configuration consistent across environments: threshold={dev_ats['threshold']}")

    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
