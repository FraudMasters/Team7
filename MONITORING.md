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

## ML Model Monitoring

ML model monitoring goes beyond basic inference metrics to track model health, detect performance degradation, and ensure models continue to make accurate predictions over time.

### Why ML Monitoring Matters

ML models degrade over time due to:
- **Data Drift:** Input data distribution changes (e.g., new resume formats)
- **Concept Drift:** Relationship between inputs and outputs changes
- **Model Entropy:** Model performance degrades without retraining
- **Feature Changes:** New skills, technologies, or job market trends

### ML Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML MONITORING PIPELINE                       │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   Resume     │───▶│   Feature    │───▶│  Prediction  │    │
│  │    Input     │    │ Extraction   │    │   & Score    │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│         │                   │                    │             │
│         ▼                   ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              MONITORING METRICS COLLECTION              │ │
│  │  • Feature distributions (keywords, skills, experience) │ │
│  │  • Prediction scores (match percentages)                │ │
│  │  • Model confidence (probability distributions)         │ │
│  │  • Prediction latency (inference time)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                    │
│                           ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              DRIFT DETECTION ENGINE                     │ │
│  │  • Compare current vs. baseline distributions           │ │
│  │  • Statistical tests (KS test, Chi-square)              │ │
│  │  • Alert on significant drift                           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                    │
│                           ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              PERFORMANCE TRACKING                       │ │
│  │  • Accuracy metrics over time                           │ │
│  │  • Prediction quality scores                           │ │
│  │  • Model comparison (A/B testing)                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

### ML Model Metrics

| Metric | Type | Description | Healthy Range | Alert Threshold |
|--------|------|-------------|---------------|-----------------|
| `ml_model_accuracy` | Gauge | Model accuracy on validation set | > 85% | < 80% warning, < 75% critical |
| `ml_prediction_distribution` | Histogram | Distribution of prediction scores | Stable mean/stddev | Mean shift > 10% or stddev change > 20% |
| `ml_feature_drift_score` | Gauge | Statistical drift score for features | < 0.1 | > 0.1 warning, > 0.2 critical |
| `ml_model_confidence` | Histogram | Confidence scores of predictions | Mean > 0.7 | Mean < 0.6 warning |
| `ml_retraining_age` | Gauge | Days since last model retraining | < 30 days | > 30 warning, > 60 critical |
| `ml_prediction_volume` | Counter | Total predictions made | Increasing | Sudden drop > 50% |

**Key Query Examples:**
```promql
# Model accuracy trend
ml_model_accuracy{model_name="ranking_random_forest"}

# Prediction distribution shift
avg(ml_prediction_score{model_name="ranking_random_forest"}) by (model_name)

# Feature drift detection
ml_feature_drift_score{feature_name="skills"} > 0.1

# Model confidence over time
histogram_quantile(0.95, sum(rate(ml_model_confidence_bucket[5m])) by (le, model_name))

# Time since retraining
ml_retraining_age{model_name="ranking_random_forest"}
```

---

### Drift Detection

Drift detection monitors changes in the statistical properties of model inputs and outputs.

#### Types of Drift

| Drift Type | Description | Detection Method | Impact |
|------------|-------------|------------------|---------|
| **Covariate Drift** | Input feature distribution changes | Kolmogorov-Smirnov test, Population Stability Index (PSI) | Model may mispredict on new data |
| **Prior Probability Drift** | Class distribution changes | Chi-square test, KL divergence | Model may be biased toward old patterns |
| **Concept Drift** | Relationship between inputs and outputs changes | Accuracy tracking, error rate monitoring | Model becomes less accurate |
| **Feature Entropy** | New features emerge or old features disappear | Feature frequency tracking | Model may not recognize new patterns |

#### Drift Detection Metrics

**Population Stability Index (PSI):**

PSI measures how much a variable's distribution has changed over time.

| PSI Range | Interpretation | Action |
|-----------|----------------|--------|
| 0 - 0.1 | No significant drift | Monitor |
| 0.1 - 0.2 | Moderate drift | Investigate |
| > 0.2 | Significant drift | Retrain model |

**Example PromQL for PSI:**
```promql
# Calculate PSI for a feature (simplified)
abs(
  avg(ml_feature_value{feature="skills", window="baseline"}) -
  avg(ml_feature_value{feature="skills", window="current"})
) / stddev(ml_feature_value{feature="skills", window="baseline"})
```

**Kolmogorov-Smirnov Test:**

Detects if two samples come from the same distribution.

```python
# Backend implementation example
from scipy.stats import ks_2samp

def detect_feature_drift(baseline_features, current_features):
    """
    Detect drift using KS test

    Args:
        baseline_features: Feature values from training data
        current_features: Feature values from recent predictions

    Returns:
        {
            'ks_statistic': 0.15,
            'p_value': 0.001,
            'drift_detected': True,
            'drift_severity': 'high'
        }
    """
    ks_statistic, p_value = ks_2samp(baseline_features, current_features)

    return {
        'ks_statistic': ks_statistic,
        'p_value': p_value,
        'drift_detected': p_value < 0.05,  # 95% confidence
        'drift_severity': 'high' if ks_statistic > 0.15 else 'medium' if ks_statistic > 0.1 else 'low'
    }
```

#### Monitoring Key Features

Monitor these features for drift in the resume analysis pipeline:

| Feature | Monitoring Approach | Drift Indicators |
|---------|-------------------|------------------|
| **Skills** | Track top 100 skills frequency | New technologies (e.g., "Docker", "Kubernetes") emerge |
| **Experience Duration** | Track years of experience distribution | Shift in seniority levels of applicants |
| **Language** | Track language distribution (en/ru) | Change in applicant geography |
| **Document Format** | Track PDF vs DOCX ratio | New document types appear |
| **Text Length** | Track resume word count distribution | Resume length trends change |
| **Keywords** | Track keyword extraction results | New terminology or buzzwords emerge |

#### Drift Detection Alerts

Set up Grafana alerts for drift:

```yaml
# Feature Drift Alert
groups:
  - name: ml_drift_detection
    rules:
      - alert: HighFeatureDrift
        expr: ml_feature_drift_score > 0.2
        for: 5m
        labels:
          severity: critical
          component: ml
        annotations:
          summary: "Significant feature drift detected"
          description: "Feature '{{ $labels.feature_name }}' has drift score {{ $value }} (threshold: 0.2)"

      - alert: ModelAccuracyDrop
        expr: ml_model_accuracy < 0.75
        for: 10m
        labels:
          severity: critical
          component: ml
        annotations:
          summary: "Model accuracy dropped below 75%"
          description: "Model '{{ $labels.model_name }}' accuracy is {{ $value }}"

      - alert: PredictionDistributionShift
        expr: abs(avg(ml_prediction_score{model_name="ranking_random_forest"}) offset 1h - avg(ml_prediction_score{model_name="ranking_random_forest"})) > 0.1
        for: 5m
        labels:
          severity: warning
          component: ml
        annotations:
          summary: "Prediction distribution shifted significantly"
          description: "Prediction mean shifted by {{ $value }} in the last hour"
```

---

### Performance Tracking

Track ML model performance over time to identify degradation and retraining needs.

#### Performance Metrics

| Metric | Description | Calculation | Target |
|--------|-------------|-------------|--------|
| **Accuracy** | Percentage of correct predictions | (TP + TN) / Total | > 85% |
| **Precision** | True positives / All predicted positives | TP / (TP + FP) | > 80% |
| **Recall** | True positives / All actual positives | TP / (TP + FN) | > 80% |
| **F1 Score** | Harmonic mean of precision and recall | 2 × (Precision × Recall) / (Precision + Recall) | > 80% |
| **AUC-ROC** | Area under ROC curve | sklearn.metrics.roc_auc_score | > 0.85 |
| **Mean Squared Error** | Average squared difference | sklearn.metrics.mean_squared_error | < 0.1 |

#### Model Performance Dashboard Queries

**Accuracy Trend by Model:**
```promql
# Rolling accuracy over 7 days
avg(ml_model_accuracy{model_name="ranking_random_forest"}[7d])
```

**Prediction Quality Distribution:**
```promql
# Distribution of prediction confidence scores
sum(rate(ml_model_confidence_bucket[5m])) by (le, model_name)
```

**Model Comparison:**
```promql
# Compare accuracy across models
avg(ml_model_accuracy) by (model_name)
```

**Performance Degradation Detection:**
```promql
# Detect 10% drop in accuracy compared to baseline
(avg(ml_model_accuracy{model_name="ranking_random_forest"} offset 1h) - avg(ml_model_accuracy{model_name="ranking_random_forest"})) / avg(ml_model_accuracy{model_name="ranking_random_forest"} offset 1h) > 0.1
```

---

### Model Retracking & Retraining

Monitor when models need retraining.

#### Retraining Triggers

| Trigger | Metric | Threshold | Action |
|---------|--------|-----------|--------|
| **Time-based** | Days since retraining | > 30 days | Schedule retraining |
| **Performance-based** | Model accuracy | < 80% | Immediate retraining |
| **Drift-based** | Feature drift score | > 0.2 | Investigate, retrain if needed |
| **Volume-based** | Predictions since retraining | > 10,000 | Consider retraining |

#### Retraining Metrics

```promql
# Days since last retraining
ml_retraining_age{model_name="ranking_random_forest"}

# Predictions since retraining
ml_predictions_total{model_name="ranking_random_forest"} - ml_predictions_total{model_name="ranking_random_forest"} @ end(last_retraining_timestamp)

# Retraining frequency
count(increase(ml_retraining_total[30d])) by (model_name)
```

#### Retraining Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              MODEL RETRAINING WORKFLOW                          │
│                                                                  │
│  1. TRIGGER DETECTION                                            │
│     ├── Performance drop detected                               │
│     ├── Drift score exceeds threshold                           │
│     └── Scheduled retraining date reached                       │
│                           │                                     │
│                           ▼                                     │
│  2. DATA COLLECTION                                             │
│     ├── Recent labeled data (last 30 days)                      │
│     ├── Validation set (20% holdout)                            │
│     └── Test set (unseen data)                                  │
│                           │                                     │
│                           ▼                                     │
│  3. MODEL TRAINING                                              │
│     ├── Train new model version                                 │
│     ├── Hyperparameter tuning                                   │
│     └── Cross-validation                                        │
│                           │                                     │
│                           ▼                                     │
│  4. MODEL EVALUATION                                            │
│     ├── Compare new vs. old model                               │
│     ├── Verify performance improvement                          │
│     └── Check for regression on edge cases                      │
│                           │                                     │
│                           ▼                                     │
│  5. MODEL DEPLOYMENT                                            │
│     ├── A/B testing (10% traffic to new model)                  │
│     ├── Monitor for 24 hours                                    │
│     └── Full rollout if successful                              │
│                           │                                     │
│                           ▼                                     │
│  6. CLEANUP                                                      │
│     ├── Archive old model version                               │
│     ├── Update baseline metrics                                 │
│     └── Log retraining metadata                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Model A/B Testing

Test new model versions before full deployment.

#### A/B Testing Metrics

| Metric | Control (Model A) | Test (Model B) | Significance Test |
|--------|-------------------|----------------|-------------------|
| Accuracy | 85% | 87% | p-value < 0.05 |
| p95 Inference Time | 12s | 14s | Not significant |
| Prediction Volume | 1000 | 1000 | Equal traffic split |

#### A/B Testing PromQL Queries

```promql
# Compare accuracy between model versions
avg(ml_model_accuracy) by (model_version)

# Compare inference time
histogram_quantile(0.95, sum(rate(ml_inference_duration_seconds_bucket[5m])) by (le, model_version))

# Traffic split percentage
sum(rate(ml_predictions_total{model_version="v1.2"}[5m])) / sum(rate(ml_predictions_total[5m])) * 100

# Statistical significance (requires external calculation)
# Export metrics to Python/R for t-test or chi-square test
```

#### A/B Testing Configuration

```python
# A/B testing middleware (backend/api/ab_testing.py)
import random
import logging
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Track which model version made predictions
ab_test_predictions = Counter(
    'ml_ab_test_predictions_total',
    'Predictions made during A/B test',
    ['model_version', 'variant']
)

def get_model_version_for_request(resume_id: str, user_id: str = None) -> str:
    """
    Determine which model version to use for A/B testing

    Args:
        resume_id: Unique identifier for the resume
        user_id: Optional user identifier for consistent splitting

    Returns:
        Model version to use ('v1.1' or 'v1.2')
    """
    # 10% of traffic gets new model (v1.2)
    TRAFFIC_SPLIT = 0.10

    # Use user_id for consistent assignment if provided
    if user_id:
        # Hash user_id for deterministic assignment
        hash_val = hash(user_id) % 100
        use_new_model = hash_val < (TRAFFIC_SPLIT * 100)
    else:
        # Random assignment for anonymous requests
        use_new_model = random.random() < TRAFFIC_SPLIT

    model_version = "v1.2" if use_new_model else "v1.1"
    variant = "test" if use_new_model else "control"

    # Log the assignment
    logger.info(
        f"A/B test assignment",
        extra={
            "resume_id": resume_id,
            "user_id": user_id,
            "model_version": model_version,
            "variant": variant,
            "traffic_split": TRAFFIC_SPLIT
        }
    )

    # Track prediction count
    ab_test_predictions.labels(
        model_version=model_version,
        variant=variant
    ).inc()

    return model_version
```

---

### Model Health Dashboard

Create a dedicated dashboard in Grafana for ML model health monitoring.

**Dashboard Panels:**

1. **Model Accuracy Trend** - Timeseries of accuracy over 30 days
2. **Feature Drift Scores** - Gauge panel for top 10 features
3. **Prediction Distribution** - Histogram of prediction scores
4. **Model Confidence** - Heatmap of confidence distributions
5. **Retraining Status** - Single stat panel showing days since retraining
6. **A/B Test Results** - Comparison table of model versions
7. **Prediction Volume** - Timeseries of predictions per model
8. **Inference Time by Model** - Box plot of latency distributions

**Dashboard JSON Location:**
`monitoring/grafana/dashboards/ml-model-health.json`

---

### ML Monitoring Best Practices

#### ✅ DO

1. **Establish Baselines**
   - Capture feature distributions during training
   - Store baseline metrics for comparison
   - Document expected performance ranges

2. **Monitor Continuously**
   - Check drift metrics every hour
   - Review accuracy trends daily
   - Validate predictions on sample data weekly

3. **Set Up Alerts**
   - Alert on significant drift (> 0.2 PSI)
   - Alert on accuracy drops (> 10%)
   - Alert on prediction anomalies

4. **Version Models**
   - Track model versions in Git
   - Archive old model versions
   - Maintain rollback capability

5. **Document Retraining**
   - Log retraining triggers
   - Record performance improvements
   - Note any data quality issues

#### ❌ DON'T

1. **Don't Ignore Drift**
   - Small drift compounds over time
   - Investigate all drift alerts

2. **Don't Retrain Too Frequently**
   - Requires significant computation
   - May introduce instability
   - Set minimum retraining interval (7 days)

3. **Don't Skip Validation**
   - Always test on holdout set
   - Verify performance before deployment
   - Monitor for regression

4. **Don't Forget Edge Cases**
   - Test on rare resume formats
   - Validate on new skills/technologies
   - Check language-specific performance

---

### Troubleshooting ML Models

#### Model Accuracy Suddenly Dropped

**Symptoms:**
- Accuracy drops from 85% to 70%
- Drift alerts firing
- Prediction distribution shifted

**Investigation:**

```logql
# Check for recent code changes
{job="backend"} |~ "model.*version|model.*loaded"

# Check for data quality issues
{job="backend"} |~ "extraction.*error|parse.*error"

# Check for feature drift
{job="backend"} |~ "drift.*score|feature.*distribution"

# Check prediction distribution
{job="backend"} | json | unwrap prediction_score
```

**Solutions:**
1. Roll back to previous model version if degradation is severe
2. Investigate data quality issues
3. Collect new training data if drift is confirmed
4. Retrain model with updated data

#### High Feature Drift Detected

**Symptoms:**
- PSI score > 0.2 for skills feature
- New technologies not recognized
- Model confidence dropping

**Investigation:**

```promql
# Identify which features are drifting
ml_feature_drift_score{feature_name=~".*"} > 0.1

# Check prediction confidence for drifted features
avg(ml_model_confidence{feature_drift_detected="true"}) by (feature_name)
```

**Solutions:**
1. Update skill taxonomy with new technologies
2. Add training examples with new features
3. Retrain model with updated data
4. Monitor feature extraction pipeline

#### Model Inference Slow

**Symptoms:**
- p95 inference time > 60 seconds
- Tasks timing out
- Queue backup

**Investigation:**

```promql
# Check inference time by model
histogram_quantile(0.95, sum(rate(ml_inference_duration_seconds_bucket[5m])) by (le, model_name))

# Check if model is loading repeatedly
rate(ml_model_load_total[5m])
```

**Solutions:**
1. Pre-load models on worker startup (not per-request)
2. Implement model caching
3. Use batch inference for multiple resumes
4. Scale up Celery workers

---

### ML Monitoring Checklist

#### Daily Monitoring
- [ ] Check model accuracy metrics
- [ ] Review drift detection alerts
- [ ] Verify inference time performance
- [ ] Check prediction volume trends

#### Weekly Monitoring
- [ ] Analyze feature distributions
- [ ] Review model comparison metrics
- [ ] Validate on sample predictions
- [ ] Check retraining schedule

#### Monthly Monitoring
- [ ] Evaluate retraining necessity
- [ ] Review model performance over time
- [ ] Update baseline metrics if needed
- [ ] Document model behavior changes

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

## Log Querying with Loki

Loki uses LogQL (Loki Query Language) for querying logs. LogQL is similar to PromQL but designed for log data.

### LogQL Syntax Overview

```
{label selectors} |=|!|~ filter operators
```

**Components:**
1. **Label Selectors** - Target specific log streams (like Prometheus)
2. **Filter Operators** - Search within log content
3. **Pipeline Operators** - Transform and parse log data

### Label Selectors

Label selectors work exactly like Prometheus, targeting log streams by labels:

**Exact Match:**
```logql
{job="backend"}
{service="backend", environment="production"}
```

**Regex Match:**
```logql
{job=~"backend.*"}
{service=~"backend|frontend"}
{level=~"ERROR|CRITICAL"}
```

**Not Equal:**
```logql
{job!="backend"}
{service!="backend", level="ERROR"}
```

**Multiple Labels:**
```logql
{job="backend", level="ERROR"} |= "database"
{job=~"celery.*", level=~"WARNING|ERROR"}
```

**Available Labels in AgentHR:**
- `job`: backend, frontend, celery-worker
- `service`: backend, frontend, celery
- `environment`: production, development, test
- `level`: INFO, WARNING, ERROR, CRITICAL, DEBUG
- `module`: Python module name (e.g., analyzers.unified_matcher)
- `correlation_id`: Request tracking identifier

### Filter Operators

Filter operators search within the log line content:

**Line Filter (`|=`):** Contains string
```logql
{job="backend"} |= "error"
{service="backend"} |= "timeout"
```

**Not Line Filter (`!=`):** Does not contain string
```logql
{job="backend"} != "debug"
{service="backend"} != "health check"
```

**Regex Filter (`|~`):** Matches regex pattern
```logql
{job="backend"} |~ "error.*database"
{service="backend"} |~ "\d{3,}ms"  # Find durations
```

**Not Regex Filter (`!~`):** Does not match regex
```logql
{job="backend"} !~ "200 OK"
{service="backend"} !~ "^GET /health"
```

### Common Query Patterns

#### 1. Query by Correlation ID

Trace a single request through the system:

```logql
{job="backend"} |= "correlation_id=\"a1b2c3d4-e5f6-7890-abcd-ef1234567890\""
```

Or search across all services:

```logql
{job=~"backend|frontend|celery"} |~ "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

#### 2. Find Errors and Exceptions

**All errors:**
```logql
{level="ERROR"}
```

**Errors by service:**
```logql
{job="backend", level="ERROR"}
```

**Exceptions with traceback:**
```logql
{job="backend"} |~ "Traceback|Exception|Error"
```

**HTTP 5xx errors:**
```logql
{job="backend"} |= "status_code=5"
```

#### 3. Performance Analysis

**Slow operations (>1 second):**
```logql
{job="backend"} |~ "duration_ms.*[1-9][0-9]{3,}"
```

**Database query timing:**
```logql
{job="backend"} |~ "db_query_duration"
```

**Celery task runtime:**
```logql
{job="celery-worker"} |~ "task_runtime"
```

**API endpoint performance:**
```logql
{job="backend"} |~ "POST /api/resumes.*duration"
```

#### 4. Resume and Job Matching

**Analyze specific resume:**
```logql
{job="backend"} |= "resume_id=\"uuid-123\""
```

**Job matching operations:**
```logql
{job="backend"} |~ "match_score|vacancy_id"
```

**ML model predictions:**
```logql
{job="backend"} |~ "model_name|prediction_type"
```

**Skill extraction:**
```logql
{job="backend"} |~ "keyword|skill_extraction"
```

#### 5. Celery Task Monitoring

**Failed tasks:**
```logql
{job="celery-worker", level="ERROR"}
```

**Task status:**
```logql
{job="celery-worker"} |= "task.*success|task.*failed"
```

**Queue depth monitoring:**
```logql
{job="celery-worker"} |= "queue_length"
```

**Specific task by ID:**
```logql
{job="celery-worker"} |= "task_id=\"abc-123\""
```

#### 6. Database Queries

**Slow queries:**
```logql
{job="backend"} |~ "db_query_duration.*[1-9][0-9]{3,}ms"
```

**Query by table:**
```logql
{job="backend"} |= "table=\"resumes\""
```

**Connection pool issues:**
```logql
{job="backend"} |~ "pool.*timeout|connection.*exhausted"
```

#### 7. Security and Authentication

**Failed login attempts:**
```logql
{job="backend"} |~ "authentication.*failed|login.*failed"
```

**Authorization errors:**
```logql
{job="backend"} |~ "401|403|unauthorized|forbidden"
```

**User activity:**
```logql
{job="backend"} |= "user_id=\"123\""
```

### Advanced LogQL Features

#### Log Parser Pipeline

Extract and transform log data:

**JSON Parser:**
```logql
{job="backend"} | json
```

Then extract fields:
```logql
{job="backend"} | json | line_format "{{.correlation_id}} - {{.message}}"
```

**Regex Parser:**
```logql
{job="backend"} | regexp "(?P<timestamp>\\d{4}-\\d{2}-\\d{2}) (?P<level>\\w+) (?P<message>.*)"
```

**Label Extraction:**
```logql
{job="backend"} | label_format level={{.level}}
```

#### Aggregation Operators

**Count entries:**
```logql
count_over_time({job="backend"}[5m])
```

**Rate of log lines:**
```logql
rate({job="backend"}[5m])
```

**Sum values:**
```logql
sum_over_time({job="backend"} | json | unwrap duration_ms [5m])
```

**Percentiles:**
```logql
quantile_over_time(0.95, {job="backend"} | json | unwrap duration_ms [5m])
```

#### Time Ranges

**Last 5 minutes:**
```logql
{job="backend"}[5m]
```

**Last 1 hour:**
```logql
{job="backend"}[1h]
```

**Custom range:**
```logql
{job="backend"}[30s]
```

### Performance Best Practices

#### 1. Use Labels Effectively

✅ **Good:** Filter by labels first
```logql
{job="backend", level="ERROR"}
```

❌ **Bad:** Filter everything by content
```logql
{} |= "ERROR"
```

#### 2. Avoid Expensive Regex

✅ **Good:** Use string contains
```logql
{job="backend"} |= "error"
```

❌ **Bad:** Complex regex on all logs
```logql
{job="backend"} |~ ".*[Ee]rror.*"
```

#### 3. Limit Query Time Range

✅ **Good:** Recent data
```logql
{job="backend"}[1h]
```

❌ **Bad:** Very large ranges
```logql
{job="backend"}[7d]
```

#### 4. Combine Filters

✅ **Good:** Specific query
```logql
{job="backend", level="ERROR"} |= "database" |~ "timeout"
```

❌ **Bad:** Broad query
```logql
{} |= "error"
```

### Query Examples by Use Case

#### Debugging Production Issues

**1. User reports slow resume analysis:**
```logql
{job="backend"} |~ "resume_id=\"USER-RESUME-ID\""
```

Then check ML inference:
```logql
{job="backend"} |~ "resume_id=\"USER-RESUME-ID\"" |~ "inference|model"
```

**2. High error rate detected:**
```logql
{level="ERROR"}[5m]
```

Break down by service:
```logql
count_over_time({level="ERROR"}[5m]) by (job)
```

**3. Task queue backup:**
```logql
{job="celery-worker"} |= "queue_length"
```

Check worker status:
```logql
{job="celery-worker"} |~ "worker.*status"
```

#### Performance Analysis

**1. P95 response time:**
```logql
{job="backend"} | json | unwrap duration_ms | quantile_over_time(0.95, [5m])
```

**2. Database bottleneck:**
```logql
{job="backend"} |~ "db_query_duration" | json | unwrap duration_ms
```

**3. ML model performance:**
```logql
{job="backend"} |~ "ml_inference_duration" | json | unwrap duration_ms
```

#### Security Auditing

**1. Failed authentication:**
```logql
{job="backend"} |~ "auth.*failed|login.*failed"
```

**2. Unauthorized access attempts:**
```logql
{job="backend"} |= "401|403"
```

**3. Admin actions:**
```logql
{job="backend"} |~ "user.*admin|admin.*action"
```

### Loki API Queries

Query Loki directly via HTTP API:

**Basic query:**
```bash
curl -s -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={job="backend"} |= "error"' \
  --data-urlencode 'limit=100' | jq '.'
```

**Query with time range:**
```bash
curl -s -G http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="backend", level="ERROR"}' \
  --data-urlencode 'start=2024-01-15T00:00:00Z' \
  --data-urlencode 'end=2024-01-15T23:59:59Z' \
  --data-urlencode 'limit=1000' | jq '.'
```

**Query by label:**
```bash
curl -s http://localhost:3100/loki/api/v1/label/job/values | jq '.data[]'
```

### Grafana Integration

**In Grafana Explore:**
1. Navigate to Explore
2. Select Loki datasource
3. Enter LogQL query
4. Use "Label filters" button for easy label selection
5. Click "Run query"
6. Logs appear with full context and correlation

**Dashboard Panel Queries:**
```logql
{job="backend", level="ERROR"} | logfmt | line_format "{{.message}}"
```

**Table Panel:**
```logql
{job="backend"} | json | line_format "{{.timestamp}} {{.level}} {{.message}}"
```

### Troubleshooting Queries

**Query returns no results:**
1. Check label values exist:
   ```bash
   curl http://localhost:3100/loki/api/v1/labels | jq '.data[]'
   ```
2. Verify time range has data
3. Check syntax (matching brackets, quotes)
4. Test with broader query first

**Query is slow:**
1. Add more specific label selectors
2. Reduce time range
3. Avoid expensive regex patterns
4. Use `| unwrap` for numeric operations instead of regex

**Too many results:**
1. Add more filters
2. Reduce time range
3. Use aggregation: `count_over_time()`
4. Use `limit` parameter

---

## Request Tracing

Request tracing allows you to follow a single request as it travels through multiple services, making it easier to debug issues and understand system behavior.

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     REQUEST TRACING FLOW                        │
│                                                                  │
│  1. Frontend Request                                           │
│     ├── Generate correlation_id                                │
│     └── Send to Backend with X-Request-ID header               │
│                           │                                     │
│                           ▼                                     │
│  2. Backend API Processing                                     │
│     ├── Log correlation_id                                     │
│     ├── Process request (HTTP → Business Logic)                │
│     └── Forward to Celery if needed                            │
│                           │                                     │
│                           ▼                                     │
│  3. Background Task (Celery)                                   │
│     ├── Inherit correlation_id                                 │
│     ├── Execute ML analysis                                    │
│     └── Update database                                        │
│                           │                                     │
│                           ▼                                     │
│  4. Database Operations                                        │
│     ├── Query with trace metadata                              │
│     └── Return results                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Correlation ID Pattern

Every request in AgentHR includes a `correlation_id` that links all log entries across services.

#### Frontend (React)

```javascript
// Generate correlation ID on frontend
const generateCorrelationId = () => {
  return 'xxxx-xxxx-4xxx-yxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Send request with correlation ID
const correlationId = generateCorrelationId();

fetch('http://localhost:8000/api/resumes/upload', {
  method: 'POST',
  headers: {
    'X-Request-ID': correlationId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
}).then(response => {
  console.log(`Request ${correlationId} completed`);
});
```

#### Backend (FastAPI)

```python
from fastapi import Header, Request
import uuid
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Extract or generate correlation ID for each request"""
    correlation_id = request.headers.get("X-Request-ID")

    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Add to request state for use in endpoints
    request.state.correlation_id = correlation_id

    # Log the incoming request
    logger.info(
        f"Incoming request",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        }
    )

    # Process request
    response = await call_next(request)

    # Add correlation ID to response headers
    response.headers["X-Request-ID"] = correlation_id

    return response

# Usage in endpoint
@app.post("/api/resumes/upload")
async def upload_resume(request: Request):
    correlation_id = request.state.correlation_id

    logger.info(
        f"Processing resume upload",
        extra={
            "correlation_id": correlation_id,
            "action": "resume_upload_start"
        }
    )

    # ... processing logic ...

    logger.info(
        f"Resume upload completed",
        extra={
            "correlation_id": correlation_id,
            "action": "resume_upload_complete",
            "resume_id": resume.id
        }
    )
```

#### Celery Tasks

```python
from celery import Celery
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def analyze_resume_task(self, resume_id: str, correlation_id: str):
    """Background task with correlation ID tracing"""

    logger.info(
        f"Starting resume analysis",
        extra={
            "correlation_id": correlation_id,
            "task_id": self.request.id,
            "resume_id": resume_id,
            "action": "analysis_start"
        }
    )

    try:
        # Step 1: Extract text
        logger.info(
            f"Extracting text from resume",
            extra={
                "correlation_id": correlation_id,
                "step": "text_extraction",
                "resume_id": resume_id
            }
        )
        text = extract_text(resume_id)

        # Step 2: Detect language
        logger.info(
            f"Detecting language",
            extra={
                "correlation_id": correlation_id,
                "step": "language_detection"
            }
        )
        lang = detect_language(text)

        # Step 3: Extract keywords
        logger.info(
            f"Extracting keywords",
            extra={
                "correlation_id": correlation_id,
                "step": "keyword_extraction",
                "language": lang
            }
        )
        keywords = extract_keywords(text, lang)

        # Step 4: Save results
        logger.info(
            f"Saving analysis results",
            extra={
                "correlation_id": correlation_id,
                "step": "save_results",
                "keywords_count": len(keywords)
            }
        )
        save_results(resume_id, keywords)

        logger.info(
            f"Analysis completed successfully",
            extra={
                "correlation_id": correlation_id,
                "action": "analysis_complete",
                "duration_seconds": self.request.time_running
            }
        )

    except Exception as e:
        logger.error(
            f"Analysis failed",
            extra={
                "correlation_id": correlation_id,
                "action": "analysis_failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise
```

### Tracing Workflows

#### Complete Request Trace

**Scenario:** User uploads a resume and wants to see the full processing journey

**Step 1: Capture correlation ID from frontend**
```javascript
const correlationId = 'abc-123-def-456';
```

**Step 2: Find all logs for this request in Loki**
```logql
# All logs for this correlation ID across all services
{job=~"backend|celery-worker|frontend"} |~ "abc-123-def-456"
```

**Step 3: Filter by service to see the flow**
```logql
# Backend logs only
{job="backend"} |~ "abc-123-def-456"

# Celery worker logs only
{job="celery-worker"} |~ "abc-123-def-456"
```

**Step 4: View the complete trace timeline**
```logql
{job=~"backend|celery-worker"} |~ "abc-123-def-456" | logfmt | line_format "{{.timestamp}} {{.level}} [{{.job}}] {{.action}} - {{.message}}"
```

This produces output like:
```
2024-01-15T10:30:00Z INFO [backend] resume_upload_start - Processing resume upload
2024-01-15T10:30:01Z INFO [backend] resume_upload_complete - Resume upload completed
2024-01-15T10:30:02Z INFO [celery-worker] analysis_start - Starting resume analysis
2024-01-15T10:30:03Z INFO [celery-worker] text_extraction - Extracting text from resume
2024-01-15T10:30:05Z INFO [celery-worker] language_detection - Detecting language
2024-01-15T10:30:06Z INFO [celery-worker] keyword_extraction - Extracting keywords
2024-01-15T10:30:15Z INFO [celery-worker] save_results - Saving analysis results
2024-01-15T10:30:16Z INFO [celery-worker] analysis_complete - Analysis completed successfully
```

#### Performance Tracing

**Scenario:** Resume analysis is slow, identify the bottleneck

**Step 1: Find slow analyses**
```logql
{job="celery-worker"} | json | unwrap duration_seconds | quantile_over_time(0.95, [5m]) > 30
```

**Step 2: Get correlation IDs for slow requests**
```logql
{job="celery-worker"} | json | unwrap duration_seconds > 30
```

**Step 3: Trace slow request through all services**
```logql
{job=~"backend|celery-worker"} |~ "correlation_id=\"SLOW-REQUEST-UUID\""
```

**Step 4: Identify slow step**
```logql
{job="celery-worker"} |~ "correlation_id=\"SLOW-REQUEST-UUID\"" | json | unwrap step_duration_ms
```

### Tracing Tools

#### 1. Grafana Trace View

In Grafana Explore:
1. Select Loki datasource
2. Enter correlation ID query: `{job="backend"} |~ "abc-123-def-456"`
3. Click "Show context" to see surrounding logs
4. Use "Jump to" to navigate to specific time points

#### 2. Distributed Tracing with Loki

**Trace by labels:**
```logql
{job="backend", correlation_id="abc-123-def-456"}
```

**Trace with time range:**
```logql
{job="backend"} |~ "abc-123-def-456" | line_format "{{.timestamp}} {{.message}}"
```

**Extract timing information:**
```logql
{job="celery-worker"} |~ "abc-123-def-456" | json | unwrap duration_seconds
```

#### 3. Correlation ID Table

Create a dashboard panel showing all requests by correlation ID:

```logql
{job=~"backend|celery-worker"}
| json
| label_format correlation_id={{.correlation_id}}, action={{.action}}, job={{.job}}
| line_format "{{.correlation_id}} | {{.job}} | {{.action}} | {{.duration_ms}}"
```

### Best Practices

#### ✅ DO

1. **Always generate correlation IDs on the frontend** for user-initiated requests
2. **Include correlation ID in all log statements** across all services
3. **Return correlation ID in API responses** so clients can reference it
4. **Pass correlation ID to background tasks** as an explicit parameter
5. **Use structured logging** with consistent field names
6. **Log at entry/exit points** of each service boundary

#### ❌ DON'T

1. **Don't generate multiple correlation IDs** for a single logical request
2. **Don't log sensitive data** with correlation IDs (passwords, tokens)
3. **Don't rely on timestamps alone** for request correlation
4. **Don't omit correlation IDs from error logs** (they're most critical there)
5. **Don't use random UUIDs without logging them** consistently

### Request Tracing Example: Complete Flow

**User uploads resume → Backend validates → Celery analyzes → DB stores → Frontend notified**

```logql
# Trace complete upload workflow
{job=~"frontend|backend|celery-worker"} |~ "abc-123-def-456"
```

**Expected timeline:**
```
1. [frontend] Generated correlation_id: abc-123-def-456
2. [backend] Received upload request (abc-123-def-456)
3. [backend] Validated file type (abc-123-def-456)
4. [backend] Saved file to disk (abc-123-def-456)
5. [backend] Queued Celery task (abc-123-def-456)
6. [backend] Returned response to client (abc-123-def-456)
7. [celery-worker] Started analysis task (abc-123-def-456)
8. [celery-worker] Extracted text from PDF (abc-123-def-456)
9. [celery-worker] Detected language: en (abc-123-def-456)
10. [celery-worker] Extracted keywords (abc-123-def-456)
11. [celery-worker] Saved to database (abc-123-def-456)
12. [celery-worker] Task completed (abc-123-def-456)
```

---

## Debugging Workflows

Systematic procedures for diagnosing and resolving common issues in AgentHR.

### Debugging Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEBUGING METHODOLOGY                         │
│                                                                  │
│  1. Define Problem                                              │
│     ├── What is the symptom?                                    │
│     ├── When does it occur?                                     │
│     └── What is the expected behavior?                          │
│                           │                                     │
│                           ▼                                     │
│  2. Gather Information                                          │
│     ├── Check metrics (Grafana/Prometheus)                      │
│     ├── Search logs (Loki)                                      │
│     ├── Correlate events (correlation_id)                       │
│     └── Reproduce issue                                         │
│                           │                                     │
│                           ▼                                     │
│  3. Form Hypothesis                                             │
│     ├── Which component is failing?                             │
│     ├── What is the root cause?                                 │
│     └── What changed recently?                                  │
│                           │                                     │
│                           ▼                                     │
│  4. Test Hypothesis                                             │
│     ├── Verify with targeted queries                            │
│     ├── Test in isolation                                       │
│     └── Check configurations                                    │
│                           │                                     │
│                           ▼                                     │
│  5. Implement Fix                                               │
│     ├── Apply fix                                               │
│     ├── Test resolution                                         │
│     └── Monitor for recurrence                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Common Debugging Scenarios

#### Scenario 1: Resume Analysis Stuck in "Pending" State

**Symptoms:**
- Resume uploaded successfully
- Status remains "pending" after 30+ seconds
- No analysis results available

**Debugging Workflow:**

**Step 1: Check Celery Worker Status**
```bash
# Verify workers are running
docker-compose ps celery-worker

# Check worker logs
docker-compose logs celery-worker --tail=100
```

**Expected output:** Workers should show "celery@worker: Ready"
**Problem if:** No workers running or workers show "Disconnected"

**Step 2: Check Task Queue**
```logql
# Search for task creation
{job="backend"} |~ "resume_id=\"PROBLEM-RESUME-ID\"" |~ "task.*delay"
```

**Step 3: Check if Task Started**
```logql
# Celery received task?
{job="celery-worker"} |~ "resume_id=\"PROBLEM-RESUME-ID\""
```

**Step 4: Check for Errors**
```logql
# Any errors related to this resume?
{job="celery-worker", level="ERROR"} |~ "PROBLEM-RESUME-ID"
```

**Common Causes & Solutions:**

| Cause | Check | Solution |
|-------|-------|----------|
| No workers running | `docker-compose ps celery-worker` | `docker-compose up -d celery-worker` |
| Redis connection failed | Check logs for "Redis connection refused" | Verify Redis is running: `docker-compose up -d redis` |
| File not found | `{job="backend"} |~ "FileNotFoundError"` | Check upload directory permissions |
| Out of memory | `{job="celery-worker"} |~ "MemoryError"` | Increase worker memory limit |
| ML model not loaded | `{job="celery-worker"} |~ "Model.*not.*found"` | Download missing SpaCy models |

**Verification:**
```bash
# Trigger test analysis
curl -X POST http://localhost:8000/api/resumes/test-resume-id/analyze

# Check it completes within 30 seconds
```

---

#### Scenario 2: High API Latency (>5s)

**Symptoms:**
- API responses slow
- User complaints about load times
- Grafana shows p95 latency spike

**Debugging Workflow:**

**Step 1: Identify Slow Endpoints**
```promql
# P95 latency by endpoint
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```

**Step 2: Find Correlation IDs for Slow Requests**
```logql
# Find requests taking >5 seconds
{job="backend"} | json | unwrap duration_ms > 5000
```

**Step 3: Trace Slow Request**
```logql
# Full trace of slow request
{job="backend"} |~ "correlation_id=\"SLOW-REQUEST-ID\""
```

**Step 4: Identify Bottleneck**
```logql
# Check database query time
{job="backend"} |~ "correlation_id=\"SLOW-REQUEST-ID\"" | json | unwrap db_query_duration_ms

# Check external API calls
{job="backend"} |~ "correlation_id=\"SLOW-REQUEST-ID\"" |~ "http.*duration"

# Check ML inference time
{job="backend"} |~ "correlation_id=\"SLOW-REQUEST-ID\"" |~ "inference.*duration"
```

**Step 5: Check Database Performance**
```promql
# P95 query duration
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))

# Active connections
pg_stat_database_numbackends

# Cache hit ratio
sum(rate(pg_stat_database_blks_hit[5m])) / (sum(rate(pg_stat_database_blks_hit[5m])) + sum(rate(pg_stat_database_blks_read[5m]))) * 100
```

**Common Causes & Solutions:**

| Cause | Indicator | Solution |
|-------|-----------|----------|
| N+1 query problem | Many similar DB queries | Use `select_in` loading in SQLAlchemy |
| Missing index | Slow query on specific table | Add database index |
| Connection pool exhaustion | `numbackends` near max | Increase pool size |
| ML model slow loading | First request to endpoint | Pre-load models on startup |
| External API timeout | Waiting for LanguageTool | Add timeout, use fallback |

**Verification:**
```bash
# Test endpoint performance
ab -n 100 -c 10 http://localhost:8000/api/resumes/

# Should see p95 < 500ms
```

---

#### Scenario 3: High Error Rate (>5%)

**Symptoms:**
- Spike in 5xx errors
- Many HTTP 500 responses
- Alert notifications firing

**Debugging Workflow:**

**Step 1: Check Error Rate**
```promql
# Error percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

**Step 2: Identify Failing Endpoints**
```promql
# Error rate by endpoint
sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
```

**Step 3: Find Error Logs**
```logql
# All errors in last 5 minutes
{level="ERROR"}[5m]

# Errors by endpoint
{job="backend", level="ERROR"} |= "POST /api/resumes"
```

**Step 4: Check for Common Patterns**
```logql
# Database connection errors
{job="backend"} |~ "connection.*refused|pool.*exhausted"

# File system errors
{job="backend"} |~ "FileNotFoundError|Permission denied"

# Validation errors
{job="backend"} |~ "ValidationError|422"

# ML model errors
{job="celery-worker"} |~ "Model.*Error|Spacy.*Error"
```

**Step 5: Correlate with Deployments**
```bash
# Check recent changes
git log --since="1 hour ago"

# Check if deployment coincides with error spike
docker-compose ps
```

**Common Causes & Solutions:**

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `500` + `FileNotFoundError` | Resume file missing | Check file storage, restore from backup |
| `500` + `Connection pool exhausted` | Too many DB connections | Increase pool size or add connection limit |
| `422` + `ValidationError` | Client sending invalid data | Add client-side validation, update API docs |
| `500` + `Spacy.*Error` | ML model not loaded | Restart workers, verify model installation |
| `503` + `Service Unavailable` | Upstream service down | Check Redis, PostgreSQL availability |

**Verification:**
```bash
# Test endpoint returns 2xx
curl -w "%{http_code}" -o /dev/null -s http://localhost:8000/api/resumes/

# Should return 200
```

---

#### Scenario 4: Memory Leak (Gradual Slowdown)

**Symptoms:**
- System starts fast, slows down over hours
- Container memory usage increases continuously
- OOM kills after days

**Debugging Workflow:**

**Step 1: Monitor Memory Usage**
```promql
# Memory trend
container_memory_usage_bytes{container="backend"}

# Memory rate of change
rate(container_memory_usage_bytes{container="backend"}[1h])
```

**Step 2: Check for Growing Objects**
```logql
# Look for increasing metrics
{job="backend"} |~ "cache.*size|object.*count"
```

**Step 3: Profile Memory**
```bash
# Access container
docker-compose exec backend bash

# Use memory_profiler
pip install memory_profiler
python -m memory_profiler backend/api/main.py
```

**Step 4: Check Common Leak Sources**

**Celery task leaks:**
```logql
{job="celery-worker"} |~ "task.*result|task.*cache"
```

**Session leaks:**
```logql
{job="backend"} |~ "session.*created|session.*not.*closed"
```

**Model caching issues:**
```logql
{job="backend"} |~ "model.*loaded|cache.*size"
```

**Common Causes & Solutions:**

| Cause | Evidence | Solution |
|-------|----------|----------|
| Unbounded cache growth | Cache size keeps increasing | Set maxsize on caches, use TTL |
| SQLAlchemy sessions not closed | Many "session created" logs | Use context managers for sessions |
| ML models loaded repeatedly | Model loaded multiple times | Load models once at startup |
| File handles not closed | Too many open files error | Use `with open()` context manager |
| Celery result backend growing | Redis memory growing | Enable result expiration (`result_expires`) |

**Verification:**
```bash
# Monitor memory for 1 hour
watch -n 60 'docker stats backend --no-stream --format "table {{.MemUsage}}"'

# Memory should stabilize, not grow indefinitely
```

---

#### Scenario 5: Celery Task Queue Backup

**Symptoms:**
- Tasks waiting too long
- Queue depth > 100
- Users experience delays

**Debugging Workflow:**

**Step 1: Check Queue Depth**
```promql
# Current queue length
celery_queue_length
```

**Step 2: Check Worker Status**
```promql
# Active workers
celery_workers_up

# Tasks per worker
celery_worker_tasks_active
```

**Step 3: Identify Long-Running Tasks**
```logql
# Tasks running >5 minutes
{job="celery-worker"} | json | unwrap runtime_seconds > 300
```

**Step 4: Check Failure Rate**
```promql
# Failed task percentage
sum(rate(celery_tasks_total{status="failed"}[5m])) / sum(rate(celery_tasks_total[5m])) * 100
```

**Step 5: Find Stuck Tasks**
```logql
# Tasks started but not completed
{job="celery-worker"} |~ "task.*started" |~ "correlation_id=\"STUCK-TASK-ID\""

# No corresponding "completed" log
```

**Common Causes & Solutions:**

| Cause | Check | Solution |
|-------|-------|----------|
| Not enough workers | `celery_workers_up` < expected | Scale up workers: `docker-compose up -d --scale celery-worker=4` |
| Long-running tasks | Task runtime > 5 minutes | Break into smaller tasks, add timeouts |
| Workers crashed | `{job="celery-worker", level="ERROR"}` | Fix error, restart workers |
| Too many tasks enqueued | `celery_queue_length` > 1000 | Implement rate limiting |
| DB connection exhaustion | `pg_stat_database_numbackends` high | Increase DB pool or add connection limits |

**Verification:**
```bash
# Queue should drain within minutes
watch -n 10 'curl -s http://localhost:5555/api/tasks | jq ".queue_length"'

# Workers should show "Ready"
docker-compose logs celery-worker --tail=20 | grep "Ready"
```

---

### Debugging Checklist

Use this checklist when investigating issues:

#### Initial Assessment
- [ ] Define problem: What, when, where?
- [ ] Check current alerts (Grafana)
- [ ] Verify service status (docker-compose ps)
- [ ] Reproduce issue if possible

#### Information Gathering
- [ ] Check metrics (Prometheus/Grafana dashboards)
- [ ] Search recent logs (Loki)
- [ ] Find correlation IDs for affected requests
- [ ] Check error rates by service

#### Root Cause Analysis
- [ ] Identify failing component
- [ ] Trace request flow through system
- [ ] Check recent changes/deploys
- [ ] Review configuration files

#### Hypothesis Testing
- [ ] Form hypothesis about root cause
- [ ] Verify with targeted queries
- [ ] Test in isolation
- [ ] Check for similar past issues

#### Resolution
- [ ] Implement fix
- [ ] Verify issue resolved
- [ ] Monitor for 24 hours
- [ ] Document for future reference

### Debugging Tools Quick Reference

| Tool | Purpose | Command/URL |
|------|---------|-------------|
| **Grafana** | Metrics visualization | http://localhost:3001 |
| **Prometheus** | Metrics query | http://localhost:9090/graph |
| **Loki** | Log search | http://localhost:3100 |
| **Flower** | Celery monitoring | http://localhost:5555 |
| **docker-compose logs** | Container logs | `docker-compose logs -f backend` |
| **curl** | Test API endpoints | `curl -v http://localhost:8000/health` |
| **ab** | Load testing | `ab -n 100 -c 10 http://localhost:8000/api/resumes/` |
| **jq** | JSON parsing | `curl ... | jq '.'` |

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

### Alert Rules Overview

The monitoring stack includes pre-configured alert rules in `monitoring/grafana/provisioning/alerts/alert_rules.yml`:

| Alert Group | Alerts | Severity |
|-------------|--------|----------|
| **API Performance** | HighAPIErrorRate, CriticalAPIErrorRate, HighAPILatency, CriticalAPILatency | Warning/Critical |
| **Celery Tasks** | CeleryQueueBackup, CriticalCeleryQueueBackup, HighCeleryTaskFailureRate, CriticalCeleryTaskFailureRate, CeleryWorkersDown, SlowCeleryTasks | Warning/Critical |
| **ML Inference** | SlowMLInference, CriticalMLInference | Warning/Critical |
| **Database** | SlowDatabaseQueries, CriticalDatabaseQueries | Warning/Critical |
| **System** | ServiceDown, HighMemoryUsage | Warning/Critical |

**Total:** 16 alert rules across 5 groups

### Alert Notification Channels

Grafana supports multiple notification channels. Configure them via environment variables or the Grafana UI at http://localhost:3001/alerting/notifications.

---

## Email Alerts

### Configuration

Add the following environment variables to your `.env` file:

```bash
# SMTP Configuration
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password
GRAFANA_SMTP_FROM_ADDRESS=grafana@yourdomain.com
GRAFANA_SMTP_FROM_NAME=Grafana Alerts

# Alert Recipient
ALERT_EMAIL_ADDRESS=alerts@example.com
```

### Email Provider Examples

#### Gmail

```bash
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password  # Use an App Password, not your account password
```

**Creating a Gmail App Password:**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable **2-Step Verification** (if not already enabled)
3. Navigate to **Security** → **App Passwords**
4. Select "Mail" and your device
5. Generate and copy the 16-character password
6. Paste into `GRAFANA_SMTP_PASSWORD`

**⚠️ Important:** Gmail requires App Passwords for applications. Your regular password won't work.

#### Outlook / Office365

```bash
GRAFANA_SMTP_HOST=smtp.office365.com:587
GRAFANA_SMTP_USER=your_email@outlook.com
GRAFANA_SMTP_PASSWORD=your_password
```

#### SendGrid

```bash
GRAFANA_SMTP_HOST=smtp.sendgrid.net:587
GRAFANA_SMTP_USER=apikey
GRAFANA_SMTP_PASSWORD=SG.your_api_key_here
```

#### AWS SES (Simple Email Service)

```bash
GRAFANA_SMTP_HOST=email-smtp.us-east-1.amazonaws.com:587
GRAFANA_SMTP_USER=your_ses_smtp_username
GRAFANA_SMTP_PASSWORD=your_ses_smtp_password
```

### Applying Email Configuration

1. **Add to .env:**
   ```bash
   # Edit .env file
   nano .env
   ```

2. **Restart Grafana:**
   ```bash
   docker-compose restart grafana
   ```

3. **Verify Configuration:**
   - Go to http://localhost:3001/alerting/notifications
   - Click on "email-alerts" contact point
   - Click "Send test notification"
   - Check your inbox for the test email

---

## Slack Alerts

### Webhook Integration

Slack notifications use Incoming Webhooks to post alerts to channels.

#### Setup Steps

1. **Create a Slack App**
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Select "From scratch"
   - Name your app (e.g., "Grafana Alerts")
   - Select your workspace

2. **Enable Incoming Webhooks**
   - Navigate to "Incoming Webhooks" in the app settings
   - Toggle "Activate Incoming Webhooks" to On
   - Click "Add New Webhook to Workspace"

3. **Select Channel**
   - Choose the channel where alerts should be posted
   - Click "Allow"

4. **Copy Webhook URL**
   - Copy the webhook URL (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)
   - Add to your `.env` file:
   ```bash
   ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

5. **Restart Grafana:**
   ```bash
   docker-compose restart grafana
   ```

#### Customizing Slack Messages

The webhook integration automatically formats alerts with:
- Alert name and severity
- Current value and threshold
- Alert state (Firing/Resolved)
- Direct link to the alert in Grafana
- Timestamp

To customize the message format, edit `monitoring/grafana/provisioning/alerting/contactpoints.yml`:

```yaml
slug: webhook-alerts
settings:
  url: ${ALERT_WEBHOOK_URL}
  # Optional: Customize message format
  # title: '{{ .Status }}: {{ .Labels.alertname }}'
  # body: |
  #   *Alert:* {{ .Labels.alertname }}
  #   *Severity:* {{ .Labels.severity }}
  #   *Value:* {{ .Value }}
  #   *Details:* {{ .ExternalURL }}
```

---

## PagerDuty Alerts

### Configuration

PagerDuty integration requires a Grafana plugin and API credentials.

#### Setup Steps

1. **Install PagerDuty Plugin** (if not pre-installed)
   ```bash
   # Access Grafana container
   docker-compose exec grafana bash

   # Install plugin
   grafana-cli plugins install grafana-pagerduty-datasource

   # Restart Grafana
   exit
   docker-compose restart grafana
   ```

2. **Get PagerDuty Credentials**
   - Log into PagerDuty
   - Go to **Integrations** → **API Access**
   - Create a new API key or use existing one
   - Note your PagerDuty account subdomain (e.g., `company.pagerduty.com`)

3. **Configure in Grafana UI**
   - Navigate to http://localhost:3001/alerting/notifications
   - Click "Add contact point"
   - Select "PagerDuty" from the dropdown
   - Enter:
     - **Name:** `pagerduty-alerts`
     - **Integration Key:** Your PagerDuty integration key
     - **Severity:** Map alert severities (Critical → High, Warning → Low)
   - Click "Save"

4. **Link Alerts to PagerDuty**
   - Go to http://localhost:3001/alerting/rules
   - For each alert rule, click "Edit"
   - Under "Contact point", select "pagerduty-alerts"
   - Save changes

#### Alternative: Using Webhook with PagerDuty Events API

If the plugin isn't available, use PagerDuty's Events v2 API:

```bash
# Add to .env
PAGERDUTY_INTEGRATION_KEY=your_integration_key_here
PAGERDUTY_API_URL=https://events.pagerduty.com/v2/enqueue
```

Then configure a webhook in Grafana pointing to the PagerDuty Events API with a custom payload format.

---

## Microsoft Teams Alerts

### Webhook Integration

#### Setup Steps

1. **Create Incoming Webhook in Teams**
   - Go to your Microsoft Team channel
   - Click the "..." (ellipsis) next to the channel name
   - Select **Connectors**
   - Search for "Incoming Webhook"
   - Click "Configure"
   - Name it "Grafana Alerts" (optional: add an image)
   - Click "Create"
   - Copy the webhook URL

2. **Configure in Grafana**
   ```bash
   # Add to .env
   ALERT_WEBHOOK_URL=https://your-org.webhook.office.com/webhookb2/xxx/IncomingWebhook/yyy/zzz
   ```

3. **Restart Grafana**
   ```bash
   docker-compose restart grafana
   ```

#### Customizing Teams Messages

Edit `monitoring/grafana/provisioning/alerting/contactpoints.yml` to format messages as Teams adaptive cards:

```yaml
settings:
  url: ${ALERT_WEBHOOK_URL}
  http_method: POST
  # Custom JSON payload for Teams
  # {
  #   "type": "message",
  #   "attachments": [
  #     {
  #       "contentType": "application/vnd.microsoft.card.adaptive",
  #       "content": {
  #         "type": "AdaptiveCard",
  #         "body": [
  #           {
  #             "type": "TextBlock",
  #             "text": "{{ .Labels.alertname }}",
  #             "weight": "bolder",
  #             "size": "medium"
  #           }
  #         ]
  #       }
  //     }
  //   ]
  // }
```

---

## Discord Alerts

### Webhook Integration

#### Setup Steps

1. **Create Discord Webhook**
   - Open Discord Server Settings
   - Go to **Integrations** → **Webhooks**
   - Click "New Webhook"
   - Select the channel
   - Name it "Grafana Alerts"
   - Copy the webhook URL

2. **Configure in Grafana**
   ```bash
   # Add to .env
   ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
   ```

3. **Restart Grafana**
   ```bash
   docker-compose restart grafana
   ```

#### Discord Message Formatting

Discord supports embedded messages. Configure in `contactpoints.yml`:

```yaml
settings:
  url: ${ALERT_WEBHOOK_URL}
  # Discord embed format
  # {
  #   "embeds": [{
  #     "title": "{{ .Labels.alertname }}",
  #     "description": "{{ .Annotations.description }}",
  #     "color": {{ if eq .Status "firing" }}16711680{{ else }}65280{{ end }},
  #     "fields": [
  #       {"name": "Severity", "value": "{{ .Labels.severity }}"},
  #       {"name": "Value", "value": "{{ .Value }}"}
  //     ]
  //   }]
  // }
```

---

## Custom Webhook Endpoints

For custom integrations, configure any HTTP endpoint as a notification target.

### Configuration

```bash
# Add to .env
ALERT_WEBHOOK_URL=https://your-custom-endpoint.com/alerts
```

### Webhook Payload Format

Grafana sends the following JSON payload:

```json
{
  "receiver": "webhook-alerts",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighAPIErrorRate",
        "severity": "critical",
        "job": "backend"
      },
      "annotations": {
        "description": "API error rate is above 15%",
        "summary": "Critical error rate detected"
      },
      "startsAt": "2024-01-15T10:30:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://localhost:3001/",
      "fingerprint": "abc123"
    }
  ],
  "groupLabels": {},
  "commonLabels": {},
  "commonAnnotations": {},
  "externalURL": "http://localhost:3001/"
}
```

### Custom Endpoint Requirements

Your endpoint should:
- Accept HTTP POST requests
- Process JSON payloads
- Return HTTP 2xx on success
- Handle retries gracefully (Grafana retries on failure)

---

## Testing Alert Notifications

### Test Email

1. **Navigate to:** http://localhost:3001/alerting/notifications
2. **Click:** "email-alerts" contact point
3. **Click:** "Send test notification" button
4. **Check:** Your email inbox (including spam folder)

### Test Webhook (Slack/Discord/Teams)

1. **Navigate to:** http://localhost:3000/alerting/notifications
2. **Click:** "webhook-alerts" contact point
3. **Click:** "Send test notification" button
4. **Verify:** Message appears in your channel

### Test Alert Rules

Manually trigger alerts to verify end-to-end functionality:

```bash
# Test 1: Service Down Alert
# Stop backend service
docker-compose stop backend
# Wait 2 minutes, check alert fires at: http://localhost:3001/alerting/rules
# Restart backend
docker-compose start backend

# Test 2: High Error Rate Alert
# Generate errors
for i in {1..500}; do
  curl -s http://localhost:8000/api/nonexistent-$i
done
# Wait 2 minutes, check "HighAPIErrorRate" alert
```

---

## Notification Best Practices

### 1. Use Appropriate Severity Levels

- **Critical:** Service down, data loss, security breach
- **Warning:** Performance degradation, high resource usage
- **Info:** Routine tasks, capacity planning

### 2. Set Up Multiple Channels

```bash
# Primary (immediate): Slack/Discord for critical
# Secondary (follow-up): Email for warnings
# Tertiary (documentation): PagerDuty for incidents
```

### 3. Configure Notification Policies

Create routing rules in Grafana:

1. Go to http://localhost:3001/alerting/routes
2. Define routes based on labels:
   ```
   severity=critical → Slack + PagerDuty
   severity=warning → Email
   ```
3. Set mute timings for maintenance windows

### 4. Test Regularly

- Weekly test notifications
- Verify channel configurations
- Update contact points as team changes

### 5. Avoid Alert Fatigue

- Tune thresholds to reduce false positives
- Use meaningful alert descriptions
- Group related alerts
- Set appropriate `for` durations (wait time before firing)

---

## Troubleshooting Notifications

### Emails Not Arriving

**Check Grafana logs:**
```bash
docker-compose logs grafana | grep -i smtp
```

**Common issues:**
- **Gmail:** Use App Password, not account password
- **Firewall:** Ensure port 587 is not blocked
- **Authentication:** Verify username/password are correct
- **From Address:** Must match SMTP user for some providers

**Test SMTP manually:**
```bash
docker-compose exec grafana nc -vz smtp.gmail.com 587
```

### Webhook Failures

**Check webhook URL accessibility:**
```bash
# Test from Grafana container
docker-compose exec grafana curl -X POST $ALERT_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

**Common issues:**
- **Firewall:** Webhook URL blocked from container
- **SSL:** Certificate validation errors
- **Rate Limiting:** Service rejecting too many requests
- **Expired Tokens:** Slack/Discord webhooks expire

### Alert Not Firing

**Verify in Prometheus:**
1. Go to http://localhost:9090/alerts
2. Check if alert is in "Pending" or "Firing" state
3. Verify metric data exists

**Check evaluation interval:**
- Default: 30 seconds
- Alert must be true for entire `for` duration before firing

**Check notification linkage:**
1. Go to http://localhost:3001/alerting/rules
2. Click alert rule
3. Verify "Contact point" is set
4. Check "Notification policies" aren't blocking

---

## Alert Configuration Files

| File | Purpose |
|------|---------|
| `monitoring/grafana/provisioning/alerts/alert_rules.yml` | Alert rule definitions |
| `monitoring/grafana/provisioning/alerting/contactpoints.yml` | Notification channels (email, webhook) |
| `monitoring/grafana/provisioning/alerting/policies.yml` | Notification routing policies |
| `monitoring/prometheus/prometheus.yml` | Prometheus alert configuration |

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
