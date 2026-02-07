# Microservices Testing Guide

## Overview

This guide explains how to run all tests against the microservices architecture via the API Gateway to verify zero functionality loss after the refactoring.

## Prerequisites

### 1. Start All Services

Start the microservices and API Gateway:

```bash
docker-compose -f docker-compose.microservices.yml up -d
```

### 2. Verify Services are Running

Check service health:

```bash
# Check API Gateway (port 8888)
curl http://localhost:8888/health

# Check individual microservices (ports 8001-8009)
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009; do
    echo "Port $port:"
    curl -s http://localhost:$port/health | jq .
done
```

### 3. Install Test Dependencies

```bash
# Install pytest and related packages
pip install pytest pytest-asyncio pytest-cov httpx

# Or install from requirements
pip install -r requirements-test.txt
```

## Test Suites

### 1. Gateway Integration Tests

**Location:** `tests/integration/test_gateway.py`

Tests API Gateway functionality:
- Gateway health and accessibility
- Routing to all microservices
- CORS headers
- Rate limiting
- JWT authentication
- Error handling
- Performance

**Run:**
```bash
# Run all gateway tests
./tests/run_microservices_tests.sh -t tests/integration/test_gateway.py

# Or with pytest directly
pytest tests/integration/test_gateway.py -v

# Skip slow tests
pytest tests/integration/test_gateway.py -v -m "not slow"
```

### 2. Microservices Integration Tests

**Location:** `tests/integration/test_microservices.py`

Tests microservices architecture:
- Service health checks and readiness
- Inter-service communication (gRPC/REST)
- End-to-end workflows
- Database isolation
- Distributed tracing
- Service discovery

**Run:**
```bash
# Run all microservices tests
./tests/run_microservices_tests.sh -t tests/integration/test_microservices.py

# Or with pytest directly
pytest tests/integration/test_microservices.py -v

# Skip slow tests
pytest tests/integration/test_microservices.py -v -m "not slow"
```

### 3. Backend Unit Tests

**Location:** `backend/tests/`

Original backend unit and integration tests:
- Analyzer tests (enhanced_matcher, skill_extraction, etc.)
- API endpoint tests
- Integration tests for specific features
- Performance tests

**Run:**
```bash
# From backend directory
cd backend
./run_backend_tests.sh

# Or with specific options
./run_backend_tests.sh -v    # Verbose
./run_backend_tests.sh -c    # With coverage
./run_backend_tests.sh -p    # Parallel execution
```

## Running All Tests

### Quick Test (All Tests)

```bash
./tests/run_microservices_tests.sh
```

### With Options

```bash
# Verbose output
./tests/run_microservices_tests.sh -v

# With coverage report
./tests/run_microservices_tests.sh -c

# Skip slow tests
./tests/run_microservices_tests.sh -s

# Combine options
./tests/run_microservices_tests.sh -v -c -s
```

### Environment Variables

```bash
# Custom gateway host/port
GATEWAY_HOST=localhost GATEWAY_PORT=8888 ./tests/run_microservices_tests.sh

# With Docker service names
GATEWAY_HOST=api_gateway GATEWAY_PORT=8888 ./tests/run_microservices_tests.sh
```

## Test Verification

The verification command specified in the subtask is:

```bash
pytest tests/ -v --tb=short | grep -q 'passed' && echo 'All tests passed'
```

This will:
1. Run all tests in the `tests/` directory
2. Show verbose output
3. Use short traceback format
4. Check if any tests passed
5. Print "All tests passed" if successful

## Expected Test Results

### Zero Functionality Loss Criteria

All tests must pass to verify zero functionality loss:

| Test Suite | Purpose | Expected Result |
|------------|---------|-----------------|
| Gateway Integration | Verify gateway routing | All pass |
| Microservices Integration | Verify inter-service communication | All pass |
| Backend Unit Tests | Verify core functionality | All pass |
| Backend Integration Tests | Verify end-to-end workflows | All pass |

### Service Coverage

The tests should verify all microservices:

1. **Resume Processing Service** (8001)
   - Resume upload, parsing, analysis

2. **Matching Service** (8002)
   - Skill matching, comparison, ranking

3. **Candidate Service** (8003)
   - Candidate CRUD, notes, tags

4. **Vacancy Service** (8004)
   - Vacancy management, bulk operations

5. **Taxonomy Service** (8005)
   - Skill taxonomies, synonyms

6. **Analytics Service** (8006)
   - Analytics dashboards, reports

7. **ATS Simulation Service** (8007)
   - ATS scoring, screening

8. **Notification Service** (8008)
   - Email, SMS, notifications

9. **Integration Service** (8009)
   - Third-party integrations

## Troubleshooting

### Tests Fail with "Gateway not running"

**Solution:** Start the API Gateway
```bash
docker-compose -f docker-compose.microservices.yml up api_gateway
```

### Tests Fail with "Service not available"

**Solution:** Start the specific microservice or all services
```bash
# Start all services
docker-compose -f docker-compose.microservices.yml up -d

# Check service status
docker-compose -f docker-compose.microservices.yml ps
```

### Tests Timeout

**Solution:** Services may be slow to start
```bash
# Wait for services to be healthy
watch -n 2 'docker-compose -f docker-compose.microservices.yml ps'

# Or increase test timeout in pytest.ini
```

### Import Errors

**Solution:** Set PYTHONPATH correctly
```bash
export PYTHONPATH="$PYTHONPATH:."
pytest tests/ -v
```

### Database Errors

**Solution:** Ensure database migrations are applied
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Or for specific service
docker-compose exec resume_processing alembic upgrade head
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Microservices Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: agenthr_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: |
          docker-compose -f docker-compose.microservices.yml up -d
          sleep 30

      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt

      - name: Run tests
        run: |
          ./tests/run_microservices_tests.sh -v -c

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Reports

### Coverage Report

Generate HTML coverage report:

```bash
./tests/run_microservices_tests.sh -c

# Open the report
open htmlcov/index.html
```

### JUnit XML Report

For CI/CD integration:

```bash
pytest tests/ -v --junitxml=test-results.xml
```

## Performance Baselines

After migration, performance should be within acceptable bounds:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Gateway latency | < 100ms | Gateway health check time |
| Service response time | < 500ms | API endpoint response time |
| End-to-end workflow | < 5s | Complete upload → match workflow |

## Success Criteria

The test suite passes when:

1. ✅ All gateway integration tests pass
2. ✅ All microservices integration tests pass
3. ✅ All backend unit tests pass
4. ✅ No regressions in existing functionality
5. ✅ Performance is within acceptable bounds
6. ✅ Zero data loss or corruption

## Next Steps

After all tests pass:

1. ✅ Update implementation plan status to "completed"
2. ✅ Document any issues found and resolved
3. ✅ Sign off on zero functionality loss
4. ✅ Proceed to deployment phase
