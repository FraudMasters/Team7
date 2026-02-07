# Backend Configuration Module

This module provides centralized configuration management for the Resume Analysis Platform backend.

## Overview

The configuration system provides:

- **Environment-specific profiles** - Separate configurations for development, staging, and production
- **Environment variable overrides** - Override any setting via environment variables
- **YAML config files** - Store environment-specific settings in version control
- **Configuration validation** - Startup validation prevents invalid configurations
- **Hot-reload support** - Update non-critical settings without restarting
- **Audit logging** - Track all configuration changes
- **Encryption support** - Encrypt sensitive values like API keys

## Quick Start

```python
from config import get_settings

# Load configuration for current environment
settings = get_settings()

# Access configuration values
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
print(f"Log Level: {settings.log_level}")
print(f"Max Upload Size: {settings.max_upload_size_mb}MB")
```

## Module Structure

```
backend/config/
├── __init__.py              # Public API exports
├── base.py                  # BaseConfig class with all settings
├── environments.py          # Environment-specific config classes
├── validators.py            # Configuration validation functions
├── validation.py            # Full validation suite
├── encryption.py            # Sensitive value encryption/decryption
├── audit.py                 # Configuration change audit logging
├── hotreload.py             # Hot-reload functionality
├── config.dev.yml           # Development environment config
├── config.staging.yml       # Staging environment config
└── config.production.yml    # Production environment config
```

## Public API

### `get_settings()`

Get the current configuration instance.

```python
from config import get_settings

settings = get_settings()
print(settings.environment)
```

**Returns:** `BaseConfig` instance

### `get_environment_config(environment)`

Get configuration for a specific environment.

```python
from config import get_environment_config

# Get development config
dev_config = get_environment_config("development")

# Get production config
prod_config = get_environment_config("production")
```

**Parameters:**
- `environment` (str): Environment name (`development`, `staging`, `production`)

**Returns:** `BaseConfig` instance

**Raises:** `ValueError` if environment is not recognized

### `load_config_file(environment)`

Load configuration from YAML config file.

```python
from config import load_config_file

# Load config based on ENVIRONMENT variable
config = load_config_file()

# Load specific environment config
config = load_config_file("dev")
```

**Parameters:**
- `environment` (str, optional): Environment name (`dev`, `staging`, `production`, or full names)

**Returns:** `BaseConfig` instance

**Raises:** `ValueError` if environment is invalid, `FileNotFoundError` if config file doesn't exist

## Configuration Classes

### `BaseConfig`

Base configuration class with all common settings.

**Key Attributes:**

```python
class BaseConfig(BaseSettings):
    # Environment
    environment: str

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Server
    backend_host: str
    backend_port: int
    frontend_url: str

    # File Upload
    max_upload_size_mb: int
    allowed_file_types: str

    # Logging
    log_level: str

    # LLM
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int

    # ATS
    ats_threshold: float
    ats_keyword_weight: float
    ats_experience_weight: float

    # Backup
    backup_enabled: bool
    backup_retention_days: int
    backup_dir: Path

    # Audit
    audit_log_retention_days: int
```

**Computed Properties:**

- `max_upload_size_bytes` - Upload limit converted to bytes
- `cors_origins` - List of allowed CORS origins
- `get_db_url_async()` - Async database URL for SQLAlchemy

### `DevelopmentConfig`

Development environment configuration.

**Overrides:**
- `log_level`: `DEBUG`
- `backend_host`: `127.0.0.1`
- `max_upload_size_mb`: `20`
- `analysis_timeout_seconds`: `600`
- `backup_enabled`: `False`

### `StagingConfig`

Staging environment configuration.

**Overrides:**
- `log_level`: `INFO`
- `frontend_url`: `https://staging.example.com`
- `max_upload_size_mb`: `10`
- `backup_retention_days`: `7`
- `audit_log_retention_days`: `30`

### `ProductionConfig`

Production environment configuration.

**Overrides:**
- `log_level`: `WARNING`
- `frontend_url`: `https://app.example.com`
- `max_upload_size_mb`: `10`
- `backup_retention_days`: `30`
- `audit_log_retention_days`: `90`

## Configuration Loading

The configuration system loads settings in the following priority order (highest to lowest):

1. **Environment variables** - Highest priority
2. **YAML config file** - Environment-specific overrides
3. **Class defaults** - Default values from config class

### Example Loading Process

```python
# 1. Set environment variable
export DATABASE_URL=postgresql://prod-db:5432/app

# 2. YAML config file (config.production.yml)
# database_url: postgresql://localhost:5432/app

# 3. Class default (base.py)
# database_url: str = Field(default="postgresql://localhost:5432/app")

# Result: Environment variable wins
settings = get_settings()
print(settings.database_url)
# Output: postgresql://prod-db:5432/app
```

## Validation

Configuration is validated on startup. If validation fails, the application will not start.

### Built-in Validators

```python
from config.validation import validate_config

settings = get_settings()
errors = validate_config(settings)

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
```

### Validation Checks

- `database_url` - Valid PostgreSQL connection string format
- `log_level` - Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `max_upload_size_mb` - Must be between 1-100
- `analysis_timeout_seconds` - Must be between 30-600
- `llm_temperature` - Must be between 0.0-1.0
- `ats_threshold` - Must be between 0.0-1.0
- `backup_retention_days` - Must be between 1-365

### Custom Validation

Add custom validators by using Pydantic decorators:

```python
from pydantic import field_validator

class BaseConfig(BaseSettings):
    my_setting: str = Field(default="value")

    @field_validator("my_setting")
    @classmethod
    def validate_my_setting(cls, v: str) -> str:
        if not v.startswith("prefix_"):
            raise ValueError("my_setting must start with prefix_")
        return v
```

## Encryption

Sensitive configuration values can be encrypted at rest.

### Encrypt a Value

```python
from config.encryption import encrypt_value

# Encrypt a sensitive value
encrypted = encrypt_value("my_api_key")
# Returns: gAAAAAbl...

# Store in environment variable
# export MY_API_KEY=gAAAAAbl...
```

### Decrypt a Value

```python
from config import get_settings

settings = get_settings()

# Encrypted values are automatically decrypted
api_key = settings.my_api_key  # Returns decrypted value
```

### Encryption Keys

Set the encryption key via environment variable:

```bash
# Generate a new key
python -c "from config.encryption import generate_encryption_key; print(generate_encryption_key())"

# Set the key
export CONFIG_ENCRYPTION_KEY=your-generated-key
```

**Security Note:** In production, use a secure key management system (AWS KMS, HashiCorp Vault, etc.) to store the encryption key.

## Audit Logging

All configuration changes are logged to the audit trail.

### Log a Configuration Change

```python
from config.audit import log_config_change

log_config_change(
    action="SETTING_UPDATED",
    setting_name="log_level",
    previous_value="INFO",
    new_value="DEBUG",
    changed_by="admin@example.com"
)
```

### Use as Decorator

```python
from config.audit import audit_config_change

@audit_config_change("llm_temperature")
def update_temperature(new_temp: float):
    # Update temperature
    pass
```

### Use as Context Manager

```python
from config.audit import ConfigAuditLogger

with ConfigAuditLogger("batch_update", changed_by="system"):
    # Multiple config changes
    setting1.value = "new1"
    setting2.value = "new2"
    # All changes logged together
```

### Query Audit Logs

```python
from models.config_change import ConfigChange, ConfigChangeAction

# Get recent changes
changes = (
    ConfigChange.select()
    .where(ConfigChange.action == ConfigChangeAction.SETTING_UPDATED)
    .order_by(ConfigChange.changed_at.desc())
    .limit(10)
)

for change in changes:
    print(f"{change.setting_name}: {change.previous_value} -> {change.new_value}")
```

## Hot Reload

Non-critical settings can be reloaded without restarting the service.

### Reloadable Settings

The following settings can be hot-reloaded:

```python
RELOADABLE_SETTINGS = {
    "log_level",
    "max_upload_size_mb",
    "allowed_file_types",
    "analysis_timeout_seconds",
    "llm_provider",
    "llm_model",
    "llm_temperature",
    "llm_max_tokens",
    "ats_threshold",
    "ats_visual_check_enabled",
    "ats_keyword_weight",
    "ats_experience_weight",
    "ats_education_weight",
    "ats_fit_weight",
    "backup_enabled",
    "backup_retention_days",
    "backup_schedule",
    "backup_notification_email",
    "backup_incremental_enabled",
    "backup_compression_enabled",
    "audit_log_retention_days",
}
```

### Critical Settings (Require Restart)

These settings cannot be hot-reloaded and require a service restart:

- `database_url`
- `redis_url`
- `celery_broker_url`
- `celery_result_backend`
- `backend_host`
- `backend_port`

### Trigger Hot Reload

Via API:

```bash
curl -X POST http://localhost:8000/api/config/reload
```

Via Python:

```python
from config.hotreload import reload_settings

result = reload_settings()
print(result["message"])
```

## Environment Files

### Development (`config.dev.yml`)

```yaml
environment: dev
log_level: DEBUG
backend_host: 127.0.0.1
backend_port: 8000
frontend_url: http://localhost:5173
max_upload_size_mb: 20
analysis_timeout_seconds: 600
backup_enabled: false
```

### Staging (`config.staging.yml`)

```yaml
environment: staging
log_level: INFO
frontend_url: https://staging.example.com
max_upload_size_mb: 10
backup_retention_days: 7
audit_log_retention_days: 30
```

### Production (`config.production.yml`)

```yaml
environment: production
log_level: WARNING
frontend_url: https://app.example.com
max_upload_size_mb: 10
backup_retention_days: 30
audit_log_retention_days: 90
```

## Best Practices

### 1. Use Environment Variables for Secrets

```bash
# Good: Use environment variable
export ZAI_API_KEY=sk-actual-key

# Bad: Hardcode in config file
# zai_api_key: sk-actual-key
```

### 2. Use YAML for Non-Sensitive Settings

```yaml
# config.production.yml
log_level: WARNING
max_upload_size_mb: 10
backup_enabled: true
```

### 3. Validate on Startup

```python
# In main.py
from config import get_settings
from config.validation import validate_config

settings = get_settings()
errors = validate_config(settings)

if errors:
    logger.error(f"Configuration errors: {errors}")
    sys.exit(1)
```

### 4. Use Type Hints

```python
def process_upload(settings: BaseConfig, file_data: bytes):
    max_size = settings.max_upload_size_bytes
    if len(file_data) > max_size:
        raise ValueError("File too large")
```

### 5. Document Custom Settings

```python
class BaseConfig(BaseSettings):
    """Application settings.

    Attributes:
        my_custom_setting: Description of what this does and valid values.
    """
    my_custom_setting: str = Field(
        default="default_value",
        description="Clear description of the setting",
    )
```

## Testing

### Unit Tests

```python
import pytest
from config import get_settings

def test_default_config():
    settings = get_settings()
    assert settings.environment == "development"
    assert settings.log_level == "DEBUG"

def test_config_override():
    import os
    os.environ["LOG_LEVEL"] = "ERROR"
    settings = get_settings()
    assert settings.log_level == "ERROR"
```

### Validation Tests

```python
from config.validation import validate_config
from config import get_settings

def test_validation_passes():
    settings = get_settings()
    errors = validate_config(settings)
    assert len(errors) == 0

def test_invalid_upload_size():
    settings = get_settings()
    settings.max_upload_size_mb = 200  # Over limit
    errors = validate_config(settings)
    assert len(errors) > 0
    assert "max_upload_size_mb" in str(errors)
```

## Troubleshooting

### Configuration Not Loading

**Problem:** Environment variables not being read.

**Solution:**
1. Ensure `.env` file exists in the backend directory
2. Check that variables are properly formatted
3. Verify `ENVIRONMENT` variable is set

```python
import os
print(os.getenv("ENVIRONMENT"))  # Should be: dev, staging, or production
```

### Validation Errors

**Problem:** Service fails to start with validation error.

**Solution:**
1. Check the specific error message
2. Verify the value matches expected format
3. Check numeric ranges

```python
from config.validation import validate_config
from config import get_settings

settings = get_settings()
errors = validate_config(settings)
for error in errors:
    print(error)
```

### Import Errors

**Problem:** `ImportError: No module named 'config'`

**Solution:**
```bash
# Ensure backend directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from backend directory
cd backend
python -c "from config import get_settings"
```

## API Endpoints

The configuration module exposes the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/config/reload` | POST | Reload configuration (hot-reload) |
| `/api/config/health` | GET | Check configuration health |
| `/api/config/audit-logs` | GET | Get configuration audit trail |
| `/api/config/action-types` | GET | Get available audit action types |

For full API documentation, see [Configuration Reference](../../docs/configuration/reference.md).

## Additional Resources

- [Main Configuration Guide](../../docs/configuration.md)
- [Configuration Reference](../../docs/configuration/reference.md)
- [Frontend Configuration](../../frontend/.env.example)
