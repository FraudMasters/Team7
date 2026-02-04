# Subtask 1-3: Start Keycloak Service and Verify Health

## Objective
Start the Keycloak service and verify it's healthy and accessible.

## Prerequisites
- Docker and docker-compose installed
- Subtask 1-1 completed (Keycloak service defined in docker-compose.yml)
- Subtask 1-2 completed (PostgreSQL database for Keycloak created)

## Steps to Complete

### 1. Start Keycloak Service
```bash
# Start Keycloak and its dependencies (PostgreSQL)
docker-compose up -d postgres keycloak
```

### 2. Monitor Keycloak Startup
Keycloak may take 30-60 seconds to start on first run. Monitor the logs:
```bash
docker logs -f resume_analysis_keycloak
```

Look for these success indicators:
- "Keycloak 25.0.0 started"
- "Listening on: http://0.0.0.0:8080"
- "Health topics enabled"
- No ERROR messages in the final logs

### 3. Verify Health
```bash
# Run the verification script
./scripts/verify-subtask-1-3.sh

# Or test manually
curl -f http://localhost:8080/health/ready
```

Expected response: HTTP 200 with health status JSON

### 4. Verify Services
```bash
# Check container status
docker ps | grep keycloak

# Check container health
docker inspect resume_analysis_keycloak | jq '.[0].State.Health'
```

## Troubleshooting

### Port 8080 Already in Use
```bash
# Check what's using port 8080
lsof -i :8080

# Stop conflicting service or change Keycloak port in docker-compose.yml
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs resume_analysis_db

# Verify database exists
docker exec -it postgres psql -U postgres -l | grep keycloak_db
```

### Keycloak Won't Start
```bash
# Check detailed logs
docker logs resume_analysis_keycloak --tail 100

# Common issues:
# 1. Database not ready - wait longer or restart PostgreSQL
# 2. Port conflicts - check port 8080
# 3. Resource limits - check memory/CPU availability

# Restart Keycloak
docker-compose restart keycloak
```

### Health Check Fails
```bash
# Keycloak may still be starting - wait up to 60 seconds
docker logs -f resume_analysis_keycloak

# If still failing after 60s:
docker-compose restart keycloak
./scripts/verify-subtask-1-3.sh
```

## Verification Checklist

- [ ] Keycloak container is running (`docker ps`)
- [ ] Health endpoint returns 200 (`curl http://localhost:8080/health/ready`)
- [ ] Admin console accessible at http://localhost:8080/admin
- [ ] No ERROR messages in Keycloak logs
- [ ] Container health check passing (`docker inspect`)

## Next Steps

After Keycloak is running and healthy:
1. Access admin console: http://localhost:8080/admin
2. Login with admin/admin (change password immediately)
3. Proceed to subtask-1-4: Create realm, clients, and roles

## Service URLs

- **Keycloak Admin Console**: http://localhost:8080/admin
- **Keycloak Health**: http://localhost:8080/health/ready
- **Keycloak Metrics**: http://localhost:8080/metrics

## Default Credentials

```
Username: admin
Password: admin
```

**IMPORTANT**: Change these credentials immediately after first login in production!
