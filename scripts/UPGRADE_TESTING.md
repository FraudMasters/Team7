# Upgrade Script Testing Guide

This document provides comprehensive testing procedures for the upgrade automation script (`scripts/upgrade.sh`).

## Overview

The upgrade script provides three main capabilities:
1. **Standard Upgrade**: Full backup → image update → migrations → service restart
2. **Zero-Downtime Upgrade**: Rolling updates with health checks
3. **Rollback**: Restore from latest backup

## Table of Contents

- [Prerequisites](#prerequisites)
- [Automated Testing](#automated-testing)
- [Manual Testing with Docker](#manual-testing-with-docker)
- [Test Scenarios](#test-scenarios)
- [Verification Steps](#verification-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### For Automated Tests (No Docker Required)
- Bash shell
- Basic POSIX utilities (grep, sed, awk)
- .env.example file

### For Manual/E2E Tests (Requires Docker)
- Docker Engine (20.10+)
- Docker Compose (v2.0+)
- Running AgentHR deployment
- PostgreSQL client tools (optional, for manual verification)

## Automated Testing

### Quick Test

Run the automated test script to verify upgrade.sh structure and functionality:

```bash
bash scripts/test-upgrade.sh
```

This script tests:
- ✅ Help command and documentation
- ✅ Command-line flag validation
- ✅ Script structure and syntax
- ✅ Backup management functions
- ✅ Health check functions
- ✅ Upgrade workflow steps
- ✅ Error handling mechanisms
- ✅ Rollback workflow
- ✅ Migration check functionality
- ✅ Zero-downtime upgrade logic

### Expected Output

```
=========================================
  Upgrade Script Test Suite
=========================================

[INFO] Starting automated tests for scripts/upgrade.sh

=====================================
Setting Up Test Environment
=====================================

[SUCCESS] Test environment set up successfully

========================================
TEST: Help Command
========================================

[SUCCESS] ✓ PASSED: Help command executes
[SUCCESS] ✓ PASSED: Help shows OPTIONS section
...

=========================================
  Test Results
=========================================

Total Tests:  35
Passed:       35
Failed:       0

[SUCCESS] All tests passed!
```

## Manual Testing with Docker

### Test Scenario 1: Standard Upgrade with Backup

**Objective**: Test full upgrade workflow with database backup and restore.

#### Step 1: Start Services with Current Version

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
bash scripts/health-check.sh

# Verify services are running
docker-compose ps
```

Expected: All services running and healthy.

#### Step 2: Create Test Data in Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres resume_analysis

# Create test table and insert data
CREATE TABLE upgrade_test (
    id SERIAL PRIMARY KEY,
    test_data VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO upgrade_test (test_data) VALUES
    ('Test data before upgrade'),
    ('Second test record'),
    ('Third test record');

# Verify data
SELECT * FROM upgrade_test;

# Exit psql
\q
```

Expected: 3 records created successfully.

#### Step 3: Run Upgrade with Backup

```bash
# Run standard upgrade
bash scripts/upgrade.sh

# Check logs for any errors
docker-compose logs backend | tail -50
```

Expected:
- ✅ Backup created in `./backups/db_backup_YYYYMMDD_HHMMSS.sql`
- ✅ Latest backup symlink created
- ✅ Images pulled/built successfully
- ✅ Services restarted successfully
- ✅ Health checks pass

#### Step 4: Verify Backup Created

```bash
# List backups
ls -lh backups/

# Check latest backup symlink
ls -lh backups/latest_backup.sql

# Verify backup contents
head -20 backups/db_backup_*.sql
```

Expected: Backup file exists with valid SQL content.

#### Step 5: Verify Test Data Persists

```bash
# Connect to database
docker-compose exec postgres psql -U postgres resume_analysis

# Query test data
SELECT * FROM upgrade_test;

# Exit
\q
```

Expected: All 3 test records still exist with original data.

#### Step 6: Verify Services Restart Successfully

```bash
# Check service status
docker-compose ps

# Run health checks
bash scripts/health-check.sh

# Check backend API
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173/
```

Expected: All services healthy and responding.

---

### Test Scenario 2: Rollback from Backup

**Objective**: Test rollback functionality to restore from backup.

#### Step 1: Verify Current State

```bash
# Check current data
docker-compose exec postgres psql -U postgres resume_analysis -c "SELECT * FROM upgrade_test;"
```

Expected: See existing test data.

#### Step 2: Modify Data (Simulate Breaking Change)

```bash
# Connect to database
docker-compose exec postgres psql -U postgres resume_analysis

# Modify data to simulate a problem
UPDATE upgrade_test SET test_data = 'CORRUPTED' WHERE id = 1;
DELETE FROM upgrade_test WHERE id = 2;

# Verify changes
SELECT * FROM upgrade_test;

\q
```

Expected: Data modified/corrupted.

#### Step 3: Perform Rollback

```bash
# Rollback to previous version
bash scripts/upgrade.sh --rollback

# Check logs
docker-compose logs backend | tail -30
```

Expected:
- ✅ Services stopped
- ✅ Database restored from backup
- ✅ Services restarted
- ✅ Health checks pass

#### Step 4: Verify Data Restored

```bash
# Check restored data
docker-compose exec postgres psql -U postgres resume_analysis -c "SELECT * FROM upgrade_test;"
```

Expected: Original 3 records restored with original data.

---

### Test Scenario 3: Zero-Downtime Upgrade

**Objective**: Test rolling update capability.

#### Step 1: Start Services and Monitor

```bash
# Start services
docker-compose up -d

# In a separate terminal, continuously monitor backend health
watch -n 1 'curl -sf http://localhost:8000/health && echo "HEALTHY" || echo "DOWN"'
```

#### Step 2: Perform Zero-Downtime Upgrade

```bash
# Run upgrade with zero-downtime flag
bash scripts/upgrade.sh --no-downtime
```

Expected:
- ✅ Services restart one by one
- ✅ Health checks pass after each service restart
- ✅ Minimal or no downtime observed in health monitor

#### Step 3: Verify Continuous Availability

Review the health monitoring output from Step 1.

Expected: Maximum 1-2 health check failures during restart.

---

### Test Scenario 4: Migration Check

**Objective**: Test migration detection without applying changes.

#### Step 1: Check Migration Status

```bash
# Check for pending migrations
bash scripts/upgrade.sh --check-migrations
```

Expected output if up-to-date:
```
=========================================
  Checking Database Migrations
=========================================

[INFO] Getting current database revision...
[INFO] Current revision: abc123def456
[INFO] Getting target head revision...
[INFO] Head revision: abc123def456

=========================================
  Migration Status
=========================================

[SUCCESS] ✓ Database is up to date

Current revision: abc123def456
Target revision:  abc123def456

[INFO] No pending migrations
```

Expected output if migrations pending:
```
[WARNING] ⚠ Database has pending migrations

Current revision: abc123def456
Target revision:  def456ghi789

[INFO] Pending migrations:
... migration list ...

[WARNING] Run the following command to apply migrations:
  scripts/upgrade.sh
```

---

### Test Scenario 5: Upgrade Without Backup

**Objective**: Test upgrade with --skip-backup flag.

#### Step 1: Run Upgrade Without Backup

```bash
# Count existing backups
ls -l backups/*.sql | wc -l

# Upgrade without backup
bash scripts/upgrade.sh --skip-backup

# Count backups again
ls -l backups/*.sql | wc -l
```

Expected: Backup count unchanged, upgrade completes successfully.

---

### Test Scenario 6: Simulated Version Change

**Objective**: Test upgrade with actual version change (E2E verification from spec).

#### Step 1: Tag Current Version

```bash
# Tag backend image with v1.0.0
docker tag resume_analysis_backend:latest resume_analysis_backend:v1.0.0

# Verify tag
docker images | grep resume_analysis_backend
```

#### Step 2: Make Code Change

```bash
# Edit backend version file (example)
echo "VERSION = '1.1.0'" > backend/version.py

# Rebuild images
docker-compose build backend
```

#### Step 3: Create Pre-Upgrade Test Data

```bash
# Add version tracking table
docker-compose exec postgres psql -U postgres resume_analysis <<EOF
CREATE TABLE IF NOT EXISTS version_history (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50),
    upgraded_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO version_history (version) VALUES ('1.0.0');
SELECT * FROM version_history;
EOF
```

Expected: Version 1.0.0 recorded.

#### Step 4: Run Upgrade

```bash
# Perform upgrade with backup
bash scripts/upgrade.sh
```

Expected:
- ✅ Backup created
- ✅ New images deployed
- ✅ Services restart with new version
- ✅ Migrations applied (if any)

#### Step 5: Verify Version Change

```bash
# Record new version
docker-compose exec postgres psql -U postgres resume_analysis <<EOF
INSERT INTO version_history (version) VALUES ('1.1.0');
SELECT * FROM version_history ORDER BY upgraded_at;
EOF
```

Expected: Both versions listed, showing successful upgrade.

#### Step 6: Test Rollback to Previous Version

```bash
# Rollback
bash scripts/upgrade.sh --rollback

# Check backend logs for version
docker-compose logs backend | grep -i version | tail -10
```

Expected: Services running with previous version data.

---

## Verification Steps

### After Each Upgrade

1. **Service Health**
   ```bash
   bash scripts/health-check.sh
   ```

2. **Container Status**
   ```bash
   docker-compose ps
   ```

3. **Backend API**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/docs
   ```

4. **Frontend**
   ```bash
   curl -I http://localhost:5173/
   ```

5. **Database Connectivity**
   ```bash
   docker-compose exec postgres pg_isready -U postgres
   ```

6. **Celery Workers**
   ```bash
   docker-compose logs celery_worker | tail -20
   ```

### Data Integrity Checks

1. **Query Test Data**
   ```bash
   docker-compose exec postgres psql -U postgres resume_analysis \
     -c "SELECT COUNT(*) FROM upgrade_test;"
   ```

2. **Check Database Size**
   ```bash
   docker-compose exec postgres psql -U postgres resume_analysis \
     -c "SELECT pg_size_pretty(pg_database_size('resume_analysis'));"
   ```

3. **Verify Tables**
   ```bash
   docker-compose exec postgres psql -U postgres resume_analysis \
     -c "\dt"
   ```

### Backup Verification

1. **List Backups**
   ```bash
   ls -lh backups/
   ```

2. **Check Backup Size**
   ```bash
   du -h backups/db_backup_*.sql | tail -5
   ```

3. **Verify Latest Symlink**
   ```bash
   readlink backups/latest_backup.sql
   ```

4. **Test Backup Restore (Dry-Run)**
   ```bash
   # Verify backup is valid SQL
   head -50 backups/latest_backup.sql | grep -i "PostgreSQL"
   ```

---

## Troubleshooting

### Problem: Upgrade Fails with "No running containers"

**Cause**: Services not started before upgrade.

**Solution**:
```bash
docker-compose up -d
bash scripts/health-check.sh
bash scripts/upgrade.sh
```

### Problem: Backup Fails with Permission Denied

**Cause**: Backup directory not writable.

**Solution**:
```bash
mkdir -p backups
chmod 755 backups
bash scripts/upgrade.sh
```

### Problem: Database Connection Fails During Upgrade

**Cause**: PostgreSQL not ready or connection parameters incorrect.

**Solution**:
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check logs
docker-compose logs postgres | tail -50

# Verify .env has correct DATABASE_URL
grep DATABASE_URL .env

# Restart PostgreSQL
docker-compose restart postgres
bash scripts/upgrade.sh
```

### Problem: Migration Check Shows Pending Migrations

**Cause**: Database schema out of date.

**Solution**:
```bash
# Apply migrations
bash scripts/upgrade.sh

# Or check what migrations are pending
docker-compose run --rm backend alembic history
```

### Problem: Rollback Fails with "No backup found"

**Cause**: No backup files in backups directory.

**Solution**:
```bash
# Create backup first
docker-compose exec postgres pg_dump -U postgres resume_analysis > backups/manual_backup.sql
ln -s manual_backup.sql backups/latest_backup.sql

# Retry rollback
bash scripts/upgrade.sh --rollback
```

### Problem: Zero-Downtime Upgrade Has Extended Downtime

**Cause**: Services taking too long to start or health checks timing out.

**Solution**:
```bash
# Increase health check timeout in upgrade.sh
# Check service resource limits in docker-compose.yml
# Use standard upgrade instead:
bash scripts/upgrade.sh
```

### Problem: Services Fail to Start After Upgrade

**Cause**: Migration errors, configuration issues, or image problems.

**Solution**:
```bash
# Check logs for specific errors
docker-compose logs backend | tail -100
docker-compose logs postgres | tail -50

# Rollback to previous version
bash scripts/upgrade.sh --rollback

# Investigate and fix issue before retrying upgrade
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Upgrade Script

on:
  push:
    paths:
      - 'scripts/upgrade.sh'
      - 'scripts/test-upgrade.sh'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run automated tests
        run: bash scripts/test-upgrade.sh

      - name: Setup Docker
        uses: docker/setup-buildx-action@v2

      - name: Start services
        run: |
          cp .env.example .env
          docker-compose up -d
          bash scripts/health-check.sh

      - name: Test upgrade
        run: bash scripts/upgrade.sh --skip-backup

      - name: Verify health
        run: bash scripts/health-check.sh
```

---

## Best Practices

1. **Always test upgrades in staging first**
2. **Create backups before production upgrades** (default behavior)
3. **Monitor services during zero-downtime upgrades**
4. **Keep at least 3 backup copies** (configure retention)
5. **Test rollback procedure regularly**
6. **Document version-specific upgrade notes** (see UPGRADE.md)
7. **Use --check-migrations before upgrade** to preview changes
8. **Schedule upgrades during low-traffic periods**

---

## Summary

The upgrade script provides robust automation for:
- ✅ Standard upgrades with automatic backups
- ✅ Zero-downtime rolling updates
- ✅ Safe rollback capability
- ✅ Migration detection and application
- ✅ Comprehensive health checks
- ✅ Error handling and cleanup

All upgrade workflows have been tested and verified to work correctly.
