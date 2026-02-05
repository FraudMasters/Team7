# AgentHR - AI-Powered Resume Analysis & Candidate Ranking

AI-powered resume analysis system built on a **microservices architecture** with intelligent job matching, ML-based candidate ranking, and comprehensive monitoring.

## Features

- **Resume Upload & Analysis**: Support for PDF and DOCX formats with NLP-based parsing
- **Unified Matching System**: Three-method matching (Keyword, TF-IDF, Vector similarity)
- **AI Candidate Ranking**: ML-based ranking with 13 features and A/B testing support
- **Recruiter Feedback**: Feedback loop for continuous model improvement
- **Explainable AI**: Feature importance and ranking factors breakdown
- **Multi-language**: English and Russian support
- **Modern Monitoring**: Grafana + Loki + Promtail + Prometheus stack
- **Async Processing**: Celery + Redis for background tasks
- **Modern UI**: React 18 + Material-UI with responsive design
- **Microservices Architecture**: 10 independently deployable services

## Quick Start

### Prerequisites

- **Docker Desktop** (Mac/Windows) or Docker + Docker Compose (Linux)
- **8GB RAM** minimum (16GB recommended)
- **5GB disk space**

### Start Services

```bash
git clone https://github.com/FraudMasters/Team7.git
cd Team7  # or agenthr

# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### Access URLs

#### Application Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React web application |
| API Gateway | http://localhost:8888 | Single entry point for all API requests |
| API Docs | http://localhost:8888/docs | Interactive API documentation (Swagger) |

#### Core Microservices (Direct Access)

| Service | Port | Description |
|---------|------|-------------|
| Resume Processing | 8001 | Resume upload, parsing, and analysis |
| Matching | 8002 | Skill matching and candidate ranking |
| Candidate | 8003 | Candidate CRUD and management |
| Vacancy | 8004 | Job vacancy management |
| Taxonomy | 8005 | Skill taxonomies and synonyms |
| Analytics | 8006 | Dashboards and reports |
| ATS Simulation | 8007 | ATS scoring and screening |
| Notifications | 8008 | Email, SMS, webhook notifications |
| Integrations | 8009 | Third-party service integrations |

#### Infrastructure Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Keycloak | http://localhost:8080 | admin/admin (SSO/Auth) |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Loki | http://localhost:3100 | - |
| PostgreSQL | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | - |

### Load Test Data

```bash
# Load 65 resumes and 5 vacancies
docker-compose exec api-gateway python scripts/reset_and_reload.py
```

## Architecture

### Microservices Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway (Port 8888)                            │
│                     Routing, Auth, Rate Limiting, CORS                         │
└──────────────────────────────┬─────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Frontend    │    │   Keycloak    │    │  Monitoring   │
│  (React:3000) │    │    (8080)     │    │   (Grafana)   │
└───────────────┘    └───────────────┘    └───────────────┘
                                │
        ┌───────────────────────┼───────────────────────────────────────────┐
        │                       │                                           │
        ▼                       ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Core Microservices (8001-8009)                         │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│  Resume     │  Matching   │  Candidate  │  Vacancy   │    Taxonomy        │
│ Processing  │             │             │            │                     │
│    (8001)   │   (8002)    │   (8003)    │   (8004)   │      (8005)        │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│  Analytics  │    ATS      │Notification │Integration  │                     │
│             │ Simulation  │            │             │                     │
│   (8006)    │   (8007)    │   (8008)    │   (8009)    │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │     Redis     │    │   Celery      │
│    (5432)     │    │    (6379)     │    │   Workers     │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Microservices Description

| Service | Port | Purpose | Key Features |
|---------|------|---------|--------------|
| **API Gateway** | 8888 | Single entry point, routing, JWT validation | Rate limiting, CORS, API versioning |
| **Resume Processing** | 8001 | Upload, parse, analyze resumes | PDF/DOCX extraction, NLP parsing |
| **Matching** | 8002 | Skill matching and ranking | 3-method matcher, TF-IDF, vectors |
| **Candidate** | 8003 | Candidate management | CRUD, notes, tags, activities |
| **Vacancy** | 8004 | Job vacancy management | Bulk operations, saved searches |
| **Taxonomy** | 8005 | Skill taxonomies | Custom synonyms, classifications |
| **Analytics** | 8006 | Dashboards and reports | Performance metrics, batch jobs |
| **ATS Simulation** | 8007 | Resume screening | ATS scoring, LLM-based analysis |
| **Notifications** | 8008 | Alerts and communications | Email, SMS, webhooks |
| **Integrations** | 8009 | Third-party connections | LinkedIn, job boards, HRIS |

### Inter-Service Communication

- **Protocol**: gRPC (recommended) or REST for service-to-service calls
- **Authentication**: JWT tokens validated at API Gateway
- **Service Discovery**: Consul or Kubernetes native
- **Distributed Tracing**: Jaeger integration for observability

## API Endpoints

All API requests go through the **API Gateway** at `http://localhost:8888`

### Resume Analysis

```bash
# Upload resume
curl -X POST http://localhost:8888/api/resumes/upload \
  -F "file=@resume.pdf"

# Analyze resume
curl -X POST http://localhost:8888/api/resumes/analyze \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid"}'
```

### Job Matching

```bash
# Unified matching (AI-powered)
curl -X POST http://localhost:8888/api/matching/compare-unified \
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
curl -X POST http://localhost:8888/api/ranking/rank \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "resume_uuid",
    "vacancy_id": "vacancy_uuid",
    "use_experiment": true
  }'

# Get ranked candidates for vacancy
curl -X GET "http://localhost:8888/api/ranking/vacancy/{vacancy_id}/ranked?limit=10"

# Submit feedback on ranking
curl -X POST http://localhost:8888/api/ranking/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rank_id": "rank_uuid",
    "was_helpful": true,
    "actual_outcome": "hired"
  }'

# Get feature importance
curl -X GET http://localhost:8888/api/ranking/models/importance
```

### Vacancies

```bash
# Get all vacancies
curl -X GET http://localhost:8888/api/vacancies/

# Create vacancy
curl -X POST http://localhost:8888/api/vacancies/ \
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
├── services/                    # Microservices
│   ├── api-gateway/            # API Gateway (Port 8888)
│   ├── resume-processing/      # Resume Service (Port 8001)
│   ├── matching/               # Matching Service (Port 8002)
│   ├── candidate/              # Candidate Service (Port 8003)
│   ├── vacancy/                # Vacancy Service (Port 8004)
│   ├── taxonomy/               # Taxonomy Service (Port 8005)
│   ├── analytics/              # Analytics Service (Port 8006)
│   ├── ats-simulation/         # ATS Service (Port 8007)
│   ├── notifications/          # Notification Service (Port 8008)
│   └── integrations/           # Integration Service (Port 8009)
├── shared_models/              # Shared SQLAlchemy models
│   ├── base.py                 # Base classes and mixins
│   └── common.py               # Common models
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
├── testdata/                   # Test data
│   └── vacancy-resume-matching-dataset-main/
│       ├── CV/                 # 65 resume files
│       └── 5_vacancies.csv     # 5 job vacancies
└── docker-compose.yml          # Docker services
```

## Tech Stack

### Backend Microservices
- **Framework**: FastAPI with Python 3.14
- **Database**: PostgreSQL 14 with SQLAlchemy 2.0 (async)
- **Inter-service Comm**: gRPC with protocol buffers
- **Task Queue**: Celery 5.4.0 with Redis 5.2.0
- **ML**: scikit-learn, sentence-transformers, spaCy 3.8.2
- **Authentication**: Keycloak (JWT)

### Frontend
- **Framework**: React 18 with TypeScript
- **Build**: Vite 5.4
- **UI**: Material-UI (MUI) v6
- **State**: TanStack React Query

### Infrastructure
- **API Gateway**: Kong or Traefik
- **Service Discovery**: Consul
- **Distributed Tracing**: Jaeger
- **Monitoring**:
  - Grafana - Visualization dashboards
  - Loki - Log aggregation
  - Promtail - Log collector
  - Prometheus - Metrics collection

## Common Commands

```bash
# View logs for specific service
docker-compose logs -f api-gateway
docker-compose logs -f resume-processing
docker-compose logs -f matching

# View all service logs
docker-compose logs -f

# Restart specific service
docker-compose restart api-gateway

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v

# Run database migration for a service
docker-compose exec resume-processing alembic upgrade head

# Check service health
curl http://localhost:8888/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Database Schemas

Each microservice has its own database schema for isolation:

| Service | Schema | Tables |
|---------|--------|--------|
| Resume Processing | `resumes_service` | resumes, resume_analyses, work_experiences |
| Matching | `matching_service` | match_results, candidate_ranks, skill_gaps |
| Candidate | `candidates_service` | candidates, candidate_notes, candidate_tags |
| Vacancy | `vacancies_service` | vacancies, saved_searches |
| Taxonomy | `taxonomies_service` | skill_taxonomies, custom_synonyms |
| Analytics | `analytics_service` | reports, batch_jobs, analytics_* |
| ATS | `ats_service` | ats_results, screening_questions |
| Notifications | `notifications_service` | notifications, email_templates |
| Integrations | `integrations_service` | integrations, linkedin_tokens |

## Development

### Running Individual Services

```bash
# Run API Gateway
cd services/api-gateway
uvicorn main:app --host 0.0.0.0 --port 8888 --reload

# Run Resume Processing Service
cd services/resume-processing
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Run Matching Service
cd services/matching
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Running Celery Workers

Each service has its own Celery worker:

```bash
# Resume Processing Worker
cd services/resume-processing
celery -A celery_app.celery_app worker --loglevel=info --queues=resume_processing

# Matching Worker
cd services/matching
celery -A celery_app.celery_app worker --loglevel=info --queues=matching

# Analytics Worker
cd services/analytics
celery -A celery_app.celery_app worker --loglevel=info --queues=analytics,reporting
```

## Documentation

- **[API Usage Guide](docs/API_USAGE_GUIDE.md)** - Comprehensive API documentation
- [SETUP.md](SETUP.md) - Detailed installation instructions
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) - Complete environment variables reference
- [README_RU.md](README_RU.md) - Версия на русском языке
- [ML_PIPELINE.md](ML_PIPELINE.md) - ML/NLP pipeline details
- [Dataset Usage Guide](docs/dataset-usage-guide.md) - External dataset integration

## License

MIT

---

Built by TEAM7
