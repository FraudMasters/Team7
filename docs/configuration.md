# Configuration Management

This guide explains how to configure the Resume Analysis Platform across different environments (development, staging, production).

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Backend Configuration](#backend-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Hot Reload](#hot-reload)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The platform uses a centralized configuration management system with:

- **Environment-specific profiles** - Separate configurations for dev, staging, and production
- **Environment variables** - Override settings via environment variables
- **YAML config files** - Store environment-specific settings in version control
- **Hot reload** - Update non-critical settings without restarting services
- **Configuration validation** - Startup validation prevents invalid configurations
- **Audit logging** - Track all configuration changes

## Quick Start

### Backend Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Set your environment:
   ```bash
   export ENVIRONMENT=dev  # or 'staging' or 'production'
   ```

3. Update `.env` with your values:
   ```bash
   # Database
   DATABASE_URL=postgresql://user:pass@localhost:5432/resume_analysis

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # LLM API Keys
   ZAI_API_KEY=your_api_key_here
   ```

4. Start the backend:
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

### Frontend Setup

1. Copy the environment template:
   ```bash
   cp frontend/.env.example frontend/.env
   ```

2. Update `frontend/.env` with your values:
   ```bash
   VITE_API_URL=http://localhost:8000
   VITE_APP_TITLE=Resume Analysis Platform
   ```

3. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Environment Configuration

### Development (dev)

Optimized for local development:
- DEBUG logging level
- Local services (localhost)
- 20MB upload limit
- Backups disabled
- Detailed error messages

**Config file:** `backend/config/config.dev.yml`

### Staging

Pre-production testing environment:
- INFO logging level
- Staging URLs
- 10MB upload limit
- 7-day backup retention
- Production-like settings

**Config file:** `backend/config/config.staging.yml`

### Production

Production deployment:
- WARNING logging level
- Production URLs
- 10MB upload limit
- 30-day backup retention
- Strict security settings

**Config file:** `backend/config/config.production.yml`

## Backend Configuration

### Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://postgres:postgres@localhost:5432/resume_analysis` |

Example:
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Redis Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/0` |

### Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_HOST` | Host to bind the FastAPI server | `0.0.0.0` |
| `BACKEND_PORT` | Port to bind the FastAPI server | `8000` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` |

### LLM API Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai, anthropic, google, zai) | `zai` |
| `ZAI_API_KEY` | Z.ai API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GOOGLE_API_KEY` | Google API key | - |
| `LLM_MODEL` | Default LLM model | `glm-4.7` |
| `LLM_TEMPERATURE` | Temperature for LLM calls (0.0-1.0) | `0.1` |
| `LLM_MAX_TOKENS` | Maximum tokens for LLM responses | `4096` |

### ATS Simulation Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ATS_THRESHOLD` | Minimum ATS score to pass (0.0-1.0) | `0.6` |
| `ATS_VISUAL_CHECK_ENABLED` | Enable visual format checking | `true` |
| `ATS_KEYWORD_WEIGHT` | Weight for keyword matching (0.0-1.0) | `0.3` |
| `ATS_EXPERIENCE_WEIGHT` | Weight for experience matching (0.0-1.0) | `0.3` |
| `ATS_EDUCATION_WEIGHT` | Weight for education matching (0.0-1.0) | `0.2` |
| `ATS_FIT_WEIGHT` | Weight for overall fit (0.0-1.0) | `0.2` |

### File Upload Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size in MB | `10` |
| `ALLOWED_FILE_TYPES` | Allowed file extensions | `.pdf,.docx` |
| `ANALYSIS_TIMEOUT_SECONDS` | Maximum analysis time in seconds | `300` |

### Backup Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKUP_ENABLED` | Enable automated backups | `true` |
| `BACKUP_RETENTION_DAYS` | Backup retention period in days | `30` |
| `BACKUP_SCHEDULE` | Cron expression for backups | `0 2 * * *` |
| `BACKUP_DIR` | Directory for backup files | `./data/backups` |

### S3 Backup Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKUP_S3_ENABLED` | Enable S3 off-site backup | `false` |
| `BACKUP_S3_BUCKET` | S3 bucket name for backups | - |
| `BACKUP_S3_ENDPOINT` | S3-compatible endpoint URL | - |
| `BACKUP_S3_ACCESS_KEY` | S3 access key ID | - |
| `BACKUP_S3_SECRET_KEY` | S3 secret access key | - |
| `BACKUP_S3_REGION` | S3 region | `us-east-1` |

### Logging Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `AUDIT_LOG_RETENTION_DAYS` | Audit log retention in days | `90` |

## Frontend Configuration

### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_API_TIMEOUT` | API timeout in milliseconds | `120000` |
| `VITE_API_RETRY_ENABLED` | Enable API request retry | `true` |
| `VITE_API_RETRY_MAX_ATTEMPTS` | Maximum number of retries | `3` |

### Application Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_APP_TITLE` | Application title | `Resume Analysis Platform` |
| `VITE_APP_DESCRIPTION` | Application description for SEO | `AI-powered resume analysis...` |
| `VITE_APP_VERSION` | Application version | `1.0.0` |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_ENABLE_DARK_MODE` | Enable dark mode | `false` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `false` |
| `VITE_ENABLE_ERROR_TRACKING` | Enable error tracking | `false` |
| `VITE_ENABLE_EXPERIMENTAL_FEATURES` | Enable experimental features | `false` |

### Upload Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_MAX_UPLOAD_SIZE_MB` | Maximum upload size in MB | `10` |
| `VITE_ALLOWED_FILE_TYPES` | Allowed file extensions | `.pdf,.docx` |
| `VITE_ENABLE_DRAG_DROP` | Enable drag-and-drop upload | `true` |

### UI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEFAULT_LANGUAGE` | Default language (en, ru) | `en` |
| `VITE_SUPPORTED_LANGUAGES` | Supported languages | `en,ru` |
| `VITE_THEME` | Theme (light, dark, auto) | `light` |
| `VITE_PRIMARY_COLOR` | Primary color (hex) | `#1976d2` |
| `VITE_SECONDARY_COLOR` | Secondary color (hex) | `#dc004e` |

## Hot Reload

Non-critical configuration settings can be reloaded without restarting the backend service.

### Reloadable Settings

The following settings can be hot-reloaded:
- `LOG_LEVEL`
- `MAX_UPLOAD_SIZE_MB`
- `ALLOWED_FILE_TYPES`
- `ANALYSIS_TIMEOUT_SECONDS`
- All LLM settings (provider, model, temperature, tokens)
- All ATS settings (threshold, weights, visual check)
- All backup settings (except S3 credentials)
- `BACKUP_RETENTION_DAYS`
- `AUDIT_LOG_RETENTION_DAYS`

### Triggering a Reload

```bash
curl -X POST http://localhost:8000/api/config/reload
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "changed_settings": ["log_level", "max_upload_size_mb"],
  "previous_config": {
    "log_level": "INFO",
    "max_upload_size_mb": 10
  },
  "new_config": {
    "log_level": "DEBUG",
    "max_upload_size_mb": 20
  },
  "reloaded_at": "2026-02-07T00:30:00Z"
}
```

### Critical Settings

The following settings require a service restart:
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `BACKEND_HOST`
- `BACKEND_PORT`

## Security Best Practices

### 1. Never Commit Secrets

**DO NOT commit:**
- API keys
- Database passwords
- S3 credentials
- Encryption keys

**DO commit:**
- `.env.example` files (with placeholder values)
- `config.*.yml` files (without secrets)

### 2. Use Environment Variables

Store sensitive values in environment variables:

```bash
# .env file (not in version control)
ZAI_API_KEY=sk-your-actual-key
DATABASE_URL=postgresql://user:password@host/db
```

### 3. Encrypt Sensitive Configuration

Use built-in encryption for sensitive values:

```python
from config.encryption import encrypt_value

# Encrypt a value
encrypted = encrypt_value("my_secret_key")
# Returns: gAAAAAbl...

# Store in config as encrypted value
# Decrypt automatically on load
```

### 4. Use Different Values per Environment

| Setting | Dev | Staging | Production |
|---------|-----|---------|------------|
| Database | localhost | staging-db | prod-db-replica |
| Log Level | DEBUG | INFO | WARNING |
| Backup Retention | Disabled | 7 days | 30 days |

## Troubleshooting

### Configuration Not Loading

**Problem:** Environment variables not being read.

**Solution:**
1. Ensure `.env` file exists in the backend directory
2. Check that variables are properly formatted (no spaces around `=`)
3. Verify `ENVIRONMENT` variable is set

```bash
echo $ENVIRONMENT  # Should output: dev, staging, or production
```

### Validation Errors on Startup

**Problem:** Service fails to start with validation error.

**Solution:**
1. Check the error message for the specific setting
2. Verify the value matches the expected format
3. Check ranges for numeric values

```bash
# Example: Log level must be valid
LOG_LEVEL=DEBUG  # Valid
LOG_LEVEL=TRACE  # Invalid - not a valid level
```

### Hot Reload Not Working

**Problem:** Settings not updating after reload call.

**Solution:**
1. Verify the setting is in the reloadable list
2. Check that critical settings haven't changed (requires restart)
3. Review the audit log for reload errors

```bash
curl http://localhost:8000/api/config/audit-logs | jq
```

### Database Connection Issues

**Problem:** Cannot connect to database.

**Solution:**
1. Verify `DATABASE_URL` format:
   ```
   postgresql://user:password@host:port/database
   ```
2. Check database is running
3. Verify network connectivity

### Permission Errors

**Problem:** Cannot write to backup directory.

**Solution:**
1. Check `BACKUP_DIR` exists and is writable
2. Verify file permissions

```bash
mkdir -p ./data/backups
chmod 755 ./data/backups
```

## API Endpoints

### Configuration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/config/reload` | POST | Reload configuration (hot-reload) |
| `/api/config/health` | GET | Check configuration health |
| `/api/config/audit-logs` | GET | Get configuration audit trail |
| `/api/config/action-types` | GET | Get available audit action types |

For complete API documentation, see [API Reference](./configuration/reference.md).

## Additional Resources

- [Configuration Reference](./configuration/reference.md) - Complete list of all options
- [Backend Config README](../backend/config/README.md) - Backend module documentation
- [Frontend .env.example](../frontend/.env.example) - Frontend environment template
