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

## Key Metrics

### Critical Metrics to Monitor

The following metrics are critical for maintaining system health and performance. Monitor these closely and set up alerts for threshold violations.

#### API Performance Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `http_request_duration_seconds` | Histogram | Request latency across all endpoints | p95 < 500ms | p95 > 2s warning, > 5s critical |
| `http_requests_total` | Counter | Total API requests by status code | 2xx dominant | 5xx > 5% warning, > 15% critical |
| `up{job="backend"}` | Gauge | Backend service availability | 1 (up) | 0 (down) critical |

**Key Query Examples:**
```promql
# P95 Response Time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Request Rate by Endpoint
sum(rate(http_requests_total[5m])) by (endpoint)
```

#### Celery Task Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `celery_queue_length` | Gauge | Number of tasks waiting in queue | < 20 | > 100 warning, > 500 critical |
| `celery_task_runtime_seconds` | Histogram | Task execution duration | p95 < 300s | p95 > 300s warning |
| `celery_tasks_total` | Counter | Tasks by status (success/failed) | Success > 90% | Failure > 10% warning, > 25% critical |
| `celery_workers_up` | Gauge | Number of active workers | ≥ 1 | 0 critical |

**Key Query Examples:**
```promql
# Queue Depth Trend
celery_queue_length

# Task Failure Rate
sum(rate(celery_tasks_total{status="failed"}[5m])) / sum(rate(celery_tasks_total[5m])) * 100

# Worker Availability
celery_workers_up
```

#### ML Model Inference Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `ml_inference_duration_seconds` | Histogram | Time to process resume through ML models | p95 < 30s | p95 > 30s warning, > 60s critical |
| `ml_predictions_total` | Counter | Total predictions by model and type | Increasing steadily | Sudden drop warning |
| `ml_models_loaded` | Gauge | Number of ML models currently loaded | All models | Models missing critical |

**Model Performance Targets (per spec):**
- **Resume Inference Time:** < 30 seconds (p95)
- **Model Availability:** All required models loaded
- **Prediction Throughput:** Scale with request volume

**Key Query Examples:**
```promql
# P95 Inference Time by Model
histogram_quantile(0.95, sum(rate(ml_inference_duration_seconds_bucket[5m])) by (le, model_name))

# Prediction Rate by Model
sum(rate(ml_predictions_total[5m])) by (model_name)

# Model Loading Status
sum(ml_models_loaded) by (model_type)
```

#### Database Performance Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `db_query_duration_seconds` | Histogram | Database query execution time | p95 < 500ms | p95 > 1s warning, > 3s critical |
| `pg_stat_database_numbackends` | Gauge | Active database connections | < 50 | > 100 warning |
| `pg_stat_database_blks_hit` | Counter | Cache hits (performance indicator) | High ratio | Low ratio warning |
| `postgres_up` | Gauge | Database availability | 1 (up) | 0 (down) critical |

**Key Query Examples:**
```promql
# P95 Query Duration
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))

# Cache Hit Ratio
sum(rate(pg_stat_database_blks_hit[5m])) / (sum(rate(pg_stat_database_blks_hit[5m])) + sum(rate(pg_stat_database_blks_read[5m]))) * 100

# Connection Pool Usage
pg_stat_database_numbackends
```

#### System Resource Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `container_cpu_usage_seconds_total` | Counter | CPU consumption per container | < 80% | > 90% warning |
| `container_memory_usage_bytes` | Gauge | Memory usage per container | < 80% limit | > 90% warning |
| `container_fs_usage_bytes` | Gauge | Disk usage per container | < 80% | > 90% critical |
| `up` | Gauge | Service availability | 1 (up) | 0 (down) critical |

**Key Query Examples:**
```promql
# CPU Usage by Container
rate(container_cpu_usage_seconds_total{container!="POD"}[5m]) * 100

# Memory Usage by Container
container_memory_usage_bytes{container!="POD"} / container_spec_memory_limit_bytes * 100

# Disk Usage
container_fs_usage_bytes / container_fs_limit_bytes * 100
```

---

### Monitoring Targets Summary

**Primary Monitoring Targets:**
1. **API Response Time** - Keep user experience snappy (p95 < 500ms)
2. **Error Rate** - Maintain system reliability (< 5% errors)
3. **Queue Depth** - Prevent task backup (< 100 queued)
4. **ML Inference Speed** - Meet spec requirements (p95 < 30s)
5. **Database Performance** - Ensure query efficiency (p95 < 500ms)
6. **Service Availability** - All services up and responding

**Secondary Metrics (trending):**
- Request rate patterns
- Task completion rates
- Model prediction distribution
- Cache effectiveness
- Resource utilization trends

---

## Grafana Dashboards

Grafana comes with 5 pre-configured dashboards that automatically provision on startup. Dashboards are located in `monitoring/grafana/dashboards/` and auto-refresh every 10 seconds.

### Dashboard Access

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| API Performance | http://localhost:3001/d/api-performance | Monitor API latency, errors, throughput |
| Celery Tasks | http://localhost:3001/d/celery-tasks | Task queue depth, worker status, failures |
| ML Inference | http://localhost:3001/d/ml-inference | Model performance, inference timing |
| Database Performance | http://localhost:3001/d/database-performance | Query performance, connections, cache |
| System Overview | http://localhost:3001/d/system-overview | CPU, memory, disk, network metrics |

### 1. API Performance Dashboard

**UID:** `api-performance` | **Panels:** 10 | **Tags:** api, performance, response-time

**Panels Overview:**
1. **API Status** - Overall service health (timeseries)
2. **p95 Response Time** - Gauge with thresholds: <200ms (green), <500ms (yellow), ≥500ms (red)
3. **p50 Response Time** - Gauge with thresholds: <100ms (green), <300ms (yellow), ≥300ms (red)
4. **Error Rate %** - Gauge with thresholds: <5% (green), <10% (yellow), ≥10% (red)
5. **Request Rate** - Gauge with thresholds: <100 rps (green), <500 rps (yellow), ≥500 rps (red)
6. **Response Time Percentiles** - p50, p95, p99 by endpoint
7. **Request Rate by Status Code** - 2xx, 4xx, 5xx breakdown
8. **Error Rate % by Endpoint** - Per-endpoint error tracking
9. **Request Duration Heatmap** - Visual distribution of request times
10. **Total Requests by Status Code** - Cumulative request counts

**Key Metrics Displayed:**
- Real-time API performance at multiple percentiles
- Endpoint-specific latency tracking
- Error rate monitoring with threshold alerts
- Request throughput tracking
- Duration distribution heatmap

**Required Prometheus Metrics:**
- `http_request_duration_seconds_bucket` (histogram)
- `http_requests_total` (counter with status label)
- `up{job="backend"}` (backend availability)

**When to Use:**
- Investigating API slowdowns
- Monitoring error rate spikes
- Analyzing request patterns
- Performance regression testing

---

### 2. Celery Tasks Dashboard

**UID:** `celery-tasks` | **Panels:** 9 | **Tags:** celery, tasks, workers

**Panels Overview:**
1. **Workers Status** - Worker availability over time (timeseries)
2. **Queue Depth** - Gauge: <5 (green), <20 (yellow), ≥20 (red)
3. **Active Workers** - Gauge: <1 (green), <5 (yellow), ≥5 (red)
4. **Task Rate** - Tasks/second by name and status
5. **Task Runtime** - p50, p95 percentiles by task name
6. **Failed Task Rate** - Failed tasks/second by name
7. **Successful Task Rate** - Successful tasks/second by name
8. **Task Success/Failure Rate %** - Success vs failure percentage
9. **Active Tasks per Worker** - Load balancing visualization

**Key Metrics Displayed:**
- Queue depth to detect backups
- Worker availability and load
- Task failure rates
- Task runtime distribution
- Success/failure ratios

**Required Prometheus Metrics:**
- `celery_workers_up` (worker availability gauge)
- `celery_queue_length` (queue depth gauge)
- `celery_tasks_total` (counter by name and status)
- `celery_task_runtime_seconds_bucket` (histogram)
- `celery_worker_tasks_active` (active tasks gauge)

**When to Use:**
- Monitoring background job processing
- Detecting worker failures
- Investigating task bottlenecks
- Queue capacity planning

---

### 3. ML Inference Dashboard

**UID:** `ml-inference` | **Panels:** 10 | **Tags:** ml, inference, model-performance

**Panels Overview:**
1. **ML Model Status** - Overall model health (timeseries)
2. **p95 Inference Time** - Gauge: <15s (green), <30s (yellow), ≥30s (red) ⚠️ **Spec Target**
3. **p50 Inference Time** - Gauge: <5s (green), <10s (yellow), ≥10s (red)
4. **Prediction Rate** - Gauge: <50 ops (green), <100 ops (yellow), ≥100 ops (red)
5. **Models Loaded** - Gauge: <5 (green), <10 (yellow), ≥10 (red)
6. **Inference Time Percentiles by Model** - p50, p95, p99 comparison
7. **Prediction Rate by Model** - Predictions/second by model_name
8. **Predictions by Type** - By model_name and prediction_type
9. **Inference Duration Heatmap** - Visual distribution
10. **Total Predictions by Model** - Cumulative counters

**Key Metrics Displayed:**
- ML model inference performance
- Per-model comparison
- Spec compliance (p95 < 30s)
- Model loading status
- Prediction throughput

**Required Prometheus Metrics:**
- `ml_inference_duration_seconds_bucket` (histogram with buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
- `ml_predictions_total` (counter by model_name and prediction_type)
- `ml_models_loaded` (gauge by model_type)

**Model Labels Tracked:**
- `model_name`: ranking_random_forest, ranking_gradient_boosting, skill_extractor, etc.
- `operation`: inference, training, embedding
- `prediction_type`: ranking, classification, scoring
- `model_type`: transformer, spacy, sklearn, custom

**When to Use:**
- Monitoring ML model performance
- Ensuring spec compliance (30s target)
- Comparing model performance
- Detecting model loading issues
- Performance profiling

**Spec Compliance:**
- ✅ Performance profiling for ML model inference (30s target threshold set)
- ✅ Inference timing metrics captured at multiple percentiles
- ✅ Model performance comparison visible

---

### 4. Database Performance Dashboard

**UID:** `database-performance` | **Panels:** 13 | **Tags:** database, postgres, performance, queries

**Panels Overview:**
1. **Database Status** - Overall DB health (timeseries)
2. **p95 Query Duration** - Gauge: <100ms (green), <500ms (yellow), ≥500ms (red)
3. **p50 Query Duration** - Gauge: <50ms (green), <200ms (yellow), ≥200ms (red)
4. **Active Connections** - Gauge: <50 (green), <100 (yellow), ≥100 (red)
5. **Query Rate** - Queries/second gauge
6. **Query Duration Percentiles by Operation** - p50, p95, p99 by operation and table
7. **Query Rate by Operation** - SELECT, INSERT, UPDATE, DELETE by table
8. **Database Connections Over Time** - Active vs idle
9. **Query Duration Heatmap** - Visual distribution
10. **Cache Hit vs Disk Read Rate** - Cache performance
11. **Transaction Commit/Rollback Rate** - Transaction success
12. **Cache Hit Ratio** - Percentage gauge
13. **Row Operations** - Affected rows by operation and table

**Key Metrics Displayed:**
- Query performance at multiple percentiles
- Connection pool utilization
- Cache effectiveness
- Transaction monitoring
- Row operation tracking

**Required Prometheus Metrics:**
- `db_query_duration_seconds_bucket` (histogram from SQLAlchemy instrumentation)
- `pg_stat_database_numbackends` (active connections)
- `pg_stat_database_blks_hit` (cache hits)
- `pg_stat_database_blks_read` (disk reads)
- `pg_stat_database_xact_commit` (transaction commits)
- `pg_stat_database_xact_rollback` (transaction rollbacks)

**When to Use:**
- Investigating slow queries
- Monitoring connection pool exhaustion
- Analyzing cache effectiveness
- Tracking transaction failures
- Database capacity planning

---

### 5. System Overview Dashboard

**UID:** `system-overview` | **Panels:** 7 | **Tags:** system, overview, infrastructure

**Panels Overview:**
1. **System Health** - High-level status overview
2. **CPU Usage %** - Per-container CPU utilization
3. **Memory Usage %** - Per-container memory utilization
4. **Disk Usage %** - Per-container disk utilization
5. **Network I/O** - Network traffic over time
6. **Container Status** - Table of all containers
7. **Service Uptime** - Service availability over time

**Key Metrics Displayed:**
- Container resource usage (CPU, memory, disk)
- Network I/O patterns
- Container status table
- Service uptime tracking

**Required Prometheus Metrics:**
- `container_cpu_usage_seconds_total` (from cAdvisor)
- `container_memory_usage_bytes` (from cAdvisor)
- `container_fs_usage_bytes` (from cAdvisor)
- `container_network_receive_bytes_total` (from cAdvisor)
- `container_network_transmit_bytes_total` (from cAdvisor)
- `up` (service availability)

**When to Use:**
- High-level system health check
- Resource capacity planning
- Detecting resource exhaustion
- Container status monitoring
- Network troubleshooting

---

### Dashboard Provisioning

Dashboards are automatically provisioned from JSON files in `monitoring/grafana/dashboards/`.

**Provisioning Configuration:**
- **Provider:** File-based dashboard provider
- **Dashboard Path:** `/var/lib/grafana/dashboards`
- **Docker Volume:** `./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro`
- **Auto-Discovery:** Enabled (loads all JSON files automatically)
- **Update Interval:** 10 seconds (dashboards reload automatically)
- **UI Updates:** Allowed (users can customize in Grafana UI)

**How It Works:**
1. Docker mounts local dashboard directory to Grafana container
2. Grafana provisioning config points to mounted directory
3. All JSON files are auto-loaded on startup
4. Configuration refreshes every 10 seconds
5. Users can customize dashboards in Grafana UI

**Dashboard Statistics:**
- **Total Dashboards:** 5
- **Total Panels:** 49
- **Total Metrics:** 24 unique metric types
- **Total Queries:** 54 PromQL queries
- **Gauge Panels:** 17 (with threshold indicators)
- **Timeseries Panels:** 27
- **Heatmap Panels:** 3

---

### Troubleshooting Dashboards

#### Dashboard Shows "No Data"

**Symptom:** All panels show "No Data" message

**Possible Causes:**
1. Prometheus is not scraping metrics from targets
2. Services are not running or not exposing metrics
3. Metrics have not been generated yet

**Solutions:**
```bash
# 1. Check Prometheus targets
open http://localhost:9090/targets
# Verify all targets are "UP"

# 2. Generate test data
curl http://localhost:8000/api/resumes  # API metrics
curl http://localhost:8000/health       # DB metrics

# 3. Check if metrics are available
curl http://localhost:9090/api/v1/query?query=up

# 4. Wait 15-30 seconds for Prometheus to scrape
```

#### Dashboard Not Found (404)

**Symptom:** Dashboard URL returns 404 error

**Solutions:**
```bash
# 1. Verify dashboard files exist
ls monitoring/grafana/dashboards/

# 2. Check Grafana logs for provisioning errors
docker logs grafana | grep -i error

# 3. Restart Grafana to reload provisioning
docker-compose restart grafana

# 4. Wait 10 seconds for provisioning to reload
```

#### PromQL Query Errors

**Symptom:** Panels show query syntax errors

**Solutions:**
```bash
# 1. Test queries in Prometheus UI first
open http://localhost:9090/graph

# 2. Check available metrics
open http://localhost:9090/all-metrics

# 3. Verify metric names match dashboard JSON
cat monitoring/grafana/dashboards/api-performance.json | grep '"expr"'
```

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
