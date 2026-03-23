# DigitalOcean App Platform Deployment

This directory contains the configuration for deploying AgentHR to DigitalOcean's App Platform.

## Overview

DigitalOcean App Platform is a Platform-as-a-Service (PaaS) offering that simplifies application deployment and management. This configuration deploys the complete AgentHR stack including:

- **Backend API** (FastAPI + Uvicorn)
- **Frontend** (React/Vite)
- **Celery Workers** (Background task processing)
- **Celery Beat** (Scheduled tasks)
- **PostgreSQL Database** (Managed database)
- **Redis** (Managed cache and message broker)

## Prerequisites

1. **DigitalOcean Account**
   - Sign up at https://www.digitalocean.com/
   - Enable billing

2. **DigitalOcean CLI (doctl)**
   ```bash
   # Install doctl
   # macOS
   brew install doctl

   # Linux
   cd ~
   wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
   tar xf ~/doctl-1.94.0-linux-amd64.tar.gz
   sudo mv ~/doctl /usr/local/bin

   # Authenticate
   doctl auth init
   ```

3. **GitHub Repository**
   - Fork or clone the AgentHR repository
   - Ensure code is pushed to GitHub
   - DigitalOcean will deploy from GitHub

4. **External Services**
   - **Neo4j Database**: Set up a managed Neo4j instance (Neo4j Aura recommended)
   - **DigitalOcean Spaces**: Create a Space for backups (optional but recommended)

## Configuration Steps

### 1. Update app.yaml

Edit `app.yaml` and replace the following placeholders:

```yaml
# GitHub Configuration
github:
  repo: YOUR_GITHUB_USERNAME/agenthr  # Replace with your repo

# Frontend Environment
- key: VITE_API_URL
  value: "REPLACE_WITH_BACKEND_URL"  # Will be backend service URL

# Neo4j Configuration
- key: NEO4J_URI
  value: "REPLACE_WITH_NEO4J_URI"  # e.g., bolt://neo4j.example.com:7687
- key: NEO4J_USER
  value: "REPLACE_WITH_NEO4J_USER"
- key: NEO4J_PASSWORD
  value: "REPLACE_WITH_NEO4J_PASSWORD"

# DigitalOcean Spaces (for backups)
- key: BACKUP_S3_BUCKET
  value: "REPLACE_WITH_SPACES_BUCKET"
- key: BACKUP_S3_ACCESS_KEY
  value: "REPLACE_WITH_SPACES_KEY"
- key: BACKUP_S3_SECRET_KEY
  value: "REPLACE_WITH_SPACES_SECRET"

# Alert Configuration
- key: ALERT_EMAIL_ADDRESS
  value: "REPLACE_WITH_ALERT_EMAIL"
```

### 2. Set Up Neo4j Database

AgentHR requires Neo4j for the Graphiti knowledge graph. Options:

**Option A: Neo4j Aura (Recommended)**
```bash
# 1. Sign up at https://neo4j.com/cloud/aura/
# 2. Create a free tier instance
# 3. Note the connection URI, username, and password
# 4. Update app.yaml with these credentials
```

**Option B: Self-Hosted on DigitalOcean Droplet**
```bash
# 1. Create a Droplet with Docker
# 2. Deploy Neo4j container
# 3. Configure firewall to allow bolt protocol (port 7687)
# 4. Update app.yaml with connection details
```

### 3. Create DigitalOcean Spaces (Optional)

For automated database backups:

```bash
# Create a Space for backups
doctl spaces create agenthr-backups --region nyc3

# Create access keys
doctl spaces keys create agenthr-backup-key
# Note the access key ID and secret key

# Update app.yaml with Spaces credentials
```

## Deployment

### Method 1: Web Console (Recommended for First Deployment)

1. **Navigate to App Platform**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"

2. **Connect GitHub Repository**
   - Select your GitHub repository
   - Choose the branch (typically `main`)
   - DigitalOcean will auto-detect or you can upload `app.yaml`

3. **Review Resources**
   - Review detected services, databases, and workers
   - Verify resource allocations match your needs

4. **Configure Environment Variables**
   - Add or update environment variables
   - Set SECRET variables (API keys, passwords)

5. **Review and Deploy**
   - Review pricing estimate
   - Click "Create Resources"

### Method 2: CLI Deployment

```bash
# Navigate to project root
cd /path/to/agenthr

# Validate app.yaml
doctl apps spec validate cloud/digitalocean/app.yaml

# Create the app
doctl apps create --spec cloud/digitalocean/app.yaml

# Note the App ID from output
# Example: b6bdf840-2340-4d21-98f1-2c9239e68e3e
```

### Update Existing App

```bash
# Get your App ID
doctl apps list

# Update the app
doctl apps update <APP_ID> --spec cloud/digitalocean/app.yaml
```

## Post-Deployment Configuration

### 1. Update Frontend URL

After backend deployment, update the frontend environment:

```bash
# Get backend URL
doctl apps list

# Update app.yaml with backend URL in FRONTEND_URL
# Then update the app
doctl apps update <APP_ID> --spec cloud/digitalocean/app.yaml
```

### 2. Update Backend with Frontend URL

```bash
# Get frontend URL from App Platform console
# Update VITE_API_URL in app.yaml
# Trigger a rebuild
doctl apps create-deployment <APP_ID>
```

### 3. Run Database Migrations

Migrations should run automatically via the `db-migrate` job. Verify:

```bash
# Check job status
doctl apps list-deployments <APP_ID>

# View logs
doctl apps logs <APP_ID> --type build
```

### 4. Configure Custom Domain (Optional)

```bash
# Add custom domain
doctl apps update <APP_ID> --spec app.yaml

# Update DNS records as instructed by DigitalOcean
# A record: @ -> DigitalOcean IP
# CNAME: www -> your-app.ondigitalocean.app
```

## Monitoring and Maintenance

### View Logs

```bash
# View application logs
doctl apps logs <APP_ID> --type run

# View build logs
doctl apps logs <APP_ID> --type build

# Follow logs in real-time
doctl apps logs <APP_ID> --type run --follow
```

### Access Metrics

1. Navigate to App Platform in the DigitalOcean console
2. Select your app
3. View the "Insights" tab for:
   - CPU usage
   - Memory usage
   - Request metrics
   - Error rates

### Database Backups

**Automated Backups:**
- PostgreSQL: Daily automated backups (retained for 7 days)
- Redis: Point-in-time recovery available

**Manual Backups:**
```bash
# Database connection info
doctl databases list
doctl databases connection <DATABASE_ID>

# Create manual backup
doctl databases backups create <DATABASE_ID>
```

### Scaling

**Vertical Scaling (Resize Instances):**
```yaml
# Edit app.yaml
services:
  - name: backend
    instance_size_slug: professional-xl  # Upgrade from professional-l
```

**Horizontal Scaling (Add Instances):**
```yaml
# Edit app.yaml
services:
  - name: backend
    instance_count: 3  # Increase from 2
```

Apply changes:
```bash
doctl apps update <APP_ID> --spec cloud/digitalocean/app.yaml
```

## Cost Estimation

Based on the default configuration:

| Resource | Size | Instances | Monthly Cost (est.) |
|----------|------|-----------|---------------------|
| Backend | Professional-L (8GB RAM, 4 vCPU) | 2 | $96 |
| Celery Worker | Professional-XL (16GB RAM, 8 vCPU) | 1 | $96 |
| Celery Beat | Basic-XS (512MB RAM) | 1 | $5 |
| Frontend | Basic-S (1GB RAM) | 1 | $12 |
| PostgreSQL | DB-S-2VCPU-4GB | 1 | $60 |
| Redis | DB-S-1VCPU-2GB | 1 | $30 |
| **Total** | | | **~$299/month** |

> **Note:** Prices are estimates and may vary. Check current pricing at https://www.digitalocean.com/pricing/app-platform

## Resource Specifications

### Instance Sizes

- **Basic-XS**: 512MB RAM, shared CPU - for lightweight tasks
- **Basic-S**: 1GB RAM, shared CPU - for frontend apps
- **Professional-L**: 8GB RAM, 4 dedicated vCPU - for backend API
- **Professional-XL**: 16GB RAM, 8 dedicated vCPU - for heavy workers

### Database Sizes

- **DB-S-1VCPU-2GB**: Small Redis instance
- **DB-S-2VCPU-4GB**: Small PostgreSQL instance
- Can be scaled up as needed

## Troubleshooting

### Deployment Fails

```bash
# Check deployment logs
doctl apps logs <APP_ID> --type build

# Common issues:
# 1. Missing environment variables
# 2. Dockerfile build errors
# 3. Invalid app.yaml syntax

# Validate app.yaml
doctl apps spec validate cloud/digitalocean/app.yaml
```

### Health Check Failures

```bash
# View runtime logs
doctl apps logs <APP_ID> --type run --component backend

# Common causes:
# 1. Application not listening on correct port
# 2. Database connection issues
# 3. Missing environment variables
```

### Database Connection Issues

```bash
# Get database connection details
doctl databases list
doctl databases connection <DATABASE_ID> --format Host,Port,User,Database

# Test connection from local machine
psql "postgresql://user:pass@host:port/database?sslmode=require"
```

### Out of Memory Errors

```bash
# Check metrics in console or scale up
# Edit app.yaml to increase instance_size_slug
doctl apps update <APP_ID> --spec cloud/digitalocean/app.yaml
```

## CI/CD Integration

DigitalOcean App Platform supports automatic deployments from GitHub:

```yaml
# In app.yaml
services:
  - name: backend
    github:
      deploy_on_push: true  # Auto-deploy on push to branch
```

**Recommended Workflow:**
1. Development happens in feature branches
2. Merge to `main` triggers staging deployment
3. Manual promotion to production or separate `production` branch

## Security Best Practices

1. **Use Secrets for Sensitive Data**
   - Mark environment variables as `type: SECRET` in app.yaml
   - Never commit secrets to Git

2. **Enable Trusted Sources**
   - Restrict database access to App Platform components only
   - Use DigitalOcean VPC for internal communication

3. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories

4. **Backup Strategy**
   - Enable automated database backups
   - Test restore procedures
   - Store critical backups in DigitalOcean Spaces

## Support and Resources

- **DigitalOcean Documentation**: https://docs.digitalocean.com/products/app-platform/
- **App Platform Tutorials**: https://www.digitalocean.com/community/tags/app-platform
- **DigitalOcean Community**: https://www.digitalocean.com/community/
- **Support Tickets**: https://cloud.digitalocean.com/support/tickets

## Comparison with Other Platforms

| Feature | DigitalOcean App Platform | AWS (reference) |
|---------|---------------------------|-----------------|
| Ease of Setup | Simple, PaaS-focused | Complex, requires more configuration |
| Pricing | Predictable, all-inclusive | Variable, à la carte |
| Managed Databases | Included, simple setup | Separate service (RDS) |
| Auto-scaling | Manual or scheduled | Advanced auto-scaling |
| Best For | Small to medium apps | Large, complex applications |

## Migration from Docker Compose

This configuration mirrors the production Docker Compose setup:

- **Backend service** = `backend` container
- **Celery Worker** = `celery_worker` container
- **Celery Beat** = `celery_beat` container
- **Frontend** = `frontend` container
- **PostgreSQL database** = `postgres` container (now managed)
- **Redis database** = `redis` container (now managed)

Key differences:
- Managed databases replace self-hosted containers
- No need for reverse proxy (handled by App Platform)
- Monitoring requires external setup (Prometheus/Grafana not included)

## Next Steps

1. ✅ Configure app.yaml with your settings
2. ✅ Set up external Neo4j database
3. ✅ Create DigitalOcean Spaces for backups
4. ✅ Deploy app via console or CLI
5. ✅ Configure custom domain
6. ✅ Set up monitoring and alerts
7. ✅ Test application thoroughly
8. ✅ Document any customizations

For the complete deployment guide covering all cloud platforms, see `/cloud/README.md`.
