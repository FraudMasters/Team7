# TEAM7 Resume Analysis Platform

AI-powered resume analysis system with intelligent job matching, multi-language support, and analytics dashboard.

## Features

- **Resume Upload & Analysis**: Support for PDF and DOCX formats
- **Intelligent Matching**: Skill-based job matching with synonym handling
- **Multi-language**: English and Russian support
- **Analytics Dashboard**: Hiring funnels, skill demand, recruiter performance
- **Async Processing**: Celery + Redis for background tasks
- **Modern UI**: React 18 + Material-UI with responsive design

## Quick Start

Choose your operating system:

### macOS / Linux

```bash
git clone https://github.com/FraudMasters/Team7.git
cd Team7
bash setup.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/FraudMasters/Team7.git
cd Team7
.\setup.ps1
```

Then open http://localhost:5173

### Load Test Data (Optional)

```bash
# macOS/Linux
bash scripts/load_test_data.sh

# Windows
.\scripts\load-test-data.ps1
```

This uploads 65 sample resumes and 5 job vacancies.

## Requirements

- **Docker Desktop** (Mac/Windows) or Docker + Docker Compose (Linux)
- **8GB RAM** minimum (16GB recommended)
- **5GB disk space**

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React UI |
| Backend API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Interactive documentation |
| Flower | http://localhost:5555 | Celery monitoring |

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │─────▶│   Backend    │─────▶│   Database  │
│ (React+MUI) │      │   (FastAPI)  │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
              ┌─────────┐      ┌──────────┐
              │ Celery  │      │  Redis   │
              │ Worker  │      │  Broker  │
              └─────────┘      └──────────┘
```

## How It Works

### 1. Resume Upload & Parsing

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Upload PDF/  │────▶│ Extract Text │────▶│ Save to DB   │
│   DOCX       │     │ (PyPDF2/     │     │ (status:     │
│              │     │  python-docx)│     │  uploaded)   │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 2. Resume Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESUME ANALYSIS PIPELINE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LANGUAGE DETECTION (langdetect)                            │
│     └─▶ Detects English or Russian                             │
│                                                                 │
│  2. KEYWORD EXTRACTION (KeyBERT)                                │
│     └─▶ Extracts key skills and competencies                   │
│                                                                 │
│  3. NAMED ENTITY RECOGNITION (SpaCy)                            │
│     ├─▶ en_core_web_sm (English)                               │
│     └─▶ ru_core_news_sm (Russian)                              │
│         • Organizations (companies)                            │
│         • Dates (work periods)                                  │
│         • Technical skills                                      │
│         • Person names                                          │
│                                                                 │
│  4. EXPERIENCE CALCULATION                                     │
│     ├─▶ Parse work periods from dates                          │
│     ├─▶ Detect overlapping periods (avoid double-count)       │
│     └─▶ Calculate total years/months of experience             │
│                                                                 │
│  5. GRAMMAR CHECKING (LanguageTool)                            │
│     ├─▶ Grammar errors                                          │
│     ├─▶ Spelling mistakes                                      │
│     └─▶ Style suggestions                                       │
│                                                                 │
│  6. ERROR DETECTION                                            │
│     ├─▶ Missing contact info                                    │
│     ├─▶ Resume too short                                        │
│     ├─▶ No portfolio (for juniors)                             │
│     └─▶ Inconsistent dates                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Job Matching Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                    JOB MATCHING ALGORITHM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VACANCY REQUIREMENTS                                           │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────────────┐                                       │
│  │ NORMALIZE SKILLS     │                                       │
│  │ • PostgreSQL → SQL   │                                       │
│  │ • ReactJS → React    │                                       │
│  │ • Java 8 → Java      │                                       │
│  └──────────┬──────────┘                                       │
│             │                                                   │
│             ▼                                                   │
│  ┌─────────────────────┐                                       │
│  │ COMPARE WITH RESUME │                                       │
│  │ • Direct match       │                                       │
│  │ • Synonym match      │                                       │
│  │ • Related skills     │                                       │
│  └──────────┬──────────┘                                       │
│             │                                                   │
│             ▼                                                   │
│  ┌─────────────────────┐       ┌─────────────────────┐        │
│  │ EXPERIENCE VERIFY   │──────▶│ MATCH PERCENTAGE    │        │
│  │ • Has X years with   │       │ • Matched: 75%       │        │
│  │   skill Y?           │       │ • Missing: 25%       │        │
│  └─────────────────────┘       │ • Status: matched    │        │
│                                └─────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Skill Synonym Matching

The system understands that different terms can mean the same skill:

| User Input | Matches Also |
|-----------|--------------|
| PostgreSQL | SQL, Postgres, psql |
| React | ReactJS, React.js, React.js |
| JavaScript | JS, javascript |
| Java | Java 8, Java 11, Java 17 |

## Common Commands

```bash
# View logs
docker compose logs -f

# View specific service logs
docker compose logs backend
docker compose logs frontend

# Restart services
docker compose restart

# Stop all services
docker compose down

# Stop and remove data
docker compose down -v
```

## Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL 14 with SQLAlchemy 2.0
- **ML/NLP**: KeyBERT, SpaCy, LanguageTool
- **Async**: Celery + Redis

### Frontend
- **Framework**: React 18 with TypeScript 5.6
- **Build**: Vite 5.4
- **UI**: Material-UI (MUI) v6
- **i18n**: react-i18next (EN/RU)

## Project Structure

```
├── backend/               # FastAPI backend
│   ├── analyzers/         # ML/NLP analyzers
│   ├── api/               # API endpoints
│   ├── tasks/             # Celery tasks
│   ├── models/            # SQLAlchemy models
│   └── alembic/           # Database migrations
├── frontend/              # React + Vite frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── i18n/          # Translations (EN/RU)
│   └── nginx.conf         # nginx config for production
├── scripts/               # Setup and utility scripts
│   ├── load_test_data.sh  # Test data loader
│   └── load-test-data.ps1 # Windows version
├── services/              # Shared services
│   └── data_extractor/    # PDF/DOCX extraction
├── docker-compose.yml     # Docker services
├── setup.sh               # Setup script (Mac/Linux)
├── setup.ps1              # Setup script (Windows)
├── .env.example           # Environment template
├── README.md              # This file
└── SETUP.md               # Detailed setup guide
```

## API Examples

### Upload Resume

```bash
curl -X POST http://localhost:8000/api/resumes/upload \
  -F "file=@resume.pdf"
```

### Analyze Resume

```bash
curl -X POST http://localhost:8000/api/resumes/analyze \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid", "extract_keywords": true}'
```

### Job Matching

```bash
curl -X POST http://localhost:8000/api/matching/compare \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "uuid",
    "vacancy_data": {
      "position": "Java Developer",
      "mandatory_requirements": ["Java", "Spring"]
    }
  }'
```

## Documentation

- [Setup Guide](SETUP.md) - Detailed installation instructions
- [Database Setup](backend/DATABASE_SETUP.md) - Database configuration
- [Matching Implementation](backend/MATCHING_IMPLEMENTATION.md) - Job matching details

## Troubleshooting

**Port already in use?**
Edit `.env` and change `FRONTEND_PORT` or `BACKEND_PORT`.

**Services not starting?**
```bash
docker compose logs backend
```

**PowerShell scripts blocked?**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Reset everything?**
```bash
docker compose down -v
bash setup.sh
```

## License

MIT

---

Built for TEAM7
