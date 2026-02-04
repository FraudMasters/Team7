# Disaster Recovery Guide

## Project: AgentHR Resume Analysis System

## Table of Contents

1. [Disaster Recovery Overview](#disaster-recovery-overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Backup Types and Retention](#backup-types-and-retention)
4. [Restore Procedures](#restore-procedures)
5. [S3 Off-Site Recovery](#s3-off-site-recovery)
6. [Testing Procedures](#testing-procedures)
7. [Emergency Runbook](#emergency-runbook)
8. [Preventing Data Loss](#preventing-data-loss)
9. [Monitoring and Alerts](#monitoring-and-alerts)
10. [Common Recovery Scenarios](#common-recovery-scenarios)

---

## Disaster Recovery Overview

The AgentHR system includes a comprehensive backup and disaster recovery solution designed to minimize data loss and downtime. This guide provides step-by-step procedures for recovering from various failure scenarios.

### Recovery Components

- **Automated Daily Backups**: Scheduled via Celery Beat (default: 2 AM daily)
- **Multiple Backup Types**: Database, files, models, and full system backups
- **Off-Site Storage**: Optional S3-compatible storage for disaster recovery
- **Integrity Verification**: Automatic checksum validation
- **One-Click Restore**: API and task-based restore functionality

### Architecture

```
Production System
    ↓
Daily Automated Backup (Celery Beat)
    ↓
Local Backup Storage (/data/backups)
    ↓
S3 Off-Site Sync (Optional)
    ↓
S3 Storage (AWS S3, MinIO, etc.)
```

### What Gets Backed Up

1. **PostgreSQL Database**: All tables, data, schemas, and migrations
2. **Uploaded Files**: Resume files, document uploads (stored in `/data/uploads`)
3. **ML Model Cache**: Downloaded models and embeddings (stored in `/data/models_cache`)
4. **Configuration**: Application settings and environment configurations

---

## Recovery Objectives

### Target Metrics

The backup system is designed to meet the following recovery objectives:

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** (Recovery Time Objective) | < 4 hours | Maximum time to restore system functionality |
| **RPO** (Recovery Point Objective) | < 24 hours | Maximum acceptable data loss (time since last backup) |

### What This Means

- **RTO < 4 hours**: From disaster declaration to full system restoration
- **RPO < 24 hours**: In worst case, you lose one day of data (daily backups at 2 AM)

### Achieving RTO/RPO

- **Automated Backups**: Run daily at 2 AM without manual intervention
- **Fast Restore**: Optimized restore procedures for quick recovery
- **Off-Site Storage**: S3 backups protect against site-wide disasters
- **Regular Testing**: Monthly restore tests ensure procedures work

---

## Backup Types and Retention

### Backup Categories

#### 1. Database Backups

**Location**: `/data/backups/database/`

**Format**: Compressed SQL dumps (`*.sql.gz`)

**Contents**: Complete PostgreSQL database dump including:
- All tables and data
- Indexes and constraints
- Sequences and migrations
- **Excludes**: Ownership and ACLs (for easier restoration)

**Example Filename**: `database_20240201_020000.sql.gz`

**Creation Method**: `pg_dump` with gzip compression

#### 2. Files Backups

**Location**: `/data/backups/files/`

**Format**: Compressed tar archives (`*.tar.gz`)

**Contents**: Uploaded resume files and documents
- Original directory structure preserved
- Supports incremental backups using rsync

**Example Filename**: `files_20240201_020000.tar.gz`

**Creation Method**: `tar` with gzip compression

#### 3. Models Backups

**Location**: `/data/backups/models/`

**Format**: Compressed tar archives (`*.tar.gz`)

**Contents**: ML model cache and embeddings
- SpaCy models (en_core_web_sm, ru_core_news_sm)
- Sentence transformers models
- KeyBERT models

**Example Filename**: `models_20240201_020000.tar.gz`

**Creation Method**: `tar` with gzip compression

#### 4. Full Backups

**Location**: `/data/backups/full/`

**Format**: Combined tar archives (`*.tar.gz`)

**Contents**: Database + Files + Models in single archive
- Includes metadata file (`metadata.json`)
- Easiest for complete system restore

**Example Filename**: `full_20240201_020000.tar.gz`

**Creation Method**: Combined backup of all components

### Retention Policy

| Backup Type | Retention Period | Automatic Cleanup |
|-------------|-----------------|-------------------|
| Daily Backups | 30 days | ✅ Yes (via Celery) |
| S3 Off-Site | 90 days | ✅ Yes (via lifecycle policy) |
| Manual Backups | Until manually deleted | ❌ No |

**Retention Configuration**:

```bash
# .env
BACKUP_RETENTION_DAYS=30
```

### Backup Integrity

Every backup includes:
- **SHA256 Checksum**: Automatic calculation on creation
- **Size Tracking**: File size recorded for verification
- **Metadata**: Creation timestamp, component details
- **Integrity Verification**: Can verify backups before restore

---

## Restore Procedures

### Pre-Restore Checklist

Before starting any restore operation:

- [ ] Stop all application services
- [ ] Verify backup file integrity (checksum)
- [ ] Ensure sufficient disk space (2x backup size)
- [ ] Document current system state
- [ ] Notify stakeholders of planned downtime
- [ ] Have rollback plan ready

### Health Check

Verify system is ready for restore:

```bash
# Docker deployment
docker-compose exec backend python -c "
from tasks.backup_tasks import backup_health_check_task
result = backup_health_check_task()
print(result)
"

# Check available disk space
df -h /data/backups

# Verify backup directories exist
ls -la /data/backups/
```

### Option 1: Full System Restore (Recommended)

Use this for complete disaster recovery when entire system needs restoration.

#### Step 1: Stop All Services

```bash
# Docker deployment
docker-compose down

# Verify all containers stopped
docker-compose ps
```

#### Step 2: Select Backup

```bash
# List available full backups
ls -lh /data/backups/full/*.tar.gz | tail -10

# Choose the most recent appropriate backup
# Example: full_20240201_020000.tar.gz
```

#### Step 3: Verify Backup Integrity

```bash
# Verify checksum (if available)
docker-compose run --rm backend python -c "
from services.backup_service import get_backup_service
service = get_backup_service()
result = service.verify_backup_integrity('/data/backups/full/full_20240201_020000.tar.gz')
print(result)
"

# Expected output includes: "valid": true, checksum match
```

#### Step 4: Perform Restore

**Method A: Using API (Recommended)**

```bash
# Start backend only (needed for API)
docker-compose up -d backend

# Trigger restore via API
curl -X POST http://localhost:8000/api/admin/restore \
  -H "Content-Type: application/json" \
  -d '{
    "backup_path": "/data/backups/full/full_20240201_020000.tar.gz",
    "backup_type": "full",
    "create_backup_before": true
  }'

# Monitor restore progress
docker-compose logs -f backend
```

**Method B: Using Celery Task**

```bash
# Start Celery worker
docker-compose up -d celery_worker

# Trigger restore task
docker-compose exec backend python -c "
from tasks.backup_tasks import restore_from_backup_task
result = restore_from_backup_task(
    backup_path='/data/backups/full/full_20240201_020000.tar.gz',
    backup_type='full',
    create_backup_before=True
)
print(result)
"
```

**Method C: Manual Restore**

```bash
# Extract backup to temporary directory
mkdir -p /tmp/restore
tar -xzf /data/backups/full/full_20240201_020000.tar.gz -C /tmp/restore

# Restore database
gunzip -c /tmp/restore/*_db*.sql.gz | docker-compose exec -T postgres psql -U postgres -d resume_analysis

# Restore files
tar -xzf /tmp/restore/*_files*.tar.gz -C /data/

# Restore models
tar -xzf /tmp/restore/*_models*.tar.gz -C /data/

# Cleanup
rm -rf /tmp/restore
```

#### Step 5: Verify Restoration

```bash
# Start all services
docker-compose up -d

# Run database migrations (if needed)
docker-compose exec backend alembic upgrade head

# Health check
curl http://localhost:8000/health

# Verify data
docker-compose exec backend python -c "
from sqlalchemy import create_engine
from sqlalchemy.text import text
engine = create_engine('postgresql://postgres:postgres@postgres:5432/resume_analysis')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM resumes'))
    print(f'Resumes in database: {result.scalar()}')
"
```

#### Step 6: Post-Restore Validation

- [ ] Verify database record counts
- [ ] Check uploaded files are accessible
- [ ] Test ML model loading
- [ ] Run critical workflows end-to-end
- [ ] Check Grafana dashboards
- [ ] Review logs for errors

### Option 2: Database-Only Restore

Use when only database needs recovery (files and models are intact).

```bash
# Stop backend
docker-compose stop backend

# List database backups
ls -lh /data/backups/database/*.sql.gz | tail -5

# Restore database
gunzip -c /data/backups/database/database_20240201_020000.sql.gz | \
  docker-compose exec -T postgres psql -U postgres -d resume_analysis

# Restart backend
docker-compose start backend

# Verify
curl http://localhost:8000/health
```

### Option 3: Files-Only Restore

Use when uploaded files need recovery (database is intact).

```bash
# Backup current files (optional)
mv /data/uploads /data/uploads.backup.$(date +%Y%m%d_%H%M%S)

# Restore files
tar -xzf /data/backups/files/files_20240201_020000.tar.gz -C /data/

# Verify
ls -la /data/uploads/
```

### Option 4: Models-Only Restore

Use when ML model cache needs recovery.

```bash
# Backup current models (optional)
mv /data/models_cache /data/models_cache.backup.$(date +%Y%m%d_%H%M%S)

# Restore models
tar -xzf /data/backups/models/models_20240201_020000.tar.gz -C /data/

# Verify
ls -la /data/models_cache/
```

### Rollback Procedure

If restore fails or causes issues:

```bash
# Stop services
docker-compose down

# Restore from pre-restore backup (if created)
# The restore task creates a backup before restore
ls -lh /data/backups/full/pre_restore_*

# Restore the pre-restore backup
docker-compose run --rm backend python -c "
from tasks.backup_tasks import restore_from_backup_task
from services.backup_service import get_backup_service
service = get_backup_service()
backups = service.get_backups_list()
pre_restore = [b for b in backups if 'pre_restore' in b['name']][0]
restore_from_backup_task(pre_restore['path'], 'full', False)
"

# Start services
docker-compose up -d
```

---

## S3 Off-Site Recovery

### Overview

S3 off-site backups provide protection against site-wide disasters (fire, flood, theft, etc.). Backups are automatically synced to S3-compatible storage after creation.

### Configuration

```bash
# .env
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_ENDPOINT=https://s3.amazonaws.com
BACKUP_S3_ACCESS_KEY=your-access-key
BACKUP_S3_SECRET_KEY=your-secret-key
BACKUP_S3_REGION=us-east-1
```

### Listing S3 Backups

```bash
# Via API
curl http://localhost:8000/api/admin/backups/s3

# Via Python
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
from tasks.backup_tasks import get_s3_config
service = get_backup_service(s3_config=get_s3_config())
backups = service.list_s3_backups()
for backup in backups:
    print(f\"{backup['s3_key']} - {backup['size_bytes']} bytes\")
"
```

### Downloading from S3

#### Method A: Via API

```bash
curl -X POST http://localhost:8000/api/admin/backups/s3/download \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "backups/2024/02/01/full_20240201_020000.tar.gz"
  }'
```

#### Method B: Via Python

```bash
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
from tasks.backup_tasks import get_s3_config
service = get_backup_service(s3_config=get_s3_config())
result = service.download_from_s3(
    s3_key='backups/2024/02/01/full_20240201_020000.tar.gz',
    local_path='/data/backups/full/full_20240201_020000.tar.gz'
)
print(result)
"
```

#### Method C: Via AWS CLI

```bash
# Install AWS CLI
apt-get install awscli

# Configure credentials
aws configure --profile agenthr-backup

# Download backup
aws s3 cp \
  s3://your-backup-bucket/backups/2024/02/01/full_20240201_020000.tar.gz \
  /data/backups/full/

# Verify checksum
sha256sum /data/backups/full/full_20240201_020000.tar.gz
```

### Restoring from S3 Backup

Once downloaded from S3, follow the standard restore procedures:

```bash
# 1. Download from S3 (see above)
# 2. Verify integrity
# 3. Perform restore (see Option 1: Full System Restore)
```

### S3-to-S3 Restore (Different Region)

For cross-region disaster recovery:

```bash
# Copy S3 backup to different region
aws s3 cp \
  s3://us-east-1-backups/full_20240201_020000.tar.gz \
  s3://eu-west-1-backups/full_20240201_020000.tar.gz \
  --source-region us-east-1 \
  --region eu-west-1

# Then download from new region and restore
```

### MinIO Self-Hosted S3

If using MinIO instead of AWS S3:

```bash
# .env
BACKUP_S3_ENDPOINT=http://minio:9000
BACKUP_S3_BUCKET=agenthr-backups
BACKUP_S3_ACCESS_KEY=minioadmin
BACKUP_S3_SECRET_KEY=minioadmin
```

Restore procedures are identical - just endpoint changes.

---

## Testing Procedures

### Regular Testing Schedule

| Test Type | Frequency | Owner |
|-----------|-----------|-------|
| Backup Integrity Check | Daily (automated) | System |
| Restore Test (Staging) | Monthly | DevOps |
| Full DR Drill | Quarterly | Management |
| S3 Download Test | Monthly | DevOps |

### Test 1: Backup Integrity Verification

**Purpose**: Verify backups are not corrupted

**Frequency**: Daily (automated via Celery)

**Procedure**:

```bash
# Via API - verify latest backup
curl -X POST http://localhost:8000/api/admin/backups/verify \
  -H "Content-Type: application/json" \
  -d '{
    "backup_path": "/data/backups/full/full_20240201_020000.tar.gz"
  }'

# Via Python - verify all backups
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
service = get_backup_service()
backups = service.get_backups_list()
for backup in backups[:5]:  # Check latest 5
    result = service.verify_backup_integrity(backup['path'])
    print(f\"{backup['name']}: {'PASS' if result['valid'] else 'FAIL'}\")
"
```

**Success Criteria**:
- All backups report `valid: true`
- Checksums match expected values
- Files are readable and not corrupted

### Test 2: Staging Environment Restore

**Purpose**: Verify backups can be successfully restored

**Frequency**: Monthly

**Procedure**:

```bash
# 1. Use staging docker-compose file
cp docker-compose.yml docker-compose.staging.yml
# Edit staging to use different ports/volumes

# 2. Start staging environment
docker-compose -f docker-compose.staging.yml up -d

# 3. Download latest production backup
# (From S3 or copy from production server)

# 4. Perform restore
docker-compose -f docker-compose.staging.yml exec backend python -c "
from tasks.backup_tasks import restore_from_backup_task
result = restore_from_backup_task(
    backup_path='/data/backups/full/full_20240201_020000.tar.gz',
    backup_type='full'
)
print(result)
"

# 5. Validate restoration
curl http://localhost:8001/health  # Staging port
```

**Success Criteria**:
- Restore completes without errors
- All services start successfully
- Health checks pass
- Data counts match production
- Critical workflows function correctly

**Documentation**:
```bash
# Document test results
cat > /var/log/dr-test-$(date +%Y%m).log << EOF
Disaster Recovery Test - $(date)
Backup: full_20240201_020000.tar.gz
Start Time: $(date)
Status: SUCCESS
Data Verified:
- Resumes: COUNT
- Users: COUNT
- Files: COUNT
End Time: $(date)
Duration: X hours
EOF
```

### Test 3: S3 Download Test

**Purpose**: Verify S3 backups are accessible

**Frequency**: Monthly

**Procedure**:

```bash
# List S3 backups
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
from tasks.backup_tasks import get_s3_config
service = get_backup_service(s3_config=get_s3_config())
backups = service.list_s3_backups()
print(f'Found {len(backups)} S3 backups')
latest = backups[0] if backups else None
print(f'Latest: {latest[\"s3_key\"] if latest else \"None\"}')
"

# Download latest backup
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
from tasks.backup_tasks import get_s3_config
service = get_backup_service(s3_config=get_s3_config())
result = service.download_from_s3(
    s3_key='backups/2024/02/01/full_20240201_020000.tar.gz',
    local_path='/tmp/test_restore.tar.gz'
)
print(f'Downloaded: {result[\"size_bytes\"]} bytes')
"

# Verify download
sha256sum /tmp/test_restore.tar.gz
rm /tmp/test_restore.tar.gz
```

**Success Criteria**:
- S3 connection succeeds
- Latest backup is downloadable
- Checksum is correct
- Download completes in reasonable time (< 1 hour for 10GB)

### Test 4: Full Disaster Recovery Drill

**Purpose**: End-to-end test of complete disaster recovery

**Frequency**: Quarterly

**Scenario**: Complete production server failure

**Procedure**:

1. **Declaration**: Simulate disaster declaration at 9 AM
2. **Assessment**: Document current system state
3. **Restore**: Follow full restore procedure on new infrastructure
4. **Validation**: Complete system validation checklist
5. **Cutover**: Test DNS cutover procedure
6. **Documentation**: Document lessons learned

**Timeline Goals**:
| Milestone | Target Time |
|-----------|-------------|
| Restore started | +30 minutes |
| Database restored | +2 hours |
| Services running | +3 hours |
| Validation complete | +4 hours |

**Success Criteria**:
- RTO < 4 hours achieved
- All data restored (RPO < 24 hours)
- No data corruption
- All services functional
- Performance acceptable

### Test 5: Backup Creation Test

**Purpose**: Verify backup creation works correctly

**Frequency**: Weekly

**Procedure**:

```bash
# Trigger manual backup
curl -X POST http://localhost:8000/api/admin/backups/create \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "full",
    "name": "test_backup_$(date +%Y%m%d_%H%M%S)"
  }'

# Verify backup created
ls -lh /data/backups/full/test_backup_*

# Verify backup integrity
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
service = get_backup_service()
result = service.verify_backup_integrity('/data/backups/full/test_backup_*.tar.gz')
print(result)
"
```

**Success Criteria**:
- Backup creates without errors
- File size is reasonable (> 100 MB for typical deployment)
- Checksum calculation succeeds
- All components included (db, files, models)

---

## Emergency Runbook

### Scenario 1: Database Corruption

**Symptoms**:
- Application errors "database connection failed"
- Queries returning inconsistent data
- PostgreSQL logs showing corruption

**Immediate Actions**:

```bash
# 1. Stop backend to prevent further damage
docker-compose stop backend celery_worker

# 2. Check PostgreSQL logs
docker-compose logs --tail=100 postgres

# 3. Try to identify corrupted data
docker-compose exec postgres psql -U postgres -d resume_analysis -c "\dt"

# 4. Create emergency backup of current state
docker-compose exec postgres pg_dump -U postgres resume_analysis > /tmp/emergency_backup.sql

# 5. Restore from last known good backup
# (See Database-Only Restore above)
```

**Prevention**:
- Enable PostgreSQL WAL archiving
- Regular database vacuuming
- Monitor disk space

### Scenario 2: Disk Failure

**Symptoms**:
- I/O errors in logs
- "No space left on device"
- Services crashing

**Immediate Actions**:

```bash
# 1. Check disk status
df -h
lsblk

# 2. If disk failed, replace hardware
# 3. Restore from S3 backup to new disk
# 4. Update mount points if needed

# 5. Verify backup before restore
# If original disk is partially accessible:
cp /data/backups/latest.tar.gz /tmp/  # Save to safe location
```

**Prevention**:
- RAID configuration for redundancy
- Monitor disk health (S.M.A.R.T.)
- Automated off-site backups (S3)
- Regular disk capacity planning

### Scenario 3: Accidental Data Deletion

**Symptoms**:
- User reports missing data
- Database record counts dropped
- Files deleted from uploads directory

**Immediate Actions**:

```bash
# 1. Stop application immediately
docker-compose down

# 2. Identify when data was deleted
docker-compose exec postgres psql -U postgres -d resume_analysis -c "
SELECT MAX(created_at) FROM resumes;
"

# 3. Find backup from before deletion
ls -lht /data/backups/full/

# 4. Restore to point-in-time
# Use backup created before deletion time

# 5. Start services
docker-compose up -d
```

**Prevention**:
- Regular backups (daily)
- Soft deletes in application
- User confirmation for destructive actions
- Audit logging

### Scenario 4: Ransomware Attack

**Symptoms**:
- Files encrypted with new extension
- Ransom notes in directories
- Application unable to read files

**Immediate Actions**:

```bash
# 1. ISOLATE SYSTEM - Disconnect from network
# 2. DO NOT PAY RANSOM
# 3. Assess damage
find /data -name "*.encrypted" | wc -l

# 4. Shut down compromised system
docker-compose down

# 5. Spin up clean infrastructure
# 6. Restore from offline backups (before attack)
# Use backup from day before attack

# 7. Scan restored data for malware
# 8. Change all passwords and credentials
# 9. Investigate attack vector
```

**Prevention**:
- Offline backups (S3 with versioning)
- Regular security updates
- User access controls
- Network segmentation
- Security monitoring
- Incident response plan

### Scenario 5: Complete Site Loss

**Symptoms**:
- Natural disaster (fire, flood)
- Data center failure
- All servers inaccessible

**Immediate Actions**:

```bash
# 1. Declare disaster
# 2. Activate DR team
# 3. Provision new infrastructure
#    - New cloud account or region
#    - New servers

# 4. Restore from S3 backups
#    - Download latest full backup
#    - Follow full restore procedure

# 5. Update DNS to point to new infrastructure
#    Update A records for:
#    - api.yourdomain.com
#    - app.yourdomain.com

# 6. Validate system functionality
# 7. Notify users of service restoration
```

**Prevention**:
- Multi-region deployment
- S3 cross-region replication
- DNS failover configuration
- Regular DR drills

---

## Preventing Data Loss

### Best Practices

#### 1. Backup Strategy

- **3-2-1 Rule**:
  - **3** copies of data (production + 2 backups)
  - **2** different storage types (local disk + S3)
  - **1** off-site copy (S3 in different region)

- **Backup Frequency**:
  - Database: Daily automated
  - Files: Daily automated
  - Configuration: On change
  - Before upgrades: Manual

#### 2. Monitoring

```bash
# Check backup status daily
curl http://localhost:8000/api/admin/backups/status

# Set up Grafana alerts for:
# - Backup failures
# - Missed backups (> 26 hours since last)
# - Low disk space (< 10% free)
# - S3 sync failures
```

#### 3. Testing

- Monthly restore tests to staging
- Quarterly full DR drills
- Annual backup audit

#### 4. Security

- Encrypt S3 backups at rest
- Use IAM roles for S3 access
- Rotate access keys quarterly
- Enable S3 versioning
- Use MFA for destructive operations

#### 5. Documentation

- Document all restore procedures
- Maintain runbooks for common scenarios
- Store DR docs off-site (GitHub, wiki)
- Train team on procedures

### Backup Verification Checklist

Daily:
- [ ] Automated backup completed successfully
- [ ] Backup size is reasonable
- [ ] No errors in logs

Weekly:
- [ ] Can list recent backups
- [ ] Checksums are valid
- [ ] S3 sync succeeded

Monthly:
- [ ] Test restore to staging
- [ ] Verify data integrity
- [ ] Document test results

Quarterly:
- [ ] Full DR drill
- [ ] Update runbooks
- [ ] Review RTO/RPO targets

---

## Monitoring and Alerts

### Grafana Dashboard

Access the backup monitoring dashboard:

```
URL: http://localhost:3001/d/backup-status
```

**Key Metrics**:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `backup_last_success_seconds` | Time since last successful backup | > 90000 (25 hours) |
| `backup_size_bytes` | Size of last backup | - |
| `backup_duration_seconds` | Time taken for backup | > 3600 (1 hour) |
| `backup_failures_total` | Total backup failures | Count > 0 |
| `backup_retention_count` | Number of retained backups | < 7 |
| `s3_sync_last_success_seconds` | Time since last S3 sync | > 172800 (48 hours) |
| `backup_disk_usage_bytes` | Disk space used by backups | > 80% capacity |

### Prometheus Alerts

Alert rules are defined in `monitoring/grafana/provisioning/alerts/backup_alert_rules.yml`:

```yaml
groups:
  - name: backup_alerts
    rules:
      - alert: BackupFailure
        expr: increase(backup_failures_total[1h]) > 0
        for: 5m
        annotations:
          summary: "Backup failed in last hour"

      - alert: MissedBackup
        expr: time() - backup_last_success_timestamp_seconds > 90000
        for: 10m
        annotations:
          summary: "No successful backup in 25 hours"

      - alert: LowDiskSpace
        expr: backup_disk_usage_bytes / backup_disk_capacity_bytes > 0.9
        for: 15m
        annotations:
          summary: "Backup disk > 90% full"
```

### Email Notifications

Configure email alerts:

```bash
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@agenthr.com
ALERT_EMAIL=admin@yourcompany.com

# Email notifications sent for:
# - Backup failures
# - S3 sync failures
# - Restore completions
# - Integrity check failures
```

### Health Check Endpoint

Monitor backup system health:

```bash
curl http://localhost:8000/api/admin/backups/health

# Response:
{
  "status": "healthy",
  "last_backup": "2024-02-01T02:00:00Z",
  "last_backup_age_hours": 12,
  "disk_space_percent": 45,
  "s3_enabled": true,
  "s3_last_sync": "2024-02-01T03:00:00Z",
  "checks": {
    "backup_directory": "ok",
    "s3_connection": "ok",
    "disk_space": "ok"
  }
}
```

---

## Common Recovery Scenarios

### Scenario: "I accidentally deleted important resumes"

**Recovery Time**: 30-60 minutes

**Steps**:

1. Stop application to prevent further changes
2. Identify when deletion occurred
3. Find backup from before deletion
4. Restore database-only backup
5. Verify records are restored
6. Restart application

```bash
# Example: Deletion happened at 3 PM on Feb 1
# Last backup was at 2 AM on Feb 1

docker-compose stop backend

# Find backup
ls -lh /data/backups/database/database_20240201_*.sql.gz

# Restore
gunzip -c /data/backups/database/database_20240201_020000.sql.gz | \
  docker-compose exec -T postgres psql -U postgres -d resume_analysis

# Verify
docker-compose exec backend python -c "
from database import SessionLocal
from models import Resume
db = SessionLocal()
count = db.query(Resume).count()
print(f'Resumes restored: {count}')
"

docker-compose start backend
```

### Scenario: "Server disk failed completely"

**Recovery Time**: 2-4 hours

**Steps**:

1. Procure replacement hardware/instance
2. Install Docker and dependencies
3. Clone application code
4. Download backup from S3
5. Extract and restore
6. Start services
7. Update DNS if needed

```bash
# On new server:

# 1. Install dependencies
apt-get update
apt-get install -y docker.io docker-compose git

# 2. Clone code
git clone https://github.com/your-org/agenthr.git
cd agenthr

# 3. Configure .env (use secure values)
cp .env.example .env
# Edit .env with production values

# 4. Download backup from S3
aws s3 cp \
  s3://your-backup-bucket/backups/2024/02/01/full_20240201_020000.tar.gz \
  /data/backups/full/

# 5. Start services
docker-compose up -d

# 6. Wait for startup, then restore
docker-compose exec backend python -c "
from tasks.backup_tasks import restore_from_backup_task
result = restore_from_backup_task(
    backup_path='/data/backups/full/full_20240201_020000.tar.gz',
    backup_type='full'
)
print(result)
"

# 7. Verify
curl http://localhost:8000/health
```

### Scenario: "Database migration went wrong"

**Recovery Time**: 30-60 minutes

**Steps**:

1. Stop application
2. Identify failed migration
3. Restore database backup
4. Verify schema
5. Re-apply migration correctly

```bash
# Migration failed after running

docker-compose stop backend

# Restore from backup taken before migration
gunzip -c /data/backups/database/database_before_migration.sql.gz | \
  docker-compose exec -T postgres psql -U postgres -d resume_analysis

# Verify current migration version
docker-compose exec backend alembic current

# Fix migration script
# Then re-run
docker-compose exec backend alembic upgrade head

docker-compose start backend
```

### Scenario: "Need to test older backup"

**Purpose**: Audit, investigation, or data mining

**Steps**:

1. Spin up temporary test environment
2. Download specific backup
3. Restore to test environment
4. Access data needed
5. Destroy test environment

```bash
# Create test environment
cp docker-compose.yml docker-compose.test.yml
# Edit to use different ports (8001, 5433, etc.)

# Start test DB
docker-compose -f docker-compose.test.yml up -d postgres

# Restore old backup
gunzip -c /data/backups/database/database_20240101_020000.sql.gz | \
  docker-compose -f docker-compose.test.yml exec -T postgres psql -U postgres -d resume_analysis

# Query data
docker-compose -f docker-compose.test.yml exec postgres psql -U postgres -d resume_analysis \
  -c "SELECT * FROM resumes WHERE created_at < '2024-01-01'"

# Cleanup when done
docker-compose -f docker-compose.test.yml down -v
```

---

## Additional Resources

### Related Documentation

- **Deployment Guide**: `backend/docs/DEPLOYMENT.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Monitoring Guide**: `monitoring/README.md`
- **Architecture**: `backend/docs/ARCHITECTURE.md`

### Support Contacts

- **DevOps Team**: devops@yourcompany.com
- **Database Admin**: dba@yourcompany.com
- **Emergency Contact**: +1-555-EMERG

### External References

- PostgreSQL Backup: https://www.postgresql.org/docs/current/backup.html
- AWS S3: https://docs.aws.amazon.com/s3/
- Docker Volumes: https://docs.docker.com/storage/volumes/

---

**Last Updated**: 2024-02-01
**Version**: 1.0.0
**Maintained By**: DevOps Team
