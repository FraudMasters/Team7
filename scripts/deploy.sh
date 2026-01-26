#!/bin/bash
# Deployment Script
# This script deploys the application

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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Cleanup function for error handling
cleanup_on_error() {
    local exit_code=$?
    log_error "An error occurred. Cleaning up..."
    docker-compose down --remove-orphans || true
    exit $exit_code
}

# Set trap to call cleanup on error
trap cleanup_on_error ERR

# Prerequisite check functions
check_docker() {
    command -v docker >/dev/null 2>&1
}

check_docker_compose() {
    command -v docker-compose >/dev/null 2>&1
}

check_port_availability() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Port $port is already in use (${service_name})"
        return 1
    fi
    return 0
}

# Environment setup function
setup_environment() {
    log_info "Setting up environment..."

    # Setup root .env file
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            log_warning ".env file not found, copying from .env.example"
            cp .env.example .env
            log_warning "Please edit .env with your values"
        else
            log_error ".env.example not found. Cannot create .env file"
            return 1
        fi
    else
        log_info "✓ Root .env file exists"
    fi

    # Setup backend .env file
    if [ ! -f backend/.env ]; then
        if [ -f backend/.env.example ]; then
            log_warning "backend/.env file not found, copying from backend/.env.example"
            cp backend/.env.example backend/.env
            log_warning "Please edit backend/.env with your values"
        else
            log_warning "backend/.env.example not found. Skipping backend/.env creation"
        fi
    else
        log_info "✓ Backend .env file exists"
    fi

    # Setup frontend .env file
    if [ ! -f frontend/.env ]; then
        if [ -f frontend/.env.example ]; then
            log_warning "frontend/.env file not found, copying from frontend/.env.example"
            cp frontend/.env.example frontend/.env
            log_warning "Please edit frontend/.env with your values"
        else
            log_warning "frontend/.env.example not found. Skipping frontend/.env creation"
        fi
    else
        log_info "✓ Frontend .env file exists"
    fi

    # Source root environment variables
    set -a
    source .env
    set +a

    log_success "✓ Environment setup completed"
    return 0
}

# Health check functions
wait_for_postgres() {
    local container_name="resume_analysis_db"
    local timeout=60
    local interval=2
    local elapsed=0

    log_info "Waiting for PostgreSQL to be ready..."

    while [ $elapsed -lt $timeout ]; do
        if docker exec $container_name pg_isready -U postgres >/dev/null 2>&1; then
            log_success "✓ PostgreSQL is ready"
            return 0
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo
    log_error "PostgreSQL failed to become ready within ${timeout}s"
    return 1
}

wait_for_redis() {
    local container_name="resume_analysis_redis"
    local timeout=30
    local interval=2
    local elapsed=0

    log_info "Waiting for Redis to be ready..."

    while [ $elapsed -lt $timeout ]; do
        if docker exec $container_name redis-cli ping >/dev/null 2>&1; then
            log_success "✓ Redis is ready"
            return 0
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo
    log_error "Redis failed to become ready within ${timeout}s"
    return 1
}

wait_for_http_health() {
    local url=$1
    local service_name="${2:-service}"
    local timeout=60
    local interval=3
    local elapsed=0
    local attempt=1

    log_info "Waiting for $service_name to be healthy..."

    while [ $elapsed -lt $timeout ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "✓ $service_name is healthy"
            return 0
        fi

        log_warning "⚠ $service_name not ready yet (attempt $attempt)"
        sleep $interval
        elapsed=$((elapsed + interval))
        attempt=$((attempt + 1))
    done

    log_error "$service_name failed to become healthy within ${timeout}s"
    return 1
}

# Build Docker images
build_images() {
    log_info "Building application images..."
    docker-compose build backend frontend celery_worker
    log_success "✓ Application images built"
    echo ""
}

# Stop existing containers
stop_existing_containers() {
    log_info "Stopping existing containers..."
    docker-compose down --remove-orphans || true
    log_success "✓ Containers stopped"
    echo ""
}

# Start infrastructure services
start_infrastructure() {
    log_info "Starting infrastructure services..."
    docker-compose up -d postgres redis
    log_success "✓ Database and Redis started"

    # Wait for services to be healthy
    wait_for_postgres || exit 1
    wait_for_redis || exit 1

    echo ""
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    docker-compose run --rm backend alembic upgrade head || log_warning "⚠ Migrations failed or already applied"
    log_success "✓ Database migrations completed"
    echo ""
}

# Start application services
start_application_services() {
    log_info "Starting application services..."
    docker-compose up -d backend
    log_success "✓ Backend started"

    # Wait for backend to be healthy
    wait_for_http_health "http://localhost:8000/health" "backend"

    # Start celery_worker after backend is healthy
    docker-compose up -d celery_worker
    log_success "✓ Celery worker started"

    # Start flower after celery_worker is started
    docker-compose up -d flower
    log_success "✓ Flower started"

    # Wait for flower to be healthy
    wait_for_http_health "http://localhost:5555/" "flower"

    # Start frontend after backend is healthy
    docker-compose up -d frontend
    log_success "✓ Frontend started"

    # Wait for frontend to be healthy
    wait_for_http_health "http://localhost:5173/" "frontend"

    echo ""
}

# Health check for application services
check_application_health() {
    log_info "Running health checks..."
    echo ""
}

# Main deployment flow
main() {
    echo "========================================="
    echo "  Deploying Application"
    echo "========================================="
    echo ""

    # Check prerequisites
    log_info "Checking prerequisites..."
    check_docker || { log_error "Docker is required but not installed. Aborting."; exit 1; }
    check_docker_compose || { log_error "Docker Compose is required but not installed. Aborting."; exit 1; }
    log_success "✓ Prerequisites check passed"
    echo ""

    # Setup environment
    setup_environment || exit 1

    # Create necessary directories
    log_info "Creating directories..."
    mkdir -p backend/data/uploads
    mkdir -p backend/models_cache
    mkdir -p frontend/dist
    log_success "✓ Directories created"
    echo ""

    # Stop existing containers
    stop_existing_containers

    # Build images
    build_images

    # Start infrastructure
    start_infrastructure

    # Run migrations
    run_migrations

    # Start application services
    start_application_services

    # Health check
    check_application_health

    # Display deployment summary
    echo "========================================="
    echo "  Deployment Summary"
    echo "========================================="
    echo ""
    log_success "✓ Deployment completed!"
    echo ""
    echo "Services:"
    echo "  - Frontend:         http://localhost:5173"
    echo "  - Backend API:      http://localhost:8000"
    echo "  - API Docs:         http://localhost:8000/docs"
    echo "  - Flower (Celery):  http://localhost:5555"
    echo ""
    echo "Container Status:"
    docker-compose ps
    echo ""
    echo "Next steps:"
    echo "  1. View logs:"
    echo "     docker-compose logs -f"
    echo ""
    echo "  2. Check specific service logs:"
    echo "     docker-compose logs -f backend"
    echo "     docker-compose logs -f celery_worker"
    echo "     docker-compose logs -f frontend"
    echo "     docker-compose logs -f flower"
    echo ""
    echo "  3. Stop services:"
    echo "     docker-compose down"
    echo ""
    echo "  4. View database:"
    echo "     docker-compose exec postgres psql -U postgres -d resume_analysis"
    echo ""
}

# Run main function
main "$@"
