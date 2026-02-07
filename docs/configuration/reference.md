# Configuration Reference

Complete reference of all configuration options for the Resume Analysis Platform.

## Table of Contents

- [Backend Configuration](#backend-configuration)
  - [Environment Settings](#environment-settings)
  - [Database Configuration](#database-configuration)
  - [Redis Configuration](#redis-configuration)
  - [Server Configuration](#server-configuration)
  - [Frontend CORS Configuration](#frontend-cors-configuration)
  - [ML Models Configuration](#ml-models-configuration)
  - [LanguageTool Configuration](#languagetool-configuration)
  - [File Upload Configuration](#file-upload-configuration)
  - [Analysis Configuration](#analysis-configuration)
  - [Logging Configuration](#logging-configuration)
  - [Celery Configuration](#celery-configuration)
  - [Backup Configuration](#backup-configuration)
  - [S3 Backup Configuration](#s3-backup-configuration)
  - [Audit Log Configuration](#audit-log-configuration)
  - [LLM API Configuration](#llm-api-configuration)
  - [ATS Simulation Configuration](#ats-simulation-configuration)
- [Frontend Configuration](#frontend-configuration)
  - [API Configuration](#api-configuration)
  - [Application Configuration](#application-configuration)
  - [Feature Flags](#feature-flags)
  - [Upload Configuration](#upload-configuration)
  - [UI Configuration](#ui-configuration)
  - [Display Configuration](#display-configuration)
  - [Results Display Configuration](#results-display-configuration)
  - [Error Messages Configuration](#error-messages-configuration)
  - [Performance Configuration](#performance-configuration)
  - [Analytics Configuration](#analytics-configuration)
  - [Error Tracking Configuration](#error-tracking-configuration)
  - [Authentication Configuration](#authentication-configuration)
  - [Social Sharing Configuration](#social-sharing-configuration)
  - [Help & Support Configuration](#help--support-configuration)
  - [Third-Party Integrations](#third-party-integrations)
  - [Development Settings](#development-settings)
  - [Testing Configuration](#testing-configuration)
  - [Internationalization Configuration](#internationalization-configuration)
  - [File Upload Display](#file-upload-display)
  - [Accessibility Configuration](#accessibility-configuration)
  - [Notification Configuration](#notification-configuration)
  - [Export Configuration](#export-configuration)
  - [Cache Configuration](#cache-configuration)
  - [Rate Limiting Configuration](#rate-limiting-configuration)
  - [URL Configuration](#url-configuration)
  - [SEO Configuration](#seo-configuration)

---

## Backend Configuration

### Environment Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | string | `development` | Current environment name. Must be one of: `development`, `staging`, `production`. Controls which config profile is loaded. |

**Example:**
```bash
ENVIRONMENT=production
```

---

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `postgresql://postgres:postgres@localhost:5432/resume_analysis` | PostgreSQL database connection URL. Format: `postgresql://user:password@host:port/database`. |
| `database_url` | property | - | Async database URL with `asyncpg` driver. Auto-generated from `DATABASE_URL`. |

**Example:**
```bash
DATABASE_URL=postgresql://resume_user:secure_pass@db.example.com:5432/resume_db
```

**Validation:**
- Must be a valid PostgreSQL connection URL
- Must start with `postgresql://` scheme

---

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis connection URL for caching and Celery. Format: `redis://host:port/database`. |

**Example:**
```bash
REDIS_URL=redis://redis.example.com:6379/0
```

---

### Server Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKEND_HOST` | string | `0.0.0.0` | Host address to bind the FastAPI server. Use `0.0.0.0` to listen on all interfaces, `127.0.0.1` for localhost only. |
| `BACKEND_PORT` | integer | `8000` | Port to bind the FastAPI server. Must be between 1-65535. |

**Example:**
```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080
```

---

### Frontend CORS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FRONTEND_URL` | string | `http://localhost:5173` | Frontend URL for CORS configuration. This URL is added to CORS allowed origins. |
| `cors_origins` | property | - | List of allowed CORS origins. Auto-generated from `FRONTEND_URL` plus localhost variants. |

**Example:**
```bash
FRONTEND_URL=https://app.example.com
```

**Allowed origins include:**
- `FRONTEND_URL` value
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

---

### ML Models Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODELS_CACHE_PATH` | Path | `./models_cache` | Path to cache ML models. Directory will be created if it doesn't exist. |

**Example:**
```bash
MODELS_CACHE_PATH=/var/cache/resume_analysis/models
```

---

### LanguageTool Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LANGUAGETOOL_SERVER` | string | `null` | LanguageTool server URL for grammar checking. Optional - if not set, grammar checking is disabled. |

**Example:**
```bash
LANGUAGETOOL_SERVER=http://languagetool:8010
```

---

### File Upload Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | integer | `10` | Maximum file upload size in megabytes. Range: 1-100. |
| `ALLOWED_FILE_TYPES` | string | `.pdf,.docx` | Comma-separated list of allowed file extensions. Must include the dot prefix. |
| `max_upload_size_bytes` | property | - | Maximum upload size in bytes. Auto-calculated from `MAX_UPLOAD_SIZE_MB`. |

**Example:**
```bash
MAX_UPLOAD_SIZE_MB=20
ALLOWED_FILE_TYPES=.pdf,.docx,.txt
```

**Validation:**
- `MAX_UPLOAD_SIZE_MB`: must be between 1 and 100
- `ALLOWED_FILE_TYPES`: must start with `.` for each extension

---

### Analysis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ANALYSIS_TIMEOUT_SECONDS` | integer | `300` | Maximum time for resume analysis in seconds. Range: 30-600 (5 minutes max). |

**Example:**
```bash
ANALYSIS_TIMEOUT_SECONDS=600
```

---

### Logging Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level. Must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |

**Environment defaults:**
- Development: `DEBUG`
- Staging: `INFO`
- Production: `WARNING`

**Example:**
```bash
LOG_LEVEL=DEBUG
```

---

### Celery Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CELERY_BROKER_URL` | string | `redis://localhost:6379/0` | Celery message broker URL for task queues. |
| `CELERY_RESULT_BACKEND` | string | `redis://localhost:6379/0` | Celery result backend URL for storing task results. |

**Example:**
```bash
CELERY_BROKER_URL=redis://redis.example.com:6379/0
CELERY_RESULT_BACKEND=redis://redis.example.com:6379/0
```

---

### Backup Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKUP_ENABLED` | boolean | `true` | Enable automated backups. |
| `BACKUP_RETENTION_DAYS` | integer | `30` | Default backup retention period in days. Range: 1-365. |
| `BACKUP_SCHEDULE` | string | `0 2 * * *` | Cron expression for scheduled backups. Default: daily at 2 AM. |
| `BACKUP_DIR` | Path | `./data/backups` | Directory for storing backup files. |
| `BACKUP_NOTIFICATION_EMAIL` | string | `null` | Email address for backup failure notifications. Optional. |
| `BACKUP_INCREMENTAL_ENABLED` | boolean | `true` | Enable incremental backups (only backup changes). |
| `BACKUP_COMPRESSION_ENABLED` | boolean | `true` | Enable backup compression (gzip). |

**Environment defaults:**
| Environment | Retention | Enabled |
|-------------|-----------|---------|
| Development | 7 days | false |
| Staging | 7 days | true |
| Production | 30 days | true |

**Example:**
```bash
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_DIR=/var/backups/resume_analysis
BACKUP_NOTIFICATION_EMAIL=ops@example.com
```

**Cron schedule examples:**
| Schedule | Description |
|----------|-------------|
| `0 2 * * *` | Daily at 2:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 2 * * 0` | Weekly on Sunday at 2:00 AM |
| `0 2 1 * *` | Monthly on the 1st at 2:00 AM |

---

### S3 Backup Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKUP_S3_ENABLED` | boolean | `false` | Enable S3 off-site backup. |
| `BACKUP_S3_BUCKET` | string | `null` | S3 bucket name for backups. Required if S3 enabled. |
| `BACKUP_S3_ENDPOINT` | string | `null` | S3-compatible endpoint URL (e.g., for MinIO). Optional. |
| `BACKUP_S3_ACCESS_KEY` | string | `null` | S3 access key ID. Required if S3 enabled. |
| `BACKUP_S3_SECRET_KEY` | string | `null` | S3 secret access key. Required if S3 enabled. |
| `BACKUP_S3_REGION` | string | `us-east-1` | S3 region. |

**Example:**
```bash
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=my-app-backups
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
BACKUP_S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
BACKUP_S3_REGION=us-west-2
```

**Note:** For S3-compatible services like MinIO:
```bash
BACKUP_S3_ENDPOINT=http://minio:9000
```

---

### Audit Log Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AUDIT_LOG_RETENTION_DAYS` | integer | `90` | Default audit log retention period in days. Range: 1-365. |

**Environment defaults:**
| Environment | Retention |
|-------------|-----------|
| Development | 7 days |
| Staging | 30 days |
| Production | 90 days |

**Example:**
```bash
AUDIT_LOG_RETENTION_DAYS=90
```

---

### LLM API Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | string | `zai` | LLM provider to use. Options: `openai`, `anthropic`, `google`, `zai`. |
| `ZAI_API_KEY` | string | `null` | Z.ai API key for ATS simulation. Required if provider is `zai`. |
| `ZAI_BASE_URL` | string | `https://api.z.ai/api/paas/v4` | Z.ai API base URL. |
| `OPENAI_API_KEY` | string | `null` | OpenAI API key. Required if provider is `openai`. |
| `ANTHROPIC_API_KEY` | string | `null` | Anthropic API key. Required if provider is `anthropic`. |
| `GOOGLE_API_KEY` | string | `null` | Google API key for Gemini models. Required if provider is `google`. |
| `LLM_MODEL` | string | `glm-4.7` | Default LLM model identifier. |
| `LLM_TEMPERATURE` | float | `0.1` | Temperature for LLM calls (lower = more deterministic). Range: 0.0-1.0. |
| `LLM_MAX_TOKENS` | integer | `4096` | Maximum tokens for LLM responses. Range: 256-32768. |

**Example:**
```bash
# Using Z.ai
LLM_PROVIDER=zai
ZAI_API_KEY=sk-your-zai-key
LLM_MODEL=glm-4.7
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

# Using OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=8192
```

---

### ATS Simulation Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ATS_THRESHOLD` | float | `0.6` | Minimum ATS score to pass (0.0-1.0). Resumes below this score are rejected. |
| `ATS_VISUAL_CHECK_ENABLED` | boolean | `true` | Enable visual format checking in ATS (checks for proper formatting, fonts, etc.). |
| `ATS_KEYWORD_WEIGHT` | float | `0.3` | Weight for keyword matching in ATS score. Range: 0.0-1.0. |
| `ATS_EXPERIENCE_WEIGHT` | float | `0.3` | Weight for experience matching in ATS score. Range: 0.0-1.0. |
| `ATS_EDUCATION_WEIGHT` | float | `0.2` | Weight for education matching in ATS score. Range: 0.0-1.0. |
| `ATS_FIT_WEIGHT` | float | `0.2` | Weight for overall fit assessment in ATS score. Range: 0.0-1.0. |

**Note:** Weights should sum to approximately 1.0 for balanced scoring.

**Example:**
```bash
# Strict ATS settings
ATS_THRESHOLD=0.8
ATS_KEYWORD_WEIGHT=0.4
ATS_EXPERIENCE_WEIGHT=0.3
ATS_EDUCATION_WEIGHT=0.2
ATS_FIT_WEIGHT=0.1

# Lenient ATS settings
ATS_THRESHOLD=0.5
ATS_KEYWORD_WEIGHT=0.25
ATS_EXPERIENCE_WEIGHT=0.25
ATS_EDUCATION_WEIGHT=0.25
ATS_FIT_WEIGHT=0.25
```

---

## Frontend Configuration

All frontend environment variables must be prefixed with `VITE_` to be accessible in the frontend.

### API Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_API_URL` | string | `http://localhost:8000` | Backend API base URL. |
| `VITE_API_TIMEOUT` | integer | `120000` | API request timeout in milliseconds (120 seconds default). |
| `VITE_API_RETRY_ENABLED` | boolean | `true` | Enable automatic request retry on failure. |
| `VITE_API_RETRY_MAX_ATTEMPTS` | integer | `3` | Maximum number of API retry attempts. |

**Example:**
```bash
VITE_API_URL=https://api.example.com
VITE_API_TIMEOUT=180000  # 3 minutes
VITE_API_RETRY_ENABLED=true
VITE_API_RETRY_MAX_ATTEMPTS=5
```

---

### Application Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_APP_TITLE` | string | `Resume Analysis Platform` | Application title displayed in browser tab and header. |
| `VITE_APP_DESCRIPTION` | string | `AI-powered...` | Application description for SEO metadata. |
| `VITE_APP_VERSION` | string | `1.0.0` | Application version string. |

**Example:**
```bash
VITE_APP_TITLE=My Resume Analyzer
VITE_APP_DESCRIPTION=AI-powered resume analysis platform with ML/NLP processing
VITE_APP_VERSION=2.1.0
```

---

### Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_DARK_MODE` | boolean | `false` | Enable dark mode theme option. |
| `VITE_ENABLE_ANALYTICS` | boolean | `false` | Enable analytics tracking (Google Analytics, Plausible, etc.). |
| `VITE_ENABLE_ERROR_TRACKING` | boolean | `false` | Enable error tracking (Sentry, Bugsnag, etc.). |
| `VITE_ENABLE_EXPERIMENTAL_FEATURES` | boolean | `false` | Enable experimental features (may be unstable). |

**Example:**
```bash
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ERROR_TRACKING=true
VITE_ENABLE_EXPERIMENTAL_FEATURES=false
```

---

### Upload Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_MAX_UPLOAD_SIZE_MB` | integer | `10` | Maximum file upload size in megabytes. |
| `VITE_ALLOWED_FILE_TYPES` | string | `.pdf,.docx` | Comma-separated list of allowed file extensions. |
| `VITE_ENABLE_DRAG_DROP` | boolean | `true` | Enable drag-and-drop file upload. |
| `VITE_ENABLE_FILE_PREVIEW` | boolean | `true` | Enable file preview before upload. |

**Example:**
```bash
VITE_MAX_UPLOAD_SIZE_MB=20
VITE_ALLOWED_FILE_TYPES=.pdf,.docx,.txt
VITE_ENABLE_DRAG_DROP=true
VITE_ENABLE_FILE_PREVIEW=true
```

---

### UI Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DEFAULT_LANGUAGE` | string | `en` | Default language code. Options: `en`, `ru`. |
| `VITE_SUPPORTED_LANGUAGES` | string | `en,ru` | Comma-separated list of supported language codes. |
| `VITE_THEME` | string | `light` | Default theme. Options: `light`, `dark`, `auto`. |
| `VITE_PRIMARY_COLOR` | string | `#1976d2` | Primary color in hex format. |
| `VITE_SECONDARY_COLOR` | string | `#dc004e` | Secondary color in hex format. |

**Example:**
```bash
VITE_DEFAULT_LANGUAGE=en
VITE_SUPPORTED_LANGUAGES=en,ru,es
VITE_THEME=dark
VITE_PRIMARY_COLOR=#4CAF50
VITE_SECONDARY_COLOR=#FF9800
```

---

### Display Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ITEMS_PER_PAGE` | integer | `10` | Number of items per page in results. |
| `VITE_MAX_RESULTS` | integer | `100` | Maximum number of results to display. |
| `VITE_ENABLE_PAGINATION` | boolean | `true` | Enable results pagination. |
| `VITE_SHOW_PROCESSING_TIME` | boolean | `true` | Show processing time in results. |
| `VITE_SHOW_CONFIDENCE_SCORES` | boolean | `true` | Show confidence scores in analysis. |

---

### Results Display Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_HIGHLIGHT_MATCHED_SKILLS` | boolean | `true` | Highlight matched skills in green. |
| `VITE_HIGHLIGHT_MISSING_SKILLS` | boolean | `true` | Highlight missing skills in red. |
| `VITE_SHOW_MATCH_PERCENTAGE` | boolean | `true` | Show skill match percentage. |
| `VITE_SHOW_EXPERIENCE_DETAILS` | boolean | `true` | Show experience verification details. |
| `VITE_SHOW_GRAMMAR_SUGGESTIONS` | boolean | `true` | Show grammar/spelling suggestions. |
| `VITE_AUTO_REFRESH_RESULTS` | boolean | `true` | Auto-refresh results during processing. |
| `VITE_RESULTS_REFRESH_INTERVAL` | integer | `5000` | Results refresh interval in milliseconds. |
| `VITE_MAX_REFRESH_DURATION` | integer | `60000` | Maximum auto-refresh duration in milliseconds. |

---

### Error Messages Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_SHOW_DETAILED_ERRORS` | boolean | `true` | Show detailed error messages to users. |
| `VITE_FRIENDLY_ERRORS` | boolean | `true` | Enable user-friendly error messages. |

**Note:** In production, consider setting `VITE_SHOW_DETAILED_ERRORS=false` for security.

---

### Performance Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_LAZY_LOADING` | boolean | `true` | Enable lazy loading for images. |
| `VITE_ENABLE_CODE_SPLITTING` | boolean | `true` | Enable code splitting for faster initial load. |
| `VITE_ENABLE_COMPRESSION` | boolean | `true` | Enable response compression. |

---

### Analytics Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_GA_TRACKING_ID` | string | - | Google Analytics tracking ID (e.g., `UA-XXXXXXXXX-X`). Optional. |
| `VITE_PLAUSIBLE_DOMAIN` | string | - | Plausible analytics domain. Optional. |
| `VITE_POSTHOG_KEY` | string | - | PostHog API key. Optional. |
| `VITE_POSTHOG_HOST` | string | - | PostHog host URL. Optional. |

**Example:**
```bash
# Google Analytics
VITE_GA_TRACKING_ID=UA-123456789-1

# Plausible
VITE_PLAUSIBLE_DOMAIN=example.com

# PostHog
VITE_POSTHOG_KEY=phc_your_key
VITE_POSTHOG_HOST=https://app.posthog.com
```

---

### Error Tracking Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_SENTRY_DSN` | string | - | Sentry DSN for error tracking. Optional. |
| `VITE_SENTRY_ENVIRONMENT` | string | `development` | Sentry environment name. |

**Example:**
```bash
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
VITE_SENTRY_ENVIRONMENT=production
```

---

### Authentication Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_AUTH` | boolean | `false` | Enable authentication. |
| `VITE_AUTH_PROVIDER` | string | `jwt` | Auth provider. Options: `jwt`, `oauth`, `auth0`. |
| `VITE_TOKEN_STORAGE` | string | `localStorage` | JWT token storage. Options: `localStorage`, `sessionStorage`, `cookie`. |
| `VITE_SESSION_TIMEOUT_MINUTES` | integer | `60` | Session timeout in minutes. |

---

### Social Sharing Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_SOCIAL_SHARING` | boolean | `false` | Enable social sharing buttons. |
| `VITE_TWITTER_HANDLE` | string | - | Twitter handle for sharing. Optional. |
| `VITE_FACEBOOK_PAGE` | string | - | Facebook page URL. Optional. |
| `VITE_LINKEDIN_PAGE` | string | - | LinkedIn page URL. Optional. |

---

### Help & Support Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_HELP_DOCS_URL` | string | `https://docs.your-domain.com` | Help documentation URL. |
| `VITE_SUPPORT_EMAIL` | string | `support@your-domain.com` | Support email address. |
| `VITE_REPORT_ISSUE_URL` | string | `https://github.com/your-repo/issues` | Report issue URL. |

---

### Third-Party Integrations

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_INTERCOM_APP_ID` | string | - | Intercom chat widget ID. Optional. |
| `VITE_CRISP_WEBSITE_ID` | string | - | Crisp chat widget ID. Optional. |
| `VITE_USERFEEDBACK_PROJECT_ID` | string | - | UserFeedback project ID. Optional. |

---

### Development Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DEBUG` | boolean | `false` | Enable debug mode. |
| `VITE_ENABLE_REACT_DEVTOOLS` | boolean | `true` | Enable React DevTools. |
| `VITE_SHOW_COMPONENT_NAMES` | boolean | `true` | Show component names in DevTools. |

---

### Testing Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_CYPRESS_BASE_URL` | string | `http://localhost:5173` | Cypress base URL for E2E testing. |
| `VITE_MOCK_API` | boolean | `false` | Mock API in development for testing. |

---

### Internationalization Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DATE_FORMAT` | string | `medium` | Default date format. Options: `short`, `medium`, `long`, `full`. |
| `VITE_TIME_FORMAT` | string | `short` | Default time format. Options: `short`, `medium`, `long`. |
| `VITE_TIMEZONE` | string | `UTC` | Default timezone. |

---

### File Upload Display

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_SHOW_UPLOAD_PROGRESS` | boolean | `true` | Show file upload progress. |
| `VITE_PROGRESS_UPDATE_INTERVAL` | integer | `500` | Progress update interval in milliseconds. |

---

### Accessibility Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_ARIA_LABELS` | boolean | `true` | Enable ARIA labels for accessibility. |
| `VITE_ENABLE_KEYBOARD_NAVIGATION` | boolean | `true` | Enable keyboard navigation. |
| `VITE_ENABLE_SCREEN_READER` | boolean | `true` | Enable screen reader support. |

---

### Notification Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_BROWSER_NOTIFICATIONS` | boolean | `false` | Enable browser notifications. |
| `VITE_NOTIFICATION_DURATION` | integer | `5000` | Notification duration in milliseconds. |
| `VITE_NOTIFICATION_POSITION` | string | `top-right` | Notification position. Options: `top-left`, `top-right`, `bottom-left`, `bottom-right`. |

---

### Export Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_PDF_EXPORT` | boolean | `false` | Enable PDF export. |
| `VITE_ENABLE_CSV_EXPORT` | boolean | `false` | Enable CSV export. |
| `VITE_ENABLE_JSON_EXPORT` | boolean | `true` | Enable JSON export. |

---

### Cache Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_CACHE` | boolean | `true` | Enable application cache. |
| `VITE_CACHE_DURATION` | integer | `300000` | Cache duration in milliseconds (5 minutes default). |
| `VITE_CLEAR_CACHE_ON_LOGOUT` | boolean | `true` | Clear cache on logout. |

---

### Rate Limiting Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_RATE_LIMITING` | boolean | `true` | Enable client-side rate limiting. |
| `VITE_MAX_REQUESTS_PER_MINUTE` | integer | `60` | Maximum requests per minute. |

---

### URL Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_BASE_PATH` | string | - | Base path if app is deployed to subdirectory. Optional. |
| `VITE_OUT_DIR` | string | `dist` | Build output directory. |

---

### SEO Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_SITE_NAME` | string | `Resume Analysis Platform` | Site name for SEO. |
| `VITE_SITE_URL` | string | `http://localhost:5173` | Site URL for SEO. |
| `VITE_DEFAULT_OG_IMAGE` | string | `/og-image.png` | Default Open Graph image path. |
| `VITE_TWITTER_CARD_TYPE` | string | `summary_large_image` | Twitter card type. Options: `summary`, `summary_large_image`. |

---

## Configuration Validation

### Backend Validation

The backend validates configuration on startup:

1. **Database URL**: Must be valid PostgreSQL connection string
2. **Log Level**: Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL
3. **Max Upload Size**: Must be between 1-100 MB
4. **Analysis Timeout**: Must be between 30-600 seconds
5. **LLM Temperature**: Must be between 0.0-1.0
6. **ATS Threshold**: Must be between 0.0-1.0
7. **Backup Retention**: Must be between 1-365 days

### Frontend Validation

The frontend validates configuration on load:

1. **API URL**: Must be valid URL format
2. **API Timeout**: Must be positive number
3. **Upload Size**: Must be positive number
4. **File Types**: Must start with `.` prefix
5. **Colors**: Must be valid hex color format (e.g., `#RRGGBB`)
6. **Language**: Must be in supported languages list

---

## Configuration API

### Get Current Configuration

```bash
GET /api/config
```

**Response:**
```json
{
  "environment": "production",
  "log_level": "WARNING",
  "max_upload_size_mb": 10,
  "llm_provider": "zai",
  "llm_model": "glm-4.7",
  "ats_threshold": 0.6,
  "last_reload": "2026-02-07T00:00:00Z"
}
```

### Reload Configuration

```bash
POST /api/config/reload
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "changed_settings": ["log_level"],
  "reloaded_at": "2026-02-07T00:30:00Z"
}
```

### Configuration Health Check

```bash
GET /api/config/health
```

**Response:**
```json
{
  "status": "healthy",
  "environment": "production",
  "validation_errors": [],
  "validation_warnings": []
}
```

### Get Audit Logs

```bash
GET /api/config/audit-logs
```

**Response:**
```json
{
  "total": 150,
  "logs": [
    {
      "id": 1,
      "action": "CONFIG_RELOADED",
      "previous_value": "{\"log_level\": \"INFO\"}",
      "new_value": "{\"log_level\": \"DEBUG\"}",
      "changed_by": "admin@example.com",
      "changed_at": "2026-02-07T00:30:00Z"
    }
  ]
}
```
