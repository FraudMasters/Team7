# Environment Variables — Complete Reference

Comprehensive guide to all environment variables used in AgentHR for configuration, deployment, and operation.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [Backend API Configuration](#backend-api-configuration)
- [Frontend Configuration](#frontend-configuration)
- [ML Models Configuration](#ml-models-configuration)
- [Celery Configuration](#celery-configuration)
- [LLM API Configuration](#llm-api-configuration)
- [Backup Configuration](#backup-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Alerting Configuration](#alerting-configuration)
- [Security Configuration](#security-configuration)
- [File Upload Configuration](#file-upload-configuration)
- [Analysis Configuration](#analysis-configuration)
- [Development Settings](#development-settings)
- [Production Deployment](#production-deployment)
- [Environment-Specific Examples](#environment-specific-examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

AgentHR uses environment variables for all configuration across multiple services:

```
┌─────────────────────────────────────────────────────────────┐
│                    Environment Variables                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Backend    │  │   Frontend   │  │  Monitoring  │      │
│  │  (.env)      │  │  (.env)      │  │  (.env)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │ docker-compose │                        │
│                    │   .env file    │                        │
│                    └────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Environment Files Structure

| File | Purpose | Scope |
|------|---------|-------|
| `.env` | Root configuration (shared variables) | Global |
| `backend/.env` | Backend-specific configuration | Backend API & Workers |
| `frontend/.env` | Frontend-specific configuration (VITE_*) | React UI |
| `scripts/.env` | Scripts configuration | Utility Scripts |

---

## Quick Start

### 1. Copy Environment Templates

```bash
# Root environment
cp .env.example .env

# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

### 2. Minimal Configuration

For local development, only these variables are **required**:

```bash
# .env (minimal)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=resume_analysis

# backend/.env (minimal)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_analysis
REDIS_URL=redis://localhost:6379/0

# frontend/.env (minimal)
VITE_API_URL=http://localhost:8000
```

### 3. Start Services

```bash
docker-compose up -d
```

---

## Database Configuration

### PostgreSQL Connection

**Environment Files**: `.env`, `backend/.env`, `docker-compose.yml`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `postgresql://postgres:postgres@localhost:5432/resume_analysis` | Full PostgreSQL connection URL |
| `POSTGRES_USER` | string | `postgres` | Database user |
| `POSTGRES_PASSWORD` | string | `postgres` | Database password |
| `POSTGRES_DB` | string | `resume_analysis` | Database name |
| `POSTGRES_HOST` | string | `localhost` | Database host |
| `POSTGRES_PORT` | integer | `5432` | Database port |

### Connection URL Format

```
postgresql://[user]:[password]@[host]:[port]/[database]
```

### Examples

```bash
# Local development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_analysis

# Docker deployment
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/resume_analysis

# Cloud database (e.g., AWS RDS)
DATABASE_URL=postgresql://admin:password@db.production.amazonaws.com:5432/resume_analysis

# With connection pooling (PgBouncer)
DATABASE_URL=postgresql://user:pass@pgbouncer:6432/resume_analysis
```

### Database Pool Configuration

**Environment Files**: `.env`, `backend/.env`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DB_POOL_SIZE` | integer | `20` | Maximum connection pool size |
| `DB_MAX_OVERFLOW` | integer | `10` | Additional connections beyond pool_size |
| `DB_POOL_RECYCLE` | integer | `3600` | Connection recycle time (seconds) |
| `DB_POOL_TIMEOUT` | integer | `30` | Connection timeout (seconds) |
| `DB_POOL_PRE_PING` | boolean | `true` | Test connections before use |

#### Understanding Connection Pooling

```
┌──────────────────────────────────────────────────────────────┐
│                  Connection Pool Architecture                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌────────────┐     ┌──────────────────────────────┐       │
│   │  Worker 1  │────▶│                              │       │
│   └────────────┘     │                              │       │
│   ┌────────────┐     │   Connection Pool            │       │
│   │  Worker 2  │────▶│   (DB_POOL_SIZE=20)          │       │
│   └────────────┘     │                              │       │
│   ┌────────────┐     │  ┌────┬────┬────┬────┬────┐ │       │
│   │  Worker 3  │────▶│  │ C1 │ C2 │... │ C19│ C20│ │       │
│   └────────────┘     │  └────┴────┴────┴────┴────┘ │       │
│                      │         ↓                     │       │
│   ┌────────────┐     │   ┌──────────────────┐       │       │
│   │  Worker N  │────▶│   │   PostgreSQL     │       │       │
│   └────────────┘     │   └──────────────────┘       │       │
│                      └──────────────────────────────┘       │
│                         Overflow Queue (max 10)              │
└──────────────────────────────────────────────────────────────┘
```

#### Performance Impact

**Pool Size (`DB_POOL_SIZE`)**

| Setting | Memory Usage | Concurrency | Use Case |
|---------|-------------|-------------|----------|
| `10` | ~100MB | Low traffic | Development/small deployments |
| `20` | ~200MB | Medium traffic | **Default** - Standard production |
| `50` | ~500MB | High traffic | High-volume production |
| `100+` | ~1GB+ | Very high traffic | Large-scale deployments |

**Formula**: `DB_POOL_SIZE >= number_of_workers * 2`

**Overflow (`DB_MAX_OVERFLOW`)**

| Setting | Behavior |
|---------|----------|
| `0` | No overflow - strict limit, wait for connection |
| `10` | Allow 10 extra connections during spikes |
| `20` | Allow 20 extra connections (high burst tolerance) |

**Recycle Time (`DB_POOL_RECYCLE`)**

| Setting | Behavior | Use Case |
|---------|----------|----------|
| `1800` (30 min) | Frequent recycling | High-security, prevent stale connections |
| `3600` (1 hour) | **Default** - Balanced | Standard production |
| `7200` (2 hours) | Less recycling | Better performance, trusted connections |

**Timeout (`DB_POOL_TIMEOUT`)**

| Setting | Behavior | Use Case |
|---------|----------|----------|
| `10` | Fail fast | Low-latency requirements |
| `30` | **Default** - Balanced | Standard production |
| `60` | Wait longer | High-load environments |

#### Example Configurations

**Development (Low Traffic)**
```bash
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30
```

**Standard Production**
```bash
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30
```

**High-Traffic Production**
```bash
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=60
```

**Container/Kubernetes (Multi-Instance)**
```bash
# Each pod/instance has smaller pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Total capacity = (pool_size + max_overflow) * number_of_pods
# Example: (10 + 5) * 4 pods = 60 total connections
```

#### Production Recommendations

**1. Calculate Based on Workers**
```bash
# Formula: pool_size = workers * 2
DB_POOL_SIZE=20  # For 10 Celery workers
CELERY_WORKER_CONCURRENCY=10
```

**2. Monitor Connection Usage**
```python
# Check pool utilization
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
# Logs will show: "Pool size: 20 Connections in pool: 12"
```

**3. Set Database max_connections**
```sql
-- PostgreSQL: Ensure max_connections >= total_pools
ALTER SYSTEM SET max_connections = 200;
-- Reload: SELECT pg_reload_conf();
```

**4. Enable Pre-Ping**
```bash
# Prevents "server closed the connection" errors
DB_POOL_PRE_PING=true
```

**5. Tune for Your Database**
- **PostgreSQL**: Default `max_connections=100` → Consider `DB_POOL_SIZE=40` with 2-3 app instances
- **RDS/Aurora**: Higher limits → Can use larger pools
- **Cloud SQL**: Check connection limits before setting pool size

#### Troubleshooting

**Symptom**: "connection pool exhausted" errors

**Solution**: Increase `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
```bash
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

**Symptom**: Stale connection errors after long idle periods

**Solution**: Enable pre-ping and reduce recycle time
```bash
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=1800
```

**Symptom**: Database CPU maxed out

**Solution**: Reduce pool size (too many connections can degrade performance)
```bash
DB_POOL_SIZE=10  # Reduce to lower contention
```

---

## Redis Configuration

### Basic Redis Settings

**Environment Files**: `.env`, `backend/.env`, `docker-compose.yml`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Full Redis connection URL |
| `REDIS_HOST` | string | `redis` | Redis host |
| `REDIS_PORT` | integer | `6379` | Redis port |

### Connection URL Format

```
redis://[host]:[port]/[database_number]
```

### Examples

```bash
# Local development
REDIS_URL=redis://localhost:6379/0

# Docker deployment
REDIS_URL=redis://redis:6379/0

# Redis with password
REDIS_URL=redis://:password@redis:6379/0

# Redis Sentinel (high availability)
REDIS_URL=sentinel://sentinel1:26379,sentinel2:26379/mymaster/0

# ElastiCache (AWS)
REDIS_URL=redis://my-cluster.xxxxxx.use1.cache.amazonaws.com:6379/0
```

### Redis Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_MAX_MEMORY` | string | `512mb` | Maximum memory usage |
| `REDIS_MAXMEMORY_POLICY` | string | `allkeys-lru` | Eviction policy |
| `REDIS_APPENDONLY` | string | `yes` | Enable AOF persistence |

### Docker Compose Redis Configuration

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes \
    --maxmemory 512mb \
    --maxmemory-policy allkeys-lru
```

---

## Backend API Configuration

### Server Settings

**Environment Files**: `backend/.env`, `docker-compose.yml`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKEND_HOST` | string | `0.0.0.0` | Host to bind the FastAPI server |
| `BACKEND_PORT` | integer | `8000` | Port to bind the FastAPI server |
| `API_TITLE` | string | `Resume Analysis API` | API title for documentation |
| `API_VERSION` | string | `1.0.0` | API version |

### Examples

```bash
# Development
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Production with different port
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080

# Localhost only (testing)
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

### CORS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FRONTEND_URL` | string | `http://localhost:5173` | Frontend URL for CORS |
| `CORS_ORIGINS` | string | `http://localhost:5173,http://localhost:3000` | Allowed origins (comma-separated) |

### Examples

```bash
# Development
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Production
FRONTEND_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com,https://www.example.com

# Multiple environments
CORS_ORIGINS=http://localhost:5173,https://staging.example.com,https://app.example.com
```

### Python Path

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PYTHONPATH` | string | `/app:/app/services` | Python module search path |

---

## Frontend Configuration

**Important**: All frontend environment variables must start with `VITE_` prefix to be accessible in the browser.

### API Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_API_URL` | string | `http://localhost:8000` | Backend API URL |
| `VITE_API_TIMEOUT` | integer | `120000` | API timeout (milliseconds) |
| `VITE_API_RETRY_ENABLED` | boolean | `true` | Enable API retry |
| `VITE_API_RETRY_MAX_ATTEMPTS` | integer | `3` | Maximum retry attempts |

### Examples

```bash
# Development
VITE_API_URL=http://localhost:8000

# Production
VITE_API_URL=https://api.example.com

# Behind reverse proxy
VITE_API_URL=/api

# With version prefix
VITE_API_URL=https://api.example.com/v1
```

### Application Metadata

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_APP_TITLE` | string | `Resume Analysis Platform` | Application title |
| `VITE_APP_DESCRIPTION` | string | `AI-powered resume analysis...` | Application description |
| `VITE_APP_VERSION` | string | `1.0.0` | Application version |

### Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_ENABLE_DARK_MODE` | boolean | `false` | Enable dark mode |
| `VITE_ENABLE_ANALYTICS` | boolean | `false` | Enable analytics tracking |
| `VITE_ENABLE_ERROR_TRACKING` | boolean | `false` | Enable error tracking (Sentry) |
| `VITE_ENABLE_EXPERIMENTAL_FEATURES` | boolean | `false` | Enable experimental features |

### Upload Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_MAX_UPLOAD_SIZE_MB` | integer | `10` | Maximum upload size (MB) |
| `VITE_ALLOWED_FILE_TYPES` | string | `.pdf,.docx` | Allowed file extensions |
| `VITE_ENABLE_DRAG_DROP` | boolean | `true` | Enable drag-and-drop upload |
| `VITE_ENABLE_FILE_PREVIEW` | boolean | `true` | Enable file preview |

### Display Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DEFAULT_LANGUAGE` | string | `en` | Default language (en, ru) |
| `VITE_SUPPORTED_LANGUAGES` | string | `en,ru` | Supported languages |
| `VITE_THEME` | string | `light` | Default theme (light, dark, auto) |
| `VITE_PRIMARY_COLOR` | string | `#1976d2` | Primary color (hex) |
| `VITE_ITEMS_PER_PAGE` | integer | `10` | Items per page in results |

### Results Display

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_HIGHLIGHT_MATCHED_SKILLS` | boolean | `true` | Highlight matched skills |
| `VITE_HIGHLIGHT_MISSING_SKILLS` | boolean | `true` | Highlight missing skills |
| `VITE_SHOW_MATCH_PERCENTAGE` | boolean | `true` | Show skill match percentage |
| `VITE_SHOW_EXPERIENCE_DETAILS` | boolean | `true` | Show experience details |
| `VITE_SHOW_GRAMMAR_SUGGESTIONS` | boolean | `true` | Show grammar suggestions |

### Analytics Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_GA_TRACKING_ID` | string | - | Google Analytics ID |
| `VITE_PLAUSIBLE_DOMAIN` | string | - | Plausible domain |
| `VITE_POSTHOG_KEY` | string | - | PostHog API key |
| `VITE_POSTHOG_HOST` | string | - | PostHog host URL |

### Error Tracking

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_SENTRY_DSN` | string | - | Sentry DSN |
| `VITE_SENTRY_ENVIRONMENT` | string | `development` | Sentry environment |

---

## ML Models Configuration

### Model Cache Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODELS_CACHE_PATH` | string | `./models_cache` | Path to cache ML models |
| `TRANSFORMERS_CACHE` | string | `/app/models_cache/hub` | Hugging Face cache |
| `HF_HOME` | string | `/app/models_cache` | Hugging Face home |

**Impact on Performance**: Model caching significantly reduces startup time and memory usage. First download: 100-500MB per model.

**Production Recommendation**: Use persistent volumes or network storage to preserve models across deployments.

### Examples

```bash
# Local development
MODELS_CACHE_PATH=./models_cache

# Docker volume mount
MODELS_CACHE_PATH=/app/models_cache
TRANSFORMERS_CACHE=/app/models_cache/hub
HF_HOME=/app/models_cache

# Custom cache location
MODELS_CACHE_PATH=/opt/ml-models
```

---

### KeyBERT Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KEYBERT_MODEL` | string | `distilbert-base-nli-mean-tokens` | KeyBERT model name |

**Valid Values**:

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `distilbert-base-nli-mean-tokens` | 250MB | Fast | Good | **Production default** - Balanced performance |
| `sentence-transformers/all-MiniLM-L6-v2` | 80MB | Very Fast | Good | **High volume** - Low resource usage |
| `sentence-transformers/all-mpnet-base-v2` | 400MB | Slow | Best | **Premium** - Best accuracy |

**Performance Impact**:

```
┌──────────────────────────────────────────────────────────┐
│              KeyBERT Model Performance                    │
├──────────────────────────────────────────────────────────┤
│  Model                  │ Memory │ Speed │ Quality      │
├─────────────────────────┼────────┼───────┼───────────┤
│  all-MiniLM-L6-v2       │ 80MB   │ 1.0x  │ 85%        │
│  distilbert-base-nli    │ 250MB   │ 0.8x  │ 88%        │
│  all-mpnet-base-v2      │ 400MB   │ 0.5x  │ 92%        │
└──────────────────────────────────────────────────────────┘
```

**Production Recommendation**:
- **Default**: `distilbert-base-nli-mean-tokens` for production
- **High-volume**: `all-MiniLM-L6-v2` for reduced memory
- **Premium**: `all-mpnet-base-v2` for best quality

---

### SpaCy Models

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SPACY_MODEL_EN` | string | `en_core_web_sm` | English SpaCy model |
| `SPACY_MODEL_RU` | string | `ru_core_news_sm` | Russian SpaCy model |

**Valid Values**:

| Language | Model | Size | Components | Valid Values |
|----------|-------|------|------------|--------------|
| English | `en_core_web_sm` | 12MB | PERSON, ORG, DATE, GPE | `en_core_web_sm` (small), `en_core_web_md` (medium), `en_core_web_lg` (large) |
| Russian | `ru_core_news_sm` | 17MB | PERSON, ORG, DATE, LOC | `ru_core_news_sm` (small), `ru_core_news_md` (medium), `ru_core_news_lg` (large) |

**Installation**:
```bash
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm
```

**Performance Impact**:

| Model | Memory | Load Time | Accuracy | Use Case |
|-------|--------|-----------|----------|----------|
| `sm` (small) | 12-17MB | 0.5s | ~90% | **Production default** |
| `md` (medium) | 40-50MB | 1.5s | ~93% | Enhanced accuracy |
| `lg` (large) | 500MB+ | 5s+ | ~95% | Best quality (high memory) |

**Production Recommendation**:
- Use `sm` models for production (best memory/speed balance)
- Consider `md` models if accuracy is critical and memory is available
- Avoid `lg` models in containerized environments unless necessary

**Prerequisites**:
- Ensure models are downloaded before deploying: `python -m spacy download en_core_web_sm`
- Mount model cache as volume in Docker to persist across restarts

---

### Sentence Transformers

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SENTENCE_TRANSFORMER_MODEL` | string | `sentence-transformers/all-MiniLM-L6-v2` | Model for semantic similarity |

**Valid Values**:

| Model | Size | Speed | Language | Use Case |
|-------|------|-------|----------|----------|
| `sentence-transformers/all-MiniLM-L6-v2` | 80MB | Very Fast | English only | **Default** - English resumes |
| `sentence-transformers/all-mpnet-base-v2` | 400MB | Fast | English only | Better quality |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 400MB | Medium | 50+ languages | **Multilingual** support |

**Performance Impact**:

```
┌──────────────────────────────────────────────────────────────┐
│         Sentence Transformer Model Performance               │
├──────────────────────────────────────────────────────────────┤
│  Model                         │ Memory │ Speed │ Languages │
├────────────────────────────────┼────────┼───────┼───────────┤
│  all-MiniLM-L6-v2              │ 80MB   │ 1.0x  │ EN only   │
│  all-mpnet-base-v2             │ 400MB  │ 0.7x  │ EN only   │
│  paraphrase-multilingual-MiniLM│ 400MB  │ 0.5x  │ 50+ langs │
└──────────────────────────────────────────────────────────────┘
```

**Production Recommendation**:
- **English-only**: Use `all-MiniLM-L6-v2` (fastest)
- **Multilingual**: Use `paraphrase-multilingual-MiniLM-L12-v2` for international support
- Pre-download models: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`

---

### Model Optimization

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PYTORCH_ENABLE_MPS_FALLBACK` | integer | `1` | Enable MPS fallback (Apple Silicon) |

**Valid Values**: `0` (disable), `1` (enable)

**Description**: Enables Apple Silicon GPU acceleration with CPU fallback for unsupported operations.

**Hardware Support**:

| Platform | Setting | Performance |
|----------|---------|-------------|
| Apple Silicon (M1/M2/M3) | `PYTORCH_ENABLE_MPS_FALLBACK=1` | 2-3x faster |
| NVIDIA GPU | CUDA automatic | 5-10x faster |
| CPU | N/A | Baseline |

**Production Recommendation**:
- Set to `1` on Apple Silicon Macs
- No impact on Linux/Windows servers (uses CUDA or CPU)

---

## Celery Configuration

### Broker & Backend

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CELERY_BROKER_URL` | string | `redis://localhost:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | string | `redis://localhost:6379/0` | Result backend URL |

### Worker Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CELERY_WORKER_CONCURRENCY` | integer | `2` | Number of worker processes |
| `CELERY_LOG_LEVEL` | string | `info` | Worker log level |
| `CELERY_TASK_TIME_LIMIT` | integer | `300` | Task time limit (seconds) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | integer | `280` | Task soft time limit |
| `CELERY_TASK_MAX_RETRIES` | integer | `3` | Maximum task retries |
| `CELERY_RESULT_EXPIRES` | integer | `86400` | Result expiration (seconds) |

### Worker Command Examples

```bash
# Development (low concurrency)
celery -A celery_app.celery_app worker --loglevel=info --concurrency=2

# Production (high concurrency)
celery -A celery_app.celery_app worker --loglevel=info --concurrency=8

# With specific queues
celery -A celery_app.celery_app worker --loglevel=info \
  --queues=celery,analysis,learning,reporting

# With autoscaling
celery -A celery_app.celery_app worker --loglevel=info \
  --autoscale=10,2 --max-tasks-per-child=1000
```

### Beat Scheduler (Scheduled Tasks)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CELERY_BEAT_SCHEDULE` | dict | `{}` | Scheduled tasks configuration |

**Beat Command**:
```bash
celery -A celery_app.celery_app beat --loglevel=info
```

### Queue Configuration

```
┌──────────────┐
│   celery     │ ← General tasks
├──────────────┤
│  analysis    │ ← Resume analysis tasks
├──────────────┤
│  learning    │ ← ML model training
├──────────────┤
│  reporting   │ ← Report generation
└──────────────┘
```

---

## LLM API Configuration

### Provider Selection

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | string | `zai` | LLM provider (zai, openai, anthropic, google) |

**Supported Providers**:
- `zai` - Z.ai API (supports multiple models)
- `openai` - OpenAI (GPT models)
- `anthropic` - Anthropic (Claude models)
- `google` - Google (Gemini models)

### API Keys

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ZAI_API_KEY` | string | - | Z.ai API key |
| `ZAI_BASE_URL` | string | `https://api.z.ai/api/paas/v4` | Z.ai API URL |
| `OPENAI_API_KEY` | string | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | string | - | Anthropic API key |
| `GOOGLE_API_KEY` | string | - | Google API key |

### Model Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_MODEL` | string | `glm-4.7` | Default LLM model |
| `LLM_TEMPERATURE` | float | `0.1` | Temperature (0.0-1.0) |
| `LLM_MAX_TOKENS` | integer | `4096` | Maximum tokens in response |

### Popular Models

**OpenAI**:
- `gpt-4o` - Best performance
- `gpt-4o-mini` - Fast, cost-effective
- `gpt-3.5-turbo` - Legacy

**Anthropic**:
- `claude-3-5-sonnet-20241022` - Balanced
- `claude-3-5-haiku-20241022` - Fast
- `claude-3-opus-20240229` - Best quality

**Google**:
- `gemini-1.5-pro` - Best performance
- `gemini-1.5-flash` - Fast

### API Examples

```bash
# Z.ai
LLM_PROVIDER=zai
LLM_MODEL=glm-4.7
ZAI_API_KEY=your_zai_key

# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your_openai_key

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-your_key
```

### Temperature Guide

| Value | Behavior | Use Case |
|-------|----------|----------|
| `0.0 - 0.2` | Very deterministic | Factual extraction, structured data |
| `0.3 - 0.5` | Semi-deterministic | Analysis, comparison |
| `0.7 - 0.9` | Creative | Content generation |
| `1.0` | Very random | Creative writing |

---

## Backup Configuration

### Backup Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKUP_ENABLED` | boolean | `true` | Enable automated backups |
| `BACKUP_RETENTION_DAYS` | integer | `30` | Backup retention period |
| `BACKUP_SCHEDULE` | string | `0 2 * * *` | Cron schedule (daily at 2 AM) |
| `BACKUP_DIR` | string | `./data/backups` | Backup directory |
| `BACKUP_COMPRESSION_ENABLED` | boolean | `true` | Enable backup compression |
| `BACKUP_INCREMENTAL_ENABLED` | boolean | `true` | Enable incremental backups |

### Cron Schedule Examples

```bash
# Daily at 2 AM
BACKUP_SCHEDULE=0 2 * * *

# Every 6 hours
BACKUP_SCHEDULE=0 */6 * * *

# Weekly on Sunday at 3 AM
BACKUP_SCHEDULE=0 3 * * 0

# Every hour (high frequency)
BACKUP_SCHEDULE=0 * * * *
```

### S3 Backup Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKUP_S3_ENABLED` | boolean | `false` | Enable S3 off-site backup |
| `BACKUP_S3_BUCKET` | string | - | S3 bucket name |
| `BACKUP_S3_ENDPOINT` | string | - | S3 endpoint URL |
| `BACKUP_S3_ACCESS_KEY` | string | - | S3 access key |
| `BACKUP_S3_SECRET_KEY` | string | - | S3 secret key |
| `BACKUP_S3_REGION` | string | `us-east-1` | S3 region |

### S3 Examples

```bash
# AWS S3
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=my-backup-bucket
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
BACKUP_S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
BACKUP_S3_REGION=us-east-1

# MinIO (self-hosted)
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=agenthr-backups
BACKUP_S3_ENDPOINT=http://minio:9000
BACKUP_S3_ACCESS_KEY=minioadmin
BACKUP_S3_SECRET_KEY=minioadmin
BACKUP_S3_REGION=us-east-1

# Wasabi
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=my-backups
BACKUP_S3_ENDPOINT=https://s3.wasabisys.com
BACKUP_S3_ACCESS_KEY=your_access_key
BACKUP_S3_SECRET_KEY=your_secret_key
BACKUP_S3_REGION=us-east-1
```

### Backup Notifications

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKUP_NOTIFICATION_EMAIL` | string | - | Email for backup failure notifications |

---

## Monitoring & Logging

### Logging Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | string | `json` | Log format (json, text) |
| `LOG_FILE` | string | - | Log file path (empty = stdout) |

### Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| `DEBUG` | Development debugging | Database queries, ML model internals |
| `INFO` | Normal operation | Task started, file uploaded |
| `WARNING` | Unexpected but not critical | Retry attempt, fallback used |
| `ERROR` | Error but operation continues | API failure, task failed |
| `CRITICAL` | Critical failure | Service down, data loss |

### Loki Integration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOKI_URL` | string | `http://loki:3100` | Loki URL for log aggregation |

### Prometheus Metrics

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_PROMETHEUS_METRICS` | boolean | `false` | Enable Prometheus metrics |
| `PROMETHEUS_PORT` | integer | `9090` | Prometheus metrics port |

### Grafana Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GRAFANA_USER` | string | `admin` | Grafana admin username |
| `GRAFANA_PASSWORD` | string | `admin` | Grafana admin password |

**Important**: Change the default password in production!

---

## Alerting Configuration

### SMTP Email Alerts

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GRAFANA_SMTP_HOST` | string | `smtp.gmail.com:587` | SMTP server host:port |
| `GRAFANA_SMTP_USER` | string | - | SMTP username |
| `GRAFANA_SMTP_PASSWORD` | string | - | SMTP password |
| `GRAFANA_SMTP_FROM_ADDRESS` | string | `grafana@localhost` | From email address |
| `GRAFANA_SMTP_STARTTLS_POLICY` | string | `OpportunisticStartTLS` | TLS policy |

### SMTP Examples

**Gmail**:
```bash
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password
GRAFANA_SMTP_FROM_ADDRESS=grafana@yourdomain.com
```

**Outlook**:
```bash
GRAFANA_SMTP_HOST=smtp.office365.com:587
GRAFANA_SMTP_USER=your_email@outlook.com
GRAFANA_SMTP_PASSWORD=your_password
GRAFANA_SMTP_FROM_ADDRESS=grafana@yourdomain.com
```

**SendGrid**:
```bash
GRAFANA_SMTP_HOST=smtp.sendgrid.net:587
GRAFANA_SMTP_USER=apikey
GRAFANA_SMTP_PASSWORD=SG.your_sendgrid_api_key
GRAFANA_SMTP_FROM_ADDRESS=alerts@yourdomain.com
```

### Alert Recipients

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALERT_EMAIL_ADDRESS` | string | `alerts@example.com` | Email to receive alerts |

### Webhook Alerts

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALERT_WEBHOOK_URL` | string | - | Webhook URL for alerts |
| `ALERT_WEBHOOK_USERNAME` | string | - | Webhook authentication username |
| `ALERT_WEBHOOK_PASSWORD` | string | - | Webhook authentication password |
| `ALERT_WEBHOOK_BEARER_TOKEN` | string | - | Webhook bearer token |

### Webhook Examples

**Slack**:
```bash
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Microsoft Teams**:
```bash
ALERT_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR_WEBHOOK_URL
```

**Discord**:
```bash
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

---

## Security Configuration

### Authentication

**Environment Files**: `backend/.env`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | - | Secret key for JWT tokens |
| `JWT_ALGORITHM` | string | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `30` | JWT token expiration |

#### SECRET_KEY

**Valid Values**: Any cryptographically random string (minimum 32 characters)

**Generate Secret Key**:
```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Method 3: uuidgen
uuidgen | sha256sum | head -c 32
```

**Security Requirements**:

| Aspect | Requirement | Risk |
|--------|-------------|------|
| Length | Minimum 32 characters | Brute force attacks |
| Randomness | Cryptographically secure | Predictable keys |
| Uniqueness | Different per environment | Cross-env token forgery |
| Rotation | Every 90 days | Compromised key exposure |

**Production Examples**:

```bash
# ❌ BAD - Predictable
SECRET_KEY=my-secret-key
SECRET_KEY=agenthr-production
SECRET_KEY=abc123

# ✅ GOOD - Cryptographically random
SECRET_KEY=a7f3c9e2d1b4f6a8c3e5d7b9f1a2c4e6d8b0a2f4c6e8a0b2d4f6a8c0e2d4f6a8
```

**Production Recommendations**:
1. **Never commit SECRET_KEY to version control**
2. **Use different values** for development, staging, production
3. **Store in secret managers**: AWS Secrets Manager, HashiCorp Vault, Azure Key Vault
4. **Rotate regularly**: Every 90 days in production
5. **Regenerate after suspected breach**: Immediately rotate if compromised

---

#### JWT Algorithm (`JWT_ALGORITHM`)

**Valid Values**: `HS256`, `RS256`, `ES256`

| Algorithm | Type | Security | Performance | Use Case |
|-----------|------|----------|-------------|----------|
| `HS256` | HMAC-SHA256 | Good | Fast | **Default** - Symmetric key |
| `RS256` | RSA-SHA256 | Better | Slower | Asymmetric keys (microservices) |
| `ES256` | ECDSA-SHA256 | Best | Fastest | Modern asymmetric |

**Production Recommendation**:
- **Default**: `HS256` for single-service deployments
- **Microservices**: Consider `RS256` for distributed systems

---

#### JWT Token Expiration (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)

**Valid Values**: Integer (minutes)

| Setting | Duration | Security | User Experience | Use Case |
|---------|----------|----------|-----------------|----------|
| `5` | 5 minutes | Very High | Poor (frequent login) | High-security applications |
| `15` | 15 minutes | High | Acceptable | Financial systems |
| `30` | 30 minutes | **Default** | **Good** | **Standard production** |
| `60` | 1 hour | Medium | Better | Internal tools |
| `1440` | 24 hours | Low | Best | Development only |

**Production Recommendations**:
- **Standard**: 30 minutes (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30`)
- **High-security**: 15 minutes
- **Development**: 1440 minutes (24 hours) for convenience

---

### Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | integer | `60` | API requests per minute |

**Valid Values**: Integer (requests per minute per IP/user)

**Performance Impact**:

| Setting | Requests/Min | Use Case | Protection Level |
|---------|--------------|----------|------------------|
| `10` | 10 | Strict API | High - Prevents abuse |
| `30` | 30 | Limited usage | Medium-High |
| `60` | **Default** | **Standard production** | **Medium** |
| `120` | 120 | High-volume | Low |
| `300` | 300 | Bulk operations | Minimal |

**Production Recommendations**:

```bash
# Standard production
RATE_LIMIT_PER_MINUTE=60

# High-security (financial, healthcare)
RATE_LIMIT_PER_MINUTE=30

# High-volume bulk operations
RATE_LIMIT_PER_MINUTE=300
```

---

### Security Best Practices

#### ✅ DO (Production)

```bash
# 1. Generate strong secrets
SECRET_KEY=$(openssl rand -hex 32)

# 2. Use HTTPS in production
FRONTEND_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com,https://www.example.com

# 3. Enable rate limiting
RATE_LIMIT_PER_MINUTE=60

# 4. Short token expiration
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 5. Restrict CORS origins
CORS_ORIGINS=https://app.example.com  # No wildcards

# 6. Use database SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

#### ❌ DON'T (Security Anti-Patterns)

```bash
# ❌ NEVER commit secrets to git
git add .env  # BAD - .env should be in .gitignore

# ❌ NEVER use default passwords
POSTGRES_PASSWORD=postgres  # BAD
SECRET_KEY=secret  # BAD
GRAFANA_PASSWORD=admin  # BAD

# ❌ NEVER allow all CORS origins
CORS_ORIGINS=*  # BAD - Allows any origin

# ❌ NEVER use long token expiration in production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # BAD - 7 days!

# ❌ NEVER disable rate limiting
RATE_LIMIT_PER_MINUTE=999999  # BAD

# ❌ NEVER use HTTP in production
FRONTEND_URL=http://app.example.com  # BAD - Use HTTPS
```

---

### Security Checklist

**Pre-Deployment Security Review**:

```bash
# ✅ 1. Secrets Management
[ ] SECRET_KEY is cryptographically random (32+ chars)
[ ] All default passwords changed (POSTGRES, GRAFANA, REDIS)
[ ] Secrets stored in secret managers
[ ] Different secrets for dev/staging/prod

# ✅ 2. Network Security
[ ] HTTPS enabled
[ ] CORS origins restricted
[ ] Rate limiting enabled
[ ] Database connections use SSL

# ✅ 3. Authentication
[ ] JWT expiration set to reasonable time (15-60 min)
[ ] Strong JWT algorithm (HS256 or RS256)
```

---

## File Upload Configuration

### Upload Limits

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | integer | `10` | Maximum upload size (MB) |
| `ALLOWED_FILE_TYPES` | string | `.pdf,.docx` | Allowed file extensions |
| `UPLOAD_DIR` | string | `./uploads` | Upload directory |

### Size Calculation

```python
# Convert MB to bytes
max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Example: 10 MB = 10,485,760 bytes
```

### File Type Validation

| Extension | MIME Type | Support |
|-----------|-----------|---------|
| `.pdf` | `application/pdf` | Full |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Full |

### Upload Directory Permissions

```bash
# Create upload directory with correct permissions
mkdir -p ./uploads
chmod 755 ./uploads
```

---

## Analysis Configuration

### Analysis Timeouts

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ANALYSIS_TIMEOUT_SECONDS` | integer | `300` | Maximum analysis time (5 minutes) |

### Feature Toggles

**Environment Files**: `backend/.env`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_KEYWORD_EXTRACTION` | boolean | `true` | Enable keyword extraction |
| `ENABLE_NER_EXTRACTION` | boolean | `true` | Enable named entity recognition |
| `ENABLE_GRAMMAR_CHECK` | boolean | `true` | Enable grammar checking |
| `ENABLE_EXPERIENCE_CALCULATION` | boolean | `true` | Enable experience calculation |
| `ENABLE_ERROR_DETECTION` | boolean | `true` | Enable error detection |

#### Detailed Feature Breakdown

**1. Keyword Extraction (`ENABLE_KEYWORD_EXTRACTION`)**

**Valid Values**: `true`, `false`

**What It Does**:
- Extracts top N keywords from resume using KeyBERT
- Identifies technical skills, technologies, and domain expertise
- Powers skill matching and vacancy recommendations

**Performance Impact**:

| Setting | Analysis Time | Memory | Quality Impact |
|---------|---------------|--------|----------------|
| `true` | +2-5 seconds | +100MB | High - Critical for matching |
| `false` | Baseline | Baseline | Severe - No skill extraction |

**When to Disable**:
- Debugging other features (isolate issues)
- Testing with keyword-free content
- Extremely low-resource environments

**Production Recommendation**: **ALWAYS KEEP ENABLED** - Core feature for resume analysis

---

**2. Named Entity Recognition (`ENABLE_NER_EXTRACTION`)**

**Valid Values**: `true`, `false`

**What It Does**:
- Extracts persons, organizations, dates, locations from resume
- Enables contact validation and experience timeline
- Powers company name matching and date parsing

**Performance Impact**:

| Setting | Analysis Time | Memory | Quality Impact |
|---------|---------------|--------|----------------|
| `true` | +1-3 seconds | +50MB | Medium - Important for validation |
| `false` | Baseline | Baseline | Medium - No entity extraction |

**When to Disable**:
- Testing basic analysis without entity extraction
- Language models not available (SpaCy not installed)
- Ultra-fast analysis required

**Production Recommendation**: **ENABLE** - Improves data quality and validation

---

**3. Grammar Check (`ENABLE_GRAMMAR_CHECK`)**

**Valid Values**: `true`, `false`

**What It Does**:
- Checks grammar, spelling, and style using LanguageTool API
- Provides improvement suggestions to candidates
- Validates resume readability

**Performance Impact**:

| Setting | Analysis Time | Memory | Network Dependency |
|---------|---------------|--------|-------------------|
| `true` | +5-10 seconds | +10MB | **Required** - External API |
| `false` | Baseline | Baseline | None |

**When to Disable**:
- **Offline environments** - Requires internet connection
- **High-volume processing** - Slows down pipeline significantly
- **LanguageTool API unavailable** - Service down or rate-limited
- **Non-English/Russian resumes** - Limited support

**Production Recommendation**:
- **Enable**: For premium/low-volume analysis where quality matters
- **Disable**: For high-volume batch processing or offline deployments

**Fallback Behavior**: Automatically disabled if LanguageTool API fails

---

**4. Experience Calculation (`ENABLE_EXPERIENCE_CALCULATION`)**

**Valid Values**: `true`, `false`

**What It Does**:
- Parses work experience dates from resume
- Calculates total years/months of experience
- Detects overlapping employment periods
- Validates experience against vacancy requirements

**Performance Impact**:

| Setting | Analysis Time | Memory | Quality Impact |
|---------|---------------|--------|----------------|
| `true` | +0.5-1 second | +5MB | High - Critical for matching |
| `false` | Baseline | Baseline | Severe - No experience data |

**When to Disable**:
- Resumes with no date information
- Testing without experience parsing

**Production Recommendation**: **ALWAYS KEEP ENABLED** - Essential for candidate evaluation

---

**5. Error Detection (`ENABLE_ERROR_DETECTION`)**

**Valid Values**: `true`, `false`

**What It Does**:
- Validates resume completeness (email, phone, portfolio)
- Checks resume length requirements
- Identifies missing critical information
- Detects potential fraud (e.g., missing contact info)

**Performance Impact**:

| Setting | Analysis Time | Memory | Quality Impact |
|---------|---------------|--------|----------------|
| `true` | +0.2-0.5 seconds | +5MB | Medium - Important for QA |
| `false` | Baseline | Baseline | Low - No validation |

**Error Types Detected**:

| Error Type | Severity | Detects |
|------------|----------|---------|
| Missing email | `error` | No @ symbol in text |
| Missing phone | `error` | No phone number pattern |
| Too short | `warning` | < 500 characters |
| No portfolio | `warning` | Junior role + no portfolio link |
| Date gaps | `warning` | Employment gaps > 6 months |

**When to Disable**:
- Processing partial resumes or CV fragments
- Testing analysis pipeline

**Production Recommendation**: **ENABLE** - Improves data quality and user feedback

---

#### Performance Optimization Matrix

```
┌─────────────────────────────────────────────────────────────┐
│           Feature Flags vs Performance Trade-offs            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Configuration              │ Time  │ Memory │ Quality       │
├─────────────────────────────┼───────┼────────┼───────────┤
│  All features enabled        │ 15-30s│ 500MB  │ 100%       │
│  No grammar check            │ 10-20s│ 490MB  │ 90%        │
│  No NER                      │ 12-25s│ 450MB  │ 85%        │
│  No keyword extraction       │ 10-18s│ 400MB  │ 50% (BAD)  │
│  Minimal (error detect only) │  5-10s│ 350MB  │ 30% (BAD)  │
└─────────────────────────────────────────────────────────────┘
```

#### Recommended Configurations

**Maximum Quality (Premium Analysis)**
```bash
ENABLE_KEYWORD_EXTRACTION=true
ENABLE_NER_EXTRACTION=true
ENABLE_GRAMMAR_CHECK=true
ENABLE_EXPERIENCE_CALCULATION=true
ENABLE_ERROR_DETECTION=true
```

**High Performance (Fast Analysis)**
```bash
ENABLE_KEYWORD_EXTRACTION=true
ENABLE_NER_EXTRACTION=true
ENABLE_GRAMMAR_CHECK=false      # Skip - slowest feature
ENABLE_EXPERIENCE_CALCULATION=true
ENABLE_ERROR_DETECTION=true
```

**Basic Processing (Minimal Features)**
```bash
ENABLE_KEYWORD_EXTRACTION=true
ENABLE_NER_EXTRACTION=false     # Disable - not critical
ENABLE_GRAMMAR_CHECK=false
ENABLE_EXPERIENCE_CALCULATION=true
ENABLE_ERROR_DETECTION=false
```

**Debugging (Step-by-Step)**
```bash
# Test each feature in isolation
ENABLE_ERROR_DETECTION=true     # Start here
ENABLE_KEYWORD_EXTRACTION=false
ENABLE_NER_EXTRACTION=false
ENABLE_GRAMMAR_CHECK=false
ENABLE_EXPERIENCE_CALCULATION=false
```

#### Feature Dependencies

Some features depend on others:

```
┌──────────────────────────────────────────────────┐
│          Feature Dependency Graph                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────┐                            │
│  │ Text Extraction  │                            │
│  └────────┬─────────┘                            │
│           │                                       │
│           ▼                                       │
│  ┌──────────────────────────────┐                │
│  │ Language Detection           │                │
│  └────────┬─────────────────────┘                │
│           │                                        │
│           ├───────┬────────┬────────┬─────────┐  │
│           ▼       ▼        ▼        ▼         ▼  │
│     ┌─────┐ ┌─────┐ ┌──────┐ ┌─────┐ ┌──────┐ │
│     │NER  │ │Key  │ │Gram  │ │Exp  │ │Error │ │
│     │     │ │word │ │mar   │ │erie │ │Detec ││
│     └─────┘ └─────┘ └──────┘ └─────┘ └──────┘ │
│       │       │        │        │        │      │
│       └───────┴────────┴────────┴────────┴──┘   │
│                   │                               │
│                   ▼                               │
│         ┌──────────────────┐                      │
│         │ Analysis Results │                      │
│         └──────────────────┘                      │
└──────────────────────────────────────────────────┘
```

**Key Points**:
- Language detection runs automatically before all features
- Grammar check requires network (LanguageTool API)
- Keyword extraction requires KeyBERT model
- NER requires SpaCy models
- Features run in parallel where possible

### Keyword Extraction Parameters

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KEYWORD_EXTRACTION_TOP_N` | integer | `20` | Number of keywords to extract |
| `KEYWORD_NGRAM_RANGE_MIN` | integer | `1` | Minimum n-gram size |
| `KEYWORD_NGRAM_RANGE_MAX` | integer | `2` | Maximum n-gram size |

### Resume Validation

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RESUME_MIN_LENGTH` | integer | `500` | Minimum resume length (characters) |
| `RESUME_MAX_LENGTH` | integer | `10000` | Maximum resume length (characters) |

### ATS Simulation

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ATS_THRESHOLD` | float | `0.6` | Minimum ATS score to pass (0.0-1.0) |
| `ATS_VISUAL_CHECK_ENABLED` | boolean | `true` | Enable visual format checking |
| `ATS_KEYWORD_WEIGHT` | float | `0.3` | Weight for keyword matching |
| `ATS_EXPERIENCE_WEIGHT` | float | `0.3` | Weight for experience |
| `ATS_EDUCATION_WEIGHT` | float | `0.2` | Weight for education |
| `ATS_FIT_WEIGHT` | float | `0.2` | Weight for overall fit |

**Weight Sum**: Should equal ~1.0 for accurate scoring

---

## Development Settings

### Debug Mode

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | boolean | `false` | Enable debug mode |
| `RELOAD` | boolean | `false` | Enable auto-reload |

### Testing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TESTING` | boolean | `false` | Enable test mode |

### Frontend DevTools

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DEBUG` | boolean | `false` | Enable debug mode |
| `VITE_ENABLE_REACT_DEVTOOLS` | boolean | `true` | Enable React DevTools |
| `VITE_SHOW_COMPONENT_NAMES` | boolean | `true` | Show component names in DevTools |

### Mock API

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_MOCK_API` | boolean | `false` | Mock API in development |

---

## Production Deployment

### Production Checklist

```bash
# ✅ Change all default passwords
POSTGRES_PASSWORD=<strong_password>
GRAFANA_PASSWORD=<strong_password>
SECRET_KEY=<generated_with_openssl>

# ✅ Use HTTPS
FRONTEND_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com

# ✅ Configure proper logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# ✅ Enable backups
BACKUP_ENABLED=true
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=production-backups

# ✅ Configure alerts
ALERT_EMAIL_ADDRESS=ops@example.com
GRAFANA_SMTP_USER=alerts@example.com
GRAFANA_SMTP_PASSWORD=<smtp_password>

# ✅ Set reasonable timeouts
ANALYSIS_TIMEOUT_SECONDS=300
CELERY_TASK_TIME_LIMIT=300

# ✅ Configure rate limiting
RATE_LIMIT_PER_MINUTE=60
```

### Environment-Specific Files

```bash
# Development
cp .env.example .env.development

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.production
```

### Docker Compose Override

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - LOG_LEVEL=INFO
      - DEBUG=false
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

---

## Environment-Specific Examples

### Development Environment

```bash
# .env.development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=resume_analysis_dev

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_analysis_dev
REDIS_URL=redis://localhost:6379/0

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

LOG_LEVEL=DEBUG
DEBUG=true

BACKUP_ENABLED=false

# frontend/.env.development
VITE_API_URL=http://localhost:8000
VITE_ENABLE_REACT_DEVTOOLS=true
VITE_DEBUG=true
```

### Staging Environment

```bash
# .env.staging
POSTGRES_USER=staging_user
POSTGRES_PASSWORD=<staging_password>
POSTGRES_DB=resume_analysis_staging

DATABASE_URL=postgresql://staging_user:<password>@staging-db.example.com:5432/resume_analysis_staging
REDIS_URL=redis://staging-redis.example.com:6379/0

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

FRONTEND_URL=https://staging.example.com
CORS_ORIGINS=https://staging.example.com

LOG_LEVEL=INFO
DEBUG=false

BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=7

# frontend/.env.staging
VITE_API_URL=https://staging-api.example.com
VITE_ENABLE_ERROR_TRACKING=true
VITE_SENTRY_ENVIRONMENT=staging
```

### Production Environment

```bash
# .env.production
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=<strong_production_password>
POSTGRES_DB=resume_analysis

DATABASE_URL=postgresql://prod_user:<password>@prod-db.example.com:5432/resume_analysis
REDIS_URL=redis://prod-redis.example.com:6379/0

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080

FRONTEND_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com,https://www.example.com

LOG_LEVEL=INFO
DEBUG=false

BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=agenthr-production-backups
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_REGION=us-east-1

ALERT_EMAIL_ADDRESS=ops@example.com

# Security
SECRET_KEY=<generated_with_openssl>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_PER_MINUTE=60

# frontend/.env.production
VITE_API_URL=https://api.example.com
VITE_ENABLE_ANALYTICS=true
VITE_GA_TRACKING_ID=UA-XXXXXXXXX-X
VITE_ENABLE_ERROR_TRACKING=true
VITE_SENTRY_ENVIRONMENT=production
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "
from backend.config import get_settings
s = get_settings()
print(s.database_url)
"

# Common issues:
# 1. Wrong password → Check POSTGRES_PASSWORD matches
# 2. Wrong host → Use service name in Docker (postgres, not localhost)
# 3. Port already in use → Change BACKEND_PORT or stop conflicting service
```

### Redis Connection Issues

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis

# Test from backend
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print(r.ping())
"
```

### ML Model Download Issues

```bash
# Check models cache
ls -la backend/models_cache/

# Clear cache and re-download
docker-compose exec backend rm -rf /app/models_cache/*
docker-compose restart backend

# Pre-download models
docker-compose exec backend python -c "
import spacy
spacy.cli.download('en_core_web_sm')
spacy.cli.download('ru_core_news_sm')
"
```

### Environment Variable Not Loading

```bash
# Check if .env file exists
ls -la .env

# Verify variable syntax (no spaces around =)
# ❌ WRONG: DATABASE_URL = postgresql://...
# ✅ CORRECT: DATABASE_URL=postgresql://...

# Restart services after changing .env
docker-compose down
docker-compose up -d

# Verify environment in container
docker-compose exec backend env | grep DATABASE_URL
```

### Celery Worker Not Processing Tasks

```bash
# Check worker status
docker-compose exec celery_worker celery -A celery_app.celery_app inspect active

# View worker logs
docker-compose logs celery_worker

# Check registered tasks
docker-compose exec celery_worker celery -A celery_app.celery_app inspect registered

# Common issues:
# 1. Wrong broker URL → Check CELERY_BROKER_URL
# 2. Queue mismatch → Verify queue names match
# 3. Worker concurrency too low → Increase CELERY_WORKER_CONCURRENCY
```

### Frontend Cannot Connect to Backend

```bash
# Check VITE_API_URL
cat frontend/.env | grep VITE_API_URL

# Test backend connectivity
curl http://localhost:8000/docs

# Check CORS configuration
docker-compose logs backend | grep CORS

# Common issues:
# 1. Wrong VITE_API_URL → Should match BACKEND_PORT
# 2. CORS blocked → Check FRONTEND_URL in backend .env
# 3. Backend not running → docker-compose ps backend
```

### Permission Issues with Uploads

```bash
# Check upload directory permissions
ls -la backend/uploads/

# Fix permissions
docker-compose exec backend chmod 755 /app/data/uploads

# Check disk space
df -h

# Common issues:
# 1. Directory doesn't exist → Create with mkdir -p
# 2. Wrong permissions → chmod 755 or 777 (dev only)
# 3. Disk full → Check df -h
```

### Backup Failures

```bash
# Check backup logs
docker-compose logs celery_beat | grep backup

# Verify backup directory
docker-compose exec backend ls -la /app/data/backups/

# Test S3 connection
docker-compose exec backend python -c "
import boto3
client = boto3.client('s3', ...)
print(client.list_buckets())
"

# Common issues:
# 1. Wrong S3 credentials → Verify BACKUP_S3_* variables
# 2. Insufficient permissions → Check IAM policies
# 3. Network issues → Test S3 endpoint connectivity
```

### Monitoring Issues

```bash
# Check Grafana
docker-compose logs grafana | grep error

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Loki
docker-compose logs loki
docker-compose logs promtail

# Common issues:
# 1. Wrong password → Reset GRAFANA_PASSWORD
# 2. Dashboard not loading → Check provisioning files
# 3. No metrics → Verify ENABLE_PROMETHEUS_METRICS=true
```

---

## Best Practices

### Security

✅ **DO**:
- Use strong, unique passwords in production
- Rotate secrets regularly (every 90 days)
- Use different values for dev/staging/prod
- Store secrets in secret managers (AWS Secrets Manager, HashiCorp Vault)
- Enable HTTPS in production
- Restrict CORS origins to specific domains
- Use environment-specific .env files

❌ **DON'T**:
- Commit .env files to version control
- Use default passwords in production
- Share secrets via email/chat
- Hardcode secrets in code
- Use `*` for CORS_ORIGINS in production

### Performance

✅ **DO**:
- Adjust worker concurrency based on CPU cores
- Enable model caching in production
- Use connection pooling for databases
- Set appropriate timeouts
- Monitor resource usage

❌ **DON'T**:
- Set concurrency higher than CPU cores
- Disable all logging in production
- Use very long timeouts (can hang workers)

### Reliability

✅ **DO**:
- Enable automated backups
- Configure alert notifications
- Use health checks in Docker
- Set up log aggregation (Loki)
- Monitor disk space

❌ **DON'T**:
- Skip backup configuration
- Ignore alert setup
- Run without monitoring

---

## Additional Resources

- [README.md](../README.md) - Project overview
- [ML_PIPELINE.md](../ML_PIPELINE.md) - ML/NLP pipeline details
- [SETUP.md](../SETUP.md) - Installation guide
- [Grafana Documentation](https://grafana.com/docs/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## Quick Reference

### Essential Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop all services
docker-compose down

# Execute command in container
docker-compose exec backend bash

# Check environment in container
docker-compose exec backend env

# Run database migration
docker-compose exec backend alembic upgrade head

# Load test data
docker-compose exec backend python scripts/reset_and_reload.py
```

### Default Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | `80`/`3000`/`5173` | http://localhost |
| Backend API | `8000` | http://localhost:8000 |
| API Docs | `8000` | http://localhost:8000/docs |
| Grafana | `3001` | http://localhost:3001 |
| Prometheus | `9090` | http://localhost:9090 |
| Loki | `3100` | http://localhost:3100 |
| PostgreSQL | `5432` | - |
| Redis | `6379` | - |
| cAdvisor | `8080` | http://localhost:8080 |

---

**Last Updated**: 2024-02-01
**Version**: 1.0.0
