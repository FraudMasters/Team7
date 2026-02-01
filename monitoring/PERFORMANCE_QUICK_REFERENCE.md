# Performance Validation - Quick Reference

## Goal
Verify monitoring overhead < 5% response time increase

## One-Command Test
```bash
./monitoring/validate-monitoring-overhead.sh
```

## Expected Results
- ✅ Overhead: < 5%
- ✅ CPU: < 50%
- ✅ Memory increase: < 50 MiB
- ✅ No memory leaks

## What's Tested
1. Response time (100 requests to /api/resumes)
2. Prometheus metrics accuracy
3. Monitoring overhead calculation
4. Container CPU usage
5. Container memory usage
6. Memory leak detection

## Troubleshooting

### High Overhead (> 5%)
- Reduce log level to WARNING
- Sample metrics (track every 10th request)
- Fewer histogram buckets
- Check for blocking I/O

### Memory Leaks
- Verify correlation ID cleanup
- Check DB connection pooling
- Review log buffer sizes
- Monitor label cardinality

### High CPU (> 50%)
- Implement metric sampling
- Reduce logging verbosity
- Check string formatting in logs
- Verify async operations

## Customization
```bash
NUM_REQUESTS=200 \
EXPECTED_OVERHEAD_THRESHOLD=3 \
BACKEND_URL=http://localhost:8001 \
./monitoring/validate-monitoring-overhead.sh
```

## Manual Test
```bash
# Measure response time
time for i in {1..100}; do
  curl -s http://localhost:8000/api/resumes > /dev/null
done

# Check Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])/rate(http_request_duration_seconds_count[5m])' | jq .

# Check container stats
docker stats resume_analysis_backend --no-stream
```

## Component Overhead Estimates
- Prometheus middleware: 1-2ms
- Correlation ID: < 1ms
- Structured logging: 1-3ms
- DB query metrics: < 0.5ms per query
- **Total: 3-6ms per request**

## Success Criteria
- [ ] Overhead < 5%
- [ ] All tests pass
- [ ] No memory leaks
- [ ] CPU usage acceptable
- [ ] Prometheus metrics accurate

## Documentation
Full guide: `monitoring/MONITORING_PERFORMANCE_VALIDATION.md`
