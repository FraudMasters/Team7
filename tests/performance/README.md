# Performance and Load Testing

This directory contains comprehensive performance tests for the recruitment platform.

## Test Files

### load_test.py
End-to-end load testing using Locust framework with 100 concurrent users.

**Test Scenarios:**
- Browse candidates (70% weight) - Most common action
- View candidate details (20% weight) - Medium frequency
- Upload and analyze resume (10% weight) - Heavy operation

**Performance Thresholds:**
- Candidate list P95 response time: < 2 seconds
- Resume upload/analysis P95 time: < 30 seconds
- Redis cache hit rate: > 70%
- No memory leaks in worker processes

## Prerequisites

1. Install Locust:
```bash
pip install locust==2.32.2
```

2. Ensure services are running:
```bash
docker-compose up -d postgres redis backend celery_worker
```

3. Verify backend is accessible:
```bash
curl http://localhost:8000/health
```

## Running Load Tests

### Quick Start (Headless Mode)

Run with default settings (100 users, 10 spawn rate, 1 minute):
```bash
cd /path/to/project
locust -f tests/performance/load_test.py --headless -u 100 -r 10 -t 1m
```

### Custom Load Settings

Run with 200 users, 20 spawn rate, for 5 minutes:
```bash
locust -f tests/performance/load_test.py --headless -u 200 -r 20 -t 5m
```

### Interactive Web UI

Start Locust with web interface for real-time monitoring:
```bash
locust -f tests/performance/load_test.py
```

Then open: http://localhost:8089

### Different Target Host

Test against staging or production:
```bash
TARGET_HOST=https://staging.example.com locust -f tests/performance/load_test.py --headless -u 50 -r 5 -t 2m
```

## Environment Variables

- `TARGET_HOST`: API base URL (default: http://localhost:8000)
- `REDIS_HOST`: Redis host for cache monitoring (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)

## Understanding Results

### Performance Summary

After the test completes, you'll see a summary like:

```
================================================================================
LOAD TEST PERFORMANCE SUMMARY
================================================================================

Cache Hit Rate: 78.45%
  Hits: 1234
  Misses: 340
  Status: ✓ PASS (threshold: 70%)

Response Times (P95):
--------------------------------------------------------------------------------
/api/candidates/
  P95: 1456ms
  Avg: 892ms
  Count: 2000
  Status: ✓ PASS (threshold: 2000ms)

/api/resumes/upload
  P95: 28450ms
  Avg: 19200ms
  Count: 150
  Status: ✓ PASS (threshold: 30000ms)

================================================================================
```

### Key Metrics

1. **Cache Hit Rate**: Percentage of requests served from cache
   - Target: > 70%
   - Higher is better (indicates effective caching)

2. **P95 Response Time**: 95th percentile response time
   - 95% of requests complete faster than this
   - More reliable than average (outliers don't skew it)

3. **Requests Per Second (RPS)**: Throughput metric
   - How many requests the system can handle
   - Higher is better

4. **Failure Rate**: Percentage of failed requests
   - Should be 0% in a healthy system
   - Investigate any failures

## Troubleshooting

### Connection Refused

**Problem**: `Connection refused` error

**Solution**: Ensure backend is running:
```bash
docker-compose up -d backend
curl http://localhost:8000/health
```

### No Candidates Found

**Problem**: Tests fail because no candidates exist in database

**Solution**: Seed test data:
```bash
cd backend
python scripts/load_test_data.py
```

### Timeout Errors

**Problem**: Requests timeout during test

**Solution**: Increase timeout or reduce concurrent users:
```bash
locust -f tests/performance/load_test.py --headless -u 50 -r 5 -t 1m
```

### Memory Leaks Detected

**Problem**: Memory usage grows continuously during test

**Solution**:
1. Check for unclosed database connections
2. Verify cache doesn't grow unbounded
3. Review Celery task cleanup

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for backend
        run: |
          for i in {1..30}; do
            if curl -f http://localhost:8000/health; then
              break
            fi
            sleep 2
          done

      - name: Install Locust
        run: pip install locust==2.32.2

      - name: Run load test
        run: |
          locust -f tests/performance/load_test.py \
            --headless \
            -u 100 \
            -r 10 \
            -t 1m \
            --html load-test-report.html

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: load-test-report.html
```

## Best Practices

1. **Run in staging first**: Never run load tests against production without careful planning
2. **Monitor resources**: Watch CPU, memory, and database connections during tests
3. **Start small**: Begin with low concurrency and gradually increase
4. **Test regularly**: Run load tests after major changes
5. **Keep test data realistic**: Use data similar to production volumes
6. **Analyze failures**: Always investigate why requests failed

## Performance Optimization Tips

If tests reveal performance issues:

1. **Check cache hit rate**: Low hit rate means caching needs improvement
2. **Database queries**: Use EXPLAIN ANALYZE to find slow queries
3. **Add indexes**: Ensure frequently queried columns are indexed
4. **Connection pooling**: Tune database connection pool size
5. **N+1 queries**: Look for multiple queries in loops
6. **Celery tasks**: Optimize long-running background tasks

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Backend Performance Tests](../../backend/tests/performance/test_api_performance.py)
- [Caching Documentation](../../backend/services/cache_service.py)
- [Database Indexes](../../backend/alembic/versions/20260201_add_candidate_performance_indexes.py)
