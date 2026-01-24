# Deployment Guide

This guide covers deploying the AI-Powered Resume Analysis Platform to production, including Docker deployment, cloud platforms, and monitoring setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
  - [AWS](#aws-deployment)
  - [Google Cloud Platform](#google-cloud-platform)
  - [Azure](#azure)
  - [Heroku](#heroku)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Security Considerations](#security-considerations)
- [Scaling Strategies](#scaling-strategies)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying to production, ensure you have:

- [ ] Docker and Docker Compose installed (for containerized deployment)
- [ ] PostgreSQL 14+ database (or managed cloud database)
- [ ] Redis 7+ for Celery (or managed cloud Redis)
- [ ] Domain name configured (if using custom domain)
- [ ] SSL/TLS certificates (Let's Encrypt or commercial)
- [ ] Sufficient server resources (see [System Requirements](#system-requirements))

### System Requirements

**Minimum (Development):**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB
- Bandwidth: 10 Mbps

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 50+ GB SSD
- Bandwidth: 100+ Mbps

## Docker Deployment

### 1. Prepare Environment Files

```bash
# Copy environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit environment variables
nano .env
nano backend/.env
nano frontend/.env
```

### 2. Configure Production Environment

Edit `.env` file for production:

```bash
# Database
DATABASE_URL=postgresql://user:secure_password@postgres:5432/resume_analysis
POSTGRES_USER=resume_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=resume_analysis

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend
FRONTEND_PORT=5173
FRONTEND_HOST=0.0.0.0

# Security
MAX_UPLOAD_SIZE_MB=10
ANALYSIS_TIMEOUT_SECONDS=300

# CORS (update with your frontend domain)
FRONTEND_URL=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3. Build and Start Services

```bash
# Build production images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify database connection
docker-compose exec backend python -c "from database import engine; print('Database OK')"
```

### 5. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173

# Check Celery worker
docker-compose exec backend celery -A tasks inspect ping
```

### 6. Setup Reverse Proxy (Nginx)

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /etc/ssl/certs/your-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.com.key;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 10M;
    }

    # Backend health/other endpoints
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Start Nginx:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/resume-platform
sudo ln -s /etc/nginx/sites-available/resume-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS (Elastic Container Service)

1. **Push Docker images to ECR**:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push backend
docker tag resume_analysis_backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest

# Tag and push frontend
docker tag resume_analysis_frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-frontend:latest
```

2. **Create ECS Task Definition** (`task-definition.json`):

```json
{
  "family": "resume-analysis-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {"name": "POSTGRES_PASSWORD", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/resume-analysis",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "celery-worker",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest",
      "command": ["celery", "-A", "tasks", "worker", "--loglevel=info"],
      "environment": [...]
    }
  ]
}
```

3. **Create ECS Service**:

```bash
aws ecs create-service \
  --cluster resume-analysis-cluster \
  --service-name resume-analysis-service \
  --task-definition resume-analysis-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Using AWS RDS for PostgreSQL

```bash
# Create PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier resume-analysis-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.11 \
  --allocated-storage 20 \
  --master-username admin \
  --master-user-password secure_password \
  --vpc-security-group-ids sg-xxx

# Get connection endpoint
aws rds describe-db-instances --db-instance-identifier resume-analysis-db --query "DBInstances[0].Endpoint.Address"
```

#### Using AWS ElastiCache for Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id resume-analysis-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx
```

#### Using AWS Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name resume-analysis-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name resume-analysis-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx

# Register targets
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-xxx,Port=8000
```

### Google Cloud Platform Deployment

#### Using Google Cloud Run

```bash
# Build and push backend image
gcloud builds submit --tag gcr.io/<project-id>/resume-backend

# Deploy backend to Cloud Run
gcloud run deploy resume-backend \
  --image gcr.io/<project-id>/resume-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://...,REDIS_URL=redis://...

# Deploy frontend
gcloud builds submit --tag gcr.io/<project-id>/resume-frontend
gcloud run deploy resume-frontend \
  --image gcr.io/<project-id>/resume-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Using Google Cloud SQL

```bash
# Create PostgreSQL instance
gcloud sql instances create resume-analysis-db \
  --database-version POSTGRES_14 \
  --tier db-f1-micro \
  --region us-central1

# Create database
gcloud sql databases create resume_analysis --instance resume-analysis-db

# Get connection string
gcloud sql instances describe resume-analysis-db --format="value(connectionName)"
```

### Azure Deployment

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name resume-analysis-rg --location eastus

# Create container registry
az acr create --resource-group resume-analysis-rg --name resumeAnalysisRegistry --sku Basic

# Build and push images
az acr build --registry resumeAnalysisRegistry --image resume-backend .
az acr build --registry resumeAnalysisRegistry --image resume-frontend ./frontend

# Deploy container instance
az container create \
  --resource-group resume-analysis-rg \
  --name resume-backend \
  --image resumeAnalysisRegistry.azurecr.io/resume-backend \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables DATABASE_URL=postgresql://...
```

### Heroku Deployment

#### Using Heroku Container Registry

```bash
# Login to Heroku
heroku container:login

# Create Heroku app
heroku create resume-analysis-platform

# Build and push backend
cd backend
heroku container:push web -a resume-analysis-platform
heroku container:release web -a resume-analysis-platform

# Add PostgreSQL and Redis addons
heroku addons:create heroku-postgresql:mini -a resume-analysis-platform
heroku addons:create heroku-redis:mini -a resume-analysis-platform

# Set environment variables
heroku config:set MAX_UPLOAD_SIZE_MB=10 -a resume-analysis-platform
```

`Procfile` for backend:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A tasks worker --loglevel=info
```

## Environment Configuration

### Production Environment Variables

Create `backend/.env` for production:

```bash
# Database (use managed database URL)
DATABASE_URL=postgresql://user:password@production-db:5432/resume_analysis

# Redis (use managed Redis URL)
REDIS_URL=redis://production-redis:6379/0
CELERY_BROKER_URL=redis://production-redis:6379/0
CELERY_RESULT_BACKEND=redis://production-redis:6379/0

# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS (whitelist production domains)
FRONTEND_URL=https://your-production-domain.com

# Security
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=.pdf,.docx
ANALYSIS_TIMEOUT_SECONDS=300

# ML Models (mount persistent volume)
MODELS_CACHE_PATH=/app/models_cache

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Optional: API keys for LLM features
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend Environment Variables

Create `frontend/.env` for production:

```bash
# Backend API URL (use production domain)
VITE_API_URL=https://api.your-production-domain.com

# Application
VITE_APP_TITLE=Resume Analysis Platform

# Feature flags
VITE_ENABLE_ANALYTICS=true
```

## Database Setup

### Managed PostgreSQL (Recommended)

**AWS RDS**:
- Use Multi-AZ deployment for high availability
- Enable automated backups
- Configure read replicas for scaling reads
- Use Parameter Groups for PostgreSQL optimization

**Google Cloud SQL**:
- Enable high availability (HA)
- Configure automated backups
- Use connection pooling (Cloud SQL Proxy)

**Azure Database for PostgreSQL**:
- Use Hyperscale (Citus) for scaling
- Enable Geo-Replication for disaster recovery

### Self-Managed PostgreSQL

```bash
# Install PostgreSQL 14
sudo apt install postgresql-14

# Create database and user
sudo -u postgres psql
CREATE DATABASE resume_analysis;
CREATE USER resume_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE resume_analysis TO resume_user;

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Optimized settings:
```conf
# Memory
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB

# Connections
max_connections = 200

# Write-ahead log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query planning
random_page_cost = 1.1
```

### Database Backups

```bash
# Automated daily backup
0 2 * * * pg_dump -U resume_user resume_analysis | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip < /backups/db_20240124.sql.gz | psql -U resume_user resume_analysis
```

## Monitoring & Logging

### Application Monitoring

**Prometheus + Grafana**:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Key Metrics to Monitor**:
- Request rate and latency
- Error rate by endpoint
- Celery task queue length
- Database connection pool usage
- Memory and CPU usage
- Disk I/O

### Logging

**ELK Stack (Elasticsearch, Logstash, Kibana)**:

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

### Health Checks

```bash
# Backend health endpoint
curl http://localhost:8000/health

# Database connectivity
docker-compose exec backend pg_isready -U resume_user

# Redis connectivity
docker-compose exec backend redis-cli -h redis ping

# Celery worker status
docker-compose exec backend celery -A tasks inspect ping
```

## Security Considerations

### 1. Authentication & Authorization

Before production deployment, implement authentication:

```python
# Add JWT authentication to backend
# backend/api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Validate JWT token
    if not validate_jwt(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token
```

### 2. File Upload Security

```python
# Validate file types using magic numbers
ALLOWED_MAGIC_NUMBERS = {
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def validate_file_magic(file_content: bytes) -> bool:
    for magic, mime_type in ALLOWED_MAGIC_NUMBERS.items():
        if file_content.startswith(magic):
            return True
    return False
```

### 3. Rate Limiting

```python
# Add rate limiting with slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/resumes/upload")
@limiter.limit("10/minute")
async def upload_resume(...):
    ...
```

### 4. HTTPS Only

- Force HTTPS in production
- Use HSTS headers
- Secure cookies with `Secure` and `HttpOnly` flags

### 5. Secrets Management

Use AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name prod/resume-analysis/db-password \
  --secret-string "secure_password"

# Access in application
import boto3
import json

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='prod/resume-analysis/db-password')
password = json.loads(response['SecretString'])
```

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale backend containers
docker-compose up -d --scale backend=3 --scale celery_worker=3

# Kubernetes deployment
kubectl scale deployment/backend --replicas=3
kubectl scale deployment/celery-worker --replicas=3
```

### Database Scaling

- **Read Replicas**: Offload read queries to replicas
- **Connection Pooling**: Use PgBouncer for connection pooling
- **Caching**: Cache frequently accessed data in Redis

### Celery Worker Scaling

```python
# Configure Celery for high throughput
# backend/celery_config.py
broker_transport_options = {
    'max_retries': 3,
    'retry_policy': {
        'timeout': 5.0
    }
}

worker_prefetch_multiplier = 4
task_acks_late = True
worker_max_tasks_per_child = 1000
```

## Backup & Recovery

### Database Backups

```bash
# Automated daily backup script
#!/bin/bash
# /usr/local/bin/backup-db.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="resume_analysis_${DATE}.sql.gz"

pg_dump -U resume_user resume_analysis | gzip > ${BACKUP_DIR}/${FILENAME}

# Keep last 30 days
find ${BACKUP_DIR} -name "resume_analysis_*.sql.gz" -mtime +30 -delete
```

### Disaster Recovery

1. **Multi-region deployment**: Deploy to multiple AWS/Azure regions
2. **Database replication**: Use cross-region read replicas
3. **Backup to cloud storage**: S3, GCS, or Azure Blob Storage
4. **Infrastructure as Code**: Use Terraform or CloudFormation

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify connectivity
docker-compose exec backend pg_isready -U postgres

# Restart database
docker-compose restart postgres
```

#### 2. Celery Worker Not Processing Tasks

```bash
# Check worker status
docker-compose logs celery_worker

# Verify Redis connection
docker-compose exec backend redis-cli -h redis ping

# Restart worker
docker-compose restart celery_worker
```

#### 3. High Memory Usage

```bash
# Monitor memory usage
docker stats

# Reduce Celery concurrency
# In docker-compose.yml:
command: celery -A tasks worker --loglevel=info --concurrency=1

# Limit memory in containers
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

#### 4. Slow Analysis Performance

```bash
# Add more Celery workers
docker-compose up -d --scale celery_worker=4

# Use faster ML models
# Download larger SpaCy models for better accuracy (not speed)
python -m spacy download en_core_web_md

# Cache ML models in memory (already implemented in keyword_extractor.py)
```

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f backend
```

## Performance Optimization

### 1. Use Caching

```python
# Cache analysis results
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

FastAPICache.init(RedisBackend(redis), prefix="resume-api")
```

### 2. Optimize Database Queries

```python
# Use select_in/load optimizing for SQLAlchemy
from sqlalchemy.orm import selectinload

query = (
    select(Resume)
    .options(selectinload(Resume.analysis_result))
    .where(Resume.id == resume_id)
)
```

### 3. Enable Compression

```python
# Enable gzip compression in FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Cost Optimization

### AWS Cost Savings

- Use Reserved Instances for long-running workloads
- Enable Spot Instances for Celery workers
- Use S3 Glacier for old backups
- Set up billing alerts

### GCP Cost Savings

- Use Preemptible VMs for Celery workers
- Enable Committed Use Discounts
- Use Coldline storage for old backups

### General Tips

- Monitor resource usage and right-size instances
- Use auto-scaling to pay for what you use
- Clean up unused resources regularly
- Use cost allocation tags

---

For additional help, refer to:
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [API Documentation](http://localhost:8000/docs)
- [GitHub Issues](https://github.com/your-repo/issues)
