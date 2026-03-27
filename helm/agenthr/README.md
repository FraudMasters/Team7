# AgentHR Helm Chart

Kubernetes Helm chart for deploying AgentHR - AI-powered resume analysis and HR automation platform.

## Overview

This Helm chart deploys a complete AgentHR stack including:

- **Backend API** (FastAPI) - Resume analysis and matching engine
- **Frontend** (React + MUI) - User interface
- **Celery Worker** - Async task processing for ML operations
- **Celery Beat** - Scheduled task orchestration
- **PostgreSQL** - Primary database (via Bitnami chart)
- **Redis** - Message broker and cache (via Bitnami chart)
- **Persistent Storage** - Model cache, uploads, and backups

## Prerequisites

### Required

- **Kubernetes** 1.20+ cluster
- **Helm** 3.8+ installed
- **kubectl** configured for your cluster
- **8GB RAM** minimum per node (16GB recommended)
- **20GB disk space** for persistent volumes

### Recommended

- **Ingress Controller** (nginx-ingress) for external access
- **cert-manager** for TLS certificate management
- **StorageClass** with dynamic provisioning
- **Monitoring** stack (Prometheus/Grafana) for observability

### Verify Prerequisites

```bash
# Check Kubernetes version
kubectl version --short

# Check Helm version
helm version --short

# Verify cluster access
kubectl cluster-info

# Check available storage classes
kubectl get storageclass
```

## Quick Start

### 1. Add Bitnami Repository

The chart depends on Bitnami's PostgreSQL and Redis charts:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2. Install the Chart

```bash
# Create namespace
kubectl create namespace agenthr

# Install with default values
helm install agenthr ./helm/agenthr --namespace agenthr

# Or install from packaged chart
helm install agenthr agenthr-1.0.0.tgz --namespace agenthr
```

### 3. Wait for Deployment

```bash
# Watch pod status
kubectl get pods -n agenthr -w

# Check deployment status
helm status agenthr -n agenthr
```

### 4. Access the Application

#### Port Forward (Development)

```bash
# Frontend
kubectl port-forward -n agenthr svc/agenthr-frontend 5173:5173

# Backend API
kubectl port-forward -n agenthr svc/agenthr-backend 8000:8000
```

Then access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Ingress (Production)

Enable ingress in your values file (see Configuration section).

## Installation Options

### Install with Custom Values

```bash
# Using custom values file
helm install agenthr ./helm/agenthr \
  --namespace agenthr \
  --values custom-values.yaml

# Override specific values
helm install agenthr ./helm/agenthr \
  --namespace agenthr \
  --set backend.replicaCount=2 \
  --set postgresql.auth.password=secure_password \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=agenthr.example.com
```

### Install with External Database

If you have an existing PostgreSQL database:

```bash
helm install agenthr ./helm/agenthr \
  --namespace agenthr \
  --set postgresql.enabled=false \
  --set secrets.databaseUrl="postgresql://user:pass@host:5432/dbname"
```

### Install with External Redis

If you have an existing Redis instance:

```bash
helm install agenthr ./helm/agenthr \
  --namespace agenthr \
  --set redis.enabled=false \
  --set secrets.redisUrl="redis://redis-host:6379/0"
```

## Configuration

### Basic Configuration

Create a `values.yaml` file to customize your deployment:

```yaml
# custom-values.yaml
backend:
  replicaCount: 2
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi

frontend:
  replicaCount: 2

celeryWorker:
  replicaCount: 3
  concurrency: 4

postgresql:
  auth:
    password: "your-secure-password"
  primary:
    persistence:
      size: 20Gi

redis:
  auth:
    enabled: true
    password: "your-redis-password"

ingress:
  enabled: true
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
```

### Configuration Parameters

#### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.storageClass` | Global storage class for PVCs | `""` (default) |
| `image.registry` | Global container registry | `docker.io` |
| `image.pullPolicy` | Global image pull policy | `IfNotPresent` |

#### Backend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend deployment | `true` |
| `backend.replicaCount` | Number of backend replicas | `1` |
| `backend.image.repository` | Backend image repository | `agenthr/backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.service.type` | Service type | `ClusterIP` |
| `backend.service.port` | Service port | `8000` |
| `backend.resources.limits.cpu` | CPU limit | `4000m` |
| `backend.resources.limits.memory` | Memory limit | `8Gi` |
| `backend.autoscaling.enabled` | Enable HPA | `false` |
| `backend.autoscaling.minReplicas` | Min replicas for HPA | `1` |
| `backend.autoscaling.maxReplicas` | Max replicas for HPA | `5` |

#### Frontend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.enabled` | Enable frontend deployment | `true` |
| `frontend.replicaCount` | Number of frontend replicas | `1` |
| `frontend.image.repository` | Frontend image repository | `agenthr/frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `frontend.service.port` | Service port | `5173` |
| `frontend.resources.limits.cpu` | CPU limit | `1000m` |
| `frontend.resources.limits.memory` | Memory limit | `1Gi` |

#### Celery Worker Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `celeryWorker.enabled` | Enable Celery worker | `true` |
| `celeryWorker.replicaCount` | Number of worker replicas | `1` |
| `celeryWorker.concurrency` | Worker concurrency | `4` |
| `celeryWorker.queues` | Comma-separated queue names | `celery,analysis,learning,reporting` |
| `celeryWorker.resources.limits.cpu` | CPU limit | `6000m` |
| `celeryWorker.resources.limits.memory` | Memory limit | `12Gi` |
| `celeryWorker.autoscaling.enabled` | Enable HPA | `false` |

#### Celery Beat Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `celeryBeat.enabled` | Enable Celery beat scheduler | `true` |
| `celeryBeat.replicaCount` | Number of beat replicas (keep at 1) | `1` |
| `celeryBeat.resources.limits.cpu` | CPU limit | `1000m` |
| `celeryBeat.resources.limits.memory` | Memory limit | `512Mi` |

#### PostgreSQL Configuration (Bitnami)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL dependency | `true` |
| `postgresql.auth.username` | Database username | `postgres` |
| `postgresql.auth.password` | Database password | `postgres` |
| `postgresql.auth.database` | Database name | `resume_analysis` |
| `postgresql.primary.persistence.size` | PVC size | `10Gi` |
| `postgresql.primary.resources.limits.cpu` | CPU limit | `2000m` |
| `postgresql.primary.resources.limits.memory` | Memory limit | `2Gi` |

See [Bitnami PostgreSQL Chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql) for all options.

#### Redis Configuration (Bitnami)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis dependency | `true` |
| `redis.auth.enabled` | Enable Redis authentication | `false` |
| `redis.master.persistence.size` | PVC size | `2Gi` |
| `redis.master.resources.limits.cpu` | CPU limit | `1000m` |
| `redis.master.resources.limits.memory` | Memory limit | `1Gi` |

See [Bitnami Redis Chart](https://github.com/bitnami/charts/tree/main/bitnami/redis) for all options.

#### Persistence Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.modelsCache.enabled` | Enable models cache PVC | `true` |
| `persistence.modelsCache.size` | Models cache size | `20Gi` |
| `persistence.uploads.enabled` | Enable uploads PVC | `true` |
| `persistence.uploads.size` | Uploads size | `10Gi` |
| `persistence.backups.enabled` | Enable backups PVC | `true` |
| `persistence.backups.size` | Backups size | `50Gi` |

#### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `agenthr.example.com` |
| `ingress.tls[0].secretName` | TLS secret name | `agenthr-tls` |

#### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.logLevel` | Logging level | `INFO` |
| `config.logFormat` | Log format (json/text) | `json` |
| `config.maxUploadSizeMb` | Max upload size | `10` |
| `config.allowedFileTypes` | Allowed file extensions | `.pdf,.docx` |
| `config.backupEnabled` | Enable automated backups | `true` |
| `config.backupRetentionDays` | Backup retention period | `30` |
| `config.backupSchedule` | Backup cron schedule | `0 2 * * *` |

#### Secrets Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.databaseUrl` | External database URL | `""` |
| `secrets.redisUrl` | External Redis URL | `""` |
| `secrets.openaiApiKey` | OpenAI API key (optional) | `""` |
| `secrets.anthropicApiKey` | Anthropic API key (optional) | `""` |
| `secrets.backupS3Bucket` | S3 bucket for backups | `""` |
| `secrets.backupS3AccessKey` | S3 access key | `""` |
| `secrets.backupS3SecretKey` | S3 secret key | `""` |

**⚠️ Security Note:** Never commit secrets to version control. Use Kubernetes secrets, external secret managers (Vault, AWS Secrets Manager), or sealed secrets.

## Production Deployment

### Production Checklist

- [ ] Change all default passwords
- [ ] Enable ingress with TLS
- [ ] Configure resource limits based on load testing
- [ ] Enable autoscaling for backend and workers
- [ ] Set up external secret management
- [ ] Configure S3 backups
- [ ] Enable monitoring and alerting
- [ ] Configure node affinity and pod anti-affinity
- [ ] Test disaster recovery procedures
- [ ] Document runbook procedures

### Production Values Example

```yaml
# production-values.yaml

# High availability configuration
backend:
  replicaCount: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi

frontend:
  replicaCount: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5

celeryWorker:
  replicaCount: 5
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
  concurrency: 4

# Production database
postgresql:
  auth:
    password: "CHANGE_ME_SECURE_PASSWORD"
    existingSecret: "postgres-credentials"
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: "fast-ssd"
    resources:
      limits:
        cpu: 4000m
        memory: 4Gi
      requests:
        cpu: 2000m
        memory: 2Gi

# Production Redis
redis:
  auth:
    enabled: true
    password: "CHANGE_ME_REDIS_PASSWORD"
    existingSecret: "redis-credentials"
  master:
    persistence:
      enabled: true
      size: 10Gi
      storageClass: "fast-ssd"

# Larger persistent volumes
persistence:
  modelsCache:
    enabled: true
    size: 50Gi
    storageClass: "fast-ssd"
  uploads:
    enabled: true
    size: 100Gi
    storageClass: "standard"
  backups:
    enabled: true
    size: 200Gi
    storageClass: "standard"

# Production ingress
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: agenthr.yourcompany.com
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
    - secretName: agenthr-prod-tls
      hosts:
        - agenthr.yourcompany.com

# Production configuration
config:
  logLevel: INFO
  logFormat: json
  backupEnabled: "true"
  backupS3Enabled: "true"

# Use external secrets (recommended)
secrets:
  # Reference existing secrets instead of inline values
  # Create these separately with kubectl create secret
  openaiApiKey: ""  # Use existingSecret instead
  backupS3Bucket: "agenthr-backups-prod"
  backupS3Region: "us-east-1"

# Pod anti-affinity for high availability
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - agenthr
          topologyKey: kubernetes.io/hostname
```

## Upgrade Process

### Upgrade the Chart

```bash
# Update Helm repositories
helm repo update

# Check what will change
helm diff upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --values production-values.yaml

# Perform upgrade
helm upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --values production-values.yaml \
  --timeout 10m
```

### Rolling Updates

```bash
# Update just the backend image
helm upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --reuse-values \
  --set backend.image.tag=v1.0.1

# Update with zero downtime
helm upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --values production-values.yaml \
  --wait \
  --timeout 15m
```

### Rollback

```bash
# View release history
helm history agenthr -n agenthr

# Rollback to previous version
helm rollback agenthr -n agenthr

# Rollback to specific revision
helm rollback agenthr 3 -n agenthr
```

### Database Migrations

The backend automatically runs database migrations on startup. For major version upgrades:

```bash
# Backup database first
kubectl exec -n agenthr deployment/agenthr-backend -- \
  python scripts/backup_database.py

# Then proceed with upgrade
helm upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --values production-values.yaml
```

## Uninstallation

### Delete the Release

```bash
# Uninstall chart (keeps PVCs by default)
helm uninstall agenthr -n agenthr
```

### Clean Up Persistent Volumes

**⚠️ Warning:** This will delete all data including database, uploads, and model cache!

```bash
# Delete PVCs
kubectl delete pvc -n agenthr -l app.kubernetes.io/instance=agenthr

# Delete namespace (removes everything)
kubectl delete namespace agenthr
```

### Backup Before Uninstall

```bash
# Backup database
kubectl exec -n agenthr deployment/agenthr-backend -- \
  python scripts/backup_database.py

# Or create a PVC snapshot (if supported by your storage class)
kubectl get pvc -n agenthr
# Use your cloud provider's snapshot tooling
```

## Troubleshooting

### Check Pod Status

```bash
# View all pods
kubectl get pods -n agenthr

# Describe problematic pod
kubectl describe pod -n agenthr <pod-name>

# View logs
kubectl logs -n agenthr <pod-name>

# Follow logs
kubectl logs -n agenthr <pod-name> -f

# View previous container logs (if crashed)
kubectl logs -n agenthr <pod-name> --previous
```

### Common Issues

#### Pods in Pending State

```bash
# Check events
kubectl get events -n agenthr --sort-by='.lastTimestamp'

# Check PVC status
kubectl get pvc -n agenthr

# Common causes:
# - Insufficient resources
# - PVC not bound (no storage class or insufficient disk)
# - Image pull errors
```

#### Backend Fails to Start

```bash
# Check backend logs
kubectl logs -n agenthr deployment/agenthr-backend

# Common causes:
# - Database connection failed (check PostgreSQL)
# - Redis connection failed
# - Missing secrets
# - Database migrations failed
```

#### Celery Worker Issues

```bash
# Check worker logs
kubectl logs -n agenthr deployment/agenthr-celery-worker

# Check Redis connectivity
kubectl exec -n agenthr deployment/agenthr-backend -- \
  redis-cli -h agenthr-redis-master ping

# Common causes:
# - Redis not accessible
# - Insufficient memory for ML models
# - Queue configuration mismatch
```

#### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -n agenthr -l app.kubernetes.io/name=postgresql

# Test database connection
kubectl exec -n agenthr deployment/agenthr-backend -- \
  python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://postgres:postgres@agenthr-postgresql:5432/resume_analysis'); print('Connected:', engine.connect())"

# Check database credentials
kubectl get secret -n agenthr agenthr-secrets -o yaml
```

#### Out of Memory

```bash
# Check resource usage
kubectl top pods -n agenthr

# Increase resource limits in values.yaml:
backend:
  resources:
    limits:
      memory: 16Gi  # Increase from 8Gi

celeryWorker:
  resources:
    limits:
      memory: 16Gi  # Increase from 12Gi
```

#### Disk Space Issues

```bash
# Check PVC usage
kubectl exec -n agenthr deployment/agenthr-backend -- df -h

# Resize PVC (if supported by storage class)
kubectl edit pvc -n agenthr agenthr-models-cache
# Change size: 20Gi -> 50Gi
```

### Debug Mode

Enable debug logging:

```bash
helm upgrade agenthr ./helm/agenthr \
  --namespace agenthr \
  --reuse-values \
  --set config.logLevel=DEBUG
```

### Get Helm Release Info

```bash
# Get release status
helm status agenthr -n agenthr

# Get release values
helm get values agenthr -n agenthr

# Get all values (including defaults)
helm get values agenthr -n agenthr --all

# Get manifest
helm get manifest agenthr -n agenthr
```

## Monitoring

### Health Checks

```bash
# Backend health endpoint
kubectl exec -n agenthr deployment/agenthr-backend -- \
  curl http://localhost:8000/health

# Check all service endpoints
kubectl get endpoints -n agenthr
```

### Resource Monitoring

```bash
# Install metrics-server if not available
kubectl top nodes
kubectl top pods -n agenthr

# Watch resource usage
watch kubectl top pods -n agenthr
```

### Logs Aggregation

For production, consider deploying a logging stack:

```bash
# Example: Deploy Loki stack
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true
```

## Development

### Local Development Deployment

```yaml
# dev-values.yaml
backend:
  replicaCount: 1
  image:
    tag: "dev"
    pullPolicy: Always
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi

celeryWorker:
  replicaCount: 1
  concurrency: 2

postgresql:
  auth:
    password: "dev"
  primary:
    persistence:
      size: 5Gi

redis:
  master:
    persistence:
      size: 1Gi

persistence:
  modelsCache:
    size: 10Gi
  uploads:
    size: 2Gi
  backups:
    size: 5Gi

config:
  logLevel: DEBUG
```

```bash
helm install agenthr-dev ./helm/agenthr \
  --namespace agenthr-dev \
  --create-namespace \
  --values dev-values.yaml
```

### Testing Chart Changes

```bash
# Lint the chart
helm lint ./helm/agenthr

# Dry run installation
helm install agenthr ./helm/agenthr \
  --namespace agenthr \
  --dry-run --debug

# Template rendering
helm template agenthr ./helm/agenthr \
  --namespace agenthr \
  --values custom-values.yaml > rendered.yaml
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Bitnami Charts](https://github.com/bitnami/charts)
- [AgentHR Main Documentation](../../README.md)

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/agenthr/issues
- Documentation: https://github.com/yourusername/agenthr
- Email: team@agenthr.example.com

## License

This chart is part of the AgentHR project and follows the same license.
