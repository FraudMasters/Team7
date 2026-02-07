# Backup RTO/RPO Documentation

## Project: AgentHR Resume Analysis System

## Table of Contents

1. [RTO/RPO Overview](#rto-rpo-overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Recovery Time Breakdown](#recovery-time-breakdown)
4. [Testing Requirements](#testing-requirements)
5. [Validation Procedures](#validation-procedures)
6. [Performance Monitoring](#performance-monitoring)
7. [Continuous Improvement](#continuous-improvement)
8. [Compliance and Reporting](#compliance-and-reporting)

---

## RTO/RPO Overview

Recovery Time Objective (RTO) and Recovery Point Objective (RPO) are critical metrics that define the disaster recovery capabilities of the AgentHR system. These objectives ensure business continuity and minimize data loss in the event of a disaster.

### Definitions

**RTO (Recovery Time Objective)**: The maximum acceptable length of time that a service or system can be offline after a disaster before causing unacceptable business impact.

**RPO (Recovery Point Objective)**: The maximum acceptable amount of data loss measured in time, representing the point in time to which data must be recovered after a disaster.

### Target Metrics

The AgentHR backup system is designed to meet the following recovery objectives:

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** (Recovery Time Objective) | **< 4 hours** | Maximum time from disaster declaration to full system restoration |
| **RPO** (Recovery Point Objective) | **< 24 hours** | Maximum acceptable data loss (time since last successful backup) |

### What This Means in Practice

- **RTO < 4 hours**: From the moment a disaster is declared, the system must be fully operational within 4 hours
- **RPO < 24 hours**: In the worst-case scenario, you may lose up to one day of data (daily backups run at 2 AM)

---

## Recovery Objectives

### Detailed RTO Breakdown

The 4-hour RTO is broken down into specific phases:

| Phase | Target Time | Activities |
|-------|-------------|------------|
| **Disaster Detection** | 15 minutes | Monitor alerts, confirm disaster |
| **Assessment & Declaration** | 15 minutes | Evaluate impact, declare disaster |
| **Backup Acquisition** | 30 minutes | Download backup from local or S3 storage |
| **System Preparation** | 30 minutes | Provision infrastructure, prepare environment |
| **Data Restoration** | 2 hours | Restore database, files, and models |
| **Validation & Testing** | 30 minutes | Verify system functionality, run health checks |
| **Total** | **4 hours** | Complete system recovery |

### Detailed RPO Breakdown

The 24-hour RPO is based on:

| Factor | Time Impact | Description |
|--------|-------------|-------------|
| **Backup Schedule** | Daily at 2 AM | Automated daily backups |
| **Backup Duration** | ~30 minutes | Time to complete backup creation |
| **S3 Sync** | ~15 minutes | Time to sync to off-site storage |
| **Worst Case Data Loss** | 24 hours | If disaster occurs at 1:59 AM, previous day's backup is used |

### Achieving RTO/RPO Targets

The system achieves these objectives through:

1. **Automated Daily Backups**: Run at 2 AM daily without manual intervention
2. **Optimized Restore Procedures**: Efficient restoration processes minimize downtime
3. **Off-Site Storage**: S3 backups protect against site-wide disasters
4. **Regular Testing**: Monthly restore tests ensure procedures work
5. **Monitoring and Alerts**: Real-time visibility into backup health

---

## Recovery Time Breakdown

### Full System Recovery Timeline

The following timeline details the steps and estimated time for a complete system recovery:

```
00:00 - Disaster Detected (Automated monitoring alerts)
00:15 - Disaster Declared (DevOps team assessment)
01:00 - Backup Downloaded (From local storage or S3)
01:30 - Infrastructure Ready (New server or existing staging)
03:30 - Data Restored (Database, files, models)
04:00 - System Validated (Health checks, smoke tests)
04:00 - SYSTEM ONLINE (RTO target achieved)
```

### Component-Specific Recovery Times

| Component | Recovery Time | Dependencies |
|-----------|---------------|--------------|
| **Database** | 45-60 minutes | PostgreSQL backup restoration |
| **Uploaded Files** | 20-30 minutes | Tar extraction and verification |
| **ML Models** | 15-20 minutes | Cache extraction |
| **Configuration** | 10 minutes | Environment setup |
| **Validation** | 30 minutes | Health checks and smoke tests |

### Factors Affecting Recovery Time

The following factors can impact actual recovery time:

| Factor | Impact | Mitigation |
|--------|--------|------------|
| **Backup Size** | Larger backups take longer | Use compression, archive old data |
| **Network Bandwidth** | Slow S3 downloads | Use direct-attach storage for local backups |
| **Disk Speed** | I/O performance affects restore | Use SSDs for backup storage |
| **Team Availability** | Response time affects RTO | 24/7 on-call rotation |
| **Infrastructure Provisioning** | New servers take time | Maintain staging environment |

---

## Testing Requirements

Regular testing is essential to ensure RTO/RPO objectives can be met. The following tests are required:

### 1. Backup Integrity Test

**Frequency**: Daily (automated)
**Owner**: System (Automated via Celery)

**Purpose**: Verify backups are not corrupted

**Procedure**:
```bash
# Automated integrity check runs daily after backup
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
service = get_backup_service()
backups = service.get_backups_list()
latest = backups[0]
result = service.verify_backup_integrity(latest['path'])
print(f'Backup {latest[\"name\"]}: {\"PASS\" if result[\"valid\"] else \"FAIL\"}')
"
```

**Success Criteria**:
- Latest backup reports `valid: true`
- SHA256 checksum matches expected value
- File is readable and not corrupted
- Test completes within 5 minutes

**Failure Action**: Alert DevOps team, create new backup

### 2. Restore Test (Staging Environment)

**Frequency**: Monthly
**Owner**: DevOps Engineer
**Duration Target**: < 2 hours

**Purpose**: Verify backups can be successfully restored within RTO

**Procedure**:
1. Prepare staging environment (isolated from production)
2. Download latest production backup (local or S3)
3. Perform full system restore
4. Validate restoration completeness
5. Document results and timeline

**Test Script**:
```bash
#!/bin/bash
# Monthly restore test script

echo "Starting monthly restore test - $(date)"
START_TIME=$(date +%s)

# 1. Ensure staging is clean
docker-compose -f docker-compose.staging.yml down -v

# 2. Start staging infrastructure
docker-compose -f docker-compose.staging.yml up -d postgres

# 3. Download backup (if needed)
# aws s3 cp s3://backups/latest.tar.gz /data/backups/

# 4. Perform restore
docker-compose -f docker-compose.staging.yml exec backend python -c "
from tasks.backup_tasks import restore_from_backup_task
result = restore_from_backup_task(
    backup_path='/data/backups/full/latest.tar.gz',
    backup_type='full'
)
print(result)
"

# 5. Start all services
docker-compose -f docker-compose.staging.yml up -d

# 6. Validate
sleep 30  # Wait for startup
curl -f http://localhost:8001/health || exit 1

# 7. Data verification
docker-compose -f docker-compose.staging.yml exec backend python -c "
from database import SessionLocal
from models import Resume, User
db = SessionLocal()
resume_count = db.query(Resume).count()
user_count = db.query(User).count()
print(f'Resumes: {resume_count}, Users: {user_count}')
db.close()
"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Restore test completed in ${DURATION} seconds"

# Document results
cat > /var/log/dr-test-$(date +%Y%m).log << EOF
Disaster Recovery Test - $(date)
Backup: latest.tar.gz
Start Time: $(date -d @$START_TIME)
End Time: $(date -d @$END_TIME)
Duration: $((DURATION / 60)) minutes
Status: SUCCESS
EOF
```

**Success Criteria**:
- Restore completes without errors
- All services start successfully
- Health checks pass
- Data counts match production
- Critical workflows function correctly
- Test completes within 2 hours

**Failure Action**: Investigate root cause, fix issues, document lessons learned

### 3. S3 Download Test

**Frequency**: Monthly
**Owner**: DevOps Engineer
**Duration Target**: < 1 hour (for 10GB backup)

**Purpose**: Verify S3 backups are accessible and downloadable

**Procedure**:
```bash
# Test S3 connectivity and download speed
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
from tasks.backup_tasks import get_s3_config
import time

service = get_backup_service(s3_config=get_s3_config())

# List backups
backups = service.list_s3_backups()
print(f'Found {len(backups)} S3 backups')

if backups:
    latest = backups[0]
    print(f'Testing download: {latest[\"s3_key\"]}')

    start = time.time()
    result = service.download_from_s3(
        s3_key=latest['s3_key'],
        local_path='/tmp/test_restore.tar.gz'
    )
    duration = time.time() - start

    print(f'Downloaded {result[\"size_bytes\"]} bytes in {duration:.0f} seconds')
    print(f'Speed: {result[\"size_bytes\"] / duration / 1024 / 1024:.2f} MB/s')

    # Verify
    import os
    os.remove('/tmp/test_restore.tar.gz')
"
```

**Success Criteria**:
- S3 connection succeeds
- Latest backup is downloadable
- Checksum is correct
- Download completes in reasonable time
- Download speed > 10 MB/s

**Failure Action**: Investigate S3 configuration, check network, verify credentials

### 4. Full Disaster Recovery Drill

**Frequency**: Quarterly
**Owner**: DevOps Team + Management
**Duration Target**: < 4 hours

**Purpose**: End-to-end test of complete disaster recovery process

**Scenario**: Complete production server failure requiring full restoration on new infrastructure

**Procedure**:

**Phase 1: Preparation (Week Before)**
- Schedule drill with all stakeholders
- Prepare new infrastructure (cloud account/region)
- Document current system state
- Notify users of planned downtime

**Phase 2: Execution (Drill Day)**
1. **Disaster Declaration** (0:00 - 0:15)
   - Simulate disaster detection
   - Assess impact
   - Formally declare disaster
   - Activate DR team

2. **Infrastructure Setup** (0:15 - 0:45)
   - Provision new servers
   - Install dependencies (Docker, Docker Compose)
   - Clone application code
   - Configure environment

3. **Backup Acquisition** (0:45 - 1:15)
   - Download backup from S3
   - Verify backup integrity
   - Prepare restore environment

4. **System Restoration** (1:15 - 3:15)
   - Restore database
   - Restore uploaded files
   - Restore ML models
   - Start all services

5. **Validation** (3:15 - 4:00)
   - Run health checks
   - Verify data integrity
   - Test critical workflows
   - Performance testing

6. **Documentation** (Post-Drill)
   - Document actual vs. target times
   - Identify bottlenecks
   - Document lessons learned
   - Update procedures

**Timeline Tracking**:
```bash
# Log each phase completion time
echo "$(date +%H:%M:%S) - Disaster declared" >> /var/log/dr-drill.log
echo "$(date +%H:%M:%S) - Infrastructure ready" >> /var/log/dr-drill.log
echo "$(date +%H:%M:%S) - Backup downloaded" >> /var/log/dr-drill.log
echo "$(date +%H:%M:%S) - Restore completed" >> /var/log/dr-drill.log
echo "$(date +%H:%M:%S) - Validation complete" >> /var/log/dr-drill.log
```

**Success Criteria**:
- RTO < 4 hours achieved
- All data restored (RPO < 24 hours)
- No data corruption
- All services functional
- Performance acceptable
- All critical workflows tested

**Failure Action**:
- Document what failed
- Identify root causes
- Update procedures
- Schedule retest

### 5. Backup Creation Performance Test

**Frequency**: Weekly
**Owner**: System (Automated)
**Duration Target**: < 1 hour

**Purpose**: Verify backup creation completes within acceptable time

**Procedure**:
```bash
# Trigger manual backup and measure duration
docker-compose exec backend python -c "
from tasks.backup_tasks import create_backup_task
import time

start = time.time()
result = create_backup_task(backup_type='full')
duration = time.time() - start

print(f'Backup created in {duration:.0f} seconds')
print(f'Size: {result[\"size_bytes\"] / 1024 / 1024:.2f} MB')

if duration > 3600:
    print('WARNING: Backup took longer than 1 hour')
"
```

**Success Criteria**:
- Backup creates without errors
- Completes within 1 hour
- File size is reasonable (> 100 MB for typical deployment)
- All components included

**Failure Action**: Alert DevOps team, investigate slow backup

---

## Validation Procedures

### Post-Restore Validation Checklist

After any restore operation, complete the following validation:

#### 1. System Health Checks

```bash
# Application health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

#### 2. Database Integrity

```bash
# Verify all tables exist
docker-compose exec postgres psql -U postgres -d resume_analysis -c "\dt"

# Check record counts
docker-compose exec postgres psql -U postgres -d resume_analysis -c "
SELECT
    'resumes' as table_name, COUNT(*) as count FROM resumes
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'organizations', COUNT(*) FROM organizations;
"

# Verify foreign key constraints
docker-compose exec postgres psql -U postgres -d resume_analysis -c "
SELECT COUNT(*) FROM resumes WHERE user_id NOT IN (SELECT id FROM users);
"
# Expected: 0 orphaned records
```

#### 3. File System Validation

```bash
# Check uploaded files directory
ls -la /data/uploads/
find /data/uploads/ -type f | wc -l

# Verify files match database records
docker-compose exec backend python -c "
from database import SessionLocal
from models import Resume
import os

db = SessionLocal()
resumes = db.query(Resume).all()

missing = 0
for resume in resumes:
    if not os.path.exists(resume.file_path):
        missing += 1

print(f'Missing files: {missing}/{len(resumes)}')
db.close()
"
```

#### 4. ML Model Validation

```bash
# Verify model cache
ls -la /data/models_cache/

# Test model loading
docker-compose exec backend python -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('SpaCy model loaded successfully')
except Exception as e:
    print(f'Error loading model: {e}')
"
```

#### 5. Critical Workflow Testing

```bash
# Test resume upload
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_resume.pdf"

# Test resume analysis
curl -X POST http://localhost:8000/api/resumes/ID/analyze \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test user authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

### Validation Sign-Off

After completing all validation checks, document results:

```bash
cat > /var/log/restore-validation-$(date +%Y%m%d-%H%M%S).log << EOF
Restore Validation Report
Date: $(date)
Backup: BACKUP_FILENAME
Restore Started: TIMESTAMP
Restore Completed: TIMESTAMP
Total Duration: X minutes

Validation Results:
- [PASS/FAIL] System Health Check
- [PASS/FAIL] Database Integrity (X records)
- [PASS/FAIL] File System Validation (X files)
- [PASS/FAIL] ML Model Loading
- [PASS/FAIL] Critical Workflows

Overall Status: PASS/FAIL
Validated By: NAME
EOF
```

---

## Performance Monitoring

### Key Metrics to Monitor

To ensure RTO/RPO objectives are met, monitor the following metrics:

#### Backup Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `backup_last_success_seconds` | Time since last successful backup | < 90000 (25 hours) | > 90000 |
| `backup_duration_seconds` | Time taken for backup creation | < 3600 (1 hour) | > 3600 |
| `backup_size_bytes` | Size of last backup | > 100 MB | < 100 MB (suspicious) |
| `backup_failures_total` | Total backup failures | 0 | > 0 |

#### Restore Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `restore_duration_seconds` | Time taken for last restore | < 14400 (4 hours) | > 14400 |
| `restore_success_rate` | Percentage of successful restores | 100% | < 100% |
| `restore_data_loss_hours` | Actual data loss in last restore | < 24 | > 24 |

#### S3 Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `s3_sync_last_success_seconds` | Time since last S3 sync | < 172800 (48 hours) | > 172800 |
| `s3_sync_duration_seconds` | Time for S3 sync | < 3600 (1 hour) | > 3600 |
| `s3_backup_count` | Number of backups in S3 | > 7 | < 7 |

#### Infrastructure Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `backup_disk_usage_percent` | Disk space used by backups | < 80% | > 80% |
| `database_size_bytes` | Database size | - | - |
| `uploads_size_bytes` | Uploads directory size | - | - |

### Grafana Dashboard

Monitor these metrics on the Backup Status dashboard:

```
URL: http://localhost:3001/d/backup-status
```

Key panels:
- Backup Timeline (last 30 days)
- Restore Duration Trend
- Disk Usage Over Time
- S3 Sync Status
- RTO/RPO Compliance

### Alerting Rules

Configure alerts in Grafana/Prometheus:

```yaml
groups:
  - name: rto_rpo_alerts
    rules:
      # RPO Alert
      - alert: RPOViolation
        expr: time() - backup_last_success_timestamp_seconds > 90000
        for: 10m
        annotations:
          summary: "RPO violated - no backup in 25 hours"

      # RTO Alert
      - alert: RTOViolation
        expr: restore_duration_seconds > 14400
        annotations:
          summary: "RTO violated - restore took longer than 4 hours"

      # Backup Performance
      - alert: BackupSlow
        expr: backup_duration_seconds > 3600
        annotations:
          summary: "Backup creation took longer than 1 hour"
```

---

## Continuous Improvement

### Quarterly Review Process

Every quarter, review and update RTO/RPO targets and procedures:

1. **Review Actual Performance**
   - Analyze backup/restore metrics
   - Compare actual vs. target RTO/RPO
   - Identify trends and anomalies

2. **Assess Business Requirements**
   - Meet with stakeholders
   - Review if 4-hour RTO is still appropriate
   - Evaluate if 24-hour RPO meets business needs

3. **Test Results Analysis**
   - Review monthly restore test results
   - Analyze quarterly DR drill findings
   - Identify areas for improvement

4. **Technology Assessment**
   - Evaluate new backup technologies
   - Consider infrastructure upgrades
   - Review industry best practices

5. **Update Documentation**
   - Revise procedures based on lessons learned
   - Update runbooks with new findings
   - Train team on changes

### Optimization Opportunities

Continuously look for opportunities to improve:

#### Reduce Backup Time
- Use incremental backups for large databases
- Optimize database before backup (VACUUM, ANALYZE)
- Compress backups more efficiently
- Parallel backup creation

#### Reduce Restore Time
- Pre-stage backups on fast storage
- Use database snapshots for faster restores
- Implement hot-standby replication
- Optimize restore scripts

#### Reduce Data Loss (RPO)
- Increase backup frequency to every 12 hours
- Implement continuous WAL archiving
- Use real-time replication
- Implement point-in-time recovery

#### Improve Reliability
- Add multiple backup destinations
- Implement backup checksums
- Add automated testing
- Enhance monitoring and alerting

### Success Metrics

Track the following metrics to measure improvement:

| Metric | Current | Target (6 months) | Target (12 months) |
|--------|---------|-------------------|-------------------|
| Average Backup Duration | 45 min | 40 min | 30 min |
| Average Restore Duration | 3.5 hours | 3 hours | 2 hours |
| Backup Success Rate | 99% | 99.5% | 99.9% |
| Restore Success Rate | 95% | 98% | 100% |
| Data Loss Incidents | 0/year | 0/year | 0/year |

---

## Compliance and Reporting

### Regulatory Requirements

The backup and recovery system must comply with:

**Data Protection Regulations**:
- GDPR: Right to data portability and backup
- SOC 2: Availability and processing integrity
- HIPAA: Data backup and recovery requirements (if applicable)

**Industry Standards**:
- ISO 27001: Information security management
- NIST: Cybersecurity framework
- ITIL: Service continuity management

### Audit Trail

Maintain comprehensive audit logs:

```bash
# Backup audit log
docker-compose exec backend python -c "
from services.backup_service import get_backup_service
service = get_backup_service()
backups = service.get_backups_list()

for backup in backups:
    print(f"{backup['created_at']}: {backup['name']} ({backup['size_bytes']} bytes)")
"
```

Required audit information:
- Backup creation timestamp
- Backup type and components
- Backup size and checksum
- Who initiated backup (manual vs. automated)
- S3 sync status
- Restore history

### Monthly Reporting

Generate monthly RTO/RPO compliance reports:

```python
# Generate monthly report
from datetime import datetime, timedelta
from services.backup_service import get_backup_service

service = get_backup_service()

# Get backups from last month
start_date = datetime.now() - timedelta(days=30)
backups = [b for b in service.get_backups_list()
            if b['created_at'] >= start_date]

report = {
    "period_start": start_date.isoformat(),
    "period_end": datetime.now().isoformat(),
    "total_backups": len(backups),
    "successful_backups": len([b for b in backups if b['status'] == 'success']),
    "failed_backups": len([b for b in backups if b['status'] == 'failed']),
    "average_backup_duration": sum(b['duration'] for b in backups) / len(backups),
    "rpo_compliance": "PASS" if len(backups) >= 28 else "FAIL",
    "rto_compliance": "PASS" if all(b['duration'] < 3600 for b in backups) else "FAIL"
}

print(report)
```

### Quarterly Compliance Review

Conduct quarterly compliance reviews:

1. **RPO Compliance**
   - Verify no gap > 24 hours between backups
   - Document any RPO violations
   - Identify root causes

2. **RTO Compliance**
   - Review restore test results
   - Verify restores complete < 4 hours
   - Document any RTO violations

3. **Data Integrity**
   - Verify backup integrity checks
   - Review checksum validation
   - Document any corruption issues

4. **Off-Site Storage**
   - Verify S3 backups are current
   - Test S3 restore capability
   - Document any sync failures

5. **Documentation**
   - Ensure all procedures are current
   - Verify team training is complete
   - Update runbooks as needed

---

## Additional Resources

### Related Documentation

- **Disaster Recovery Guide**: `docs/DISASTER_RECOVERY.md`
- **Backup Operations**: `docs/BACKUP_OPERATIONS.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Monitoring Guide**: `monitoring/README.md`

### Support Contacts

- **DevOps Team**: devops@yourcompany.com
- **Database Admin**: dba@yourcompany.com
- **Emergency Contact**: +1-555-EMERG

### External References

- NIST SP 800-34: Contingency Planning Guide
- ISO 27031: Guidelines for information and communication technology readiness
- DRII: Professional Practices for Business Continuity Practitioners

---

**Last Updated**: 2024-02-01
**Version**: 1.0.0
**Maintained By**: DevOps Team
**Review Frequency**: Quarterly
**Approved By**: CTO, VP Engineering
