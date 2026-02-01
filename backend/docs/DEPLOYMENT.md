# Backend Deployment Guide

## Project: AgentHR Resume Analysis System

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Docker)](#quick-start-docker)
4. [Environment Configuration](#environment-configuration)
5. [Docker Deployment](#docker-deployment)
6. [Manual Deployment](#manual-deployment)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Scaling Strategies](#scaling-strategies)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)

---

## Deployment Overview

The AgentHR backend is designed for flexible deployment using **Docker Compose** (recommended) or manual installation. The system consists of multiple services that work together:

### Core Services

- **Backend API** (FastAPI): REST API server on port 8000
- **PostgreSQL Database**: Data persistence on port 5432
- **Redis**: Caching and Celery broker on port 6379
- **Celery Worker**: Async task processing
- **Celery Beat**: Scheduled tasks (backups, reports, cleanup)

### Optional Services

- **Grafana**: Metrics dashboard on port 3001
- **Prometheus**: Metrics collection on port 9090
- **Loki**: Log aggregation on port 3100
- **PostgreSQL Exporter**: Database metrics on port 9187
- **Redis Exporter**: Redis metrics on port 9121

### Resource Requirements

**Minimum (Development)**: 4 CPU cores, 8GB RAM, 20GB disk
**Recommended (Production)**: 8+ CPU cores, 16GB+ RAM, 50GB+ disk

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ (for Docker deployment)
- **Docker Compose**: 2.0+ (for Docker deployment)
- **Python**: 3.11+ (for manual deployment)
- **PostgreSQL**: 14+ (for manual deployment)
- **Redis**: 7+ (for manual deployment)
- **Git**: For cloning the repository

### System Requirements

**Operating System**: Linux (Ubuntu 20.04+, Debian 11+) recommended
**Network**: Outbound internet access for ML model downloads and API calls
**Disk Space**: Minimum 20GB (50GB+ recommended for production)
**Memory**: 8GB minimum, 16GB+ recommended

### Optional Services

- **S3-Compatible Storage**: For off-site backups (AWS S3, MinIO, etc.)
- **SMTP Server**: For email notifications
- **LanguageTool Server**: For grammar checking (local or public API)
- **Sentry**: For error tracking and monitoring

---

## Quick Start (Docker)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/agenthr.git
cd agenthr
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

**Services will be available at**:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

---

## Environment Configuration

### Configuration File

Copy `.env.example` to `.env` and customize:

```bash
cp backend/.env.example backend/.env
```

### Critical Configuration Values

#### Database

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-strong-password
POSTGRES_DB=resume_analysis
```

#### Redis

```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### Backend Server

```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

#### Security

```bash
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### ML Models

```bash
MODELS_CACHE_PATH=./models_cache
KEYBERT_MODEL=distilbert-base-nli-mean-tokens
SPACY_MODEL_EN=en_core_web_sm
SPACY_MODEL_RU=ru_core_news_sm
```

#### LLM Provider (for ATS Simulation)

```bash
LLM_PROVIDER=zai  # Options: zai, openai, anthropic, google
LLM_MODEL=claude-3-5-sonnet-20241022
ZAI_API_KEY=your-api-key-here
```

#### Backup Configuration

```bash
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=./data/backups

# S3 Off-site Backup (optional)
BACKUP_S3_ENABLED=false
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=your-access-key
BACKUP_S3_SECRET_KEY=your-secret-key
```

### Complete Configuration Reference

See `backend/.env.example` for all available configuration options with detailed comments.

---

## Docker Deployment

### Docker Compose Services

#### Production Deployment

```bash
# Build and start all services
docker-compose up -d --build

# Scale Celery workers for high load
docker-compose up -d --scale celery_worker=4

# View service status
docker-compose ps

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

#### Service Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart specific service
docker-compose restart backend

# Rebuild and restart specific service
docker-compose up -d --build backend
```

#### Container Resource Limits

Docker Compose includes resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
    reservations:
      cpus: '2.0'
      memory: 4G
```

Adjust these in `docker-compose.yml` based on your server capacity.

### Health Checks

Services include health checks:

```bash
# Check all service health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
docker-compose exec backend curl -f http://localhost:8000/health
```

### Network Configuration

Services communicate via a dedicated Docker network (`resume_network`):

```yaml
networks:
  resume_network:
    driver: bridge
```

### Volume Management

```bash
# List volumes
docker volume ls

# Backup volumes
docker run --rm -v resume_analysis_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volumes
docker run --rm -v resume_analysis_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

---

## Manual Deployment

### 1. System Dependencies

**Ubuntu/Debian**:

```bash
sudo apt-get update
sudo apt-get install -y \
  python3.11 \
  python3.11-venv \
  postgresql-14 \
  redis-server \
  libpq-dev \
  build-essential \
  git
```

**macOS**:

```bash
brew install python@3.11 postgresql@14 redis
```

### 2. Python Environment Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Download SpaCy models
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm
```

### 3. Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE resume_analysis;
CREATE USER resume_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE resume_analysis TO resume_user;
\q

# Run migrations
alembic upgrade head
```

### 4. Redis Setup

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis
redis-cli ping  # Should return PONG
```

### 5. Start Backend Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Start Celery Worker

```bash
# Terminal 1: Start Celery worker
celery -A celery_app.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=celery,analysis,learning,reporting

# Terminal 2: Start Celery beat (scheduler)
celery -A celery_app.celery_app beat \
  --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 7. Process Management (Optional)

**Using Supervisor**:

```ini
# /etc/supervisor/conf.d/backend.conf
[program:backend]
command=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/backend.log

[program:celery]
command=/path/to/venv/bin/celery -A celery_app.celery_app worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery.log
```

**Using systemd**:

```ini
# /etc/systemd/system/backend.service
[Unit]
Description=Backend API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Change all default passwords
- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Configure proper CORS origins (set `FRONTEND_URL`)
- [ ] Set `DEBUG=false`
- [ ] Configure backup settings
- [ ] Set up monitoring (Grafana/Prometheus)
- [ ] Configure log aggregation (Loki)
- [ ] Set up error tracking (Sentry)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure S3 off-site backup
- [ ] Review resource limits
- [ ] Test all critical workflows

### Production Environment Variables

```bash
# Security
SECRET_KEY=your-production-secret-key
DEBUG=false
RELOAD=false

# Database (use strong password)
DATABASE_URL=postgresql://user:strong-password@db-host:5432/dbname

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Backups
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=production-backups

# Monitoring
ENABLE_PROMETHEUS_METRICS=true
SENTRY_DSN=https://your-sentry-dsn
```

### Reverse Proxy Configuration

#### Nginx

```nginx
# /etc/nginx/sites-available/backend
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Upload size
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

#### Apache

```apache
# /etc/apache2/sites-available/backend.conf
<VirtualHost *:80>
    ServerName api.yourdomain.com
    Redirect permanent / https://api.yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName api.yourdomain.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/api.yourdomain.com/privkey.pem

    ProxyPreserveHost On
    ProxyRequests Off

    # Upload size
    LimitRequestBody 10485760

    # API proxy
    ProxyPass /health http://127.0.0.1:8000/health
    ProxyPassReverse /health http://127.0.0.1:8000/health

    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

### SSL/TLS Setup

```bash
# Using Let's Encrypt with Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal (configured automatically)
sudo certbot renew --dry-run
```

### Database Optimization

**PostgreSQL Configuration** (`/etc/postgresql/14/main/postgresql.conf`):

```ini
# Memory settings
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 256MB

# Connection settings
max_connections = 100
pool_size = 20
max_overflow = 10

# Query optimization
random_page_cost = 1.1
effective_io_concurrency = 200

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Logging
log_min_duration_statement = 1000  # Log slow queries (>1s)
```

---

## Monitoring & Logging

### Monitoring Stack

The project includes a comprehensive monitoring stack:

- **Grafana**: Visualization dashboard (port 3001)
- **Prometheus**: Metrics collection (port 9090)
- **Loki**: Log aggregation (port 3100)
- **PostgreSQL Exporter**: Database metrics (port 9187)
- **Redis Exporter**: Redis metrics (port 9121)

### Access Monitoring

```bash
# Grafana dashboard
open http://localhost:3001
# Default credentials (change on first login)
# Username: admin
# Password: admin

# Prometheus
open http://localhost:9090
```

### Key Metrics to Monitor

- **Backend API**: Request rate, latency, error rate
- **Database**: Connection pool, query performance, locks
- **Redis**: Memory usage, hit rate, connections
- **Celery**: Task queue length, worker utilization
- **System**: CPU, memory, disk I/O

### Logging Configuration

Logs are structured JSON for easy parsing:

```python
{
  "timestamp": "2024-02-01T12:00:00Z",
  "level": "INFO",
  "logger": "backend.api.resumes",
  "message": "Resume uploaded successfully",
  "context": {
    "resume_id": 123,
    "user_id": 456,
    "file_size": 1048576
  }
}
```

### Log Queries (Loki)

```bash
# Query all errors in last hour
{level="ERROR"} | logfmt

# Query slow database queries
{logger="backend.database"} | logfmt | duration > 1000

# Query Celery task failures
{logger="backend.celery"} | logfmt | status != "SUCCESS"
```

### Alerting (Grafana)

Configure alerts in Grafana for:

- High error rate (>5%)
- High latency (>5s p95)
- Database connection exhaustion (>80%)
- Redis memory usage (>90%)
- Celery queue backlog (>1000 tasks)
- Disk space low (<10% free)

---

## Backup & Recovery

### Automated Backups

The system includes automated daily backups via Celery Beat:

```bash
# Backup configuration in .env
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
```

### Manual Backup

```bash
# Database backup
docker-compose exec backend python -m scripts.backup_database --output /backups/manual_backup.sql

# Full backup (database + uploads)
docker-compose exec backend python -m scripts.backup_full --output /backups/full_backup.tar.gz
```

### S3 Off-Site Backup

Configure S3 backup for disaster recovery:

```bash
# Enable S3 backup
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=your-access-key
BACKUP_S3_SECRET_KEY=your-secret-key
BACKUP_S3_REGION=us-east-1
```

### Restore Procedure

```bash
# 1. Stop all services
docker-compose down

# 2. Restore database
docker-compose run --rm backend \
  python -m scripts.restore_database --input /backups/backup.sql

# 3. Start services
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
```

### Backup Testing

Test backups regularly (recommended: monthly):

```bash
# Test restore to staging environment
docker-compose -f docker-compose.staging.yml up -d
# Run restore procedure
# Verify data integrity
```

---

## Scaling Strategies

### Vertical Scaling

**Increase Resources**:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
```

### Horizontal Scaling

**Multiple Backend Instances**:

```bash
# Scale backend API
docker-compose up -d --scale backend=3

# Use load balancer (nginx/haproxy)
```

**Multiple Celery Workers**:

```bash
# Scale Celery workers
docker-compose up -d --scale celery_worker=4

# Configure queues for specialized workers
celery worker -Q analysis,high_priority --concurrency=4
celery worker -Q reporting --concurrency=2
celery worker -Q learning --concurrency=2
```

### Database Scaling

**Read Replicas**:

```python
# Configure read replica in config.py
DATABASE_READ_REPLICA_URL=postgresql://user:pass@replica-host:5432/db
```

**Connection Pooling**:

```bash
# Increase pool size
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

### Caching Strategy

**Redis Caching**:

```python
# Cache expensive computations
@lru_cache(maxsize=1000)
def expensive_computation():
    ...

# Use Redis for distributed caching
from redis import Redis
redis = Redis.from_url(settings.redis_url)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms**: `connection refused` or `could not connect to server`

**Solutions**:

```bash
# Check PostgreSQL is running
docker-compose ps postgres
sudo systemctl status postgresql  # Manual deployment

# Check connection string in .env
DATABASE_URL=postgresql://user:pass@host:5432/db

# Test connection
docker-compose exec backend python -c "from backend.database import engine; print(engine.connect())"

# Check logs
docker-compose logs postgres
```

#### 2. Redis Connection Failed

**Symptoms**: `Error connecting to Redis`

**Solutions**:

```bash
# Check Redis is running
docker-compose ps redis
redis-cli ping  # Should return PONG

# Check connection string
REDIS_URL=redis://localhost:6379/0

# Test connection
docker-compose exec backend python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

#### 3. ML Model Download Failed

**Symptoms**: Model download errors or slow first startup

**Solutions**:

```bash
# Pre-download models
docker-compose exec backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Cache models in volume
MODELS_CACHE_PATH=/app/models_cache  # Persisted in Docker volume

# Use mirror for faster downloads
HF_ENDPOINT=https://hf-mirror.com
```

#### 4. Celery Tasks Not Processing

**Symptoms**: Tasks stuck in `PENDING` state

**Solutions**:

```bash
# Check Celery worker is running
docker-compose ps celery_worker

# Check worker logs
docker-compose logs celery_worker

# Check queue length
docker-compose exec backend python -c "from celery import current_app; print(current_app.control.inspect().active())"

# Restart worker
docker-compose restart celery_worker
```

#### 5. Out of Memory

**Symptoms**: OOM killed, container exits

**Solutions**:

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G

# Reduce Celery concurrency
CELERY_WORKER_CONCURRENCY=2

# Enable memory monitoring
ENABLE_PROMETHEUS_METRICS=true
```

#### 6. Slow API Response

**Symptoms**: Requests timeout or slow

**Solutions**:

```bash
# Check logs for slow queries
docker-compose logs backend | grep "duration"

# Enable database query logging
LOG_LEVEL=DEBUG

# Add database indexes
docker-compose exec backend alembic upgrade head

# Scale backend
docker-compose up -d --scale backend=2

# Check resource usage
docker stats
```

### Debug Mode

Enable debug logging:

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart backend
docker-compose restart backend

# View logs
docker-compose logs -f backend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U postgres

# Redis health
docker-compose exec redis redis-cli ping

# Celery health
docker-compose exec backend celery -A celery_app.celery_app inspect active
```

---

## Security Considerations

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use ORM)
- [ ] XSS protection
- [ ] CSRF protection
- [ ] File upload validation
- [ ] Secure headers configured
- [ ] Logging and monitoring
- [ ] Regular security updates
- [ ] Firewall configured
- [ ] Database access restricted
- [ ] API authentication implemented

### Environment Variables Security

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use different .env for each environment
.env.development
.env.staging
.env.production

# Use secrets management
# - Docker Secrets
# - AWS Secrets Manager
# - HashiCorp Vault
```

### Network Security

```bash
# Docker network isolation
networks:
  resume_network:
    driver: bridge
    internal: false  # Set to true for complete isolation

# Firewall rules (ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### Database Security

```bash
# Strong password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict connections
# Listen only on localhost
# Use pg_hba.conf to restrict access

# Regular updates
sudo apt-get update && sudo apt-get upgrade postgresql
```

### API Security

```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# CORS configuration
CORSMiddleware(
    allow_origins=["https://your-frontend.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Input validation with Pydantic
class ResumeUpload(BaseModel):
    file: UploadFile
    title: str = Field(..., min_length=1, max_length=200)
```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Architecture**: `backend/docs/ARCHITECTURE.md`
- **Background Tasks**: `backend/docs/BACKGROUND_TASKS.md`
- **ML Pipeline**: `backend/docs/ML_PIPELINE.md`
- **Data Models**: `backend/docs/DATA_MODELS.md`

## Support

For issues and questions:

- **GitHub Issues**: https://github.com/your-org/agenthr/issues
- **Documentation**: https://docs.agenthr.com
- **Email**: support@agenthr.com

---

**Last Updated**: 2024-02-01
**Version**: 1.0.0
