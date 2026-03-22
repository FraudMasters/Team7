# AgentHR - AI-Powered Resume Analysis & Candidate Ranking

AI-powered resume analysis system with intelligent job matching, ML-based candidate ranking, and comprehensive monitoring.

![Coverage](.badges/coverage.svg)
![Frontend Coverage](.badges/frontend-coverage.svg)
![Backend Coverage](.badges/backend-coverage.svg)

## Features

- **Resume Upload & Analysis**: Support for PDF and DOCX formats
- **Unified Matching System**: Three-method matching (Keyword, TF-IDF, Vector similarity)
- **AI Candidate Ranking**: ML-based ranking with 13 features and A/B testing support
- **Recruiter Feedback**: Feedback loop for continuous model improvement
- **Explainable AI**: Feature importance and ranking factors breakdown
- **Multi-language**: English and Russian support
- **Modern Monitoring**: Grafana + Loki + Promtail + Prometheus stack
- **Async Processing**: Celery + Redis for background tasks
- **Modern UI**: React 18 + Material-UI with responsive design

## Quick Start

### Prerequisites

- **Docker Desktop** (Mac/Windows) or Docker + Docker Compose (Linux)
- **8GB RAM** minimum (16GB recommended)
- **5GB disk space**

### Start Services

```bash
git clone https://github.com/Soinex-Inc/agenthr.git
cd agenthr

# Start core services (recommended for development)
docker-compose --profile core up -d

# Or start minimal services (fastest startup)
docker-compose --profile minimal up -d

# Or start with full monitoring stack (production-like)
docker-compose --profile full up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

**Docker Profiles Available:**

| Profile | Services | RAM Required | Use Case |
|---------|----------|--------------|----------|
| `minimal` | DB, Redis, API, UI | ~4GB | Quick testing, CI/CD |
| `core` | + Celery workers | ~8GB | Development, async processing |
| `full` | + Monitoring stack | ~16GB | Production, full observability |

> 📖 **See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment options including Kubernetes/Helm**

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Loki | http://localhost:3100 | - |

### Load Test Data

```bash
# Load 65 resumes and 5 vacancies
docker-compose exec backend python scripts/reset_and_reload.py
```

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │─────▶│   Backend    │─────▶│   Database  │
│ (React+MUI) │      │   (FastAPI)  │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                    ┌───────┴────────────────────────┐
                    ▼                ▼               ▼
              ┌─────────┐      ┌──────────┐   ┌──────────┐
              │ Celery  │      │  Redis   │   │  Ranking │
              │ Worker  │      │  Broker  │   │  Service │
              └─────────┘      └──────────┘   └──────────┘
                                                       │
                                          ┌────────────┴─────────┐
                                          ▼          ▼           ▼
                                    ┌────────┐  ┌──────┐  ┌─────────┐
                                    │Grafana │  │ Loki │  │Prometheus│
                                    └────────┘  └──────┘  └─────────┘
```

## API Endpoints

### Resume Analysis

```bash
# Upload resume
curl -X POST http://localhost:8000/api/resumes/upload \
  -F "file=@resume.pdf"

# Analyze resume
curl -X POST http://localhost:8000/api/resumes/analyze \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid"}'
```

### Job Matching

```bash
# Unified matching (AI-powered)
curl -X POST http://localhost:8000/api/matching/compare-unified \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "uuid",
    "vacancy_data": {
      "id": "vacancy_uuid",
      "title": "Python Developer",
      "description": "We are looking for...",
      "required_skills": ["python", "django", "postgresql"]
    }
  }'
```

### AI Candidate Ranking

```bash
# Rank single candidate for vacancy
curl -X POST http://localhost:8000/api/ranking/rank \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "resume_uuid",
    "vacancy_id": "vacancy_uuid",
    "use_experiment": true
  }'

# Get ranked candidates for vacancy
curl -X GET "http://localhost:8000/api/ranking/vacancy/{vacancy_id}/ranked?limit=10"

# Submit feedback on ranking
curl -X POST http://localhost:8000/api/ranking/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rank_id": "rank_uuid",
    "was_helpful": true,
    "actual_outcome": "hired"
  }'

# Get feature importance
curl -X GET http://localhost:8000/api/ranking/models/importance
```

### Vacancies

```bash
# Get all vacancies
curl -X GET http://localhost:8000/api/vacancies/

# Create vacancy
curl -X POST http://localhost:8000/api/vacancies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Developer",
    "description": "We are looking for...",
    "required_skills": ["python", "fastapi"],
    "location": "Remote",
    "min_experience_months": 36
  }'
```

## Ranking System Details

### Features Used (13 total)

| Feature | Description |
|---------|-------------|
| `overall_match_score` | Combined score from unified matching |
| `keyword_score` | Keyword-based skill matching |
| `tfidf_score` | TF-IDF weighted matching |
| `vector_score` | Semantic similarity (sentence-transformers) |
| `skills_match_ratio` | Ratio of required skills found |
| `experience_months` | Total months of work experience |
| `experience_relevance` | Experience relevance to job requirements |
| `education_level` | Highest education level |
| `recent_experience` | Relevant experience in recent years |
| `skill_rarity_score` | Rarity of matched skills |
| `title_similarity` | Similarity between resume and job titles |
| `freshness_score` | How recent the resume is |
| `completeness_score` | Resume completeness |

### Recommendation Levels

- **excellent** (≥0.8) - Top candidate, highly recommended
- **good** (≥0.6) - Strong match, recommend interview
- **maybe** (≥0.4) - Potential match, review needed
- **poor** (<0.4) - Not a match

### A/B Testing

Candidates can be assigned to experiment groups for model comparison:
- `control` - Current production model
- `treatment` - New experimental model

## Project Structure

```
├── backend/                    # FastAPI backend
│   ├── analyzers/              # ML/NLP analyzers
│   │   ├── unified_matcher.py   # Combined 3-method matcher
│   │   ├── ranking_service.py   # ML-based candidate ranking
│   │   └── hf_skill_extractor.py
│   ├── api/                    # API endpoints
│   │   ├── ranking.py           # Ranking API
│   │   ├── matching.py          # Matching API
│   │   └── vacancies.py         # Vacancies API
│   ├── models/                 # SQLAlchemy models
│   │   ├── candidate_rank.py    # Ranking models
│   │   ├── resume.py
│   │   └── job_vacancy.py
│   ├── scripts/                # Utility scripts
│   │   └── reset_and_reload.py # Test data loader
│   └── alembic/                # Database migrations
├── frontend/                   # React + Vite frontend
│   └── src/
│       ├── components/
│       │   ├── RankingFeedback.tsx
│       │   └── RankingExplanation.tsx
│       └── pages/
├── monitoring/                 # Monitoring configs
│   ├── grafana/
│   ├── loki/
│   ├── prometheus/
│   └── promtail/
├── services/                   # Shared services
│   └── data_extractor/         # PDF/DOCX extraction
├── testdata/                   # Test data
│   └── vacancy-resume-matching-dataset-main/
│       ├── CV/                 # 65 resume files
│       └── 5_vacancies.csv     # 5 job vacancies
└── docker-compose.yml          # Docker services
```

## Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.11
- **Database**: PostgreSQL 14 with SQLAlchemy 2.0
- **ML**: scikit-learn (ranking), sentence-transformers (vectors)
- **Async**: Celery + Redis

### Frontend
- **Framework**: React 18 with TypeScript
- **Build**: Vite 5.4
- **UI**: Material-UI (MUI) v6

### Monitoring
- **Grafana** - Visualization dashboards
- **Loki** - Log aggregation
- **Promtail** - Log collector
- **Prometheus** - Metrics collection

## Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f grafana

# Restart services
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v

# Run database migration
docker-compose exec backend alembic upgrade head

# Load test data
docker-compose exec backend python scripts/reset_and_reload.py
```

## Configuration

AgentHR uses a centralized configuration management system with:

- **Environment-specific profiles** - Separate configurations for dev, staging, and production
- **YAML config files** - Store settings in version control
- **Environment variable overrides** - Override any setting via environment variables
- **Hot reload support** - Update non-critical settings without restarting
- **Configuration validation** - Startup validation prevents invalid configurations
- **Audit logging** - Track all configuration changes

### Quick Configuration

```bash
# 1. Set environment
export ENVIRONMENT=dev  # or 'staging' or 'production'

# 2. Copy environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Update with your values
# Edit .env files with your database URLs, API keys, etc.

# 4. Start services
docker-compose up -d
```

### Configuration Files

| File | Purpose |
|------|---------|
| `backend/config/config.dev.yml` | Development environment settings |
| `backend/config/config.staging.yml` | Staging environment settings |
| `backend/config/config.production.yml` | Production environment settings |
| `.env` | Root environment variables (overrides) |
| `backend/.env` | Backend-specific variables |
| `frontend/.env` | Frontend-specific variables |

For complete configuration documentation, see:
- **[Configuration Management](docs/configuration.md)** - Complete configuration guide
- **[Configuration Reference](docs/configuration/reference.md)** - All configuration options
- **[Backend Config README](backend/config/README.md)** - Backend config module documentation

## Deployment & Operations

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide (Docker, Kubernetes, Helm)
- **[UPGRADE.md](./UPGRADE.md)** - Version upgrades, migrations, and rollback procedures

## Documentation

- **[Configuration Management](docs/configuration.md)** - Complete configuration guide with examples
- **[Configuration Reference](docs/configuration/reference.md)** - All configuration options reference
- **[API Usage Guide](docs/API_USAGE_GUIDE.md)** - Comprehensive API documentation with workflow examples
- [SETUP.md](SETUP.md) - Detailed installation instructions
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) - Complete environment variables reference
- [README_RU.md](README_RU.md) - Версия на русском языке
- [ML_PIPELINE.md](ML_PIPELINE.md) - ML/NLP pipeline details
- [Dataset Usage Guide](docs/dataset-usage-guide.md) - External dataset integration guide

## License

MIT

---

Built by Soinex Inc
