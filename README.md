# AI-Powered Resume Analysis Platform

An intelligent resume analysis platform with ML/NLP processing, job matching, error detection, and web interface for outstaffing recruitment optimization.

## 🌟 Features

- **📄 Resume Upload & Parsing**: Support for PDF and DOCX formats with drag-and-drop interface
- **🔍 Intelligent Analysis**:
  - KeyBERT keyword extraction with BERT-based embeddings
  - SpaCy named entity recognition (skills, organizations, dates)
  - LanguageTool grammar and spelling checking (English & Russian)
  - Experience calculation with overlap detection
- **⚠️ Error Detection**: Identifies missing contact info, length issues, portfolio requirements
- **🎯 Job Matching**:
  - Skill synonym handling (PostgreSQL ≈ SQL, ReactJS ≈ React)
  - Match percentage calculation
  - Visual highlighting (green = matched, red = missing)
  - Experience verification by skill
- **⚡ Async Processing**: Celery + Redis for long-running analysis tasks
- **🎨 Modern UI**: React 18 + Material-UI with responsive design

## 🏗️ Architecture

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

## 📋 Tech Stack

### Backend
- **Framework**: FastAPI 0.115.0 with Python 3.9+
- **Database**: PostgreSQL 14 with SQLAlchemy 2.0 ORM
- **ML/NLP**:
  - KeyBERT (BERT-based keyword extraction)
  - SpaCy 3.8 (NER with en_core_web_sm, ru_core_web_sm)
  - LanguageTool 2.7.1 (grammar/spelling checking)
  - langdetect (automatic language detection)
- **File Processing**: PyPDF2, python-docx, pdfplumber
- **Async Processing**: Celery 5.4.0 + Redis 7
- **Testing**: pytest 8.3.3 with 70%+ coverage requirement

### Frontend
- **Framework**: React 18 with TypeScript 5.6
- **Build Tool**: Vite 5.4
- **UI Library**: Material-UI (MUI) v6
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library + Playwright (E2E)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (for infrastructure)
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)

### 1. Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd <repository-name>

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Start Infrastructure (Docker Compose)

```bash
# Start PostgreSQL, Redis, and application services
docker-compose up -d

# Check services status
docker-compose ps
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 5173
- Celery worker
- Flower monitoring on port 5555

### 3. Manual Setup (Alternative)

#### Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download ML models
python -m spacy download en_core_web_sm
python -m spacy download ru_core_web_sm

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Celery Monitoring**: http://localhost:5555 (Flower)

## 📖 API Documentation

### Resume Endpoints

#### Upload Resume

```http
POST /api/resumes/upload
Content-Type: multipart/form-data

{
  "file": <resume.pdf or resume.docx>
}
```

Response:
```json
{
  "id": "uuid",
  "filename": "resume.pdf",
  "status": "uploaded",
  "created_at": "2024-01-24T00:00:00Z"
}
```

#### Analyze Resume

```http
POST /api/resumes/analyze
Content-Type: application/json

{
  "resume_id": "uuid",
  "options": {
    "extract_keywords": true,
    "extract_entities": true,
    "check_grammar": true,
    "calculate_experience": true,
    "detect_errors": true
  }
}
```

Response:
```json
{
  "resume_id": "uuid",
  "language": "en",
  "keywords": ["Java", "Spring", "PostgreSQL"],
  "entities": {
    "organizations": ["MTS", "JBorn"],
    "dates": ["2020-05", "2023-02"],
    "technical_skills": ["Java", "Spring Boot", "Kafka"]
  },
  "grammar_issues": [
    {
      "type": "grammar",
      "message": "Missing comma",
      "context": "skills include Java Python",
      "suggestions": ["skills include Java, Python"]
    }
  ],
  "experience": {
    "total_years": 3.6,
    "total_months": 43,
    "projects_count": 2
  },
  "errors": [
    {
      "type": "missing_portfolio",
      "severity": "warning",
      "message": "Entry-level candidates should include portfolio link"
    }
  ],
  "processing_time_seconds": 2.5
}
```

#### Compare with Job Vacancy

```http
POST /api/matching/compare
Content-Type: application/json

{
  "resume_id": "uuid",
  "vacancy_data": {
    "position": "Java Developer",
    "mandatory_requirements": [
      "Java",
      "Spring",
      "PostgreSQL",
      "Kafka"
    ],
    "min_experience_years": 3
  }
}
```

Response:
```json
{
  "resume_id": "uuid",
  "vacancy_position": "Java Developer",
  "match_percentage": 75,
  "matched_skills": [
    {"skill": "Java", "status": "matched", "highlight": "green"},
    {"skill": "Spring", "status": "matched", "highlight": "green"},
    {"skill": "PostgreSQL", "status": "matched", "highlight": "green"}
  ],
  "missing_skills": [
    {"skill": "Kafka", "status": "missing", "highlight": "red"}
  ],
  "experience_verification": [
    {
      "skill": "Java",
      "required_years": 3,
      "candidate_years": 3.6,
      "meets_requirement": true
    }
  ]
}
```

### Health Check Endpoints

```http
GET /health          # Service health
GET /ready           # Readiness probe
GET /                # API root
```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=analyzers --cov-report=term-missing

# Run integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/test_error_detector.py -v
```

**Coverage Requirements**: 70%+ for core modules

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui
```

### Accuracy Validation

```bash
cd backend

# Validate error detection accuracy (target: 80%+)
python tests/accuracy_validation/validate_error_detection.py

# Validate skill matching accuracy (target: 90%+)
python tests/accuracy_validation/validate_skill_matching.py
```

## 🔧 Configuration

### Environment Variables

See `.env.example` files for all available configuration options:

- **Root `.env`**: Database and Redis configuration
- **Backend `backend/.env`**: ML model paths, API keys, CORS settings
- **Frontend `frontend/.env`**: API URL, application settings

### Key Configuration Files

- `backend/config.py` - Backend settings (Pydantic Settings)
- `backend/celery_config.py` - Celery worker configuration
- `frontend/vite.config.ts` - Frontend build configuration

## 📊 Monitoring

- **Celery Flower**: http://localhost:5555 - Monitor async tasks
- **FastAPI Docs**: http://localhost:8000/docs - Interactive API documentation
- **Database Logs**: `docker-compose logs postgres`
- **Application Logs**: `docker-compose logs backend`

## 🛠️ Development

### Code Quality

```bash
# Backend
cd backend
black .                    # Format code
flake8 .                   # Lint code
mypy .                     # Type checking

# Frontend
cd frontend
npm run lint               # ESLint
npm run format             # Prettier
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📦 Project Structure

```
.
├── backend/                    # FastAPI backend
│   ├── analyzers/              # ML/NLP analyzers
│   │   ├── keyword_extractor.py
│   │   ├── ner_extractor.py
│   │   ├── grammar_checker.py
│   │   ├── experience_calculator.py
│   │   └── error_detector.py
│   ├── api/                    # API endpoints
│   │   ├── resumes.py
│   │   ├── analysis.py
│   │   └── matching.py
│   ├── tasks/                  # Celery tasks
│   ├── tests/                  # Backend tests
│   ├── alembic/                # Database migrations
│   ├── models/                 # SQLAlchemy models
│   └── main.py                 # FastAPI app
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Utilities
│   ├── e2e/                    # E2E tests
│   └── package.json
├── services/                   # Shared services
│   └── data_extractor/         # PDF/DOCX extraction
├── docker-compose.yml          # Docker services
├── .env.example                # Root environment template
├── README.md                   # This file
└── DEPLOYMENT.md               # Deployment guide
```

## 🚢 Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick deploy with Docker:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Documentation

- [Backend API Documentation](http://localhost:8000/docs)
- [Database Setup Guide](backend/DATABASE_SETUP.md)
- [Matching Implementation](backend/MATCHING_IMPLEMENTATION.md)
- [Security Scan Report](backend/SECURITY_SCAN_REPORT.md)
- [Frontend Documentation](frontend/README.md)
- [E2E Testing Guide](frontend/e2e/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT

## 📧 Support

For support and questions, please open an issue in the repository.

---

Built with ❤️ for Iconicompany - Smart Outstaffing Platform
