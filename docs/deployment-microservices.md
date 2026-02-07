# Microservices Deployment Guide
# Руководство по развертыванию микросервисов

## Overview / Обзор

This guide provides step-by-step instructions for deploying the AgentHR microservices architecture in various environments. The system consists of:

Это руководство содержит пошаговые инструкции для развертывания микросервисной архитектуры AgentHR в различных средах. Система состоит из:

- **API Gateway** (Kong) - Single entry point for all requests / Единая точка входа для всех запросов
- **9 Core Microservices** - Independent business services / 9 основных микросервисов - независимые бизнес-сервисы
- **Infrastructure Services** - PostgreSQL, Redis, Consul, Jaeger, Loki / Инфраструктурные сервисы

### Architecture Diagram / Диаграмма архитектуры

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   Kong (8888)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
│   Resume     │   │    Matching     │   │  Candidate  │
│ Processing   │   │   Service       │   │  Service    │
│  (8001)      │   │    (8002)       │   │   (8003)    │
└──────────────┘   └─────────────────┘   └─────────────┘
        │                    │                    │
┌───────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
│   Vacancy    │   │    Taxonomy     │   │  Analytics  │
│   Service    │   │    Service      │   │  Service    │
│   (8004)     │   │    (8005)       │   │   (8006)    │
└──────────────┘   └─────────────────┘   └─────────────┘
        │                    │                    │
┌───────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
│     ATS      │   │  Notification   │   │ Integration │
│  Simulation  │   │    Service      │   │   Service   │
│   (8007)     │   │    (8008)       │   │   (8009)    │
└──────────────┘   └─────────────────┘   └─────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
│  PostgreSQL  │   │     Redis       │   │   Consul    │
│   (5432)     │   │    (6379)       │   │   (8500)    │
└──────────────┘   └─────────────────┘   └─────────────┘
```

---

## Table of Contents / Содержание

1. [Prerequisites / Предварительные требования](#prerequisites)
2. [Quick Start (Local Development) / Быстрый старт (Локальная разработка)](#quick-start-local-development)
3. [Production Deployment / Производственное развертывание](#production-deployment)
4. [Kubernetes Deployment / Развертывание в Kubernetes](#kubernetes-deployment)
5. [Environment Configuration / Конфигурация окружения](#environment-configuration)
6. [Health Checks & Monitoring / Проверки здоровья и мониторинг](#health-checks--monitoring)
7. [Troubleshooting / Решение проблем](#troubleshooting)
8. [Scaling Strategies / Стратегии масштабирования](#scaling-strategies)

---

## Prerequisites / Предварительные требования

### Minimum System Requirements / Минимальные системные требования

| Resource | Development | Production (Small) | Production (Large) |
|----------|-------------|-------------------|-------------------|
| CPU | 4 cores | 8 cores | 16+ cores |
| RAM | 8 GB | 16 GB | 32+ GB |
| Storage | 20 GB SSD | 100 GB SSD | 500+ GB SSD |
| Network | 100 Mbps | 1 Gbps | 10+ Gbps |

### Software Requirements / Требования к программному обеспечению

```bash
# Required software / Необходимое ПО
- Docker 24.0+
- Docker Compose 2.20+
- (Optional) Kubernetes 1.28+ (for K8s deployment)
- (Optional) Helm 3.12+ (for Helm charts)

# For local development / Для локальной разработки
- Python 3.11+ (if running services directly)
- Node.js 20+ (for frontend)
- Make (for build scripts)
```

### Verify Installation / Проверка установки

```bash
# Check Docker version
docker --version
# Expected output: Docker version 24.0.0 or higher

# Check Docker Compose version
docker compose version
# Expected output: Docker Compose version v2.20.0 or higher

# Verify Docker daemon is running
docker ps
# Expected output: List of containers (may be empty)
```

---

## Quick Start (Local Development) / Быстрый старт (Локальная разработка)

### Step 1: Clone Repository / Клонирование репозитория

```bash
# Clone the repository / Клонировать репозиторий
git clone https://github.com/your-org/agenthr.git
cd agenthr

# Checkout the correct branch / Переключиться на правильную ветку
git checkout main
```

### Step 2: Configure Environment / Конфигурация окружения

```bash
# Create environment file from template
# Создать файл окружения из шаблона
cp .env.example .env

# Edit environment variables (see Environment Configuration section)
# Редактировать переменные окружения (см. раздел Конфигурация окружения)
nano .env
```

### Step 3: Start Infrastructure Services / Запуск инфраструктурных сервисов

```bash
# Start PostgreSQL, Redis, Consul, Jaeger, Loki
# Запустить PostgreSQL, Redis, Consul, Jaeger, Loki
docker compose -f docker-compose.microservices.yml up -d postgres redis consul jaeger loki

# Wait for services to be healthy (30 seconds)
# Подождать, пока сервисы станут здоровыми (30 секунд)
echo "Waiting for infrastructure services..."
sleep 30

# Verify services are running
# Проверить, что сервисы запущены
docker compose -f docker-compose.microservices.yml ps postgres redis consul
```

### Step 4: Start API Gateway / Запуск API Gateway

```bash
# Start Kong API Gateway
# Запустить Kong API Gateway
docker compose -f docker-compose.microservices.yml up -d api_gateway

# Wait for Kong to initialize
# Подождать инициализации Kong
sleep 10

# Test Gateway health check
# Проверить здоровье Gateway
curl -s http://localhost:8888/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "message": "API Gateway is operational"
# }
```

### Step 5: Start Microservices / Запуск микросервисов

```bash
# Start all microservices
# Запустить все микросервисы
docker compose -f docker-compose.microservices.yml up -d \
  resume_processing \
  matching \
  candidate \
  vacancy \
  taxonomy \
  analytics \
  ats_simulation \
  notifications \
  integration

# Wait for services to start (up to 60 seconds)
# Подождать запуска сервисов (до 60 секунд)
echo "Waiting for microservices to start..."
sleep 60

# Check all services are healthy
# Проверить здоровье всех сервисов
docker compose -f docker-compose.microservices.yml ps
```

### Step 6: Run Database Migrations / Выполнение миграций базы данных

```bash
# Run migrations for each service
# Выполнить миграции для каждого сервиса

# Resume Processing Service
docker compose -f docker-compose.microservices.yml exec resume_processing \
  alembic upgrade head

# Matching Service
docker compose -f docker-compose.microservices.yml exec matching \
  alembic upgrade head

# Candidate Service
docker compose -f docker-compose.microservices.yml exec candidate \
  alembic upgrade head

# Vacancy Service
docker compose -f docker-compose.microservices.yml exec vacancy \
  alembic upgrade head

# Taxonomy Service
docker compose -f docker-compose.microservices.yml exec taxonomy \
  alembic upgrade head

# Analytics Service
docker compose -f docker-compose.microservices.yml exec analytics \
  alembic upgrade head

# ATS Simulation Service
docker compose -f docker-compose.microservices.yml exec ats_simulation \
  alembic upgrade head

# Notification Service
docker compose -f docker-compose.microservices.yml exec notifications \
  alembic upgrade head

# Integration Service
docker compose -f docker-compose.microservices.yml exec integration \
  alembic upgrade head
```

### Step 7: Verify Deployment / Проверка развертывания

```bash
# Health check script
# Скрипт проверки здоровья
#!/bin/bash

echo "=== AgentHR Microservices Health Check ==="
echo ""

services=(
  "http://localhost:8888/health:API Gateway"
  "http://localhost:8011/health:Resume Processing"
  "http://localhost:8012/health:Matching"
  "http://localhost:8013/health:Candidate"
  "http://localhost:8014/health:Vacancy"
  "http://localhost:8015/health:Taxonomy"
  "http://localhost:8016/health:Analytics"
  "http://localhost:8017/health:ATS Simulation"
  "http://localhost:8018/health:Notifications"
  "http://localhost:8019/health:Integration"
)

all_healthy=true

for service in "${services[@]}"; do
  url="${service%%:*}"
  name="${service##*:}"

  if curl -sf "$url" > /dev/null 2>&1; then
    echo "✅ $name is healthy"
  else
    echo "❌ $name is unhealthy"
    all_healthy=false
  fi
done

echo ""
if [ "$all_healthy" = true ]; then
  echo "🎉 All services are healthy!"
  exit 0
else
  echo "⚠️  Some services are unhealthy. Check logs with:"
  echo "   docker compose -f docker-compose.microservices.yml logs <service_name>"
  exit 1
fi
```

Save as `health-check.sh`, make executable: `chmod +x health-check.sh`, and run: `./health-check.sh`

### Step 8: Access Services / Доступ к сервисам

```bash
# API Gateway
open http://localhost:8888
curl http://localhost:8888/health

# Kong Admin GUI
open http://localhost:8002

# Consul UI (Service Discovery)
open http://localhost:8500

# Jaeger UI (Distributed Tracing)
open http://localhost:16686

# Grafana (Monitoring)
open http://localhost:3001
# Default credentials: admin / admin
```

---

## Production Deployment / Производственное развертывание

### Production Prerequisites / Предварительные требования для production

```bash
# Production server requirements
# Требования к production серверу
- Ubuntu 22.04 LTS or RHEL 9
- Docker 24.0+ with Docker Compose v2
- SSL certificates (Let's Encrypt or custom)
- Domain name configured with DNS
- Firewall configured (ports 80, 443, 8888)
- Backup strategy configured
- Log aggregation (Loki, ELK, or cloud service)
```

### Step 1: Prepare Production Server / Подготовка production сервера

```bash
# Update system packages
# Обновить системные пакеты
sudo apt update && sudo apt upgrade -y

# Install Docker
# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Install Docker Compose plugin
# Установить плагин Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
# Проверить установку
docker --version
docker compose version
```

### Step 2: Configure SSL/TLS / Конфигурация SSL/TLS

```bash
# Option 1: Let's Encrypt (Recommended)
# Вариант 1: Let's Encrypt (Рекомендуется)

# Install Certbot
# Установить Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
# Получить сертификат
sudo certbot certonly --standalone -d api.yourdomain.com

# Certificates will be saved to:
# Сертификаты будут сохранены в:
# /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/api.yourdomain.com/privkey.pem

# Option 2: Custom Certificates
# Вариант 2: Собственные сертификаты
# Copy your certificates to: /etc/ssl/private/agenthr/
```

### Step 3: Create Production Environment File / Создание production файла окружения

```bash
# Create production environment file
# Создать production файл окружения
cat > .env.production << 'EOF'
# Database / База данных
POSTGRES_USER=agenthr_prod
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=agenthr_production

# Redis / Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# Application / Приложение
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# SSL/TLS / SSL/TLS
SSL_CERT_PATH=/etc/letsencrypt/live/api.yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/api.yourdomain.com/privkey.pem

# CORS / CORS
CORS_ORIGINS=https://app.yourdomain.com,https://api.yourdomain.com

# External APIs / Внешние API
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# SMTP / SMTP
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password

# Monitoring / Мониторинг
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
EOF

# Secure the environment file
# Защитить файл окружения
chmod 600 .env.production
```

### Step 4: Configure Production Docker Compose / Конфигурация production Docker Compose

```bash
# Create production override file
# Создать production override файл
cat > docker-compose.production.yml << 'EOF'
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password

  redis:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes

  api_gateway:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    ports:
      - "443:8443"  # HTTPS
      - "80:8888"   # HTTP (redirect to HTTPS)
    volumes:
      - ${SSL_CERT_PATH}:/etc/ssl/certs/fullchain.pem:ro
      - ${SSL_KEY_PATH}:/etc/ssl/private/privkey.pem:ro

  resume_processing:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    environment:
      WORKERS_COUNT: 4

  matching:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
      restart_policy:
        condition: on-failure
        max_attempts: 3

  # ... configure other services similarly

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

volumes:
  postgres_prod_data:
```

### Step 5: Deploy with SSL / Развертывание с SSL

```bash
# Load production environment
# Загрузить production окружение
export $(cat .env.production | xargs)

# Start production stack
# Запустить production стек
docker compose -f docker-compose.microservices.yml \
  -f docker-compose.production.yml \
  --env-file .env.production \
  up -d

# Verify SSL is working
# Проверить работу SSL
curl -I https://api.yourdomain.com/health

# Expected output:
# HTTP/2 200
# server: openresty
# ...
```

### Step 6: Configure Firewall / Конфигурация брандмауэра

```bash
# Configure UFW (Uncomplicated Firewall)
# Настроить UFW (Uncomplicated Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Verify firewall status
# Проверить статус брандмауэра
sudo ufw status verbose
```

### Step 7: Set Up Backups / Настройка резервного копирования

```bash
# Create backup script
# Создать скрипт резервного копирования
cat > /usr/local/bin/agenthr-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Database backup
# Резервное копирование базы данных
docker compose -f docker-compose.microservices.yml exec -T postgres \
  pg_dumpall -U agenthr_prod | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Upload to S3 (optional)
# Загрузка в S3 (опционально)
# aws s3 cp "$BACKUP_DIR/db_backup_$DATE.sql.gz" s3://your-backup-bucket/

# Clean old backups
# Очистка старых резервных копий
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
EOF

chmod +x /usr/local/bin/agenthr-backup.sh

# Add to crontab (daily at 2 AM)
# Добавить в crontab (ежедневно в 2 часа ночи)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/agenthr-backup.sh") | crontab -
```

---

## Kubernetes Deployment / Развертывание в Kubernetes

### Prerequisites / Предварительные требования

```bash
# Required tools / Необходимые инструменты
- kubectl 1.28+
- helm 3.12+
- Valid Kubernetes cluster (minikube, kind, or cloud provider)
```

### Step 1: Create Kubernetes Namespace / Создание Kubernetes namespace

```bash
# Create namespace for AgentHR
# Создать namespace для AgentHR
kubectl create namespace agenthr

# Set as default namespace
# Установить как namespace по умолчанию
kubectl config set-context --current --namespace=agenthr
```

### Step 2: Create Secrets / Создание secrets

```bash
# Database credentials
# Учетные данные базы данных
kubectl create secret generic postgres-credentials \
  --from-literal=username=agenthr_prod \
  --from-literal=password=your-secure-password

# Redis credentials
# Учетные данные Redis
kubectl create secret generic redis-credentials \
  --from-literal=password=your-redis-password

# API keys
# API ключи
kubectl create secret generic api-keys \
  --from-literal=openai-api-key=sk-... \
  --from-literal=anthropic-api-key=sk-...

# TLS certificates
# TLS сертификаты
kubectl create secret tls api-gateway-tls \
  --cert=/path/to/fullchain.pem \
  --key=/path/to/privkey.pem
```

### Step 3: Deploy PostgreSQL / Развертывание PostgreSQL

```yaml
# File: k8s/postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: POSTGRES_DB
          value: agenthr_production
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
```

```bash
# Apply PostgreSQL deployment
# Применить развертывание PostgreSQL
kubectl apply -f k8s/postgres-statefulset.yaml
```

### Step 4: Deploy Microservices / Развертывание микросервисов

```yaml
# File: k8s/resume-processing-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-processing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resume-processing
  template:
    metadata:
      labels:
        app: resume-processing
        version: v1
    spec:
      containers:
      - name: resume-processing
        image: agenthr/resume-processing:latest
        ports:
        - containerPort: 8001
          name: http
        env:
        - name: DATABASE_URL
          value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/agenthr_production"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: JAEGER_HOST
          value: jaeger
        - name: JAEGER_PORT
          value: "6831"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: resume-processing
spec:
  selector:
    app: resume-processing
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

```bash
# Create similar deployments for all services:
# Создать похожие развертывания для всех сервисs:
kubectl apply -f k8s/resume-processing-deployment.yaml
kubectl apply -f k8s/matching-deployment.yaml
kubectl apply -f k8s/candidate-deployment.yaml
# ... (repeat for all services)
```

### Step 5: Deploy Kong API Gateway / Развертывание Kong API Gateway

```yaml
# File: k8s/kong-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kong
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kong
  template:
    metadata:
      labels:
        app: kong
    spec:
      containers:
      - name: kong
        image: kong:3.6-alpine
        env:
        - name: KONG_DATABASE
          value: "off"
        - name: KONG_PROXY_ACCESS_LOG
          value: /dev/stdout
        - name: KONG_ADMIN_ACCESS_LOG
          value: /dev/stdout
        - name: KONG_PROXY_ERROR_LOG
          value: /dev/stderr
        - name: KONG_ADMIN_ERROR_LOG
          value: /dev/stderr
        - name: KONG_ADMIN_LISTEN
          value: "0.0.0.0:8001"
        ports:
        - name: proxy
          containerPort: 8000
        - name: proxy-ssl
          containerPort: 8443
        - name: admin
          containerPort: 8001
        volumeMounts:
        - name: kong-config
          mountPath: /usr/local/kong/declarative
          readOnly: true
      volumes:
      - name: kong-config
        configMap:
          name: kong-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kong-config
data:
  kong.yml: |
    _format_version: "3.0"
    services:
      - name: resume_processing
        url: http://resume-processing:8001
        connect_timeout: 60000
        write_timeout: 60000
        read_timeout: 60000
      # ... add other services
    routes:
      - name: resume_processing_routes
        service: resume_processing
        paths:
          - /api/resumes
          - /api/resumes/*
        strip_path: false
      # ... add other routes
    plugins:
      - name: cors
        config:
          origins:
            - https://app.yourdomain.com
          methods:
            - GET
            - POST
            - PUT
            - DELETE
      - name: rate-limiting
        config:
          second: 100
          hour: 10000
---
apiVersion: v1
kind: Service
metadata:
  name: kong
spec:
  selector:
    app: kong
  ports:
  - name: proxy
    port: 8888
    targetPort: 8000
  - name: proxy-ssl
    port: 8443
    targetPort: 8443
  type: LoadBalancer
```

```bash
# Apply Kong deployment
# Применить развертывание Kong
kubectl apply -f k8s/kong-deployment.yaml

# Get LoadBalancer IP
# Получить IP LoadBalancer
kubectl get svc kong
```

### Step 6: Deploy Monitoring Stack / Развертывание стека мониторинга

```yaml
# File: k8s/monitoring-stack.yaml
# Prometheus, Grafana, Jaeger, Loki
# (Use Helm charts for production)
---
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: prometheus-community
spec:
  interval: 1h
  url: https://prometheus-community.github.io/helm-charts
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: kube-prometheus-stack
spec:
  interval: 1h
  chart:
    spec:
      chart: kube-prometheus-stack
      version: "55.x"
      sourceRef:
        kind: HelmRepository
        name: prometheus-community
  values:
    grafana:
      enabled: true
      service:
        type: LoadBalancer
    prometheus:
      enabled: true
    prometheus-node-exporter:
      enabled: true
```

```bash
# Install monitoring stack using Helm
# Установить стек мониторинга используя Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace agenthr \
  --set grafana.service.type=LoadBalancer
```

### Step 7: Verify Kubernetes Deployment / Проверка развертывания в Kubernetes

```bash
# Check all pods are running
# Проверить, что все поды запущены
kubectl get pods -n agenthr

# Expected output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# postgres-0                             1/1     Running   0          5m
# resume-processing-xxx-yyy              1/1     Running   0          3m
# matching-xxx-yyy                       1/1     Running   0          3m
# kong-xxx-yyy                           1/1     Running   0          2m
# kube-prometheus-stack-grafana-xxx      1/1     Running   0          1m

# Check services
# Проверить сервисы
kubectl get svc -n agenthr

# Port forward to test locally
# Проброс портов для локального тестирования
kubectl port-forward -n agenthr svc/kong 8888:8888

# Test health check
# Проверить здоровье
curl http://localhost:8888/health
```

---

## Environment Configuration / Конфигурация окружения

### Core Environment Variables / Основные переменные окружения

```bash
# === Database / База данных ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=resume_analysis
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/resume_analysis

# === Redis / Redis ===
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# === Application / Приложение ===
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# === API Gateway / API Gateway ===
KONG_LOG_LEVEL=info
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# === Service Ports / Порты сервисов ===
RESUME_PROCESSING_PORT=8001
MATCHING_PORT=8002
CANDIDATE_PORT=8003
VACANCY_PORT=8004
TAXONOMY_PORT=8005
ANALYTICS_PORT=8006
ATS_SIMULATION_PORT=8007
NOTIFICATIONS_PORT=8008
INTEGRATION_PORT=8009

# === LLM APIs (for ATS Simulation) / LLM API (для ATS симуляции) ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
Z_AI_API_KEY=

# === SMTP (for notifications) / SMTP (для уведомлений) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

# === Twilio (for SMS) / Twilio (для SMS) ===
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# === Tracing / Отслеживание ===
JAEGER_HOST=jaeger
JAEGER_PORT=6831
TRACE_SAMPLE_RATE=0.1

# === Service Discovery / Обнаружение сервисов ===
CONSUL_HOST=consul
CONSUL_PORT=8500
SERVICE_REGISTRY_ENABLED=true

# === Logging / Логирование ===
LOKI_URL=http://loki:3100

# === File Upload / Загрузка файлов ===
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=.pdf,.docx
UPLOAD_DIR=/app/data/uploads

# === Storage / Хранилище ===
S3_ENABLED=false
S3_BUCKET=
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_REGION=us-east-1

# === Backup / Резервное копирование ===
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=/app/data/backups
BACKUP_S3_ENABLED=false
BACKUP_S3_BUCKET=
BACKUP_NOTIFICATION_EMAIL=
```

### Service-Specific Configuration / Специфичная конфигурация сервисов

Each microservice can have its own configuration file in `services/<service_name>/.env`:

Каждый микросервис может иметь свой файл конфигурации в `services/<service_name>/.env`:

```bash
# services/resume_processing/.env
MODEL_CACHE_PATH=/app/models_cache
TRANSFORMERS_CACHE=/app/models_cache/hub
HF_HOME=/app/models_cache

# services/matching/.env
MATCHING_ALGORITHM=unified
TFIDF_ENABLED=true
VECTOR_SIMILARITY_ENABLED=true

# services/notifications/.env
EMAIL_ENABLED=true
SMS_ENABLED=false
WEBHOOK_ENABLED=true
```

---

## Health Checks & Monitoring / Проверки здоровья и мониторинг

### Service Health Endpoints / Эндпоинты проверки здоровья

Each microservice exposes a `/health` endpoint:

Каждый микросервис предоставляет эндпоинт `/health`:

```bash
# Health check response structure
# Структура ответа проверки здоровья
{
  "status": "healthy",  # or "unhealthy" / или "unhealthy"
  "service": "resume_processing",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "checks": {
    "database": "pass",
    "redis": "pass",
    "external_api": "pass"
  }
}
```

### Monitoring Dashboards / Панели мониторинга

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin / admin |
| Jaeger | http://localhost:16686 | No auth |
| Consul | http://localhost:8500 | No auth |
| Kong Manager | http://localhost:8002 | No auth |
| Prometheus | http://localhost:9090 | No auth |

### Key Metrics to Monitor / Ключевые метрики для мониторинга

```yaml
# Application Metrics / Метрики приложения
- Request rate (requests/second)
- Error rate (errors/second)
- Latency (P50, P95, P99)
- Active connections
- Queue depth

# Infrastructure Metrics / Инфраструктурные метрики
- CPU usage (%)
- Memory usage (%)
- Disk I/O (ops/sec)
- Network throughput (Mbps)
- Database connections

# Business Metrics / Бизнес-метрики
- Resumes processed per hour
- Matching requests per minute
- Notification delivery rate
- API gateway success rate
```

---

## Troubleshooting / Решение проблем

### Common Issues / Распространенные проблемы

#### 1. Service Fails to Start / Сервис не запускается

```bash
# Check service logs
# Проверить логи сервиса
docker compose -f docker-compose.microservices.yml logs <service_name>

# Example / Пример:
docker compose -f docker-compose.microservices.yml logs resume_processing

# Check if port is already in use
# Проверить, занят ли порт
sudo lsof -i :8001

# Check service dependencies
# Проверить зависимости сервиса
docker compose -f docker-compose.microservices.yml ps
```

#### 2. Database Connection Errors / Ошибки подключения к базе данных

```bash
# Test database connectivity
# Проверить подключение к базе данных
docker compose -f docker-compose.microservices.yml exec postgres psql -U postgres -d resume_analysis -c "SELECT 1"

# Check database is healthy
# Проверить здоровье базы данных
docker compose -f docker-compose.microservices.yml ps postgres

# View database logs
# Просмотреть логи базы данных
docker compose -f docker-compose.microservices.yml logs postgres
```

#### 3. High Memory Usage / Высокое использование памяти

```bash
# Check container resource usage
# Проверить использование ресурсов контейнером
docker stats

# Limit memory in docker-compose.yml
# Ограничить память в docker-compose.yml
services:
  matching:
    deploy:
      resources:
        limits:
          memory: 4G
```

#### 4. Intermittent Timeouts / Прерывистые таймауты

```bash
# Increase timeout in Kong configuration
# Увеличить таймаут в конфигурации Kong
# Edit infrastructure/api-gateway/kong.yml:
services:
  - name: matching
    url: http://matching:8002
    read_timeout: 120000  # 120 seconds
    write_timeout: 120000
```

#### 5. Celery Tasks Not Processing / Задачи Celery не обрабатываются

```bash
# Check Celery worker status
# Проверить статус worker Celery
docker compose -f docker-compose.microservices.yml exec celery_worker celery -A celery_app inspect active

# Check Redis connection
# Проверить подключение к Redis
docker compose -f docker-compose.microservices.yml exec redis redis-cli ping

# View worker logs
# Просмотреть логи worker
docker compose -f docker-compose.microservices.yml logs celery_worker
```

### Debug Mode / Режим отладки

```bash
# Enable debug logging for a service
# Включить debug-логирование для сервиса
docker compose -f docker-compose.microservices.yml run --rm \
  -e LOG_LEVEL=DEBUG \
  resume_processing python main.py

# Interactive debugging with pdb
# Интерактивная отладка с pdb
docker compose -f docker-compose.microservices.yml run --rm \
  --service-ports \
  resume_processing python -m pdb main.py
```

### Getting Logs / Получение логов

```bash
# Follow logs for all services
# Следить за логами всех сервисов
docker compose -f docker-compose.microservices.yml logs -f

# Get logs for specific service
# Получить логи конкретного сервиса
docker compose -f docker-compose.microservices.yml logs -f resume_processing

# Get logs from last hour
# Получить логи за последний час
docker compose -f docker-compose.microservices.yml logs --since 1h resume_processing

# Export logs to file
# Экспортировать логи в файл
docker compose -f docker-compose.microservices.yml logs > logs.txt 2>&1
```

---

## Scaling Strategies / Стратегии масштабирования

### Horizontal Scaling / Горизонтальное масштабирование

```bash
# Scale individual services
# Масштабировать отдельные сервисы
docker compose -f docker-compose.microservices.yml up -d --scale matching=3

# This will create 3 instances of the Matching Service
# Это создаст 3 экземпляра Matching Service
```

### Vertical Scaling / Вертикальное масштабирование

```yaml
# In docker-compose.microservices.yml
services:
  matching:
    deploy:
      resources:
        limits:
          cpus: '8.0'      # Increase from 4.0
          memory: 16G      # Increase from 8G
```

### Kubernetes HPA (Horizontal Pod Autoscaler) / HPA Kubernetes

```yaml
# File: k8s/matching-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: matching-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: matching
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Maintenance & Operations / Обслуживание и операции

### Database Migrations / Миграции базы данных

```bash
# Run migrations for all services
# Выполнить миграции для всех сервисов
for service in resume_processing matching candidate vacancy taxonomy analytics ats_simulation notifications integration; do
  echo "Migrating $service..."
  docker compose -f docker-compose.microservices.yml exec $service alembic upgrade head
done

# Rollback migrations
# Откатить миграции
docker compose -f docker-compose.microservices.yml exec resume_processing alembic downgrade -1
```

### Updating Services / Обновление сервисов

```bash
# Pull latest images
# Загрузить последние образы
docker compose -f docker-compose.microservices.yml pull

# Restart services with zero downtime
# Перезапустить сервисы с нулевым простоем
docker compose -f docker-compose.microservices.yml up -d --no-deps --build <service_name>

# Example: Update Resume Processing Service
# Пример: Обновить Resume Processing Service
docker compose -f docker-compose.microservices.yml up -d --no-deps --build resume_processing
```

### Backup & Restore / Резервное копирование и восстановление

```bash
# Create backup
# Создать резервную копию
./scripts/backup.sh

# Restore from backup
# Восстановить из резервной копии
./scripts/restore.sh backup_file.sql.gz
```

---

## Security Hardening / Усиление безопасности

### Production Security Checklist / Чеклист безопасности для production

- [ ] Change all default passwords / Изменить все пароли по умолчанию
- [ ] Enable SSL/TLS for all services / Включить SSL/TLS для всех сервисов
- [ ] Configure firewall rules / Настроить правила брандмауэра
- [ ] Enable rate limiting at API Gateway / Включить ограничение частоты запросов на API Gateway
- [ ] Set up log aggregation / Настроить агрегацию логов
- [ ] Configure intrusion detection / Настроить обнаружение вторжений
- [ ] Enable audit logging / Включить аудит логов
- [ ] Regular security updates / Регулярные обновления безопасности
- [ ] Secrets management (HashiCorp Vault or AWS Secrets Manager) / Управление секретами

---

## Appendix / Приложение

### Service Port Reference / Справочник портов сервисов

| Service | Internal Port | External Port (Docker) |
|---------|--------------|------------------------|
| API Gateway | 8000 | 8888 |
| Resume Processing | 8001 | 8011 |
| Matching | 8002 | 8012 |
| Candidate | 8003 | 8013 |
| Vacancy | 8004 | 8014 |
| Taxonomy | 8005 | 8015 |
| Analytics | 8006 | 8016 |
| ATS Simulation | 8007 | 8017 |
| Notifications | 8008 | 8018 |
| Integration | 8009 | 8019 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Consul | 8500 | 8500 |
| Jaeger | 16686 | 16686 |
| Grafana | 3000 | 3001 |
| Kong Admin | 8001 | 8001 |
| Kong Manager | 8002 | 8002 |

### Useful Commands / Полезные команды

```bash
# Stop all services / Остановить все сервисы
docker compose -f docker-compose.microservices.yml down

# Stop and remove volumes / Остановить и удалить тома
docker compose -f docker-compose.microservices.yml down -v

# View resource usage / Просмотр использования ресурсов
docker stats

# Execute command in container / Выполнить команду в контейнере
docker compose -f docker-compose.microservices.yml exec <service> <command>

# Rebuild container / Пересобрать контейнер
docker compose -f docker-compose.microservices.yml build <service>

# Prune unused resources / Очистить неиспользуемые ресурсы
docker system prune -a
```

---

**Last Updated:** 2025-02-05

**Version:** 1.0.0

For issues or questions, please refer to:
Для проблем или вопросов, пожалуйста, обращайтесь к:
- GitHub Issues: https://github.com/your-org/agenthr/issues
- Documentation: /docs/
- API Documentation: /docs/api/
