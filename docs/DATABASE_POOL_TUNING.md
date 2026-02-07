# Database Pool Tuning Guide

## Executive Summary

This guide provides comprehensive instructions for analyzing workload and tuning the database connection pool for optimal performance in the AgentHR backend. Connection pool tuning is critical for applications with high concurrent request volumes to prevent connection exhaustion and minimize latency.

**What You'll Learn:**
- How to analyze your database workload patterns
- Formulas for calculating optimal pool size and overflow
- How to monitor pool health and performance metrics
- Step-by-step tuning process for production environments

**Key Configuration Parameters:**

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| `DB_POOL_SIZE` | 10 | 1-100 | Base number of persistent connections |
| `DB_MAX_OVERFLOW` | 20 | 0-100 | Additional connections created during peak load |
| `DB_POOL_TIMEOUT` | 30 | 1-300 | Max wait time (seconds) to acquire connection |
| `DB_POOL_RECYCLE` | 3600 | 0-86400 | Recycle connections after N seconds |

**Total Max Connections** = `DB_POOL_SIZE` + `DB_MAX_OVERFLOW` = **30** (default)

---

## Table of Contents

1. [Understanding Connection Pooling](#understanding-connection-pooling)
2. [Workload Analysis](#workload-analysis)
3. [Pool Sizing Formulas](#pool-sizing-formulas)
4. [Monitoring Setup](#monitoring-setup)
5. [Tuning Process](#tuning-process)
6. [Common Scenarios](#common-scenarios)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Understanding Connection Pooling

### What is a Connection Pool?

A connection pool maintains a cache of database connections that can be reused across requests, eliminating the overhead of establishing a new connection for each request.

**SQLAlchemy's QueuePool Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│                  (FastAPI Endpoints)                    │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Request Connection
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Connection Pool                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Pool Size (Permanent Connections)                │  │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │  │
│  │  │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │...│ │ 9 │ │10 │ │  │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Overflow (Temporary, On-Demand Connections)     │  │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │  │
│  │  │11 │ │12 │ │13 │ │14 │ │15 │ │...│ │29 │ │30 │ │  │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ │  │
│  └───────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Active Connection
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                    │
│              (max_connections = 100 default)            │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

**Pool Size (`DB_POOL_SIZE`):**
- Permanent connections maintained at all times
- Should match your average concurrent database workload
- Too small: Connection wait times increase
- Too large: Wasted database resources

**Max Overflow (`DB_MAX_OVERFLOW`):**
- Additional connections created during traffic spikes
- Temporary connections that return to pool when idle
- Should match your peak load above baseline
- Prevents connection exhaustion during bursts

**Pool Timeout (`DB_POOL_TIMEOUT`):**
- Maximum time to wait for an available connection
- If exceeded, request fails with timeout error
- Should be set based on acceptable request latency

**Pool Recycle (`DB_POOL_RECYCLE`):**
- Connections closed and recreated after N seconds
- Prevents issues with stale/corrupted connections
- Should be less than database's `idle_session_timeout`

---

## Workload Analysis

Before tuning the pool, you must understand your application's database access patterns.

### Step 1: Measure Current Metrics

**Enable Query Logging:**

```bash
# In .env file
LOG_LEVEL=DEBUG
```

**Collect Metrics Over Time:**

Monitor your application under typical load for at least 24-48 hours:

```bash
# Access pool metrics endpoint
curl http://localhost:8000/metrics | grep db_pool
```

**Key Metrics to Track:**

| Metric | Prometheus Metric | What It Tells You |
|--------|------------------|-------------------|
| Pool size used | `db_pool_size` | Current pool configuration |
| Overflow used | `db_pool_overflow` | How many overflow connections active |
| Checked out | `db_pool_checked_out` | Connections currently in use |
| Available | `db_pool_available` | Idle connections ready for use |
| Checkout duration | `db_pool_checkout_duration_seconds` | Time to acquire connection |

### Step 2: Analyze Traffic Patterns

**Concurrent Request Analysis:**

Use application logs or Prometheus to determine:

```python
# Average concurrent database requests
avg_concurrent_requests = (requests_per_minute * avg_query_duration_seconds) / 60

# Example calculation:
# - 1000 requests/minute
# - Average query duration: 0.5 seconds
# avg_concurrent_requests = (1000 * 0.5) / 60 = 8.3 connections
```

**Peak vs. Average:**

```
Average Load: 50-100 concurrent requests
Peak Load: 200-300 concurrent requests (during business hours)
Peak Duration: 2-3 hours
```

### Step 3: Database Limits

**Check PostgreSQL Maximum Connections:**

```sql
-- Run in PostgreSQL
SHOW max_connections;
-- Default: 100 (varies by hosting provider)

-- Check current usage
SELECT count(*) FROM pg_stat_activity;
```

**Important Formula:**

```
Total App Connections ≤ (PostgreSQL max_connections * 0.8)
Leave 20% buffer for superusers, maintenance, and other apps
```

### Step 4: Query Performance Profile

**Slow Query Identification:**

```python
# Check query duration metrics
curl http://localhost:8000/metrics | grep db_query_duration_seconds

# Look for:
# - P95 duration > 100ms: Consider query optimization
# - P95 duration > 500ms: Major optimization needed
```

**N+1 Query Impact:**

N+1 queries multiply pool pressure:
- **1 request** with N+1 queries = N+1 connection checkouts
- **100 requests** × **10 queries** each = 1,000 connection checkouts
- **Solution:** Use eager loading (see PERFORMANCE_IMPROVEMENTS.md)

---

## Pool Sizing Formulas

### Formula 1: Baseline Pool Size

Calculate the base pool size for average load:

```python
baseline_pool_size = ceil(
    (average_concurrent_db_requests * 1.2)
)

# Safety factor of 1.2 (20% buffer)
# Example: 10 concurrent requests × 1.2 = 12 connections
# Set DB_POOL_SIZE = 12
```

**Rationale:**
- Pool size should be slightly above average concurrent load
- The 20% buffer handles minor traffic fluctuations
- Prevents connection wait during normal operations

### Formula 2: Overflow Sizing

Calculate overflow for peak load spikes:

```python
max_overflow = ceil(
    (peak_concurrent_db_requests - baseline_pool_size) * 0.8
)

# Example calculation:
# - Peak concurrent: 50 requests
# - Baseline pool: 12 connections
# - max_overflow = (50 - 12) * 0.8 = 30.4 → 30 connections
# Set DB_MAX_OVERFLOW = 30
```

**Rationale:**
- Overflow handles the difference between peak and baseline
- 80% factor accounts for not all peak requests needing DB simultaneously
- Overflow connections are temporary and only created when needed

### Formula 3: Timeout Calculation

Calculate pool timeout based on acceptable latency:

```python
pool_timeout_seconds = ceil(
    p95_query_duration_seconds * 3
)

# Example:
# - P95 query duration: 0.2 seconds
# - pool_timeout = 0.2 * 3 = 0.6 → 1 second (minimum)
# Set DB_POOL_TIMEOUT = 30 (default is usually sufficient)
```

**Rationale:**
- Timeout should accommodate multiple queuing cycles
- Most requests should acquire connection in < 1 second under normal load
- 30-second default handles extreme cases

### Formula 4: Recycle Interval

Set connection recycle to match database settings:

```python
pool_recycle_seconds = min(
    postgresql_idle_session_timeout - 300,
    3600  # 1 hour default
)

# Example:
# - PostgreSQL idle_session_timeout: 3600 seconds
# - pool_recycle = 3600 - 300 = 3300 seconds
# Set DB_POOL_RECYCLE = 3300
```

**Rationale:**
- Recycle connections before database closes them
- 5-minute safety buffer prevents race conditions
- Prevents "server closed the connection" errors

---

## Monitoring Setup

### Prometheus Metrics Endpoint

The backend exposes pool metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics | grep db_pool
```

**Available Pool Metrics:**

```
# Pool configuration
db_pool_size 10.0
db_pool_overflow 20.0

# Real-time pool state
db_pool_checked_out 7.0
db_pool_available 3.0

# Checkout timing
db_pool_checkout_duration_seconds_bucket{le="0.1"} 850
db_pool_checkout_duration_seconds_bucket{le="0.5"} 950
db_pool_checkout_duration_seconds_bucket{le="1.0"} 990
db_pool_checkout_duration_seconds_bucket{le="+Inf"} 1000
db_pool_checkout_duration_seconds_sum 45.5
db_pool_checkout_duration_seconds_count 1000
```

### Grafana Dashboard

**Recommended Panel Configuration:**

**Panel 1: Pool Utilization Gauge**
```promql
(db_pool_checked_out / (db_pool_size + db_pool_overflow)) * 100
```
- **Warning:** > 70%
- **Critical:** > 90%

**Panel 2: Overflow Usage Trend**
```promql
rate(db_pool_overflow[5m])
```
- Monitor how often overflow is used

**Panel 3: Checkout Duration (P95)**
```promql
histogram_quantile(0.95, rate(db_pool_checkout_duration_seconds_bucket[5m]))
```
- **Warning:** > 0.5 seconds
- **Critical:** > 2.0 seconds

**Panel 4: Checkout Errors**
```promql
rate(db_pool_checkouts_total{status="error"}[5m])
```
- Should be zero under normal operation

### Alerting Rules

**Example Prometheus Alert:**

```yaml
groups:
  - name: database_pool
    rules:
      - alert: HighPoolUtilization
        expr: |
          (db_pool_checked_out / (db_pool_size + db_pool_overflow)) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database pool utilization above 80%"
          description: "Pool at {{ $value }}% capacity"

      - alert: PoolCheckoutTimeout
        expr: |
          rate(db_pool_checkouts_total{status="timeout"}[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Database pool checkout timeouts detected"

      - alert: SlowCheckout
        expr: |
          histogram_quantile(0.95,
            rate(db_pool_checkout_duration_seconds_bucket[5m])
          ) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P95 pool checkout time exceeds 1 second"
```

### Health Check Integration

The pool metrics are included in the `/ready` endpoint:

```bash
curl http://localhost:8000/ready
```

**Response:**
```json
{
  "status": "ready",
  "database": {
    "connected": true,
    "pool": {
      "size": 10,
      "checked_out": 3,
      "available": 7,
      "overflow": 0
    }
  }
}
```

---

## Tuning Process

Follow this systematic approach to tune your pool for production.

### Phase 1: Baseline Setup (1-2 days)

**Step 1: Start with Conservative Defaults**

```bash
# .env file
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

**Step 2: Enable Monitoring**

```bash
# Verify metrics are available
curl http://localhost:8000/metrics | grep db_pool
```

**Step 3: Deploy to Staging**

Deploy with monitoring and observe for 24-48 hours under typical load.

### Phase 2: Workload Analysis (1 week)

**Step 1: Collect Metrics**

Gather data across different time periods:

- **Off-peak hours** (night/weekend)
- **Normal business hours**
- **Peak traffic periods**

**Step 2: Identify Patterns**

```python
# Calculate from metrics
avg_checked_out = average(db_pool_checked_out)
max_checked_out = max(db_pool_checked_out)
p95_checked_out = percentile(db_pool_checked_out, 95)
overflow_usage_rate = (db_pool_overflow > 0) / total_samples
```

**Step 3: Document Findings**

Create a workload profile:

| Metric | Value | Notes |
|--------|-------|-------|
| Avg concurrent requests | 8 | Normal hours |
| Peak concurrent requests | 35 | 10am-2pm weekday |
| P95 query duration | 0.15s | Good performance |
| Pool utilization (avg) | 65% | Healthy |
| Pool utilization (peak) | 95% | Needs attention |
| Overflow usage frequency | 15% of time | Occasional spikes |

### Phase 3: Calculate Target Settings

Using formulas from [Pool Sizing Formulas](#pool-sizing-formulas):

**Given:**
- Average concurrent: 8 requests
- Peak concurrent: 35 requests
- P95 query duration: 0.15s

**Calculations:**

```python
# Baseline pool size
baseline = ceil(8 * 1.2) = 10 connections

# Overflow
overflow = ceil((35 - 10) * 0.8) = 20 connections

# Timeout
timeout = ceil(0.15 * 3) = 1 second → use 30 (default)
```

**Result:**
```bash
DB_POOL_SIZE=10      # Matches average load + buffer
DB_MAX_OVERFLOW=20   # Handles peak spikes
DB_POOL_TIMEOUT=30   # Default is sufficient
DB_POOL_RECYCLE=3600 # Default (1 hour)
```

### Phase 4: Incremental Rollout

**Step 1: Deploy to Staging**

Deploy new settings and monitor for 24 hours:

```bash
# Deploy to staging
kubectl set env deployment/backend DB_POOL_SIZE=10 DB_MAX_OVERFLOW=20 -n staging

# Watch metrics
watch -n 5 'curl -s http://staging.example.com/metrics | grep db_pool'
```

**Step 2: Load Testing**

Simulate peak load:

```bash
# Use existing load test script
cd backend
python tests/performance/test_query_performance.py --iterations 1000 --verbose
```

**Step 3: Deploy to Production (Canary)**

Deploy to 10% of production instances first:

```bash
# Canary deployment
kubectl set env deployment/backend DB_POOL_SIZE=10 DB_MAX_OVERFLOW=20 -n production --server-side

# Monitor for 2 hours
# If no issues, proceed to full rollout
```

**Step 4: Full Rollout**

Deploy to all production instances:

```bash
kubectl set env deployment/backend DB_POOL_SIZE=10 DB_MAX_OVERFLOW=20 -n production
```

### Phase 5: Validation (1 week)

**Monitor Key Indicators:**

| Indicator | Good | Bad | Action |
|-----------|------|-----|--------|
| Pool utilization (avg) | 40-70% | > 85% | Increase pool |
| Pool utilization (peak) | < 90% | > 95% | Increase overflow |
| Checkout P95 duration | < 0.5s | > 1s | Check DB performance |
| Timeout errors | 0 | > 0 | Increase pool or timeout |
| Overflow usage | < 30% time | > 50% | Increase pool size |

---

## Common Scenarios

### Scenario 1: Low-Traffic Application

**Context:**
- Internal tool with < 100 users
- < 10 concurrent requests
- Peak: 20 concurrent requests

**Recommended Settings:**

```bash
DB_POOL_SIZE=5       # Small permanent pool
DB_MAX_OVERFLOW=10   # Handle occasional spikes
DB_POOL_TIMEOUT=30   # Default is fine
DB_POOL_RECYCLE=3600
```

**Justification:**
- Small pool size matches low average load
- Overflow handles rare spikes
- Minimal database resource usage

### Scenario 2: Medium-Traffic SaaS Application

**Context:**
- 1,000+ daily active users
- 50-100 average concurrent requests
- Peak: 300 concurrent requests

**Recommended Settings:**

```bash
DB_POOL_SIZE=20      # Base pool for average load
DB_MAX_OVERFLOW=40   # Handle traffic spikes
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

**Justification:**
- Pool size = 50 × 1.2 ≈ 60 → 20 (round up)
- Overflow = (300 - 20) × 0.8 ≈ 224 → 40 (conservative)
- Total max: 60 connections

### Scenario 3: High-Traffic Enterprise Application

**Context:**
- 10,000+ daily active users
- 200-500 average concurrent requests
- Peak: 1,000+ concurrent requests

**Recommended Settings:**

```bash
DB_POOL_SIZE=50      # Larger base pool
DB_MAX_OVERFLOW=100  # Significant overflow capacity
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

**Justification:**
- Pool size = 300 × 1.2 ≈ 360 → 50 (conservative, rely on overflow)
- Overflow = (1000 - 50) × 0.8 = 760 → 100 (with connection pooling at app level)
- **Note:** Consider connection pooling at application level (PgBouncer)

**Additional Recommendations:**
- Implement PgBouncer for transaction pooling
- Use read replicas for reporting queries
- Consider database sharding for > 10,000 concurrent

### Scenario 4: Bursty Traffic Pattern

**Context:**
- Typical load: 10 concurrent requests
- Periodic spikes: 500 concurrent requests (batch jobs, cron jobs)
- Spikes last 5-10 minutes

**Recommended Settings:**

```bash
DB_POOL_SIZE=15      # Match typical load
DB_MAX_OVERFLOW=100  # Handle large bursts
DB_POOL_TIMEOUT=60   # Longer timeout for burst periods
DB_POOL_RECYCLE=3600
```

**Justification:**
- Small pool for efficiency during normal operations
- Large overflow for bursts
- Longer timeout accommodates queuing during bursts

---

## Troubleshooting

### Problem: "Pool Exhausted" Errors

**Symptom:**
```
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**Diagnosis:**
```bash
# Check pool metrics
curl http://localhost:8000/metrics | grep db_pool_checked_out

# If consistently at max:
db_pool_checked_out 30.0  # At max (pool_size + max_overflow)
```

**Solutions (in order):**

1. **Increase max_overflow:**
   ```bash
   DB_MAX_OVERFLOW=40  # Increase from 20
   ```

2. **Increase pool_size:**
   ```bash
   DB_POOL_SIZE=15  # Increase from 10
   ```

3. **Optimize queries** (see PERFORMANCE_IMPROVEMENTS.md):
   - Eliminate N+1 queries
   - Add eager loading
   - Use bulk operations

4. **Check database limit:**
   ```sql
   SHOW max_connections;
   -- If too low, increase in postgresql.conf or contact hosting provider
   ```

### Problem: Slow Checkout Times

**Symptom:**
```bash
# P95 checkout duration > 1 second
histogram_quantile(0.95, rate(db_pool_checkout_duration_seconds_bucket[5m])) = 1.5
```

**Diagnosis:**

1. **Pool too small:**
   ```bash
   # If pool utilization > 80%:
   db_pool_checked_out / (db_pool_size + db_pool_overflow) = 0.85
   ```

2. **Slow queries blocking connections:**
   ```bash
   # Check query duration
   curl http://localhost:8000/metrics | grep db_query_duration_seconds
   ```

**Solutions:**

1. **Increase pool size:**
   ```bash
   DB_POOL_SIZE=20  # Increase from 10
   ```

2. **Optimize slow queries:**
   - Add database indexes
   - Use JOINs instead of multiple queries
   - See PERFORMANCE_IMPROVEMENTS.md

3. **Increase timeout:**
   ```bash
   DB_POOL_TIMEOUT=60  # Increase from 30
   ```

### Problem: High Memory Usage

**Symptom:**
Application memory usage increases with pool size.

**Cause:**
Each PostgreSQL connection consumes memory:
- Default: ~10MB per connection
- 30 connections = ~300MB
- 100 connections = ~1GB

**Solutions:**

1. **Reduce pool size** (if underutilized)
2. **Tune PostgreSQL memory:**
   ```sql
   -- In postgresql.conf
   shared_buffers = 256MB
   work_mem = 4MB
   ```
3. **Use PgBouncer** for connection pooling at database level

### Problem: "Server Closed Connection" Errors

**Symptom:**
```
sqlalchemy.exc.DBAPIError: server closed the connection unexpectedly
```

**Cause:**
Database closed idle connection before pool recycled it.

**Solution:**
```bash
# Reduce recycle interval
DB_POOL_RECYCLE=1800  # 30 minutes instead of 1 hour

# Or set lower than PostgreSQL idle_session_timeout
```

**Verify:**
```sql
-- Check PostgreSQL setting
SHOW idle_session_timeout;

-- Set pool_recycle to 5 minutes less
DB_POOL_RECYCLE=<idle_session_timeout - 300>
```

### Problem: Overflow Never Used

**Symptom:**
```bash
# Overflow metric always zero
db_pool_overflow 0.0
```

**Analysis:**
This might indicate:
- Overflow is oversized (wasted configuration)
- Peak load not yet observed

**Action:**

1. **Check during peak traffic:**
   ```bash
   # Monitor during business hours
   watch -n 5 'curl -s http://localhost:8000/metrics | grep db_pool'
   ```

2. **If never used after 1 week, reduce:**
   ```bash
   DB_MAX_OVERFLOW=10  # Reduce from 20
   ```

3. **Re-test during expected peak events** (e.g., month-end, holidays)

---

## Best Practices

### 1. Start Conservative, Scale Gradually

```bash
# Initial deployment
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Scale up only after monitoring confirms need
```

**Why:** Oversizing wastes database resources and can degrade performance.

### 2. Monitor Before and After Changes

```bash
# Baseline metrics
curl http://localhost:8000/metrics | grep db_pool > baseline.txt

# Make changes

# After 24 hours, compare
curl http://localhost:8000/metrics | grep db_pool > after.txt
diff baseline.txt after.txt
```

### 3. Set Alerts for Pool Health

Configure Prometheus alerts (see [Alerting Rules](#alerting-rules)) for:
- Pool utilization > 80%
- Checkout timeouts detected
- Slow checkout P95

### 4. Document Your Rationale

Keep a record of why you chose specific values:

```markdown
# Pool Configuration Log

Date: 2025-02-04
Settings: DB_POOL_SIZE=15, DB_MAX_OVERFLOW=30

Rationale:
- Average concurrent: 12 requests (from metrics)
- Peak concurrent: 50 requests (from metrics)
- Pool size: 12 * 1.2 = 15
- Overflow: (50 - 15) * 0.8 = 28 → 30

Next Review: 2025-03-04
```

### 5. Test Under Load

Before deploying to production:

```bash
# Run performance benchmark
cd backend
python tests/performance/test_query_performance.py --iterations 1000

# Verify:
# - No timeout errors
# - P95 checkout < 0.5s
# - Pool utilization < 80%
```

### 6. Consider PgBouncer for High Scale

For applications requiring > 100 connections:

**Benefits:**
- Connection pooling at database level
- Reduced memory usage
- Better connection reuse across app instances

**Setup:**
```dockerfile
# docker-compose.yml
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    DATABASE_URL: postgresql://postgres:postgres@db:5432/resume_analysis
    POOL_MODE: transaction
  ports:
    - "6432:6432"
```

Then update `DATABASE_URL`:
```bash
DATABASE_URL=postgresql://postgres:postgres@pgbouncer:6432/resume_analysis
```

### 7. Recycle Connections Regularly

Always set `DB_POOL_RECYCLE` to prevent stale connections:

```bash
DB_POOL_RECYCLE=3600  # Recycle every hour
```

### 8. Use Separate Pools for Different Workloads

For complex applications, consider multiple database engines:

```python
# Read/write pool (smaller, for transactions)
write_engine = create_async_engine(
    settings.get_db_url_async(),
    pool_size=5,
    max_overflow=10
)

# Read pool (larger, for reporting queries)
read_engine = create_async_engine(
    settings.get_db_url_async(),
    pool_size=20,
    max_overflow=40
)
```

### 9. Account for Multiple App Instances

If running multiple instances of the backend:

```python
total_connections = (pool_size + max_overflow) * num_instances

# Example:
# - 3 app instances
# - pool_size=10, max_overflow=20
# - total_connections = 30 * 3 = 90 connections
# - PostgreSQL max_connections must be ≥ 100
```

**Formula:**
```python
max_instances = floor(
    (postgresql_max_connections * 0.8) / (pool_size + max_overflow)
)
```

### 10. Review Quarterly

Traffic patterns change over time. Schedule quarterly reviews:

- Re-run workload analysis
- Adjust pool settings if needed
- Update documentation with new findings

---

## Quick Reference

### Configuration Examples by Scale

| Scale | Concurrent Requests | Pool Size | Max Overflow | Total Max |
|-------|--------------------|-----------|--------------|-----------|
| Small | < 20 | 5 | 10 | 15 |
| Medium | 20-100 | 15 | 30 | 45 |
| Large | 100-500 | 40 | 80 | 120 |
| Enterprise | 500+ | 100+ | Use PgBouncer | - |

### Environment Variables

```bash
# .env file
DB_POOL_SIZE=10              # Base pool size (1-100)
DB_MAX_OVERFLOW=20           # Overflow capacity (0-100)
DB_POOL_TIMEOUT=30           # Checkout timeout in seconds (1-300)
DB_POOL_RECYCLE=3600         # Recycle interval in seconds (0-86400)
```

### Monitoring Commands

```bash
# Current pool status
curl http://localhost:8000/metrics | grep db_pool

# Pool utilization percentage
curl -s http://localhost:8000/metrics | \
  awk '/db_pool_checked_out/{checked=$2} /db_pool_size/{size=$2} /db_pool_overflow/{overflow=$2} END{print (checked/(size+overflow))*100"%"}'

# Checkout P95 duration
curl -s http://localhost:8000/metrics | \
  grep db_pool_checkout_duration_seconds | grep 'le="1"'
```

### Validation Checklist

Before considering pool tuning complete:

- [ ] Workload analysis completed (24-48 hours of metrics)
- [ ] Pool size matches average load × 1.2
- [ ] Overflow handles peak load
- [ ] Checkout P95 < 0.5 seconds
- [ ] No timeout errors in logs
- [ ] PostgreSQL max_connections verified
- [ ] Prometheus alerts configured
- [ ] Documentation updated
- [ ] Load testing completed
- [ ] Canary deployment successful

---

## Additional Resources

### Internal Documentation

- [PERFORMANCE_IMPROVEMENTS.md](../.auto-claude/specs/094-implement-database-query-optimization-and-connecti/PERFORMANCE_IMPROVEMENTS.md) - Query optimization results
- [QUERY_AUDIT.md](../.auto-claude/specs/094-implement-database-query-optimization-and-connecti/QUERY_AUDIT.md) - N+1 query patterns
- [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) - API performance considerations

### External References

- [SQLAlchemy Pool Configuration](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/usage.html)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-02-04
**Related Spec:** 094-implement-database-query-optimization-and-connecti
