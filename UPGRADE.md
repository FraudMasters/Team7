# AgentHR Upgrade Guide

This guide covers upgrading AgentHR to newer versions, including version compatibility, migration procedures, and rollback steps.

## Table of Contents

- [Before You Upgrade](#before-you-upgrade)
- [Version Compatibility](#version-compatibility)
- [Upgrade Process](#upgrade-process)
- [Migration Notes](#migration-notes)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

## Before You Upgrade

### Prerequisites

- **Backup**: Always backup your data before upgrading
- **Downtime**: Plan for 5-15 minutes of downtime
- **Resources**: Ensure sufficient disk space (at least 10GB free)
- **Access**: Verify you have access to all service credentials
- **Testing**: Have a rollback plan ready

### Create Backup

```bash
# Stop services
docker-compose down

# Backup PostgreSQL database
docker-compose up -d db
docker-compose exec db pg_dump -U agenthr_user agenthr_db > backup-$(date +%Y%m%d-%H%M%S).sql

# Backup uploaded files
tar -czf uploads-backup-$(date +%Y%m%d-%H%M%S).tar.gz backend/uploads/

# Backup configuration
cp .env .env.backup-$(date +%Y%m%d-%H%M%S)
cp docker-compose.yml docker-compose.yml.backup

# Stop database
docker-compose down
```

## Version Compatibility

### Current Version: 1.0.0

| From Version | To Version | Direct Upgrade | Notes |
|--------------|------------|----------------|-------|
| 0.9.x | 1.0.0 | ✅ Yes | Database migration required |
| 0.8.x | 1.0.0 | ⚠️ Via 0.9.x | Upgrade to 0.9.x first |
| 0.7.x | 1.0.0 | ❌ No | Multi-step upgrade required |

### Component Version Matrix

| AgentHR | Python | Node.js | PostgreSQL | Redis | Docker |
|---------|--------|---------|------------|-------|--------|
| 1.0.0 | 3.11+ | 18+ | 15+ | 7+ | 24+ |
| 0.9.x | 3.10+ | 16+ | 14+ | 6+ | 23+ |
| 0.8.x | 3.9+ | 16+ | 13+ | 6+ | 20+ |

## Upgrade Process

### Standard Upgrade (Docker-based)

#### Step 1: Prepare for Upgrade

```bash
# Navigate to project directory
cd agenthr

# Check current version
docker-compose exec backend python -c "from app.version import __version__; print(__version__)"

# Stop all services
docker-compose down

# Create backup (see above)
```

#### Step 2: Update Code

```bash
# Pull latest code
git fetch origin
git checkout tags/v1.0.0  # Replace with desired version

# Or pull latest from main branch
git pull origin main
```

#### Step 3: Update Dependencies

```bash
# Pull latest Docker images
docker-compose pull

# Rebuild images if using local builds
docker-compose build --no-cache
```

#### Step 4: Update Configuration

```bash
# Review .env.example for new variables
diff .env .env.example

# Add any new required environment variables to .env
nano .env
```

#### Step 5: Run Database Migrations

```bash
# Start database only
docker-compose up -d db

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose run --rm backend alembic upgrade head

# Verify migration
docker-compose run --rm backend alembic current
```

#### Step 6: Start All Services

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Check logs for errors
docker-compose logs -f --tail=100
```

#### Step 7: Verify Upgrade

```bash
# Check backend version
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:3000

# Test key functionality
curl -X GET http://localhost:8000/api/vacancies/

# Verify monitoring
curl http://localhost:3001  # Grafana
```

### Upgrade from 0.9.x to 1.0.0

#### Breaking Changes

- **Matching API**: Unified matching endpoint replaces individual matchers
- **Ranking Service**: New ML-based ranking system
- **Database Schema**: New tables for ranking and feedback

#### Migration Steps

```bash
# 1. Backup (critical for this upgrade)
docker-compose exec db pg_dump -U agenthr_user agenthr_db > backup-pre-1.0.0.sql

# 2. Stop services
docker-compose down

# 3. Update code
git checkout tags/v1.0.0

# 4. Update .env with new variables
cat >> .env << EOF
# Ranking Service (new in 1.0.0)
RANKING_MODEL_PATH=models/ranking_model.pkl
ENABLE_AB_TESTING=true
EOF

# 5. Pull new images
docker-compose pull

# 6. Start database
docker-compose up -d db
sleep 10

# 7. Run migrations
docker-compose run --rm backend alembic upgrade head

# 8. Initialize ranking models
docker-compose run --rm backend python scripts/init_ranking_models.py

# 9. Start all services
docker-compose up -d

# 10. Verify
curl http://localhost:8000/api/health
curl http://localhost:8000/api/ranking/models/importance
```

### Upgrade from 0.8.x to 1.0.0

**⚠️ Multi-step upgrade required**

```bash
# Step 1: Upgrade to 0.9.0 first
git checkout tags/v0.9.0
docker-compose pull
docker-compose up -d db
docker-compose run --rm backend alembic upgrade head
docker-compose up -d

# Step 2: Verify 0.9.0 is working
curl http://localhost:8000/api/health

# Step 3: Upgrade to 1.0.0
# Follow "Upgrade from 0.9.x to 1.0.0" steps above
```

## Migration Notes

### Database Schema Changes

#### Version 1.0.0

**New Tables:**
- `candidate_ranks` - ML-based ranking results
- `ranking_feedback` - Recruiter feedback for model improvement
- `ab_experiments` - A/B testing assignments

**Modified Tables:**
- `resumes`: Added `completeness_score`, `freshness_score` columns
- `matches`: Added `unified_score`, `vector_score` columns

**Migration Script:**
```bash
# Apply migrations
docker-compose run --rm backend alembic upgrade head

# Backfill completeness scores for existing resumes
docker-compose run --rm backend python scripts/backfill_resume_scores.py
```

#### Version 0.9.0

**New Tables:**
- `unified_matches` - Combined matching results

**Modified Tables:**
- `skills`: Added `rarity_score` column

### API Changes

#### Version 1.0.0

**New Endpoints:**
```
POST /api/ranking/rank                    # Rank candidate
GET  /api/ranking/vacancy/{id}/ranked     # Get ranked candidates
POST /api/ranking/feedback                # Submit feedback
GET  /api/ranking/models/importance       # Feature importance
```

**Deprecated Endpoints:**
```
POST /api/matching/compare-keywords       # Use /api/matching/compare-unified
POST /api/matching/compare-tfidf          # Use /api/matching/compare-unified
POST /api/matching/compare-vector         # Use /api/matching/compare-unified
```

**Breaking Changes:**
- Unified matching now returns additional fields: `unified_score`, `recommendation`
- Resume analysis includes new ML-extracted fields

### Configuration Changes

#### New Environment Variables (1.0.0)

```bash
# Ranking Service
RANKING_MODEL_PATH=models/ranking_model.pkl
RANKING_FEATURE_IMPORTANCE_PATH=models/feature_importance.json
ENABLE_AB_TESTING=true

# Model Configuration
RANKING_MODEL_VERSION=1.0.0
RANKING_MIN_CONFIDENCE=0.4

# Feature Flags
ENABLE_VECTOR_SIMILARITY=true
ENABLE_SKILL_RARITY_SCORING=true
```

## Rollback Procedures

### Quick Rollback

If the upgrade fails or issues are detected:

#### Step 1: Stop Services

```bash
docker-compose down
```

#### Step 2: Restore Previous Version

```bash
# Restore code
git checkout tags/v0.9.0  # Previous version

# Restore configuration
cp .env.backup-YYYYMMDD-HHMMSS .env
```

#### Step 3: Restore Database

```bash
# Start database only
docker-compose up -d db
sleep 10

# Drop current database
docker-compose exec db psql -U agenthr_user -c "DROP DATABASE agenthr_db;"
docker-compose exec db psql -U agenthr_user -c "CREATE DATABASE agenthr_db;"

# Restore backup
cat backup-YYYYMMDD-HHMMSS.sql | docker-compose exec -T db psql -U agenthr_user agenthr_db

# Verify restore
docker-compose exec db psql -U agenthr_user agenthr_db -c "SELECT COUNT(*) FROM resumes;"
```

#### Step 4: Restore Uploaded Files

```bash
# Remove current uploads
rm -rf backend/uploads/*

# Restore from backup
tar -xzf uploads-backup-YYYYMMDD-HHMMSS.tar.gz
```

#### Step 5: Start Services

```bash
# Pull previous images
docker-compose pull

# Start all services
docker-compose up -d

# Verify rollback
curl http://localhost:8000/api/health
docker-compose logs -f --tail=100
```

### Database Migration Rollback

If only database migration failed:

```bash
# Check current migration version
docker-compose run --rm backend alembic current

# Rollback to specific version
docker-compose run --rm backend alembic downgrade <revision>

# Rollback one version
docker-compose run --rm backend alembic downgrade -1

# View migration history
docker-compose run --rm backend alembic history
```

### Partial Rollback (Keep Data)

If you want to rollback code but keep new data:

```bash
# Stop services
docker-compose down

# Restore code only
git checkout tags/v0.9.0

# Do NOT restore database

# Update .env to be compatible with old version
nano .env

# Start services
docker-compose up -d
```

**⚠️ Warning:** This approach may cause issues if schema changes are incompatible.

## Troubleshooting

### Common Issues

#### Issue: Migration Fails with "relation already exists"

```bash
# Solution: Mark migration as complete
docker-compose run --rm backend alembic stamp head
```

#### Issue: Services won't start after upgrade

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Common fixes:
# 1. Clear old containers
docker-compose down -v
docker-compose up -d

# 2. Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

#### Issue: Database connection errors

```bash
# Verify database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec db psql -U agenthr_user agenthr_db -c "SELECT 1;"

# Reset database connection
docker-compose restart db
sleep 10
docker-compose restart backend
```

#### Issue: Missing environment variables

```bash
# Compare with example
diff .env .env.example

# Add missing variables
nano .env

# Restart services
docker-compose restart
```

#### Issue: Old data not appearing

```bash
# Check database has data
docker-compose exec db psql -U agenthr_user agenthr_db -c "SELECT COUNT(*) FROM resumes;"

# Verify uploaded files exist
ls -la backend/uploads/

# Check API can access data
curl http://localhost:8000/api/resumes/
```

#### Issue: Performance degradation after upgrade

```bash
# Run database optimization
docker-compose exec db psql -U agenthr_user agenthr_db << EOF
VACUUM ANALYZE;
REINDEX DATABASE agenthr_db;
EOF

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: `docker-compose logs -f --tail=500`
2. **Review migrations**: `docker-compose run --rm backend alembic history`
3. **Test database**: `docker-compose exec db psql -U agenthr_user agenthr_db`
4. **Check GitHub Issues**: [github.com/Soinex-Inc/agenthr/issues](https://github.com/Soinex-Inc/agenthr/issues)
5. **Contact Support**: Create an issue with:
   - Version upgrading from/to
   - Error messages from logs
   - Steps already attempted

## Best Practices

1. **Always backup** before upgrading
2. **Test upgrades** in a staging environment first
3. **Read release notes** for breaking changes
4. **Monitor logs** during and after upgrade
5. **Verify functionality** before declaring success
6. **Keep backups** for at least 30 days
7. **Document customizations** that may conflict with upgrades
8. **Plan downtim** during low-usage periods
9. **Have rollback plan** ready before starting
10. **Update documentation** if you modify the upgrade process

## Zero-Downtime Upgrades (Advanced)

For production systems requiring minimal downtime:

### Blue-Green Deployment

```bash
# 1. Setup second environment (green)
git clone agenthr agenthr-green
cd agenthr-green
git checkout tags/v1.0.0

# 2. Configure on different ports
sed -i 's/3000/3001/g' docker-compose.yml
sed -i 's/8000/8001/g' docker-compose.yml

# 3. Share database (read-only mode on blue)
# Configure .env to use same database

# 4. Start green environment
docker-compose up -d

# 5. Run migrations on green
docker-compose run --rm backend alembic upgrade head

# 6. Verify green is working
curl http://localhost:8001/api/health

# 7. Switch traffic (load balancer/nginx)
# Update nginx config to point to green

# 8. Monitor for issues

# 9. Shutdown blue environment
cd ../agenthr
docker-compose down
```

### Rolling Updates (Kubernetes)

For Kubernetes deployments, refer to the Kubernetes upgrade guide in the `k8s/` directory.

---

**Last Updated**: 2026-03-22
**Current Version**: 1.0.0
