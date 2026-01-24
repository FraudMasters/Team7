# Database Setup and Migration Guide

This document describes how to set up and manage database migrations for the Resume Analysis System.

## Overview

The system uses:
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic 1.13+

## Database Schema

### Tables

#### `resumes`
Stores uploaded resume files and processing metadata.

- `id` (UUID, PK): Unique identifier
- `filename` (VARCHAR 255): Original filename
- `file_path` (VARCHAR 512): Storage path
- `content_type` (VARCHAR 100): MIME type (application/pdf, etc.)
- `status` (ENUM): pending, processing, completed, failed
- `raw_text` (TEXT): Extracted text content
- `language` (VARCHAR 10): Detected language (en, ru)
- `error_message` (TEXT): Error details if processing failed
- `created_at`, `updated_at` (TIMESTAMPTZ): Timestamps

**Indexes**: `status` (for querying by processing state)

#### `analysis_results`
Stores NLP/ML analysis results for resumes.

- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to resumes table (CASCADE delete)
- `errors` (JSON): Detected errors (grammar, spelling, missing elements)
- `skills` (JSON): Extracted skills with metadata
- `experience_summary` (JSON): Total experience and per-skill breakdown
- `recommendations` (JSON): Improvement suggestions
- `keywords` (JSON): KeyBERT extracted keywords with scores
- `entities` (JSON): Named entities (organizations, dates, education)
- `created_at`, `updated_at` (TIMESTAMPTZ): Timestamps

**Constraints**: `resume_id` unique (one analysis per resume)

#### `job_vacancies`
Stores job descriptions for matching against resumes.

- `id` (UUID, PK): Unique identifier
- `title` (VARCHAR 255): Job title
- `description` (TEXT): Full job description
- `required_skills` (JSON): Mandatory skills array
- `min_experience_months` (INTEGER): Minimum required experience
- `additional_requirements` (JSON): Preferred skills array
- `industry` (VARCHAR 100): Industry sector
- `work_format` (VARCHAR 50): remote, office, hybrid
- `location` (VARCHAR 255): Location requirements
- `external_id` (VARCHAR 255): External system ID (job board API)
- `source` (VARCHAR 50): Source (manual, api, scrape)
- `created_at`, `updated_at` (TIMESTAMPTZ): Timestamps

**Indexes**: `external_id` (for deduplication)

#### `match_results`
Stores resume-to-vacancy matching results.

- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to resumes (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to job_vacancies (CASCADE delete)
- `match_percentage` (NUMERIC 5,2): Overall match score (0-100)
- `matched_skills` (JSON): Skills found with highlighting info
- `missing_skills` (JSON): Required skills not found
- `additional_skills_matched` (JSON): Additional skills matched
- `experience_verified` (BOOLEAN): Whether experience requirements met
- `experience_details` (JSON): Per-skill experience breakdown
- `created_at`, `updated_at` (TIMESTAMPTZ): Timestamps

**Indexes**: `resume_id`, `vacancy_id` (for querying by resume or vacancy)

## Setup

### 1. Configure Database URL

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/resume_analysis
```

Or create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/resume_analysis
```

### 2. Start PostgreSQL with Docker Compose

```bash
docker-compose up -d postgres
```

### 3. Run Initial Migration

```bash
cd backend
alembic upgrade head
```

This will create all tables in the database.

### 4. Verify Migration

```bash
alembic current
```

Expected output:
```
Current revision(s): 001_init
```

## Using Alembic

### Creating New Migrations

After modifying database models in `backend/models/`, generate a migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Review the generated migration file in `backend/alembic/versions/` before applying.

### Applying Migrations

Apply all pending migrations:

```bash
alembic upgrade head
```

Apply specific migration:

```bash
alembic upgrade <revision_id>
```

### Rolling Back Migrations

Rollback one migration:

```bash
alembic downgrade -1
```

Rollback to specific revision:

```bash
alembic downgrade <revision_id>
```

### Viewing Migration History

```bash
alembic history
```

### Database Inspection

Connect to the database and inspect tables:

```bash
docker-compose exec postgres psql -U user -d resume_analysis

# Inside psql
\dt                    # List tables
\d+ resumes            # Describe table structure
SELECT * FROM resumes; # View data
```

## Database Models

### Using Models in Python

```python
from models import Resume, AnalysisResult, JobVacancy, MatchResult
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create a new resume
resume = Resume(
    filename="resume.pdf",
    file_path="/uploads/resume.pdf",
    content_type="application/pdf",
    status=ResumeStatus.PENDING
)
session.add(resume)
session.commit()

# Query resumes
pending_resumes = session.query(Resume).filter(
    Resume.status == ResumeStatus.PENDING
).all()
```

## Testing

### Verify Alembic Configuration

```bash
python backend/verify_alembic.py
```

This script checks:
- Alembic configuration is valid
- Database models can be imported
- Migration files are discoverable

### Reset Database (Development Only)

⚠️ **Warning**: This deletes all data!

```bash
# Drop all tables
alembic downgrade base

# Recreate tables
alembic upgrade head
```

## Troubleshooting

### Migration Conflicts

If multiple developers create migrations with the same revision ID, rename the migration file's revision ID to a unique value (e.g., use timestamp).

### Database Connection Issues

1. Verify PostgreSQL is running: `docker-compose ps`
2. Check connection string in `.env` or environment
3. Ensure database exists: `docker-compose exec postgres createdb -U user resume_analysis`

### Enum Type Issues

PostgreSQL enums must be created before being used. The `001_init.py` migration handles this. If you encounter issues with the `resumestatus` enum:

```sql
DROP TYPE IF EXISTS resumestatus CASCADE;
```

Then rerun the migration.

## Best Practices

1. **Always review** auto-generated migrations before committing
2. **Use transactions** when applying migrations to production
3. **Backup database** before running major migrations
4. **Test migrations** on a staging database first
5. **Keep migrations reversible** by implementing `downgrade()` functions
6. **Never modify** existing migration files - always create new ones
7. **Use descriptive** migration messages (e.g., "add_index_on_resumes_status")

## Further Reading

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
