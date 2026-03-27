# AgentHR Deployment Guide

Complete deployment guide for AgentHR - AI-powered resume analysis and candidate ranking system.

## Table of Contents

- [Overview](#overview)
- [One-Click Cloud Deployments](#one-click-cloud-deployments)
  - [DigitalOcean App Platform](#digitalocean-app-platform)
  - [AWS Marketplace](#aws-marketplace)
- [Docker Deployment](#docker-deployment)
  - [Quick Start](#quick-start)
  - [Docker Profiles](#docker-profiles)
  - [Environment-Specific Deployments](#environment-specific-deployments)
- [Kubernetes/Helm Deployment](#kuberneteshelm-deployment)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Scaling](#scaling)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

AgentHR supports multiple deployment strategies:

- **Cloud Platforms**: One-click deployments to DigitalOcean and AWS Marketplace
- **Docker Compose**: For local development, testing, and single-server deployments
- **Kubernetes/Helm**: For production-grade, scalable cloud deployments

### Architecture Components

| Component | Purpose | Required |
|-----------|---------|----------|
| PostgreSQL | Primary database | ✅ Yes |
| Redis | Celery broker & cache | ✅ Yes |
| Backend (FastAPI) | REST API server | ✅ Yes |
| Frontend (React) | Web UI | ✅ Yes |
| Celery Worker | Async task processing | ⚠️ Recommended |
| Celery Beat | Scheduled tasks | ⚠️ Recommended |
| Grafana | Monitoring dashboards | ❌ Optional |
| Loki | Log aggregation | ❌ Optional |
| Prometheus | Metrics collection | ❌ Optional |

---

## One-Click Cloud Deployments

Deploy AgentHR to production-ready cloud platforms with minimal configuration. These deployment options include managed databases, automatic scaling, and built-in monitoring.

### DigitalOcean App Platform

Deploy AgentHR to DigitalOcean's fully-managed App Platform with one click:

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/Soinex-Inc/agenthr/tree/main&refcode=agenthr)

**What's Included:**
- ✅ Managed PostgreSQL database (v15)
- ✅ Managed Redis cluster (v7)
- ✅ Automatic SSL/TLS certificates
- ✅ Built-in load balancing
- ✅ Automatic scaling (backend & workers)
- ✅ Zero-downtime deployments
- ✅ Built-in monitoring & logs

**Estimated Cost**: ~$299/month for production deployment (see [DigitalOcean pricing guide](./cloud/digitalocean/README.md#cost-estimation))

**Configuration Guide**: See [./cloud/digitalocean/README.md](./cloud/digitalocean/README.md) for:
- Pre-deployment checklist
- Environment variable configuration
- Post-deployment setup
- Scaling recommendations
- Troubleshooting

### AWS Marketplace

Deploy AgentHR on AWS using CloudFormation for enterprise-grade infrastructure:

**[Launch CloudFormation Stack](./cloud/aws/marketplace.yaml)** | **[📖 Detailed AWS Guide](./cloud/aws/README.md)**

**What's Included:**
- ✅ VPC with public/private subnets
- ✅ RDS PostgreSQL Multi-AZ
- ✅ ElastiCache Redis with failover
- ✅ Application Load Balancer
- ✅ EC2 instance with Docker Compose
- ✅ S3 backup bucket with lifecycle policies
- ✅ CloudWatch alarms & monitoring
- ✅ AWS Secrets Manager integration

**Estimated Cost**: ~$450/month for production deployment (see [AWS pricing guide](./cloud/aws/README.md#cost-estimation))

**Deployment Steps:**

1. **Download the CloudFormation template:**
   ```bash
   curl -O https://raw.githubusercontent.com/Soinex-Inc/agenthr/main/cloud/aws/marketplace.yaml
   ```

2. **Deploy via AWS Console:**
   - Navigate to CloudFormation → Create Stack
   - Upload `marketplace.yaml`
   - Fill in parameters (database password, key pair, etc.)
   - Review and create

3. **Or deploy via AWS CLI:**
   ```bash
   aws cloudformation create-stack \
     --stack-name agenthr-production \
     --template-body file://marketplace.yaml \
     --parameters \
       ParameterKey=Environment,ParameterValue=production \
       ParameterKey=DBPassword,ParameterValue=your-secure-password \
       ParameterKey=KeyPairName,ParameterValue=your-key-pair \
     --capabilities CAPABILITY_IAM
   ```

4. **Monitor deployment:**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name agenthr-production \
     --query 'Stacks[0].StackStatus'
   ```

**Configuration Guide**: See [./cloud/aws/README.md](./cloud/aws/README.md) for complete deployment instructions, troubleshooting, and production best practices.

---

## Docker Deployment

### Quick Start

**1. Clone and navigate to project:**

```bash
git clone https://github.com/Soinex-Inc/agenthr.git
cd agenthr
```

**2. Copy environment file:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

**3. Start services (default profile):**

```bash
# Start minimal services (fastest startup)
docker-compose up -d

# Or with full monitoring stack
docker-compose --profile full up -d
```

**4. Verify services are running:**

```bash
docker-compose ps
```

**5. Load test data (optional):**

```bash
docker-compose exec backend python scripts/reset_and_reload.py
```

### Docker Profiles

AgentHR uses Docker Compose profiles to control which services run. Choose based on your needs:

#### Profile Comparison

| Profile | Services | Use Case | RAM Required |
|---------|----------|----------|--------------|
| **minimal** | postgres, redis, backend, frontend | Quick testing, minimal resources | ~4GB |
| **core** | minimal + celery_worker, celery_beat | Development, async processing | ~8GB |
| **full** | core + grafana, loki, prometheus, exporters | Production-like, full monitoring | ~16GB |

#### Minimal Profile

**Services:** Database, Redis, Backend API, Frontend only

```bash
docker-compose --profile minimal up -d
```

**Best for:**
- Quick testing
- Frontend development
- CI/CD pipelines
- Resource-constrained environments

**Limitations:**
- No async resume analysis
- No scheduled backups
- No monitoring/observability

#### Core Profile

**Services:** All minimal + Celery Worker, Celery Beat

```bash
docker-compose --profile core up -d
```

**Best for:**
- Full development environment
- Backend development
- Testing async workflows
- Staging environments

**Features:**
- ✅ Async resume analysis
- ✅ Background job processing
- ✅ Scheduled backups
- ✅ ML model caching
- ❌ No built-in monitoring

#### Full Profile

**Services:** All core + Grafana, Loki, Prometheus, Promtail, Exporters, cAdvisor

```bash
docker-compose --profile full up -d
```

**Best for:**
- Production deployments
- Performance testing
- Monitoring & alerting
- Production debugging

**Features:**
- ✅ Complete observability stack
- ✅ Real-time metrics & logs
- ✅ Pre-configured dashboards
- ✅ Container metrics
- ✅ Database metrics
- ✅ Celery metrics

**Access URLs (Full Profile):**

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Loki | http://localhost:3100 | - |

### Environment-Specific Deployments

AgentHR provides environment-specific configurations for development, staging, and production.

#### Development

**Features:**
- Hot-reload enabled
- Debug logging
- Source code mounted
- Lower resource limits

```bash
# Use development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile core up -d
```

**Environment file:**

```bash
cp .env.dev.example .env.dev
```

**Key Settings:**
- `LOG_LEVEL=DEBUG`
- `ENVIRONMENT=development`
- Code changes reload automatically
- Faster startup times

#### Staging

**Features:**
- Production-like build
- Moderate resource allocation
- Info-level logging
- No source mounts

```bash
# Use staging environment
docker-compose -f docker-compose.yml -f docker-compose.staging.yml --profile full up -d
```

**Environment file:**

```bash
cp .env.staging.example .env.staging
```

**Key Settings:**
- `LOG_LEVEL=INFO`
- `ENVIRONMENT=staging`
- Production Docker builds
- Moderate concurrency

#### Production

**Features:**
- Optimized builds
- Maximum resource allocation
- Warning-level logging
- Auto-restart policies
- Multi-worker processes

```bash
# Use production environment
docker-compose -f docker-compose.yml -f docker-compose.production.yml --profile full up -d
```

**Environment file:**

```bash
cp .env.production.example .env.production
# IMPORTANT: Change all default passwords and secrets!
```

**Key Settings:**
- `LOG_LEVEL=WARNING`
- `ENVIRONMENT=production`
- 4 uvicorn workers
- Auto-restart on failure
- Redis persistence enabled
- Higher Celery concurrency

**Production Checklist:**

- [ ] Change all default passwords (PostgreSQL, Grafana, etc.)
- [ ] Set secure `POSTGRES_PASSWORD`
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup retention policy
- [ ] Configure S3 backup (optional)
- [ ] Set up email alerts (`ALERT_EMAIL_ADDRESS`)
- [ ] Configure webhook alerts (optional)
- [ ] Review resource limits for your hardware
- [ ] Set up external secret management
- [ ] Configure reverse proxy (nginx/traefik)

---

## Kubernetes/Helm Deployment

For production-scale deployments on Kubernetes.

### Prerequisites

**Required:**
- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.x installed
- Minimum: 3 nodes with 8GB RAM each

**Optional:**
- Ingress controller (nginx, traefik)
- Cert-manager for SSL
- External secrets operator
- Monitoring stack (if not using built-in)

### Installation

**1. Add Helm dependencies:**

```bash
cd helm/agenthr

# Update dependencies (PostgreSQL, Redis from Bitnami)
helm dependency update
```

**2. Create namespace:**

```bash
kubectl create namespace agenthr
```

**3. Create secrets:**

```bash
# Create secret for sensitive data
kubectl create secret generic agenthr-secrets \
  --from-literal=postgres-password=your_secure_password \
  --from-literal=openai-api-key=your_openai_key \
  --from-literal=anthropic-api-key=your_anthropic_key \
  --namespace agenthr
```

**4. Install with default values:**

```bash
# Basic installation
helm install agenthr . --namespace agenthr

# Or with custom values
helm install agenthr . \
  --namespace agenthr \
  --values values.yaml \
  --set postgresql.auth.password=your_secure_password
```

**5. Verify deployment:**

```bash
# Check pod status
kubectl get pods -n agenthr

# Check services
kubectl get svc -n agenthr

# View logs
kubectl logs -n agenthr -l app.kubernetes.io/name=agenthr-backend
```

### Configuration

#### Custom Values File

Create `values-production.yaml`:

```yaml
# Production configuration example

# Backend API scaling
backend:
  replicaCount: 3
  resources:
    requests:
      cpu: 2000m
      memory: 4Gi
    limits:
      cpu: 4000m
      memory: 8Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Celery worker scaling
celeryWorker:
  replicaCount: 2
  resources:
    requests:
      cpu: 3000m
      memory: 6Gi
    limits:
      cpu: 6000m
      memory: 12Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 8

# PostgreSQL (using Bitnami chart)
postgresql:
  enabled: true
  auth:
    password: "use-secret-here"
    existingSecret: "agenthr-secrets"
  primary:
    persistence:
      size: 50Gi
      storageClass: "fast-ssd"
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi

# Redis (using Bitnami chart)
redis:
  enabled: true
  master:
    persistence:
      size: 10Gi
      storageClass: "fast-ssd"

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
  hosts:
    - host: agenthr.example.com
      paths:
        - path: /api
          pathType: Prefix
          backend:
            service:
              name: backend
              port: 8000
        - path: /
          pathType: Prefix
          backend:
            service:
              name: frontend
              port: 5173
  tls:
    - secretName: agenthr-tls
      hosts:
        - agenthr.example.com

# Persistent storage
persistence:
  modelsCache:
    size: 100Gi
    storageClass: "standard"
  uploads:
    size: 50Gi
  backups:
    size: 200Gi
```

**Deploy with custom values:**

```bash
helm upgrade --install agenthr . \
  --namespace agenthr \
  --values values-production.yaml
```

### Scaling

#### Manual Scaling

```bash
# Scale backend API
kubectl scale deployment agenthr-backend --replicas=5 -n agenthr

# Scale Celery workers
kubectl scale deployment agenthr-celery-worker --replicas=4 -n agenthr
```

#### Horizontal Pod Autoscaling (HPA)

Enable autoscaling in `values.yaml`:

```yaml
backend:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

**Verify HPA:**

```bash
kubectl get hpa -n agenthr
```

#### Update Deployment

```bash
# Update with new values
helm upgrade agenthr . --namespace agenthr --values values-production.yaml

# Rollback if needed
helm rollback agenthr -n agenthr
```

#### Uninstall

```bash
helm uninstall agenthr -n agenthr
```

---

## Environment Configuration

### Required Environment Variables

**Database:**
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=resume_analysis
DATABASE_URL=postgresql://user:pass@postgres:5432/resume_analysis
```

**Redis:**
```bash
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**Backend:**
```bash
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**Frontend:**
```bash
FRONTEND_PORT=5173
FRONTEND_URL=http://localhost:5173
```

### Optional Environment Variables

**AI/LLM Features:**
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Backup Configuration:**
```bash
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=agenthr-backups
BACKUP_S3_ENDPOINT=s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=your_key
BACKUP_S3_SECRET_KEY=your_secret
BACKUP_S3_REGION=us-east-1
```

**Monitoring & Alerts:**
```bash
ALERT_EMAIL_ADDRESS=alerts@example.com
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptom:** Containers exit immediately or fail health checks

**Check logs:**
```bash
# View all logs
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f backend
```

**Common causes:**
- Database not ready yet (wait 30-60 seconds)
- Port conflicts (another service using 5432, 6379, 8000, or 3000)
- Insufficient memory/CPU resources
- Missing environment variables

**Solutions:**
```bash
# Check service health
docker-compose ps

# Restart specific service
docker-compose restart backend

# Rebuild if code/config changed
docker-compose up -d --build backend
```

#### 2. Out of Memory Errors

**Symptom:** `Killed` messages in logs, containers restarting

**Check resource usage:**
```bash
docker stats
```

**Solutions:**
- Reduce Docker Compose profile (full → core → minimal)
- Increase Docker Desktop memory allocation
- Adjust resource limits in docker-compose.yml
- Reduce Celery worker concurrency

**Adjust Celery concurrency:**
```bash
# In .env file
docker-compose exec celery_worker celery -A celery_app.celery_app inspect active
```

**Edit docker-compose.yml:**
```yaml
celery_worker:
  command: celery -A celery_app.celery_app worker --concurrency=2  # Reduce from 4
```

#### 3. Database Connection Errors

**Symptom:** `could not connect to server` or `connection refused`

**Check PostgreSQL:**
```bash
# Is PostgreSQL running?
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec backend psql $DATABASE_URL -c "SELECT 1"
```

**Common solutions:**
```bash
# Wait for PostgreSQL to be ready
docker-compose up -d postgres
sleep 30
docker-compose up -d backend

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

#### 4. Frontend Can't Reach Backend

**Symptom:** API calls fail with network errors

**Check configuration:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS settings
docker-compose logs backend | grep CORS
```

**Solution:**
```bash
# In .env file, ensure:
FRONTEND_URL=http://localhost:3000

# Restart backend
docker-compose restart backend
```

#### 5. Models Taking Too Long to Download

**Symptom:** First startup very slow, backend timing out

**Explanation:** Hugging Face models (~2-4GB) download on first run

**Solution:**
```bash
# Pre-download models
docker-compose exec backend python -c "
from transformers import AutoTokenizer, AutoModel
AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
"

# Or use persistent volume (already configured)
# Models cache to: backend_models volume
```

#### 6. Celery Tasks Not Processing

**Symptom:** Jobs stuck in queue, not completing

**Check Celery worker:**
```bash
# Is worker running?
docker-compose ps celery_worker

# Check worker status
docker-compose exec celery_worker celery -A celery_app.celery_app inspect active

# View worker logs
docker-compose logs celery_worker
```

**Common solutions:**
```bash
# Restart worker
docker-compose restart celery_worker

# Check Redis connection
docker-compose exec celery_worker redis-cli -h redis ping

# Purge stuck tasks (WARNING: clears queue)
docker-compose exec celery_worker celery -A celery_app.celery_app purge
```

#### 7. Grafana Dashboards Not Loading

**Symptom:** Grafana shows no data or connection errors

**Check data sources:**
```bash
# Are Prometheus/Loki running?
docker-compose ps prometheus loki

# Test Prometheus
curl http://localhost:9090/-/healthy

# Test Loki
curl http://localhost:3100/ready
```

**Solutions:**
```bash
# Restart monitoring stack
docker-compose restart grafana prometheus loki

# Re-provision dashboards
docker-compose exec grafana grafana-cli admin reset-admin-password admin
```

#### 8. Port Already in Use

**Symptom:** `Bind for 0.0.0.0:XXXX failed: port is already allocated`

**Find what's using the port:**
```bash
# On macOS/Linux
lsof -i :8000
lsof -i :5432

# On Linux
netstat -tulpn | grep 8000
```

**Solutions:**
- Stop conflicting service
- Or change port in .env file:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

#### 9. Kubernetes Pod Crashes

**Symptom:** Pods in `CrashLoopBackOff` state

**Diagnose:**
```bash
# Check pod status
kubectl get pods -n agenthr

# View pod logs
kubectl logs -n agenthr <pod-name>

# Describe pod for events
kubectl describe pod -n agenthr <pod-name>

# Check resource constraints
kubectl top pods -n agenthr
```

**Common causes:**
- Insufficient resources (CPU/memory limits too low)
- Missing secrets or ConfigMaps
- Database not ready
- Image pull errors

**Solutions:**
```bash
# Increase resources in values.yaml
# Check secrets exist
kubectl get secrets -n agenthr

# Verify ConfigMaps
kubectl get configmap -n agenthr

# Force recreate pod
kubectl delete pod -n agenthr <pod-name>
```

#### 10. Helm Installation Fails

**Symptom:** `helm install` errors

**Common errors:**

**Missing dependencies:**
```bash
cd helm/agenthr
helm dependency update
helm dependency build
```

**Invalid values:**
```bash
# Validate values file
helm lint . --values values-production.yaml

# Dry-run to see what would be created
helm install agenthr . --dry-run --debug --namespace agenthr
```

**Existing resources:**
```bash
# Release already exists
helm list -n agenthr
helm uninstall agenthr -n agenthr

# Or upgrade instead
helm upgrade --install agenthr . -n agenthr
```

### Performance Optimization

#### Speed Up Development Startup

```bash
# Use minimal profile
docker-compose --profile minimal up -d

# Skip logs/monitoring
docker-compose up -d postgres redis backend frontend
```

#### Optimize for Production

**In docker-compose.production.yml:**
- Multi-worker backend (4 uvicorn workers)
- Higher Celery concurrency
- Redis persistence enabled
- Auto-restart policies

**In Kubernetes:**
- Enable HPA (Horizontal Pod Autoscaling)
- Use node affinity for database pods
- Configure resource requests accurately
- Use ReadWriteMany volumes for shared storage

### Health Checks

**Backend health:**
```bash
curl http://localhost:8000/health
```

**Database health:**
```bash
docker-compose exec postgres pg_isready
```

**Redis health:**
```bash
docker-compose exec redis redis-cli ping
```

**All services:**
```bash
docker-compose ps
```

### Getting Help

**Check logs:**
```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl logs -n agenthr -l app=agenthr --tail=100 -f
```

**Common log locations:**
- Backend: `docker-compose logs backend`
- Celery: `docker-compose logs celery_worker`
- Database: `docker-compose logs postgres`
- Grafana: http://localhost:3001 (Explore → Loki)

**Community Resources:**
- GitHub Issues: https://github.com/yourusername/agenthr/issues
- API Documentation: http://localhost:8000/docs
- Grafana Dashboards: http://localhost:3001

---

## Next Steps

- **Development:** See [README.md](./README.md) for development guide
- **API Reference:** Visit http://localhost:8000/docs
- **Monitoring:** Configure alerts in Grafana
- **Backups:** Set up S3 backup in production
- **Security:** Review security checklist for production deployments
