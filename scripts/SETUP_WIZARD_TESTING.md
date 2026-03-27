# Setup Wizard Testing Guide

This document describes the comprehensive testing strategy for the interactive setup wizard (`scripts/setup-wizard.sh`).

## Test Strategy

The setup wizard testing is divided into two categories:

1. **Automated Tests** - Tests that can run without Docker daemon (using dry-run mode)
2. **Manual Tests** - End-to-end tests that require Docker to be running

## Automated Tests

The automated test suite (`scripts/test-setup-wizard.sh`) validates:

### 1. Help Documentation
- ✅ Help command displays usage information
- ✅ All flags and options are documented
- ✅ Examples are provided

### 2. Command-Line Interface
- ✅ All valid profiles are accepted (minimal, core, full, monitoring-only)
- ✅ Invalid profiles are rejected
- ✅ All command-line flags are recognized
- ✅ Unknown flags are rejected with helpful error messages

### 3. Dry-Run Mode
- ✅ Dry-run mode executes without errors
- ✅ Dry-run mode doesn't modify files
- ✅ Dry-run mode shows what actions would be taken
- ✅ Dry-run mode is lenient with missing prerequisites

### 4. Configuration Validation
- ✅ .env file creation from .env.example
- ✅ Required variables are validated for each profile
- ✅ DATABASE_URL format validation
- ✅ Docker Compose configuration validation
- ✅ Port availability checking

### 5. Error Handling
- ✅ Missing .env.example is detected
- ✅ Invalid configuration is detected
- ✅ Missing required variables are reported
- ✅ Helpful error messages are displayed

### 6. Health Check Integration
- ✅ Health check script is called
- ✅ Health check validation runs in dry-run mode
- ✅ Health check can be skipped with flag

### 7. Profile-Specific Features
- ✅ Each profile has appropriate configuration
- ✅ Optional features can be enabled with flags
- ✅ Profile-specific variables are validated

## Manual Tests (Requires Docker)

The following tests require Docker daemon to be running and should be performed manually:

### Test 1: Full End-to-End with Default Settings

**Objective**: Verify complete deployment with default configuration

**Steps**:
```bash
# 1. Clean environment
docker compose down -v
rm -f .env

# 2. Run wizard with defaults
bash scripts/setup-wizard.sh --non-interactive --profile core

# 3. Verify
- .env file is created
- All services start successfully
- Health checks pass
- Services are accessible at documented URLs
```

**Expected Result**:
- Exit code: 0
- .env file contains all required variables
- Services: postgres, redis, backend, frontend, celery_worker, celery_beat are running
- Backend responds at http://localhost:8000/health
- Frontend loads at http://localhost:5173

### Test 2: Interactive Mode

**Objective**: Verify interactive prompts and user input handling

**Steps**:
```bash
# 1. Clean environment
docker compose down -v
rm -f .env

# 2. Run wizard interactively
bash scripts/setup-wizard.sh

# 3. Test user interactions:
- Select different profiles (try all 4 options)
- Enter custom database credentials
- Enable/disable optional features
- Test input validation
```

**Expected Result**:
- All prompts are clear and helpful
- Invalid inputs are rejected with helpful messages
- Default values work correctly
- Configuration is saved correctly to .env

### Test 3: Minimal Profile

**Objective**: Verify minimal profile deploys only core infrastructure

**Steps**:
```bash
docker compose down -v
bash scripts/setup-wizard.sh --non-interactive --profile minimal
docker compose ps
```

**Expected Result**:
- Only postgres and redis containers are running
- No application containers (backend, frontend, celery) are started
- Health check validates database and redis only

### Test 4: Full Profile

**Objective**: Verify full profile deploys complete stack

**Steps**:
```bash
docker compose down -v
bash scripts/setup-wizard.sh --non-interactive --profile full
docker compose ps
```

**Expected Result**:
- All containers are running:
  - postgres, redis (infrastructure)
  - backend, frontend (application)
  - celery_worker, celery_beat (workers)
  - prometheus, grafana, flower (monitoring)
  - neo4j (if configured)
- All health checks pass
- Monitoring dashboards are accessible

### Test 5: Invalid Configuration Detection

**Objective**: Verify wizard catches configuration errors

**Steps**:
```bash
# 1. Create invalid .env
cat > .env << EOF
# Missing required variables
POSTGRES_USER=testuser
EOF

# 2. Run wizard with validate-only
bash scripts/setup-wizard.sh --validate-only --non-interactive
```

**Expected Result**:
- Exit code: 1 (failure)
- Error messages clearly identify missing variables
- No services are started
- Helpful guidance is provided

### Test 6: Invalid DATABASE_URL Format

**Objective**: Verify DATABASE_URL validation

**Steps**:
```bash
# 1. Create .env with invalid DATABASE_URL
cp .env.example .env
sed -i '' 's|postgresql://|mysql://|' .env

# 2. Run wizard
bash scripts/setup-wizard.sh --validate-only --non-interactive
```

**Expected Result**:
- Warning about invalid DATABASE_URL format
- Helpful message about correct format
- Validation may continue (non-fatal) but warns user

### Test 7: Port Conflicts

**Objective**: Verify wizard handles port conflicts gracefully

**Steps**:
```bash
# 1. Start a service on port 8000
python3 -m http.server 8000 &
HTTP_SERVER_PID=$!

# 2. Run wizard
bash scripts/setup-wizard.sh --profile core

# 3. Cleanup
kill $HTTP_SERVER_PID
```

**Expected Result**:
- Wizard detects port 8000 is in use
- Warning message is displayed
- In interactive mode, prompts user to continue
- In non-interactive mode, continues with warning

### Test 8: Upgrade Path (Existing .env)

**Objective**: Verify wizard handles existing .env files

**Steps**:
```bash
# 1. Deploy initial version
bash scripts/setup-wizard.sh --non-interactive --profile core

# 2. Run wizard again
bash scripts/setup-wizard.sh --non-interactive --profile core
```

**Expected Result**:
- Wizard detects existing .env
- In interactive mode, prompts whether to overwrite
- In non-interactive mode, uses existing .env
- No data loss

### Test 9: Optional Features

**Objective**: Verify optional feature flags work correctly

**Steps**:
```bash
# Test monitoring
bash scripts/setup-wizard.sh --non-interactive --profile core --enable-monitoring
docker compose ps | grep -E "(prometheus|grafana|flower)"

# Test backups
bash scripts/setup-wizard.sh --non-interactive --profile core --enable-backups
docker compose ps | grep backup

# Test Neo4j
bash scripts/setup-wizard.sh --non-interactive --profile core --enable-neo4j
docker compose ps | grep neo4j
```

**Expected Result**:
- Optional services are started when flags are provided
- Configuration is added to .env
- Services are healthy

### Test 10: Health Check Validation

**Objective**: Verify health checks run and report correctly

**Steps**:
```bash
# 1. Deploy services
bash scripts/setup-wizard.sh --non-interactive --profile core

# 2. Wait for services to stabilize
sleep 30

# 3. Manual health check
bash scripts/health-check.sh
```

**Expected Result**:
- All services report healthy
- Endpoints are accessible:
  - Backend: http://localhost:8000/health
  - Frontend: http://localhost:5173
  - Database: Connection successful
  - Redis: PING successful
  - Celery: Worker is active

### Test 11: Service Startup Order

**Objective**: Verify services start in correct order with dependencies

**Steps**:
```bash
docker compose down -v
bash scripts/setup-wizard.sh --non-interactive --profile core
docker compose logs --tail=50
```

**Expected Result**:
- Database starts first
- Redis starts early
- Backend waits for database to be ready
- Frontend and workers start after backend
- No restart loops or dependency failures

### Test 12: Cleanup and Retry

**Objective**: Verify wizard can handle retries after failures

**Steps**:
```bash
# 1. Simulate failure (invalid config)
cat > .env << EOF
POSTGRES_USER=user
POSTGRES_PASSWORD=
EOF

# 2. Try to start
bash scripts/setup-wizard.sh --profile core
# (Should fail)

# 3. Fix config and retry
cp .env.example .env
bash scripts/setup-wizard.sh --profile core
```

**Expected Result**:
- First attempt fails with clear error
- Second attempt succeeds
- No leftover state causes issues

## Running Automated Tests

To run the automated test suite:

```bash
bash scripts/test-setup-wizard.sh
```

This will run all tests that don't require Docker daemon and provide a summary report.

## Test Results

Expected automated test results:
- All automated tests should pass
- Some tests may show warnings for environment-specific issues
- Manual tests are documented but must be run separately

## Continuous Integration

For CI/CD pipelines:

```bash
# Run automated tests (no Docker required)
bash scripts/test-setup-wizard.sh

# Run manual tests (requires Docker)
docker info  # Verify Docker is available
bash scripts/setup-wizard.sh --non-interactive --profile core
bash scripts/health-check.sh
```

## Known Limitations

1. **Docker Daemon**: Most end-to-end tests require Docker daemon to be running
2. **Port Availability**: Tests may fail if required ports are in use
3. **Environment-Specific**: Some tests depend on environment setup (e.g., .env.example)
4. **Timing**: Service startup may vary based on system resources

## Troubleshooting Test Failures

### "Prerequisites check failed"
- Ensure Docker and Docker Compose are installed
- Start Docker daemon
- Run with `--dry-run` flag for validation-only testing

### "Port already in use"
- Check which process is using the port: `lsof -i :<port>`
- Stop conflicting services
- Use different ports in .env file

### "Configuration validation failed"
- Verify .env.example exists
- Check .env file has all required variables
- Review error messages for specific missing variables

### "Services not starting"
- Check Docker logs: `docker compose logs`
- Verify system resources (memory, disk space)
- Check for image build failures

## Contributing

When adding new features to the setup wizard:

1. Add automated tests in `scripts/test-setup-wizard.sh`
2. Document manual test procedures in this file
3. Update the verification checklist
4. Test both interactive and non-interactive modes
5. Test all profiles (minimal, core, full, monitoring-only)

## References

- Setup Wizard: `scripts/setup-wizard.sh`
- Health Check: `scripts/health-check.sh`
- Automated Tests: `scripts/test-setup-wizard.sh`
- Docker Compose: `docker-compose.yml`
- Environment Template: `.env.example`
