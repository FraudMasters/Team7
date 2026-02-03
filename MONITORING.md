# Monitoring & Observability — Complete Guide

Comprehensive monitoring, logging, and observability setup for AgentHR using Grafana, Loki, Promtail, and Prometheus.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │  Frontend   │  │   Backend   │  │   Celery Workers    │   │
│  │  (React)    │  │  (FastAPI)  │  │   (Background)      │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          │                │                     │
          │ Logs           │ Logs                │ Logs
          │ Metrics        │ Metrics             │ Metrics
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COLLECTION LAYER                             │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Promtail   │      │  Prometheus  │      │   Promtail   │ │
│  │  (Log Agent) │      │ (Metrics)    │      │  (Log Agent) │ │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │
└─────────┼─────────────────────┼─────────────────────┼──────────┘
          │                     │                     │
          ▼                     ▼                     │
┌─────────────────┐   ┌─────────────────┐              │
│      Loki       │   │   Prometheus    │              │
│ (Log Storage)   │   │  (Time-Series   │              │
│                 │   │   Database)     │              │
└────────┬────────┘   └────────┬────────┘              │
         │                     │                       │
         ▼                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION LAYER                          │
│                                                                  │
│                     ┌─────────────────┐                        │
│                     │     Grafana     │                        │
│                     │  (Dashboards)   │                        │
│                     └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

The monitoring stack is automatically started with docker-compose:

```bash
docker-compose up -d
```

All monitoring services will be available within 30-60 seconds.

### Access URLs

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | http://localhost:3001 | admin/admin | Visualization dashboards |
| **Prometheus** | http://localhost:9090 | - | Metrics query and exploration |
| **Loki** | http://localhost:3100 | - | Log storage and queries |
| **Flower** | http://localhost:5555 | - | Celery task monitoring |

### First-Time Setup for Grafana

1. **Login to Grafana**
   ```bash
   # Navigate to http://localhost:3001
   # Default credentials: admin/admin
   # You'll be prompted to change password on first login
   ```

2. **Add Data Sources** (typically pre-configured)

   If not auto-configured, add these data sources:

   - **Prometheus**
     - URL: `http://prometheus:9090`
     - Access: Server (default)

   - **Loki**
     - URL: `http://loki:3100`
     - Access: Server (default)

3. **Import Dashboards**

   Dashboards are located in `monitoring/grafana/dashboards/`. Import them via:
   - Grafana UI → Dashboards → Import
   - Or use the provisioning configuration (auto-imports on startup)

---

## Architecture Components

### 1. Grafana — Visualization

**Purpose**: Unified dashboards for metrics and logs

**Port**: 3001

**Features**:
- Real-time metrics visualization
- Log aggregation and search
- Alert management
- Multi-datasource queries

**Configuration**: `monitoring/grafana/`

### 2. Loki — Log Aggregation

**Purpose**: Horizontally-scalable, highly-available log aggregation system

**Port**: 3100

**Features**:
- Label-based log storage (like Prometheus)
- Full-text search
- Efficient compression
- Integrates with Grafana

**Configuration**: `monitoring/loki/`

### 3. Promtail — Log Collector

**Purpose**: Agent that sends logs to Loki

**Features**:
- Reads log files from applications
- Extracts labels and metadata
- Pushes logs to Loki
- Supports multiple targets (containers, files)

**Configuration**: `monitoring/promtail/config.yml`

### 4. Prometheus — Metrics Collection

**Purpose**: Time-series database for metrics

**Port**: 9090

**Features**:
- Multi-dimensional data model
- PromQL query language
- Service discovery
- Alerting rules

**Configuration**: `monitoring/prometheus/`

---

## What Gets Monitored

### Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | HTTP request latency |
| `resume_analysis_duration` | Histogram | Resume analysis time |
| `matching_operation_duration` | Histogram | Job matching operation time |
| `celery_task_duration` | Histogram | Celery task execution time |
| `active_resumes_count` | Gauge | Current number of resumes |
| `ranking_model_accuracy` | Gauge | ML model accuracy |

### Celery Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `celery_task_received_total` | Counter | Tasks received by workers |
| `celery_task_started_total` | Counter | Tasks started |
| `celery_task_succeeded_total` | Counter | Tasks completed successfully |
| `celery_task_failed_total` | Counter | Tasks that failed |
| `celery_task_runtime` | Histogram | Task runtime duration |
| `celery_queue_length` | Gauge | Tasks in queue |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `container_cpu_usage_seconds_total` | Counter | CPU usage per container |
| `container_memory_usage_bytes` | Gauge | Memory usage per container |
| `container_network_receive_bytes_total` | Counter | Network received |
| `container_network_transmit_bytes_total` | Counter | Network transmitted |
| `postgres_connections_active` | Gauge | Active PostgreSQL connections |

---

## Log Structure

### Log Levels

```
CRITICAL 50 - Critical errors requiring immediate attention
ERROR    40 - Errors that don't stop the application
WARNING  30 - Warning messages for potential issues
INFO     20 - Informational messages about normal operation
DEBUG    10 - Detailed debugging information
```

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "backend",
  "module": "analyzers.unified_matcher",
  "function": "compare_unified",
  "message": "Successfully matched resume to vacancy",
  "context": {
    "resume_id": "uuid-123",
    "vacancy_id": "uuid-456",
    "match_score": 0.87,
    "duration_ms": 234
  }
}
```

### Log Labels

All logs are labeled for easy filtering in Loki:

- `service`: backend, frontend, celery-worker
- `environment`: production, development, test
- `level`: INFO, WARNING, ERROR, CRITICAL
- `module`: Python module or React component
- `version`: Application version

---

## Common Queries

### Grafana Logs (Loki)

**View all backend errors:**
```logql
{service="backend", level="ERROR"}
```

**Search for specific resume ID:**
```logql
{service="backend"} |= "resume-uuid-123"
```

**Find slow operations (>1s):**
```logql
{service="backend"} |~ "duration_ms.*[1-9][0-9]{3,}"
```

**Trace request flow:**
```logql
{service="backend"} |= "request-id-abc-123"
```

### Prometheus Queries

**Request rate (per second):**
```promql
rate(http_requests_total[5m])
```

**P95 latency:**
```promql
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

**Error rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**CPU usage by container:**
```promql
rate(container_cpu_usage_seconds_total{container!="POD"}[5m])
```

**Memory usage:**
```promql
container_memory_usage_bytes{container!="POD"}
```

---

## Alerting

### Pre-configured Alerts

Located in `monitoring/prometheus/alerts/`:

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | Error rate > 5% for 5m | Critical |
| HighLatency | P95 latency > 2s for 5m | Warning |
| HighMemoryUsage | Memory > 90% for 5m | Warning |
| CeleryQueueFull | Queue length > 1000 | Warning |
| DatabaseDown | PostgreSQL not responding | Critical |

### Alert Notifications

Configure alerts in Grafana:
1. Navigate to Alerting → Notification Channels
2. Add channel (Slack, Email, PagerDuty, etc.)
3. Link alert rules to notification channels

---

## Troubleshooting

### Grafana Issues

**Problem: Grafana won't start**
```bash
# Check logs
docker-compose logs grafana

# Common issue: Permission problems
# Fix: Reset permissions
sudo chown -R 472:472 monitoring/grafana/data
```

**Problem: Data source connection failed**
```bash
# Verify Prometheus is accessible
docker-compose exec grafana curl http://prometheus:9090/-/healthy

# Verify Loki is accessible
docker-compose exec grafana curl http://loki:3100/ready
```

### Loki Issues

**Problem: No logs appearing in Grafana**
```bash
# Check Promtail is running
docker-compose ps promtail

# Verify Promtail can reach Loki
docker-compose logs promtail | grep "error"

# Check Loki logs
docker-compose logs loki | grep "error"
```

**Problem: Logs are delayed**
```bash
# Check Promtail buffer settings
# In monitoring/promtail/config.yml, adjust:
# - entries_buffer_size (default: 512)
# - timeout for pushing to Loki
```

### Prometheus Issues

**Problem: Metrics not appearing**
```bash
# Check if targets are up
# Navigate to http://localhost:9090/targets

# Verify /metrics endpoint
docker-compose exec backend curl http://localhost:8000/metrics

# Check Prometheus logs
docker-compose logs prometheus | grep "error"
```

**Problem: High memory usage**
```bash
# Check retention settings
# In monitoring/prometheus/prometheus.yml:
# --storage.tsdb.retention.time=15d
```

---

## Performance Tuning

### Grafana Optimization

1. **Reduce dashboard refresh rate**
   - Default: 30s
   - Recommended: 1m for production

2. **Limit query time range**
   - Avoid queries > 7 days for real-time monitoring
   - Use summary tables for historical data

3. **Use dashboard variables**
   - Pre-compute common filters
   - Reduce query complexity

### Loki Optimization

1. **Optimize log labels**
   - Use high-cardinality labels sparingly
   - Keep label values unique and consistent

2. **Compression**
   - Enable Snappy compression (default)
   - Reduces storage by ~50%

3. **Retention policy**
   ```yaml
   # In monitoring/loki/local-config.yaml
   limits_config:
     retention_period: 30d
   ```

### Prometheus Optimization

1. **Scrape interval tuning**
   ```yaml
   # Default: 15s
   # Recommended: 30s for production
   scrape_interval: 30s
   ```

2. **Reduce metrics cardinality**
   - Avoid high-cardinality labels (like user_id)
   - Use sensible label combinations

3. **Recording rules**
   - Pre-compute expensive queries
   - Reduce dashboard load time

---

## Maintenance

### Backup Configuration

```bash
# Backup Grafana dashboards
docker-compose exec grafana grafana-cli admin export-dashboard > dashboards-backup.json

# Backup Prometheus data
docker-compose exec prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus

# Backup Loki data
docker-compose exec loki tar czf /tmp/loki-backup.tar.gz /loki
```

### Clean Old Data

```bash
# Clean old logs (Loki)
# Configure retention in monitoring/loki/local-config.yaml

# Clean old metrics (Prometheus)
# Configure retention in monitoring/prometheus/prometheus.yml
```

### Update Monitoring Stack

```bash
# Pull latest images
docker-compose pull grafana loki promtail prometheus

# Restart services
docker-compose up -d grafana loki promtail prometheus
```

---

## Next Steps

- **[DEBUGGING.md](DEBUGGING.md)** - Debugging procedures and common issues
- **[PERFORMANCE.md](PERFORMANCE.md)** - Performance monitoring and optimization
- **[ALERTING.md](ALERTING.md)** - Setting up advanced alerting rules

---

For questions or issues, refer to the main [README.md](README.md) or open an issue on GitHub.
