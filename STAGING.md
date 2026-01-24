# Staging Deployment Guide

This guide covers deploying and verifying the AI-Powered Resume Analysis Platform to a staging environment.

## Quick Start

### 1. Deploy to Staging

```bash
# Deploy all services to staging
bash scripts/deploy_staging.sh
```

This will:
- Stop any existing containers
- Pull latest Docker images
- Build application images
- Start PostgreSQL, Redis, Backend, Celery Worker, Frontend, and Flower
- Run database migrations
- Perform health checks

### 2. Verify Deployment

```bash
# Run end-to-end verification
bash scripts/verify_staging_deployment.sh
```

This will:
- Check all service health endpoints
- Test resume upload functionality
- Test resume analysis
- Test job matching endpoint
- Verify Celery worker status
- Check database connectivity
- Report any issues

## Manual Testing Steps

After deployment, perform these manual verification steps:

### 1. Access Frontend

Open browser: `http://localhost:5173`

**Checks:**
- [ ] Homepage loads without errors
- [ ] No console errors (open DevTools → Console)
- [ ] Navigation menu visible
- [ ] Upload page accessible

### 2. Upload Test Resume

Navigate to: `http://localhost:5173/upload`

**Steps:**
1. Drag and drop a PDF resume file
2. Or click to select a file
3. Wait for upload completion
4. Note the resume ID

**Expected:**
- Progress bar shows upload progress
- Success message with resume ID
- Redirect to results page

### 3. View Analysis Results

Navigate to: `http://localhost:5173/results/{resume_id}`

**Checks:**
- [ ] Error detection results displayed
- [ ] Green/red skill highlighting works
- [ ] Grammar errors with suggestions shown
- [ ] Experience summary displayed
- [ ] No console errors

### 4. Test Job Comparison

Navigate to: `http://localhost:5173/compare/{resume_id}/test-vacancy`

**Checks:**
- [ ] Match percentage displayed
- [ ] Matched skills shown in green
- [ ] Missing skills shown in red
- [ ] Experience verification shown
- [ ] Comparison view rendered correctly

### 5. Test Async Processing

**Steps:**
1. Upload a large resume (>2 pages)
2. Check Celery tasks at: `http://localhost:5555`
3. Verify task appears in Flower UI
4. Verify task completes successfully

**Expected:**
- Task queued in Celery
- Progress updates visible in Flower
- Task completes without errors

## Service URLs

After deployment, access services at:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Flower (Celery Monitoring)**: http://localhost:5555
  - Default credentials: admin / staging_admin

## Environment Configuration

Staging uses `.env` file with these important variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:staging_pass@postgres:5432/resume_analysis_staging

# Backend
BACKEND_PORT=8000
LOG_LEVEL=INFO
DEBUG=false

# Frontend
VITE_API_URL=http://localhost:8000

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Flower
FLOWER_USER=admin
FLOWER_PASSWORD=staging_admin
```

## Troubleshooting

### Backend Not Starting

**Check logs:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs backend
```

**Common issues:**
- Database not ready: Wait 10-15 seconds for PostgreSQL to initialize
- Port already in use: Change `BACKEND_PORT` in `.env`
- Missing models: Run `docker-compose exec backend python -m spacy download en_core_web_sm`

### Frontend Not Starting

**Check logs:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs frontend
```

**Common issues:**
- Build failed: Check `package.json` dependencies
- API unreachable: Verify `VITE_API_URL` in `.env`
- Port conflict: Change `FRONTEND_PORT` in `.env`

### Celery Worker Not Processing Tasks

**Check status:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec celery_worker celery -A tasks inspect active
```

**Check Flower:**
- Open http://localhost:5555
- Verify workers are listed
- Check for errors in task tracebacks

### Database Migration Errors

**Run migrations manually:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec backend alembic upgrade head
```

**Reset database (WARNING: destroys data):**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec backend alembic downgrade base
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec backend alembic upgrade head
```

## Monitoring

### View Logs

**All services:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f
```

**Specific service:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f backend
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f celery_worker
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f frontend
```

**Last 100 lines:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs --tail=100 backend
```

### Check Container Status

```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml ps
```

Expected output:
```
NAME                                STATUS
resume_analysis_backend             Up (healthy)
resume_analysis_celery_worker       Up
resume_analysis_flower              Up
resume_analysis_frontend            Up
resume_analysis_nginx               Up
resume_analysis_postgres            Up (healthy)
resume_analysis_redis               Up (healthy)
```

### Monitor Celery Tasks

Open Flower UI: http://localhost:5555

- **Workers**: View active workers and their stats
- **Tasks**: View task history, execution time, success/failure
- **Monitor**: Real-time task execution monitoring

## Performance Verification

### Analysis Speed Test

```bash
# Time a resume analysis
time curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "test-id"}' \
  http://localhost:8000/api/resumes/analyze
```

**Expected:** <10 seconds for typical 2-page resume

### Memory Usage

```bash
docker stats
```

**Expected:**
- Backend: <2GB RAM
- Celery Worker: <2GB RAM
- Frontend: <512MB RAM

### Database Performance

```bash
# Connect to database
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec postgres psql -U postgres -d resume_analysis_staging

# Check table sizes
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Cleanup

### Stop All Services

```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml down
```

### Remove Volumes (WARNING: destroys data)

```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml down -v
```

### Remove Everything (including images)

```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml down -v --rmi all
```

## Next Steps

After successful staging deployment:

1. **Security Review**
   - Change default passwords
   - Enable HTTPS/SSL
   - Configure firewall rules
   - Set up authentication

2. **Load Testing**
   - Test with concurrent users
   - Verify Celery worker scaling
   - Check database performance under load

3. **Production Preparation**
   - Set up monitoring and alerting
   - Configure backup strategy
   - Prepare production environment variables
   - Test disaster recovery procedures

4. **Documentation**
   - Document any staging-specific issues
   - Update runbooks with learned lessons
   - Record performance baselines

## Support

For issues or questions:
- Check logs: `docker-compose logs -f [service]`
- Review deployment guide: `DEPLOYMENT.md`
- Check API documentation: http://localhost:8000/docs
