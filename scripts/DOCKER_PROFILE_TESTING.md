# Docker Compose Profile Testing Guide

This document describes how to test the Docker Compose profile deployments for the AgentHR platform.

## Overview

The platform supports three deployment profiles:
- **minimal**: PostgreSQL, Redis, Backend, Frontend (essential services only)
- **core**: Minimal + Celery Worker, Celery Beat (adds async task processing)
- **full**: Core + Monitoring stack (Grafana, Prometheus, Loki, Promtail, exporters)

## Prerequisites

Before running the tests, ensure:
- Docker is installed and running
- Docker Compose v2 is available
- `.env` file exists in the project root
- Ports are available: 3000, 5432, 6379, 8000, 3001, 9090, 3100 (depending on profile)

## Automated Testing

Use the provided test script to run all profile tests automatically:

```bash
bash scripts/test-docker-profiles.sh
```

The script will:
1. Check prerequisites (Docker, .env file, etc.)
2. Test minimal profile deployment
3. Test core profile deployment
4. Test full profile deployment
5. Run health checks
6. Display test summary

## Manual Testing

### Test 1: Minimal Profile

Start the minimal profile:
```bash
docker compose --profile minimal up -d
```

Verify services:
```bash
# Check running containers
docker compose ps

# Verify PostgreSQL
docker exec resume_analysis_db pg_isready -U postgres

# Verify Redis
docker exec resume_analysis_redis redis-cli ping

# Check logs
docker compose logs -f
```

Expected services:
- `resume_analysis_db` (PostgreSQL)
- `resume_analysis_redis` (Redis)
- `resume_analysis_backend` (FastAPI)
- `resume_analysis_frontend` (React/Vite)

Clean up:
```bash
docker compose down
```

### Test 2: Core Profile

Start the core profile:
```bash
docker compose --profile core up -d
```

Verify additional services:
```bash
# Check all containers
docker compose ps

# Verify Celery Worker
docker logs resume_analysis_celery_worker

# Verify Celery Beat
docker logs resume_analysis_celery_beat

# Run health checks
bash scripts/health-check.sh
```

Expected services (in addition to minimal):
- `resume_analysis_celery_worker` (Async task processing)
- `resume_analysis_celery_beat` (Scheduled tasks)

Clean up:
```bash
docker compose down
```

### Test 3: Full Profile

Start the full profile:
```bash
docker compose --profile full up -d
```

Verify monitoring stack:
```bash
# Check all containers
docker compose ps

# Verify Grafana is accessible
curl -f http://localhost:3001

# Verify Prometheus
curl -f http://localhost:9090

# Verify Loki
curl -f http://localhost:3100/ready

# Run health checks
bash scripts/health-check.sh
```

Expected services (in addition to core):
- `resume_analysis_grafana` (Visualization & dashboards)
- `resume_analysis_prometheus` (Metrics collection)
- `resume_analysis_loki` (Log aggregation)
- `resume_analysis_promtail` (Log collector)
- `resume_analysis_postgres_exporter` (PostgreSQL metrics)
- `resume_analysis_celery_exporter` (Celery metrics)
- `resume_analysis_cadvisor` (Container metrics)

Access the services:
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

Clean up:
```bash
docker compose down -v
```

## Health Check Validation

The health-check.sh script validates all running services:

```bash
bash scripts/health-check.sh
```

Expected output:
- ✓ PostgreSQL is healthy
- ✓ Redis is healthy
- ✓ Backend API is healthy
- ✓ Frontend is healthy
- ✓ Celery Worker is healthy
- Summary: All services healthy

## Troubleshooting

### Services not starting

Check logs for specific service:
```bash
docker compose logs -f <service-name>
```

Check all logs:
```bash
docker compose logs -f
```

### Port conflicts

Check which ports are in use:
```bash
# On macOS/Linux
lsof -i :8000
lsof -i :5432
lsof -i :6379

# On all systems
docker compose ps
```

### Database connection issues

Verify PostgreSQL is ready:
```bash
docker exec resume_analysis_db pg_isready -U postgres
```

Check database logs:
```bash
docker compose logs postgres
```

### Clean slate restart

Remove all containers and volumes:
```bash
docker compose down -v
docker compose --profile full up -d
```

## CI/CD Integration

To run these tests in CI/CD pipelines:

```bash
#!/bin/bash
set -e

# Ensure .env file exists
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Run automated tests
bash scripts/test-docker-profiles.sh

# Clean up
docker compose down -v
```

## Expected Results

### Minimal Profile
- 4 containers running
- PostgreSQL and Redis healthy
- Backend API responding on http://localhost:8000
- Frontend serving on http://localhost:3000

### Core Profile
- 6 containers running
- All minimal services + Celery Worker + Celery Beat
- Health check script reports all services healthy
- Async task processing available

### Full Profile
- 13+ containers running
- All core services + monitoring stack
- Grafana accessible at http://localhost:3001
- Prometheus collecting metrics
- Loki aggregating logs

## Profile Selection Best Practices

- **Development**: Use `minimal` for quick iteration
- **Testing**: Use `core` to test async features
- **Production**: Use `full` for complete observability
- **Debugging**: Start with `minimal`, add profiles as needed

## Notes

- Profiles are additive: `core` includes `minimal`, `full` includes `core`
- Services can belong to multiple profiles
- Default (no profile): No services start (must specify profile)
- Health checks may take 30-60 seconds after `docker compose up`
