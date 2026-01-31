# TEAM7 Resume Analysis Platform

AI-powered resume analysis system with intelligent job matching.

## Quick Start

Choose your operating system:

### macOS / Linux

```bash
bash setup.sh
```

### Windows (PowerShell)

```powershell
.\setup.ps1
```

The script will:
1. Check Docker is installed
2. Create `.env` configuration file
3. Build and start all services
4. Run health checks

Then open http://localhost:5173 in your browser.

## Load Test Data

After setup, load sample resumes and vacancies:

### macOS / Linux

```bash
bash scripts/load_test_data.sh
```

### Windows (PowerShell)

```powershell
.\scripts\load-test-data.ps1
```

This will upload:
- **65 resumes** (DOCX format)
- **5 job vacancies** (from various tech roles)

## Requirements

- **Docker Desktop** (Mac/Windows) or Docker + Docker Compose (Linux)
- **8GB RAM** minimum (16GB recommended)
- **5GB disk space**

### Windows Notes

- Requires **Windows 10/11** with Docker Desktop installed
- Run PowerShell as **Administrator** if needed
- If script execution is blocked, run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React UI |
| Backend API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Flower | http://localhost:5555 | Celery task monitoring |

## Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start all services
docker-compose up -d
# Windows: docker compose up -d

# 3. View logs
docker-compose logs -f
# Windows: docker compose logs -f
```

## Common Commands

```bash
# View all logs
docker-compose logs -f           # Mac/Linux
docker compose logs -f           # Windows

# View specific service logs
docker-compose logs -f backend   # Mac/Linux
docker compose logs backend      # Windows

# Restart services
docker-compose restart           # Mac/Linux
docker compose restart           # Windows

# Stop all services
docker-compose down              # Mac/Linux
docker compose down              # Windows

# Stop and remove volumes (deletes data)
docker-compose down -v           # Mac/Linux
docker compose down -v           # Windows
```

## Features

- **Resume Upload & Analysis**: Upload PDF/DOCX resumes for AI analysis
- **Job Matching**: Compare resumes against job vacancies
- **Multi-language**: English and Russian support
- **Analytics Dashboard**: Track hiring metrics and funnels
- **Skill Taxonomy**: Custom skill matching with synonyms
- **Feedback System**: Improve matching accuracy over time

## Test Data

The repository includes sample data for testing:

- **65 resumes** in `testdata/vacancy-resume-matching-dataset-main/CV/`
- **5 vacancies** in `testdata/vacancy-resume-matching-dataset-main/5_vacancies.csv`

Vacancies include:
- Software Developer - .NET
- Remote Software Developer (Python/Java/C++)
- Backend Software Developer (LAMP stack)
- Junior Level Software Developer
- Software Developer (Java/C#)

## Troubleshooting

**Port already in use?**
Edit `.env` and change `FRONTEND_PORT` or `BACKEND_PORT`.

**Services not starting?**
```bash
docker-compose logs backend    # Mac/Linux
docker compose logs backend    # Windows
```

**PowerShell says scripts are disabled?**
Run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**Need to reset everything?**
```bash
docker-compose down -v          # Mac/Linux
docker compose down -v          # Windows
bash setup.sh                   # Mac/Linux
.\setup.ps1                     # Windows
```

## Project Structure

```
├── backend/               # FastAPI backend
├── frontend/              # React + Vite frontend
├── docker-compose.yml     # Docker services configuration
├── setup.sh               # Setup script for Mac/Linux
├── setup.ps1              # Setup script for Windows
├── scripts/
│   ├── load_test_data.sh      # Test data loader (Mac/Linux)
│   └── load-test-data.ps1     # Test data loader (Windows)
├── testdata/              # Sample resumes and vacancies
└── .env.example           # Environment variables template
```

## Support

For issues or questions, contact the TEAM7 team.
