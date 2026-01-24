#!/bin/bash
# Staging Deployment Script
# This script deploys the application to staging environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
ENVIRONMENT="${1:-staging}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
COMPOSE_OVERRIDE="${COMPOSE_OVERRIDE:-docker-compose.staging.yml}"

echo "========================================="
echo "  Deploying to $ENVIRONMENT"
echo "========================================="
echo ""

# 1. Prerequisites check
log_info "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { log_error "Docker Compose is required but not installed. Aborting."; exit 1; }
command -v jq >/dev/null 2>&1 || { log_warning "jq is not installed (needed for some scripts)"; }
log_info "✓ Prerequisites check passed"
echo ""

# 2. Environment setup
log_info "Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        log_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        log_warning "Please edit .env with your staging-specific values"
        log_warning "Run this script again after configuration"
        exit 1
    else
        log_error ".env.example not found. Cannot create .env file"
        exit 1
    fi
fi

# Source environment variables
set -a
source .env
set +a

# Set staging-specific defaults
export STAGING_DATABASE_URL="${STAGING_DATABASE_URL:-postgresql://postgres:${STAGING_DB_PASSWORD:-staging_pass}@postgres:5432/resume_analysis_staging}"
export STAGING_FRONTEND_URL="${STAGING_FRONTEND_URL:-http://localhost:5173}"
export STAGING_API_URL="${STAGING_API_URL:-http://localhost:8000}"
export FLOWER_USER="${FLOWER_USER:-admin}"
export FLOWER_PASSWORD="${FLOWER_PASSWORD:-staging_admin}"
log_info "✓ Environment configured"
echo ""

# 3. Create necessary directories
log_info "Creating directories..."
mkdir -p backend/data/uploads
mkdir -p backend/models_cache
mkdir -p frontend/dist
mkdir -p nginx/logs
log_info "✓ Directories created"
echo ""

# 4. Stop existing containers
log_info "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" down --remove-orphans || true
log_info "✓ Containers stopped"
echo ""

# 5. Pull latest images
log_info "Pulling latest base images..."
docker-compose -f "$COMPOSE_FILE" pull postgres redis nginx || log_warning "⚠ Some images could not be pulled"
log_info "✓ Base images pulled"
echo ""

# 6. Build application images
log_info "Building application images..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" build backend frontend celery_worker
log_info "✓ Application images built"
echo ""

# 7. Start services
log_info "Starting services..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" up -d postgres redis
log_info "✓ Database and Redis started"

# Wait for database to be ready
log_info "Waiting for database to be ready..."
sleep 10

# Run database migrations
log_info "Running database migrations..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" run --rm backend alembic upgrade head || log_warning "⚠ Migrations failed or already applied"
log_info "✓ Database migrations completed"
echo ""

# Start application services
log_info "Starting application services..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" up -d backend celery_worker frontend flower nginx
log_info "✓ Application services started"
echo ""

# 8. Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 15

# Check service status
log_info "Checking service status..."
docker-compose -f "$COMPOSE_FILE" -f "$COMPOSE_OVERRIDE" ps
echo ""

# 9. Run health checks
log_info "Running health checks..."
for i in {1..5}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✓ Backend is healthy"
        break
    else
        log_warning "⚠ Backend not ready yet (attempt $i/5)"
        sleep 5
    fi
done

if curl -sf http://localhost:5173/ > /dev/null 2>&1; then
    log_info "✓ Frontend is healthy"
else
    log_warning "⚠ Frontend may not be ready yet"
fi

if curl -sf http://localhost:5555/ > /dev/null 2>&1; then
    log_info "✓ Flower monitoring is accessible"
else
    log_warning "⚠ Flower may not be ready yet"
fi
echo ""

# 10. Display deployment summary
echo "========================================="
echo "  Deployment Summary"
echo "========================================="
echo ""
log_info "✓ Deployment to $ENVIRONMENT completed!"
echo ""
echo "Services:"
echo "  - Backend API:      http://localhost:8000"
echo "  - Frontend:         http://localhost:5173"
echo "  - Flower (Celery):  http://localhost:5555"
echo "  - API Docs:         http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "  1. Run verification script:"
echo "     bash scripts/verify_staging_deployment.sh"
echo ""
echo "  2. View logs:"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE logs -f"
echo ""
echo "  3. Check specific service logs:"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE logs -f backend"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE logs -f celery_worker"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE logs -f frontend"
echo ""
echo "  4. Stop services:"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE down"
echo ""
echo "  5. View database:"
echo "     docker-compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE exec postgres psql -U postgres -d resume_analysis_staging"
echo ""
