# Environment Variables — Complete Reference

Comprehensive guide to all environment variables used in AgentHR for configuration, deployment, and operation.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Variable Interdependencies](#variable-interdependencies)
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
- [Quick Reference Tables](#quick-reference-tables)
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

## Variable Interdependencies

This section explains how environment variables relate to and depend on each other. Understanding these relationships is crucial for proper configuration and avoiding runtime errors.

### High-Level Interdependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   Environment Variable Relationships            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │   Database   │────▶│   Backend    │────▶│   Frontend   │  │
│  │   Variables  │     │   Variables  │     │   Variables  │  │
│  └──────────────┘     └──────┬───────┘     └──────┬───────┘  │
│                              │                     │           │
│                              ▼                     ▼           │
│                        ┌────────────────────────────┐         │
│                        │    Cross-Service Config    │         │
│                        │  (CORS, URLs, Security)    │         │
│                        └────────────────────────────┘         │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │     Redis    │────▶│    Celery    │────▶│   ML Models  │  │
│  │  Variables   │     │  Variables   │     │  Variables   │  │
│  └──────────────┘     └──────────────┘     └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Database Configuration Interdependencies

#### Database URL Construction

```
┌─────────────────────────────────────────────────────────────┐
│            DATABASE_URL Construction Logic                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DATABASE_URL =                                            │
│    "postgresql://" +                                       │
│    POSTGRES_USER + ":" +                                   │
│    POSTGRES_PASSWORD + "@" +                               │
│    POSTGRES_HOST + ":" +                                   │
│    POSTGRES_PORT + "/" +                                   │
│    POSTGRES_DB                                             │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │ Component    │  │ Example Value │  │ Required?    │  │
│  ├───────────────┼─────────────────┼─────────────────┤  │
│  │ POSTGRES_USER│ postgres        │ ✅ Yes         │  │
│  │ POSTGRES_    │ postgres        │ ✅ Yes         │  │
│  │   PASSWORD   │                 │                │  │
│  │ POSTGRES_    │ localhost:5432  │ ✅ Yes         │  │
│  │   HOST:PORT  │                 │                │  │
│  │ POSTGRES_DB  │ resume_analysis │ ✅ Yes         │  │
│  └───────────────┴─────────────────┴─────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Database Pool ↔ Celery Workers Relationship

**Critical Formula**: `DB_POOL_SIZE >= CELERY_WORKER_CONCURRENCY * 2`

```
┌──────────────────────────────────────────────────────────────┐
│        Pool Size Calculation Based on Workers               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   CELERY_WORKER_CONCURRENCY=2                               │
│         │                                                    │
│         │ Formula: pool_size = workers * 2                  │
│         ▼                                                    │
│   DB_POOL_SIZE=20  (Recommended: 10x workers for spikes)    │
│         │                                                    │
│         │ Additional capacity for overflow                  │
│         ▼                                                    │
│   DB_MAX_OVERFLOW=10  (Spare connections)                   │
│                                                              │
│   Total Capacity: 30 concurrent connections                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Pool Settings Interdependency Matrix**:

| Variable | Depends On | Affects | Formula/Rule |
|----------|-----------|---------|--------------|
| `DB_POOL_SIZE` | `CELERY_WORKER_CONCURRENCY` | `DB_MAX_OVERFLOW` | `>= workers * 2` |
| `DB_MAX_OVERFLOW` | `DB_POOL_SIZE` | Total connections | `~ pool_size / 2` |
| `DB_POOL_RECYCLE` | Database idle timeout | Connection stability | `< database timeout` |
| `DB_POOL_TIMEOUT` | Expected load | User experience | `30` (balanced) |
| `DB_POOL_PRE_PING` | Network stability | Error rate | `true` (always) |

**Example Configurations**:

```bash
# Scenario 1: Development (2 workers)
CELERY_WORKER_CONCURRENCY=2
DB_POOL_SIZE=20      # 2 * 2 * 5 (safety factor)
DB_MAX_OVERFLOW=10

# Scenario 2: Production (10 workers)
CELERY_WORKER_CONCURRENCY=10
DB_POOL_SIZE=50      # 10 * 2 * 2.5
DB_MAX_OVERFLOW=20

# Scenario 3: High-traffic (20 workers)
CELERY_WORKER_CONCURRENCY=20
DB_POOL_SIZE=100     # 20 * 2 * 2.5
DB_MAX_OVERFLOW=30
```

---

### Redis ↔ Celery Configuration Interdependencies

#### Broker and Backend URL Construction

```
┌─────────────────────────────────────────────────────────────┐
│         Celery-Redis Connection Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  REDIS_URL   │────▶│   Celery     │                     │
│  │  redis://... │     │   Tasks      │                     │
│  └──────────────┘     └──────┬───────┘                     │
│                             │                                │
│                             │ Uses for:                     │
│                             ├─ CELERY_BROKER_URL           │
│                             ├─ CELERY_RESULT_BACKEND       │
│                             └─ Lock/Cache storage          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           URL Relationship Examples                  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Scenario 1: Shared (Default)                         │   │
│  │   REDIS_URL              = redis://localhost:6379/0  │   │
│  │   CELERY_BROKER_URL      = redis://localhost:6379/0  │   │
│  │   CELERY_RESULT_BACKEND  = redis://localhost:6379/0  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Scenario 2: Separate Databases                       │   │
│  │   REDIS_URL              = redis://localhost:6379/0  │   │
│  │   CELERY_BROKER_URL      = redis://localhost:6379/1  │   │
│  │   CELERY_RESULT_BACKEND  = redis://localhost:6379/2  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Scenario 3: Redis Cluster (Production)               │   │
│  │   REDIS_URL              = redis://cluster:6379/0    │   │
│  │   CELERY_BROKER_URL      = redis://cluster:6379/0    │   │
│  │   CELERY_RESULT_BACKEND  = redis://cluster:6379/0    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Celery Task Configuration Interdependencies

```
┌─────────────────────────────────────────────────────────────┐
│         Task Time Limit Hierarchy                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HARD Limit (CELERY_TASK_TIME_LIMIT)                        │
│  │  300 seconds (5 minutes)                                 │
│  │                                                          │
│  │  ┌─ SOFT Limit (CELERY_TASK_SOFT_TIME_LIMIT)            │
│  │  │   280 seconds (4.67 minutes)                         │
│  │  │                                                     │
│  │  │   ┌─ Analysis Timeout (ANALYSIS_TIMEOUT_SECONDS)    │
│  │  │   │   180 seconds (3 minutes)                        │
│  │  │   │                                                │
│  │  │   │   Must be: SOFT < HARD                          │
│  │  │   │           Analysis << SOFT                       │
│  │  │   │                                                │
│  │  │   └────────────────────────────────                 │
│  │  │                                                     │
│  │  └────────────────────────────────                     │
│  │                                                          │
│  └─────────────────────────────────────────────────────    │
│                                                             │
│  Rule: ANALYSIS < SOFT < HARD                              │
│  Rule: SOFT should be 10-20 seconds before HARD            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Celery Configuration Matrix**:

| Variable | Depends On | Affects | Validation Rule |
|----------|-----------|---------|-----------------|
| `CELERY_BROKER_URL` | `REDIS_URL` | Task queue connectivity | Must be valid Redis URL |
| `CELERY_RESULT_BACKEND` | `REDIS_URL` | Result retrieval | Must be valid Redis URL |
| `CELERY_TASK_TIME_LIMIT` | `CELERY_TASK_SOFT_TIME_LIMIT` | Task termination | `> SOFT_LIMIT` by ~20s |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `ANALYSIS_TIMEOUT_SECONDS` | Graceful shutdown | `> ANALYSIS_TIMEOUT` |
| `CELERY_WORKER_CONCURRENCY` | CPU cores | `DB_POOL_SIZE`, memory | `<= CPU cores` |
| `CELERY_RESULT_EXPIRES` | Storage capacity | Redis memory usage | `86400` (1 day default) |

---

### Frontend ↔ Backend Configuration Interdependencies

#### CORS Configuration Flow

```
┌─────────────────────────────────────────────────────────────┐
│            Frontend-Backend Communication Flow             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │   Frontend       │         │    Backend       │        │
│  │   (Browser)      │         │   (FastAPI)      │        │
│  └────────┬─────────┘         └────────┬─────────┘        │
│           │                           │                   │
│           │ VITE_API_URL              │                   │
│           │ http://localhost:8000     │                   │
│           │                           │                   │
│           └─────────▶ HTTP Request ──▶│                   │
│                                       │                   │
│                                       │ Check CORS        │
│                                       │                   │
│                                       │ FRONTEND_URL      │
│                                       │ http://localhost:5173
│                                       │                   │
│                                       │ Is origin in      │
│                                       │ CORS_ORIGINS?    │
│                                       │                   │
│                         ┌─────────────┴─────────────┐     │
│                         │                           │     │
│                    Yes  │                           │ No  │
│                         ▼                           ▼     │
│                  ┌──────────┐               ┌──────────┐  │
│                  │ Allow   │               │ Block   │  │
│                  │ Response│               │ (CORS)  │  │
│                  └──────────┘               └──────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Frontend-Backend Relationship Matrix**:

| Frontend Variable | Backend Variable | Relationship | Error If Mismatch |
|-------------------|------------------|--------------|------------------|
| `VITE_API_URL` | `BACKEND_HOST`:`BACKEND_PORT` | Must match | Connection refused |
| `VITE_API_URL` (origin) | `FRONTEND_URL` | Should match | CORS errors |
| `VITE_API_URL` (origin) | `CORS_ORIGINS` | Must be in list | **CORS blocked** |
| `VITE_API_TIMEOUT` | `ANALYSIS_TIMEOUT_SECONDS` | Frontend > Backend | Premature timeout |

**Configuration Examples**:

```bash
# ✅ CORRECT - Matching configurations
# backend/.env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# frontend/.env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=120000  # 2 minutes

# ❌ WRONG - CORS will block
# backend/.env
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173

# frontend/.env
VITE_API_URL=http://localhost:3000  # Different port - NOT in CORS_ORIGINS!
```

---

### ML Model Configuration Interdependencies

#### Model Cache Path Relationships

```
┌─────────────────────────────────────────────────────────────┐
│           ML Model Cache Storage Hierarchy                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MODELS_CACHE_PATH=/app/models_cache                        │
│         │                                                   │
│         ├─────────────────────────────────────┐             │
│         │                                     │             │
│         ▼                                     ▼             │
│  TRANSFORMERS_CACHE                   HF_HOME              │
│  /app/models_cache/hub              /app/models_cache      │
│         │                                     │             │
│         │                                     │             │
│         ▼                                     │             │
│  ┌──────────────────┐                        │             │
│  │  Hugging Face    │                        │             │
│  │  Models          │                        │             │
│  │  (KeyBERT,       │                        │             │
│  │   SentTrans)     │                        │             │
│  └──────────────────┘                        │             │
│                                              │             │
│         ┌────────────────────────────────────┘             │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐                                      │
│  │  SpaCy Models    │                                      │
│  │  (en_core_web_sm│                                      │
│  │   ru_core_news) │                                      │
│  └──────────────────┘                                      │
│                                                             │
│  All paths should point to SAME directory for efficiency    │
└─────────────────────────────────────────────────────────────┘
```

**Model Configuration Matrix**:

| Variable | Depends On | Affects | Recommendation |
|----------|-----------|---------|----------------|
| `MODELS_CACHE_PATH` | Disk space | `TRANSFORMERS_CACHE`, `HF_HOME` | Persistent volume |
| `TRANSFORMERS_CACHE` | `MODELS_CACHE_PATH` | Hugging Face models | `${MODELS_CACHE_PATH}/hub` |
| `HF_HOME` | `MODELS_CACHE_PATH` | Hugging Face config | `${MODELS_CACHE_PATH}` |
| `KEYBERT_MODEL` | `TRANSFORMERS_CACHE` | Memory, speed | `distilbert-base-nli-mean-tokens` |
| `SPACY_MODEL_EN` | `MODELS_CACHE_PATH` | NER accuracy | `en_core_web_sm` |
| `SPACY_MODEL_RU` | `MODELS_CACHE_PATH` | NER accuracy | `ru_core_news_sm` |

**Memory Interdependencies**:

```
┌─────────────────────────────────────────────────────────────┐
│        Model Memory Usage & Trade-offs                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Total Memory = DB_Pool + KeyBERT + SpaCy_EN + SpaCy_RU    │
│                                                             │
│  Example Configuration:                                     │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Model                    │ Memory │ Impact       │      │
│  ├──────────────────────────┼────────┼──────────────┤      │
│  │ KeyBERT (distilbert)     │ 250MB  │ Medium       │      │
│  │ SpaCy EN (sm)            │  12MB  │ Low          │      │
│  │ SpaCy RU (sm)            │  17MB  │ Low          │      │
│  │ DB Pool (20 connections) │ 200MB  │ High         │      │
│  │ OVERHEAD                 │ 100MB  │ Baseline     │      │
│  ├──────────────────────────┼────────┼──────────────┤      │
│  │ TOTAL                    │ 579MB  │              │      │
│  └──────────────────────────┴────────┴──────────────┘      │
│                                                             │
│  If using larger models:                                    │
│  - KeyBERT (mpnet): +150MB                                  │
│  - SpaCy (md): +60MB per language                           │
│  - SpaCy (lg): +480MB per language                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Security Configuration Interdependencies

#### JWT Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│            JWT Token Lifecycle                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Login Request                                          │
│     │                                                       │
│     ▼                                                       │
│  2. Validate Credentials                                    │
│     │                                                       │
│     ▼                                                       │
│  3. Generate Token                                          │
│     │                                                       │
│     ├─ SECRET_KEY (signing)                                │
│     ├─ JWT_ALGORITHM (HS256/RS256)                         │
│     └─ JWT_ACCESS_TOKEN_EXPIRE_MINUTES (30)               │
│                                                             │
│  4. Return Token to Client                                  │
│     │                                                       │
│     ├─ Token includes expiration timestamp                 │
│     └─ Client stores token                                 │
│                                                             │
│  5. Authenticated Request                                   │
│     │                                                       │
│     ├─ Client sends token in header                        │
│     ├─ Server validates with SECRET_KEY                    │
│     ├─ Check expiration (<= EXPIRE_MINUTES)                │
│     └─ Allow/Deny request                                  │
│                                                             │
│  Interdependency:                                           │
│  SHORTER expiration = More secure but worse UX              │
│  LONGER expiration = Better UX but less secure              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Security Configuration Matrix**:

| Variable | Depends On | Affects | Security Trade-off |
|----------|-----------|---------|-------------------|
| `SECRET_KEY` | Cryptographically random | All JWT tokens | **Critical** - Must be strong |
| `JWT_ALGORITHM` | Key type (symmetric/asymmetric) | Token validation | `HS256` (fast) vs `RS256` (secure) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | User experience requirement | Login frequency | `30` (balanced) |
| `RATE_LIMIT_PER_MINUTE` | Expected traffic | API protection | `60` (standard) |
| `CORS_ORIGINS` | `FRONTEND_URL` | XSS protection | Must be specific domains |

**Security Level Configurations**:

```bash
# High Security (Financial/Healthcare)
SECRET_KEY=<very-strong-random-key>
JWT_ALGORITHM=RS256  # Asymmetric
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
RATE_LIMIT_PER_MINUTE=30

# Standard Security (Most Applications)
SECRET_KEY=<strong-random-key>
JWT_ALGORITHM=HS256  # Symmetric (faster)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_PER_MINUTE=60

# Relaxed Security (Internal Tools)
SECRET_KEY=<random-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
RATE_LIMIT_PER_MINUTE=120
```

---

### Analysis Feature Interdependencies

#### Feature Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│           Analysis Pipeline Dependencies                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐                                      │
│  │ Text Extraction  │                                      │
│  └────────┬─────────┘                                      │
│           │                                               │
│           ▼                                               │
│  ┌──────────────────┐                                      │
│  │ Language Detect  │                                      │
│  └────────┬─────────┘                                      │
│           │                                               │
│           ├───────────────────────────────────────┐       │
│           │                                       │       │
│           ▼                                       ▼       │
│  ┌──────────────────┐                    ┌────────────┐  │
│  │ Select Models    │                    │ All Features│  │
│  │ based on language│                    │ continue   │  │
│  └────────┬─────────┘                    └────────────┘  │
│           │                                       │       │
│           │                                       │       │
│           ├─────────┬──────────┬──────────┬───────┘       │
│           │         │          │          │               │
│           ▼         ▼          ▼          ▼               │
│     ┌─────────┐ ┌─────┐ ┌──────────┐ ┌──────┐           │
│     │  NER    │ │Key  │ │ Grammar  │ │ Exp  │           │
│     │Extract. │ │word │ │  Check   │ │Calc. │           │
│     └────┬────┘ └──┬──┘ └────┬─────┘ └──┬───┘           │
│          │        │         │          │               │
│          │        │         │          │               │
│          ▼        ▼         ▼          ▼               │
│     ┌──────────────────────────────────────┐           │
│     │      Error Detection (always)        │           │
│     └──────────────┬───────────────────────┘           │
│                    │                                   │
│                    ▼                                   │
│          ┌──────────────────────┐                      │
│          │   Analysis Results   │                      │
│          └──────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Feature Toggle Matrix**:

| Feature | Required Variables | Optional Variables | Conflicts With |
|---------|-------------------|-------------------|----------------|
| `ENABLE_KEYWORD_EXTRACTION` | `KEYBERT_MODEL`, `TRANSFORMERS_CACHE` | `KEYWORD_EXTRACTION_TOP_N` | None |
| `ENABLE_NER_EXTRACTION` | `SPACY_MODEL_EN`, `SPACY_MODEL_RU` | `MODELS_CACHE_PATH` | None |
| `ENABLE_GRAMMAR_CHECK` | Network access | `LLM_PROVIDER` | Offline environments |
| `ENABLE_EXPERIENCE_CALCULATION` | None | `RESUME_MIN_LENGTH` | None |
| `ENABLE_ERROR_DETECTION` | `RESUME_MIN_LENGTH` | None | None |

**Performance Impact Chain**:

```
┌─────────────────────────────────────────────────────────────┐
│      Configuration → Performance Impact Chain              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENABLE_GRAMMAR_CHECK=true                                 │
│      │                                                      │
│      ├─ Requires: Network connection                       │
│      ├─ Adds: +5-10 seconds per analysis                   │
│      ├─ Depends on: LanguageTool API availability          │
│      └─ Fallback: Disables automatically if fails          │
│                                                             │
│  ENABLE_NER_EXTRACTION=true                                │
│      │                                                      │
│      ├─ Requires: SpaCy models loaded                      │
│      ├─ Adds: +1-3 seconds per analysis                    │
│      ├─ Memory: +50MB per language model                   │
│      └─ Depends on: `SPACY_MODEL_*` variables              │
│                                                             │
│  ENABLE_KEYWORD_EXTRACTION=true                            │
│      │                                                      │
│      ├─ Requires: KeyBERT model loaded                     │
│      ├─ Adds: +2-5 seconds per analysis                    │
│      ├─ Memory: +100-400MB (depending on model)            │
│      └─ Depends on: `KEYBERT_MODEL`, `TRANSFORMERS_CACHE`  │
│                                                             │
│  Total Time = Base + NER + Keywords + Grammar               │
│  Total Memory = Base + NER + Keywords + DB_Pool            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Complete Interdependency Quick Reference

#### Critical Variable Relationships

| Variable Group | Primary Variables | Critical Dependencies | Validation |
|----------------|------------------|----------------------|------------|
| **Database** | `DATABASE_URL`, `DB_POOL_SIZE` | `CELERY_WORKER_CONCURRENCY` | `DB_POOL_SIZE >= workers * 2` |
| **Celery** | `CELERY_BROKER_URL`, `CELERY_WORKER_CONCURRENCY` | `REDIS_URL`, `DB_POOL_SIZE` | Worker concurrency <= CPU cores |
| **Frontend-Backend** | `VITE_API_URL`, `CORS_ORIGINS` | `BACKEND_PORT`, `FRONTEND_URL` | API URL origin in CORS_ORIGINS |
| **Security** | `SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | None (independent) | Secret key >= 32 chars |
| **ML Models** | `MODELS_CACHE_PATH`, `KEYBERT_MODEL` | `TRANSFORMERS_CACHE`, `HF_HOME` | All paths point to same dir |
| **Analysis** | `ENABLE_*` flags | Model variables | Grammar check requires network |

#### Configuration Validation Checklist

Before deploying, verify these relationships:

```bash
# ✅ 1. Database & Celery Alignment
if [ $CELERY_WORKER_CONCURRENCY -gt 2 ]; then
    [ $DB_POOL_SIZE -ge $(($CELERY_WORKER_CONCURRENCY * 2)) ] || echo "ERROR: Pool too small"
fi

# ✅ 2. Time Limit Hierarchy
[ $ANALYSIS_TIMEOUT_SECONDS -lt $CELERY_TASK_SOFT_TIME_LIMIT ] || echo "ERROR: Analysis timeout too high"
[ $CELERY_TASK_SOFT_TIME_LIMIT -lt $CELERY_TASK_TIME_LIMIT ] || echo "ERROR: Soft limit >= hard limit"

# ✅ 3. CORS Configuration
# VITE_API_URL origin must be in CORS_ORIGINS
# e.g., if VITE_API_URL=http://localhost:8000
# then CORS_ORIGINS must contain http://localhost:8000 or http://localhost:*

# ✅ 4. Model Cache Consistency
# All model cache paths should be under same parent directory
[ -n "$MODELS_CACHE_PATH" ] || echo "ERROR: MODELS_CACHE_PATH not set"

# ✅ 5. Security Settings
[ ${#SECRET_KEY} -ge 32 ] || echo "WARNING: SECRET_KEY too short"
[ $JWT_ACCESS_TOKEN_EXPIRE_MINUTES -le 1440 ] || echo "WARNING: Token expiry > 24 hours"
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

## Backend Localization Configuration

### Language Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEFAULT_LANGUAGE` | string | `en` | Default language for backend processing |
| `SUPPORTED_LANGUAGES` | string | `en,ru` | Comma-separated list of supported languages |

**Supported Languages**:

| Code | Language | Features | Model Requirements |
|------|----------|----------|-------------------|
| `en` | English | Full support | `en_core_web_sm` SpaCy model |
| `ru` | Russian | Full support | `ru_core_news_sm` SpaCy model |

**Language Detection Flow**:

```
┌─────────────────────────────────────────────────────────────┐
│              Language Detection & Processing                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Resume Uploaded                                            │
│       │                                                     │
│       ▼                                                     │
│  Detect Language (auto-detect)                              │
│       │                                                     │
│       ├─ Supported? ──No──▶ Skip language-specific features │
│       │                                                     │
│       └─ Yes ──▶ Load Language-Specific Models             │
│                     │                                       │
│                     ├─ English ─▶ en_core_web_sm           │
│                     ├─ Russian ─▶ ru_core_news_sm          │
│                     └─ Other ──▶ Use DEFAULT_LANGUAGE model│
│                                                             │
│  Process with Language-Specific Features:                   │
│  - NER extraction (Named Entity Recognition)                │
│  - Grammar checking (LanguageTool)                          │
│  - Date parsing (experience calculation)                    │
│  - Text normalization                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Configuration Examples**:

```bash
# English-only deployment
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en

# Bilingual deployment (English and Russian)
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,ru

# Russian-first deployment
DEFAULT_LANGUAGE=ru
SUPPORTED_LANGUAGES=ru,en
```

**Model Dependencies**:

Language-specific features require the corresponding SpaCy models:
- English: `SPACY_MODEL_EN=en_core_web_sm`
- Russian: `SPACY_MODEL_RU=ru_core_news_sm`

Models must be downloaded before first use:
```bash
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm
```

**Production Recommendations**:
- Only include languages you actually support in `SUPPORTED_LANGUAGES`
- Set `DEFAULT_LANGUAGE` to your most common language
- Ensure language-specific models are pre-downloaded
- Monitor memory usage when loading multiple language models (~20-50MB per language)
- Consider using CPU-based models (_sm) for production

**Interdependencies**:
- Affects model loading (only loads models for supported languages)
- Impacts NER extraction quality (language-dependent)
- Grammar checking requires language-specific LanguageTool configuration
- Date parsing varies by language format

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

## LanguageTool Configuration

### Grammar & Spelling Checking

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LANGUAGETOOL_SERVER` | string | `http://localhost:8081/v2/check` | LanguageTool API server URL |
| `LANGUAGETOOL_USE_PUBLIC_AS_FALLBACK` | boolean | `true` | Fall back to public API if local server fails |

**Server Options**:

| Deployment | Server URL | Notes |
|------------|-----------|-------|
| **Local Server** | `http://localhost:8081/v2/check` | Recommended for privacy and speed |
| **Public API** | `https://api.languagetool.org/v2/check` | Rate limited (20 requests/day) |
| **Custom Server** | `http://your-server:port/v2/check` | Self-hosted instance |

**Local Server Setup**:

```bash
# Using Docker (recommended)
docker run -p 8081:8010 \
  -e LANGUAGETOOL_LANGUAGE=en,ru \
  -v lt-data:/ngrams \
  languagetoolorg/languagetool:latest

# Or download and run locally
wget https://languagetool.org/download/LanguageTool-5.9.zip
unzip LanguageTool-5.9.zip
cd LanguageTool-5.9
java -cp languagetool-server.jar org.languagetool.server.HTTPServer \
  --port 8081 --language-models /path/to/ngrams
```

**Fallback Behavior**:

```
┌─────────────────────────────────────────────────────────────┐
│         LanguageTool Fallback Logic                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Grammar Check Request                                      │
│       │                                                     │
│       ▼                                                     │
│  Try LANGUAGETOOL_SERVER                                    │
│       │                                                     │
│       ├─ Success → Return results                           │
│       │                                                     │
│       └─ Failure AND LANGUAGETOOL_USE_PUBLIC_AS_FALLBACK   │
│             │                                              │
│             ▼                                              │
│       Try Public API                                       │
│             │                                              │
│             ├─ Success → Return results (with warning)     │
│             └─ Failure → Skip grammar check                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Performance Impact**:

- **Local server**: ~50-100ms per check, no rate limits
- **Public API**: ~200-500ms per check, 20 requests/day limit
- **Disabled**: Grammar check skipped (set `ENABLE_GRAMMAR_CHECK=false`)

**Production Recommendations**:
- Use local server for production deployments
- Set `LANGUAGETOOL_USE_PUBLIC_AS_FALLBACK=true` for resilience
- Monitor server health and restart if unresponsive
- Consider caching results for repeated text

**Interdependencies**:
- Requires `ENABLE_GRAMMAR_CHECK=true` to be active
- Adds ~2-3 seconds to total analysis time per resume
- Network connection required (unless using local server)

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

## Backend Email Notifications

### SMTP Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SMTP_HOST` | string | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | integer | `587` | SMTP server port |
| `SMTP_USER` | string | - | SMTP username |
| `SMTP_PASSWORD` | string | - | SMTP password or app-specific password |
| `SMTP_FROM` | string | `noreply@resume-analysis.com` | From email address |
| `SMTP_TLS` | boolean | `true` | Enable TLS encryption |

**Common SMTP Providers**:

| Provider | Host | Port | Notes |
|----------|------|------|-------|
| **Gmail** | `smtp.gmail.com` | `587` | Requires App Password |
| **Outlook** | `smtp.office365.com` | `587` | Standard credentials |
| **SendGrid** | `smtp.sendgrid.net` | `587` | API key as password |
| **AWS SES** | `email-smtp.us-east-1.amazonaws.com` | `587` | IAM credentials |
| **Mailgun** | `smtp.mailgun.org` | `587` | SMTP credentials |

**Gmail Setup (App Password)**:

```bash
# 1. Enable 2-Factor Authentication on your Google Account
# 2. Generate App Password: https://myaccount.google.com/apppasswords
# 3. Use App Password in configuration

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password (16 chars)
SMTP_FROM=noreply@yourdomain.com
SMTP_TLS=true
```

**SendGrid Setup**:

```bash
# 1. Create SendGrid account: https://sendgrid.com/
# 2. Generate API Key with "Mail Send" permissions
# 3. Use API Key as SMTP password

SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your_sendgrid_api_key_here
SMTP_FROM=noreply@yourdomain.com
SMTP_TLS=true
```

**AWS SES Setup**:

```bash
# 1. Verify domain in AWS SES Console
# 2. Create SMTP credentials (IAM user)
# 3. Use generated credentials

SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIAIOSFODNN7EXAMPLE
SMTP_PASSWORD=BLongPasswordWith+Characters/And/Numbers
SMTP_FROM=noreply@yourdomain.com
SMTP_TLS=true
```

**TLS Configuration**:

```
┌─────────────────────────────────────────────────────────────┐
│              SMTP Connection Security                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SMTP_TLS=true (Recommended)                                │
│       │                                                     │
│       ├─ STARTTLS command                                  │
│       ├─ Encrypted connection (TLS 1.2+)                   │
│       └─ Secure credential transmission                    │
│                                                             │
│  SMTP_TLS=false (Not Recommended)                          │
│       │                                                     │
│       ├─ Plaintext connection                              │
│       └─ Credentials sent unencrypted ⚠️                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Production Recommendations**:
- Always use `SMTP_TLS=true` in production
- Use app-specific passwords (not primary account passwords)
- Set up SPF, DKIM, and DMARC records for better deliverability
- Monitor email sending limits (quotas vary by provider)
- Use dedicated transactional email services (SendGrid, AWS SES) for production
- Test email delivery before production deployment
- Implement retry logic for failed emails
- Monitor bounce rates and blacklist status

**Security Best Practices**:
- Store `SMTP_PASSWORD` in secrets manager (never in code)
- Use minimal permissions for SMTP account
- Rotate SMTP credentials regularly (every 90 days)
- Monitor for unusual sending activity
- Implement rate limiting to prevent account suspension
- Use separate SMTP accounts for dev/staging/production

**Troubleshooting**:

```bash
# Test SMTP connection
openssl s_client -connect smtp.gmail.com:587 -starttls smtp

# Common errors:
# 535 5.7.8 Username and Password not accepted → Use App Password
# 550 5.7.1 Relaying denied → Check SMTP_USER and FROM address match
# Connection timeout → Check firewall allows port 587
```

---

## Backend Webhook Configuration

### Analysis Completion Webhooks

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WEBHOOK_URL` | string | - | Webhook endpoint URL for analysis completion |
| `WEBHOOK_SECRET` | string | - | Webhook signature secret for verification |

**Webhook Purpose**:
When configured, the backend sends HTTP POST requests to `WEBHOOK_URL` when:
- Resume analysis completes successfully
- Analysis fails or times out
- Batch analysis jobs complete
- Critical errors occur

**Webhook Payload Format**:

```json
{
  "event": "analysis.completed",
  "timestamp": "2026-02-01T12:34:56Z",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "data": {
    "resume_id": "123",
    "filename": "resume.pdf",
    "ats_score": 0.75,
    "keywords_matched": ["python", "django", "api"],
    "processing_time_seconds": 12.5
  },
  "signature": "sha256=..."
}
```

**Webhook Events**:

| Event | Trigger | Retry Policy |
|-------|---------|--------------|
| `analysis.completed` | Analysis finishes successfully | 3 retries with exponential backoff |
| `analysis.failed` | Analysis fails or times out | 3 retries with exponential backoff |
| `analysis.batch_completed` | Batch job completes | No retry (informational) |
| `system.error` | Critical system error | 5 retries with exponential backoff |

**Signature Verification**:

Webhooks include an HMAC signature in the `X-Webhook-Signature` header:

```python
# Backend generates signature
import hmac
import hashlib

signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    json.dumps(payload).encode(),
    hashlib.sha256
).hexdigest()
header = f"sha256={signature}"
```

Verify signatures in your webhook handler:

```python
# Your webhook server verifies signature
import hmac
import hashlib

def verify_webhook(payload, signature_header):
    signature = signature_header.split('=')[1]
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

**Configuration Examples**:

```bash
# Slack webhook
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_SECRET=$(openssl rand -hex 32)

# Discord webhook
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
WEBHOOK_SECRET=$(openssl rand -hex 32)

# Custom webhook server
WEBHOOK_URL=https://your-server.com/api/webhooks/resume-analysis
WEBHOOK_SECRET=$(openssl rand -hex 32)
```

**Webhook Server Implementation Example**:

```python
# Flask webhook server
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret-here"

@app.route('/webhooks/resume-analysis', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_data()

    if not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    # Process webhook
    data = request.get_json()
    if data['event'] == 'analysis.completed':
        # Send notification, update database, etc.
        print(f"Analysis {data['analysis_id']} completed with score {data['data']['ats_score']}")

    return jsonify({'status': 'received'}), 200

def verify_signature(payload, signature_header):
    signature = signature_header.split('=')[1]
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

if __name__ == '__main__':
    app.run(port=5000)
```

**Production Recommendations**:
- Always use HTTPS for `WEBHOOK_URL` (never HTTP)
- Generate strong random secret with `openssl rand -hex 32`
- Verify webhook signatures to prevent request forgery
- Implement idempotency (handle duplicate webhook deliveries)
- Return 200 status code quickly, process asynchronously
- Use exponential backoff for retries (1s, 2s, 4s, 8s, 16s)
- Monitor webhook delivery success rate
- Implement dead letter queue for failed webhooks
- Set reasonable timeout (5-10 seconds) for webhook requests

**Security Best Practices**:
- Treat `WEBHOOK_SECRET` like a password (store in secrets manager)
- Rotate `WEBHOOK_SECRET` regularly (every 90 days)
- Never log full webhook payload in production (PII risk)
- Validate webhook URL format and scheme
- Implement rate limiting on your webhook endpoint
- Use IP whitelisting if possible
- Monitor for suspicious webhook activity

**Troubleshooting**:

```bash
# Test webhook endpoint
curl -X POST WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=test" \
  -d '{"test": true}'

# Check backend logs for webhook delivery errors
grep "webhook" /var/log/backend.log

# Common errors:
# Connection timeout → Check firewall, webhook server availability
# 401 Unauthorized → Signature verification failed, check WEBHOOK_SECRET
# 404 Not Found → WEBHOOK_URL incorrect or webhook server down
# 500 Internal Server Error → Webhook server error, check webhook server logs
```

**Interdependencies**:
- Webhooks sent after analysis completes (depends on `ANALYSIS_TIMEOUT_SECONDS`)
- Requires internet connectivity for external webhook URLs
- Adds ~1-3 seconds to analysis completion if webhook is slow
- Retry attempts use Celery task queue (depends on `CELERY_BROKER_URL`)

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

### File Cleanup Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_FILE_CLEANUP` | boolean | `true` | Enable automatic file cleanup |
| `FILE_CLEANUP_INTERVAL_HOURS` | integer | `24` | Cleanup check interval (hours) |
| `FILE_RETENTION_HOURS` | integer | `48` | File retention period (hours) |

**Cleanup Process**:

```
┌─────────────────────────────────────────────────────────────┐
│              Automatic File Cleanup Process                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every FILE_CLEANUP_INTERVAL_HOURS (24 hours by default)    │
│       │                                                     │
│       ▼                                                     │
│  Scan UPLOAD_DIR for uploaded files                         │
│       │                                                     │
│       ├─ For each file:                                     │
│       │   │                                                 │
│       │   ├─ Check age (creation_time)                      │
│       │   │                                                 │
│       │   ├─ If age > FILE_RETENTION_HOURS:                 │
│       │   │   ├─ Delete file                               │
│       │   │   └─ Log deletion                              │
│       │   │                                                 │
│       │   └─ Else: Keep file                               │
│                                                             │
│  Summary logged: Files deleted, disk space reclaimed        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Configuration Examples**:

```bash
# Development - Frequent cleanup, short retention
ENABLE_FILE_CLEANUP=true
FILE_CLEANUP_INTERVAL_HOURS=6     # Check every 6 hours
FILE_RETENTION_HOURS=12            # Keep files for 12 hours

# Staging - Moderate cleanup
ENABLE_FILE_CLEANUP=true
FILE_CLEANUP_INTERVAL_HOURS=12
FILE_RETENTION_HOURS=24            # Keep files for 1 day

# Production - Standard cleanup
ENABLE_FILE_CLEANUP=true
FILE_CLEANUP_INTERVAL_HOURS=24     # Check once per day
FILE_RETENTION_HOURS=48            # Keep files for 2 days

# Audit/Legal - Long retention
ENABLE_FILE_CLEANUP=true
FILE_CLEANUP_INTERVAL_HOURS=24
FILE_RETENTION_HOURS=720           # Keep files for 30 days
```

**Cleanup Schedule Examples**:

| Retention | Interval | Files Kept | Disk Usage | Best For |
|-----------|----------|------------|------------|----------|
| 12 hours | 6 hours | 0.5 days | Low | Development, testing |
| 24 hours | 12 hours | 1-2 days | Medium | Staging environments |
| 48 hours | 24 hours | 2-3 days | Medium | Production (default) |
| 720 hours | 24 hours | 30 days | High | Audit requirements |

**Production Recommendations**:
- Set `FILE_RETENTION_HOURS` based on legal/audit requirements
- Adjust `FILE_CLEANUP_INTERVAL_HOURS` based on upload volume
- Monitor disk usage to ensure cleanup is working
- Consider disabling cleanup during debugging (`ENABLE_FILE_CLEANUP=false`)
- Ensure cleanup interval is shorter than retention period
- Account for backup schedules when setting retention

**Interdependencies**:
- Requires Celery beat for scheduled cleanup tasks
- Cleanup task logs to `LOG_FILE` if configured
- Disk space monitoring recommended for production
- Cleanup runs even if analysis tasks are running

**Monitoring**:

```bash
# Check for recent cleanup activity
grep "File cleanup" /var/log/backend.log | tail -20

# Monitor upload directory size
du -sh ./uploads

# Find old files (if cleanup not working)
find ./uploads -type f -mtime +2
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

### Backend Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_EXPERIMENTAL_FEATURES` | boolean | `false` | Enable experimental features |
| `ENABLE_BETA_FEATURES` | boolean | `false` | Enable beta features |

**Experimental Features**:
When `ENABLE_EXPERIMENTAL_FEATURES=true`, the following experimental features are enabled:
- Advanced ML models (may be slower or resource-intensive)
- New analysis algorithms (under testing)
- Experimental UI components (if using corresponding frontend flag)
- Debug endpoints and additional logging

⚠️ **Warning**: Experimental features may be:
- Unstable or buggy
- Slow or resource-intensive
- Changed or removed in future versions
- Not suitable for production use

**Beta Features**:
When `ENABLE_BETA_FEATURES=true`, the following beta features are enabled:
- Newly released features (mostly stable but may have edge cases)
- Advanced configurations and tuning options
- Pre-release optimizations

ℹ️ **Note**: Beta features are more stable than experimental features but may still have issues. Good for staging environments.

**Recommended Usage**:

| Environment | Experimental | Beta | Notes |
|-------------|---------------|------|-------|
| Development | `true` | `true` | Test all features |
| Staging | `false` | `true` | Test production-ready features |
| Production | `false` | `false` | Stable features only |

**Feature Feedback**:
If you enable experimental or beta features, please:
- Report issues on GitHub with detailed descriptions
- Monitor system performance and resource usage
- Provide feedback on feature quality and usefulness
- Check release notes for changes to experimental features

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

---

## Production Security & Deployment Checklist

### 1. Secrets Management

#### ✅ Pre-Deployment Secrets Setup

```bash
# Generate all required secrets
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)

# Store in secure secret manager (AWS example)
aws secretsmanager create-secret \
  --name agenthr/production \
  --secret-string '{
    "SECRET_KEY":"'$SECRET_KEY'",
    "POSTGRES_PASSWORD":"'$POSTGRES_PASSWORD'",
    "REDIS_PASSWORD":"'$REDIS_PASSWORD'",
    "GRAFANA_ADMIN_PASSWORD":"'$GRAFANA_ADMIN_PASSWORD'"
  }'
```

#### ✅ Recommended Secret Managers

| Provider | Service | Integration | Cost |
|----------|---------|-------------|------|
| AWS | Secrets Manager | AWS SDK/Boto3 | $0.40/secret/month |
| AWS | Parameter Store | AWS SDK/Boto3 | Free tier available |
| HashiCorp | Vault | API/Consul | Open Source |
| Azure | Key Vault | Azure SDK | Pay-per-operation |
| Google Cloud | Secret Manager | GCP SDK | $0.03/secret/month |

#### ✅ Docker Secret Integration

```yaml
# docker-compose.prod.yml
version: '3.8'
secrets:
  db_password:
    external: true
  jwt_secret:
    external: true

services:
  backend:
    secrets:
      - db_password
      - jwt_secret
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      SECRET_KEY_FILE: /run/secrets/jwt_secret
```

#### ✅ Environment Variable Injection

```bash
# Load secrets from AWS Secrets Manager at runtime
export SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id agenthr/production \
  --query SecretString --output text | jq -r '.SECRET_KEY')

export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id agenthr/production \
  --query SecretString --output text | jq -r '.POSTGRES_PASSWORD')

# Verify secrets are loaded
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."  # Show only first 10 chars
echo "POSTGRES_PASSWORD length: ${#POSTGRES_PASSWORD}"
```

#### ❌ Common Secrets Mistakes

| Mistake | Risk | Solution |
|---------|-------|----------|
| Committing `.env` files | Public exposure | Add `.env` to `.gitignore` |
| Using same secrets across environments | Cross-contamination | Unique secrets per env |
| Hardcoding secrets in code | Exposure in version control | Use environment variables |
| Sharing secrets via chat/email | Interception | Use secure sharing links |
| Never rotating secrets | Extended breach window | Rotate every 90 days |

---

### 2. SSL/TLS Configuration

#### ✅ SSL/TLS Certificate Setup

```bash
# Option 1: Let's Encrypt (recommended for production)
sudo apt-get install certbot
sudo certbot certonly --standalone -d api.example.com -d app.example.com

# Copy certificates to project
mkdir -p certs/
sudo cp /etc/letsencrypt/live/api.example.com/fullchain.pem certs/backend.crt
sudo cp /etc/letsencrypt/live/api.example.com/privkey.pem certs/backend.key
sudo chmod 644 certs/backend.crt
sudo chmod 600 certs/backend.key
```

#### ✅ Docker Compose SSL Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - SSL_ENABLED=true
      - SSL_CERTFILE=/app/certs/backend.crt
      - SSL_KEYFILE=/app/certs/backend.key
    volumes:
      - ./certs:/app/certs:ro
    ports:
      - "8443:8443"  # HTTPS port

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
```

#### ✅ Nginx Reverse Proxy SSL Config

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name api.example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name api.example.com;

        ssl_certificate /etc/nginx/certs/backend.crt;
        ssl_certificate_key /etc/nginx/certs/backend.key;

        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### ✅ Database SSL Configuration

```bash
# Force SSL connections to PostgreSQL
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"

# Or with certificate verification (most secure)
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=verify-full&sslrootcert=/app/certs/ca.crt"
```

| SSL Mode | Description | Security | Use Case |
|----------|-------------|----------|----------|
| `disable` | No SSL | ❌ None | Local development only |
| `allow` | Try SSL, fallback to no SSL | ⚠️ Low | Legacy systems |
| `prefer` | Try SSL, allow no SSL | ⚠️ Low | Testing |
| `require` | Require SSL, no verification | ✅ Medium | **Production minimum** |
| `verify-ca` | Verify CA certificate | ✅ High | Recommended |
| `verify-full` | Verify CA + hostname | ✅✅ Highest | **Best practice** |

#### ✅ SSL Certificate Renewal

```bash
# Test renewal (dry-run)
sudo certbot renew --dry-run

# Setup auto-renewal cron job
sudo crontab -e

# Add line:
0 0 * * * certbot renew --quiet --post-hook "docker-compose restart nginx"
```

---

### 3. Firewall & Network Security

#### ✅ UFW Firewall Setup (Ubuntu)

```bash
# Enable UFW
sudo ufw enable

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow backend API port (if exposed directly)
sudo ufw allow 8443/tcp comment 'Backend API HTTPS'

# Allow monitoring ports (internal network only)
sudo ufw allow from 10.0.0.0/8 to any port 9090 comment 'Prometheus internal'
sudo ufw allow from 10.0.0.0/8 to any port 3001 comment 'Grafana internal'

# Check status
sudo ufw status numbered
```

#### ✅ Docker Network Isolation

```yaml
# docker-compose.prod.yml
version: '3.8'

# Create isolated networks
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No internet access
  monitoring:
    driver: bridge

services:
  # Frontend can access backend
  frontend:
    networks:
      - frontend
      - backend
    ports:
      - "443:443"

  # Backend isolated to internal networks
  backend:
    networks:
      - backend
    environment:
      - REDIS_URL=redis://redis:6379/0

  # Redis completely isolated
  redis:
    networks:
      - backend
    # No exposed ports!

  # Monitoring on separate network
  grafana:
    networks:
      - monitoring
    ports:
      - "3001:3000"
```

#### ✅ Security Groups (AWS)

```bash
# Security group for Backend
aws ec2 create-security-group \
  --group-name agenthr-backend-prod \
  --description "AgentHR Backend Production"

# Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH from specific IP only
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR.OFFICE.IP/32

# Allow internal traffic (VPC only)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 10.0.0.0/16
```

#### ✅ Network Security Checklist

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Firewall enabled | `sudo ufw status` | `Status: active` |
| Open ports | `sudo ss -tulpn` | Only required ports open |
| Docker networks | `docker network ls` | Isolated networks configured |
| SSL enforced | `curl -I https://api.example.com` | HTTP/2 200 |
| Database SSL | `psql "postgresql://...?sslmode=require"` | Connection succeeds |
| No plaintext auth | `tcpdump -A -i eth0` | No passwords in packets |

---

### 4. Backup & Restore Procedures

#### ✅ Automated Backup Setup

```bash
# 1. Enable automated backups in backend/.env
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_RETENTION_COUNT=10

# 2. Configure S3 backup
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=agenthr-production-backups
BACKUP_S3_REGION=us-east-1
BACKUP_S3_PREFIX=database/
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com

# 3. AWS credentials with backup permissions
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### ✅ S3 Bucket Setup with Lifecycle

```bash
# Create S3 bucket with versioning
aws s3api create-bucket \
  --bucket agenthr-production-backups \
  --region us-east-1 \
  --create-bucket-configuration LocationConstraint=us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket agenthr-production-backups \
  --versioning-configuration Status=Enabled

# Set up lifecycle policy (move to Glacier after 30 days, delete after 90 days)
cat > backup-lifecycle.json <<EOF
{
  "Rules": [
    {
      "Id": "BackupLifecycle",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 90
      },
      "Filter": {
        "Prefix": "database/"
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket agenthr-production-backups \
  --lifecycle-configuration file://backup-lifecycle.json
```

#### ✅ Manual Backup Procedure

```bash
#!/bin/bash
# scripts/backup_production.sh

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/backups"
BACKUP_FILE="${BACKUP_DIR}/agenthr_backup_${BACKUP_DATE}.sql"

echo "Starting backup at ${BACKUP_DATE}"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# 1. Database backup
echo "Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump \
  -U postgres \
  -d resume_analysis \
  --clean \
  --if-exists \
  > ${BACKUP_FILE}

# 2. Compress backup
echo "Compressing backup..."
gzip ${BACKUP_FILE}
BACKUP_FILE="${BACKUP_FILE}.gz"

# 3. Upload to S3
echo "Uploading to S3..."
aws s3 cp ${BACKUP_FILE} \
  s3://agenthr-production-backups/database/backup_${BACKUP_DATE}.sql.gz \
  --storage-class STANDARD_IA

# 4. Verify upload
echo "Verifying backup..."
aws s3 ls s3://agenthr-production-backups/database/backup_${BACKUP_DATE}.sql.gz

# 5. Clean up local file
rm ${BACKUP_FILE}

echo "Backup completed successfully: backup_${BACKUP_DATE}.sql.gz"
```

#### ✅ Restore Procedure

```bash
#!/bin/bash
# scripts/restore_production.sh

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  exit 1
fi

BACKUP_FILE=$1
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

echo "⚠️  WARNING: This will REPLACE the current database!"
echo "Backup file: ${BACKUP_FILE}"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Restore cancelled"
  exit 0
fi

# 1. Download backup from S3 (if needed)
if [[ $BACKUP_FILE == s3://* ]]; then
  echo "Downloading from S3..."
  aws s3 cp ${BACKUP_FILE} /tmp/restore.sql.gz
  BACKUP_FILE=/tmp/restore.sql.gz
fi

# 2. Create pre-restore backup
echo "Creating pre-restore backup..."
./scripts/backup_production.sh

# 3. Stop application services
echo "Stopping services..."
docker-compose stop backend celery_worker celery_beat

# 4. Restore database
echo "Restoring database..."
gunzip -c ${BACKUP_FILE} | docker-compose exec -T postgres psql \
  -U postgres \
  -d resume_analysis

# 5. Restart services
echo "Restarting services..."
docker-compose start backend celery_worker celery_beat

# 6. Verify restore
echo "Verifying restore..."
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@postgres:5432/resume_analysis')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM users')
print(f'Users in database: {cur.fetchone()[0]}')
conn.close()
"

echo "Restore completed successfully!"
```

#### ✅ Backup Testing & Verification

```bash
# Schedule monthly restore test (0 3 1 * * - first day of month at 3 AM)
crontab -e

# Add:
0 3 1 * * /path/to/scripts/test_restore.sh

# test_restore.sh
#!/bin/bash
TEST_DATE=$(date +%Y%m%d)
LATEST_BACKUP=$(aws s3 ls s3://agenthr-production-backups/database/ | sort | tail -n 1 | awk '{print $4}')

echo "Testing restore with: ${LATEST_BACKUP}"

# Create test database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS resume_analysis_test;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE resume_analysis_test;"

# Restore to test database
aws s3 cp s3://agenthr-production-backups/database/${LATEST_BACKUP} - \
  | gunzip \
  | docker-compose exec -T postgres psql -U postgres -d resume_analysis_test

# Verify data
docker-compose exec postgres psql -U postgres -d resume_analysis_test -c "SELECT COUNT(*) FROM resumes;"

# Clean up
docker-compose exec postgres psql -U postgres -c "DROP DATABASE resume_analysis_test;"

echo "Restore test completed successfully!"
```

#### ✅ Backup Monitoring

```yaml
# Add to Prometheus alerts (alerting.yml)
groups:
  - name: backup_rules
    rules:
      - alert: BackupNotCompleted
        expr: time() - backup_last_success_timestamp_seconds > 86400
        for: 2h
        labels:
          severity: critical
        annotations:
          summary: "Backup not completed in 24 hours"
          description: "Last successful backup was {{ $value | humanizeDuration }} ago"

      - alert: BackupSizeTooSmall
        expr: backup_size_bytes < 1000000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Backup size suspiciously small"
          description: "Backup size is only {{ $value }} bytes"
```

---

### 5. Security Hardening Checklist

#### ✅ Pre-Deployment Security Checklist

```bash
# Run this checklist before every production deployment

# 1. Verify all secrets are from secure source
echo "✓ Checking secrets source..."
test -f /run/secrets/SECRET_KEY || test -n "$SECRET_KEY" || { echo "❌ SECRET_KEY missing"; exit 1; }

# 2. Verify no default passwords
echo "✓ Checking for default passwords..."
grep -q "POSTGRES_PASSWORD=postgres" .env && { echo "❌ Default POSTGRES_PASSWORD detected"; exit 1; }
grep -q "SECRET_KEY=changeme" .env && { echo "❌ Default SECRET_KEY detected"; exit 1; }

# 3. Verify SSL/TLS is configured
echo "✓ Checking SSL configuration..."
grep -q "SSL_ENABLED=true" .env || { echo "❌ SSL not enabled"; exit 1; }
test -f certs/backend.crt || { echo "❌ SSL certificate missing"; exit 1; }

# 4. Verify HTTPS URLs
echo "✓ Checking URL schemes..."
grep -q "^FRONTEND_URL=http://" .env && { echo "❌ HTTP URL detected (use HTTPS)"; exit 1; }
grep -q "https://" .env || { echo "❌ No HTTPS URLs found"; exit 1; }

# 5. Verify CORS origins are specific
echo "✓ Checking CORS configuration..."
grep -q "CORS_ORIGINS=\*" .env && { echo "❌ Wildcard CORS detected"; exit 1; }

# 6. Verify rate limiting enabled
echo "✓ Checking rate limiting..."
grep -q "RATE_LIMIT_PER_MINUTE=" .env || { echo "❌ Rate limiting not configured"; exit 1; }

# 7. Verify DEBUG is off
echo "✓ Checking DEBUG mode..."
grep -q "DEBUG=true" .env && { echo "❌ DEBUG enabled in production"; exit 1; }

# 8. Verify logging level is INFO or WARNING
echo "✓ Checking log level..."
grep -q "LOG_LEVEL=DEBUG" .env && { echo "⚠️  DEBUG log level (should be INFO)"; }

# 9. Verify backups enabled
echo "✓ Checking backup configuration..."
grep -q "BACKUP_ENABLED=true" .env || { echo "❌ Backups not enabled"; exit 1; }

# 10. Verify monitoring enabled
echo "✓ Checking monitoring..."
grep -q "ENABLE_PROMETHEUS_METRICS=true" .env || { echo "⚠️  Monitoring not enabled"; }

echo "✅ All security checks passed!"
```

#### ✅ Post-Deployment Verification

```bash
# Run these checks immediately after deployment

# 1. Check all services are healthy
echo "✓ Checking service health..."
docker-compose ps | grep -q "Up" || { echo "❌ Services not running"; exit 1; }

# 2. Verify SSL certificate
echo "✓ Verifying SSL certificate..."
curl -I https://api.example.com 2>&1 | grep -q "HTTP/2 200" || { echo "❌ SSL not working"; exit 1; }

# 3. Test API health endpoint
echo "✓ Testing API health..."
curl -f https://api.example.com/health || { echo "❌ Health check failed"; exit 1; }

# 4. Verify database connection
echo "✓ Testing database..."
docker-compose exec -T postgres pg_isready -U postgres || { echo "❌ Database not ready"; exit 1; }

# 5. Verify Redis connection
echo "✓ Testing Redis..."
docker-compose exec -T redis redis-cli ping || { echo "❌ Redis not responding"; exit 1; }

# 6. Check no exposed ports except 80/443
echo "✓ Checking exposed ports..."
sudo ss -tulpn | grep -v ":80\|:443\|:22" && { echo "⚠️  Additional ports exposed"; }

# 7. Verify firewall is active
echo "✓ Checking firewall..."
sudo ufw status | grep -q "Status: active" || { echo "❌ Firewall not active"; exit 1; }

# 8. Check recent application logs for errors
echo "✓ Checking application logs..."
docker-compose logs --tail=50 backend | grep -i error && { echo "⚠️  Errors in logs"; }

echo "✅ Post-deployment verification passed!"
```

#### ✅ Ongoing Security Monitoring

```bash
# Add to monitoring dashboard

# 1. Track failed authentication attempts
# Query: rate(authentication_failed_total[5m]) > threshold

# 2. Monitor unusual API traffic patterns
# Query: rate(api_requests_total[1h]) > 2 * avg_over_time(rate(api_requests_total[1h])[7d:])

# 3. Alert on backup failures
# Query: backup_last_success_timestamp_seconds < time() - 86400

# 4. Monitor SSL certificate expiration
# Query: ssl_certificate_expiry_seconds < time() + 2592000 (30 days)

# 5. Track database connection pool saturation
# Query: db_pool_active_connections / db_pool_size > 0.8
```

---

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

## Quick Reference Tables

Quick reference for the most commonly used environment variables across different deployment environments.

### Core Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `DEBUG` | `true` | `false` | `false` | Never enable in production |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` | Use DEBUG for local troubleshooting |
| `LOG_FORMAT` | `text` | `json` | `json` | JSON for log aggregation in production |
| `RELOAD` | `true` | `false` | `false` | Auto-reload on code changes (dev only) |
| `TESTING` | `false` | `false` | `false` | Set to `true` only when running tests |

---

### Database Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/resume_analysis_dev` | `postgresql://staging_user:<pass>@staging-db:5432/resume_analysis_staging` | `postgresql://prod_user:<pass>@prod-db:5432/resume_analysis` | Use strong passwords in non-dev |
| `DB_POOL_SIZE` | `5` | `15` | `30-50` | Scale based on worker count |
| `DB_MAX_OVERFLOW` | `5` | `10` | `15-25` | ~50% of pool size |
| `DB_POOL_RECYCLE` | `3600` | `3600` | `3600` | Recycle connections every hour |
| `DB_POOL_TIMEOUT` | `30` | `30` | `30` | Seconds to wait for connection |

**Pool Size Formula**: `DB_POOL_SIZE >= CELERY_WORKER_CONCURRENCY * 2`

---

### Redis Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://staging-redis:6379/0` | `redis://prod-redis:6379/0` | Use Redis Sentinel for HA in prod |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | `redis://staging-redis:6379/0` | `redis://prod-redis:6379/0` | Same as REDIS_URL typically |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | `redis://staging-redis:6379/0` | `redis://prod-redis:6379/0` | Where task results stored |

---

### Backend API Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `BACKEND_HOST` | `0.0.0.0` | `0.0.0.0` | `0.0.0.0` | Bind to all interfaces |
| `BACKEND_PORT` | `8000` | `8000` | `8080` | Use 8080 in production (behind reverse proxy) |
| `FRONTEND_URL` | `http://localhost:5173` | `https://staging.example.com` | `https://app.example.com` | Must match frontend URL |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | `https://staging.example.com` | `https://app.example.com,https://www.example.com` | Comma-separated, exact match required |

---

### Frontend Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `VITE_API_URL` | `http://localhost:8000` | `https://staging-api.example.com` | `https://api.example.com` | Backend API URL |
| `VITE_ENABLE_REACT_DEVTOOLS` | `true` | `false` | `false` | Enable React DevTools plugin |
| `VITE_DEBUG` | `true` | `false` | `false` | Additional frontend debug logging |
| `VITE_ENABLE_ANALYTICS` | `false` | `false` | `true` | Google Analytics tracking |
| `VITE_ENABLE_ERROR_TRACKING` | `false` | `true` | `true` | Sentry error tracking |
| `VITE_SENTRY_ENVIRONMENT` | `development` | `staging` | `production` | Sentry environment name |

---

### Security Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `SECRET_KEY` | `dev-secret-key` | `<staging-secret>` | `<strong-secret>` | Generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | `HS256` | `RS256` | Use RS256 in production (asymmetric keys) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | `30` | `30` | Shorter is more secure |
| `RATE_LIMIT_PER_MINUTE` | `100` | `60` | `60` | Adjust based on traffic patterns |

⚠️ **CRITICAL**: Use different `SECRET_KEY` values for each environment. Never commit secrets to version control.

---

### File Upload Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `MAX_UPLOAD_SIZE_MB` | `10` | `10` | `10` | Maximum file size in MB |
| `ALLOWED_FILE_TYPES` | `.pdf,.docx` | `.pdf,.docx` | `.pdf,.docx` | Comma-separated extensions |
| `UPLOAD_DIR` | `./uploads` | `/var/uploads` | `/var/uploads` | Use absolute path in production |
| `ENABLE_FILE_CLEANUP` | `true` | `true` | `true` | Auto-delete old files |
| `FILE_RETENTION_HOURS` | `24` | `48` | `48` | How long to keep uploaded files |

---

### Celery Worker Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `CELERY_WORKER_CONCURRENCY` | `2` | `4` | `8-16` | Parallel tasks per worker |
| `CELERY_LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` | Worker log level |
| `CELERY_TASK_TIME_LIMIT` | `300` | `300` | `300` | Max seconds per task (hard limit) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `280` | `280` | `280` | Graceful shutdown time (soft limit) |
| `CELERY_TASK_MAX_RETRIES` | `3` | `3` | `3` | Retry failed tasks |
| `CELERY_RESULT_EXPIRES` | `86400` | `86400` | `86400` | Result cache duration (seconds, 1 day) |

**Worker Pool Sizing**: `DB_POOL_SIZE = CELERY_WORKER_CONCURRENCY * 10` (recommended)

---

### ML Models Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `KEYBERT_MODEL` | `distilbert-base-nli-mean-tokens` | `distilbert-base-nli-mean-tokens` | `sentence-transformers/all-MiniLM-L6-v2` | MiniLM is faster for production |
| `SPACY_MODEL_EN` | `en_core_web_sm` | `en_core_web_sm` | `en_core_web_sm` | Use `_sm` for production |
| `SPACY_MODEL_RU` | `ru_core_news_sm` | `ru_core_news_sm` | `ru_core_news_sm` | Small model for Russian |
| `SENTENCE_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | `all-MiniLM-L6-v2` | `all-MiniLM-L6-v2` | Balance speed and accuracy |
| `MODELS_CACHE_PATH` | `./models_cache` | `/app/models_cache` | `/app/models_cache` | Use persistent volume in production |

**Model Performance Trade-offs**:
- `distilbert-base`: ~250MB, moderate CPU, good accuracy
- `all-MiniLM-L6-v2`: ~80MB, low CPU, fast inference
- `en_core_web_sm`: ~12MB, optimized for production
- `en_core_web_md`: ~40MB, better accuracy, moderate resources

---

### Analysis Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `ANALYSIS_TIMEOUT_SECONDS` | `300` | `300` | `300` | Max analysis time (5 minutes) |
| `ENABLE_KEYWORD_EXTRACTION` | `true` | `true` | `true` | Extract keywords from resumes |
| `ENABLE_NER_EXTRACTION` | `true` | `true` | `true` | Named Entity Recognition |
| `ENABLE_GRAMMAR_CHECK` | `true` | `true` | `true` | Spelling/grammar checking |
| `ENABLE_EXPERIENCE_CALCULATION` | `true` | `true` | `true` | Calculate work experience |
| `ENABLE_ERROR_DETECTION` | `true` | `true` | `true` | Detect resume errors |
| `KEYWORD_EXTRACTION_TOP_N` | `20` | `20` | `20` | Number of keywords to extract |
| `ATS_THRESHOLD` | `0.6` | `0.6` | `0.6` | Minimum ATS score to pass (0.0-1.0) |

---

### LLM API Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `LLM_PROVIDER` | `zai` | `zai` | `anthropic` or `openai` | Choose provider for ATS simulation |
| `LLM_MODEL` | `claude-3-5-sonnet-20241022` | `claude-3-5-sonnet-20241022` | `claude-3-5-sonnet-20241022` | Model to use |
| `LLM_TEMPERATURE` | `0.1` | `0.1` | `0.1` | Lower = more deterministic |
| `LLM_MAX_TOKENS` | `4096` | `4096` | `4096` | Max response tokens |
| `ZAI_API_KEY` | `<dev-key>` | `<staging-key>` | `<prod-key>` | Z.ai API key |
| `OPENAI_API_KEY` | `<dev-key>` | `<staging-key>` | `<prod-key>` | OpenAI API key |
| `ANTHROPIC_API_KEY` | `<dev-key>` | `<staging-key>` | `<prod-key>` | Anthropic API key |

⚠️ **COST MANAGEMENT**: Set up spending limits on all LLM provider accounts to prevent unexpected charges.

---

### Backup Configuration

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `ENABLE_AUTO_BACKUP` | `false` | `true` | `true` | Enable automatic backups |
| `BACKUP_INTERVAL_HOURS` | `24` | `24` | `24` | Backup frequency |
| `BACKUP_RETENTION_DAYS` | `7` | `7` | `30` | Days to keep backups |
| `BACKUP_S3_ENABLED` | `false` | `true` | `true` | Store backups in S3 |
| `BACKUP_S3_BUCKET` | N/A | `staging-backups` | `production-backups` | S3 bucket name |
| `BACKUP_S3_REGION` | N/A | `us-east-1` | `us-east-1` | AWS region |

---

### Monitoring & Alerting

| Variable | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| `ENABLE_PROMETHEUS_METRICS` | `false` | `true` | `true` | Prometheus metrics endpoint |
| `PROMETHEUS_PORT` | `9090` | `9090` | `9090` | Metrics port |
| `ALERT_EMAIL_ADDRESS` | N/A | `staging@example.com` | `ops@example.com` | Alert notifications |
| `VITE_GA_TRACKING_ID` | N/A | N/A | `UA-XXXXXXXXX-X` | Google Analytics (optional) |
| `SENTRY_DSN` | N/A | `<staging-dsn>` | `<production-dsn>` | Error tracking DSN |

---

### Resource Limits (Docker)

| Resource | Development | Staging | Production | Notes |
|----------|------------|---------|------------|-------|
| **Backend CPU** | `1.0` | `2.0` | `4.0` | CPU cores |
| **Backend Memory** | `1G` | `4G` | `8G` | RAM |
| **Worker CPU** | `1.0` | `2.0` | `4.0` | CPU cores |
| **Worker Memory** | `1G` | `4G` | `8G` | RAM |
| **PostgreSQL CPU** | `0.5` | `1.0` | `2.0` | CPU cores |
| **PostgreSQL Memory** | `512M` | `2G` | `4G` | RAM |

**Scaling Guide**:
- **Small team** (< 50 users): Use development/staging values
- **Medium team** (50-200 users): Use staging values
- **Large team** (200+ users): Use production values and scale horizontally

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
