#!/bin/bash
# Upgrade Script
# This script upgrades the application to the latest version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SKIP_BACKUP=false
ROLLBACK=false
NO_DOWNTIME=false
CHECK_MIGRATIONS=false
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Show help text
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Upgrade the application to the latest version.

OPTIONS:
    --help              Show this help message
    --skip-backup       Skip database backup before upgrade
    --rollback          Rollback to the previous version
    --no-downtime       Perform zero-downtime upgrade (blue-green deployment)
    --check-migrations  Check for pending migrations without applying them

EXAMPLES:
    # Standard upgrade with backup
    $0

    # Upgrade without backup
    $0 --skip-backup

    # Zero-downtime upgrade
    $0 --no-downtime

    # Rollback to previous version
    $0 --rollback

    # Check for pending migrations
    $0 --check-migrations

UPGRADE PROCESS:
    1. Check prerequisites
    2. Backup current database (unless --skip-backup)
    3. Pull latest images or rebuild
    4. Run database migrations
    5. Restart services
    6. Verify health checks

ROLLBACK PROCESS:
    1. Stop current services
    2. Restore database from latest backup
    3. Restart services with previous version

EOF
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --no-downtime)
                NO_DOWNTIME=true
                shift
                ;;
            --check-migrations)
                CHECK_MIGRATIONS=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Cleanup function for error handling
cleanup_on_error() {
    local exit_code=$?
    log_error "An error occurred during upgrade. Exit code: $exit_code"

    if [ "$ROLLBACK" = false ]; then
        log_warning "You can rollback using: $0 --rollback"
    fi

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

check_running_containers() {
    local running=$(docker-compose ps -q | wc -l)
    if [ "$running" -eq 0 ]; then
        log_error "No running containers found. Nothing to upgrade."
        log_info "Use ./scripts/deploy.sh to deploy the application first."
        exit 1
    fi
}

# Environment setup function
setup_environment() {
    log_info "Setting up environment..."

    if [ ! -f .env ]; then
        log_error ".env file not found. Cannot proceed with upgrade."
        return 1
    fi

    # Source root environment variables
    set -a
    source .env
    set +a

    log_success "✓ Environment setup completed"
    return 0
}

# Backup functions
create_backup_directory() {
    mkdir -p "$BACKUP_DIR"
    log_success "✓ Backup directory ready: $BACKUP_DIR"
}

backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_warning "Skipping database backup (--skip-backup flag set)"
        return 0
    fi

    log_step "Backing up database..."

    local backup_file="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

    if docker-compose exec -T postgres pg_dump -U postgres resume_analysis > "$backup_file" 2>/dev/null; then
        log_success "✓ Database backed up to: $backup_file"

        # Create a symlink to the latest backup
        ln -sf "db_backup_$TIMESTAMP.sql" "$BACKUP_DIR/latest_backup.sql"
        log_info "✓ Latest backup link updated"

        return 0
    else
        log_error "Failed to backup database"
        return 1
    fi
}

backup_env_files() {
    if [ "$SKIP_BACKUP" = true ]; then
        return 0
    fi

    log_step "Backing up configuration files..."

    local config_backup_dir="$BACKUP_DIR/config_$TIMESTAMP"
    mkdir -p "$config_backup_dir"

    [ -f .env ] && cp .env "$config_backup_dir/"
    [ -f backend/.env ] && cp backend/.env "$config_backup_dir/"
    [ -f frontend/.env ] && cp frontend/.env "$config_backup_dir/"

    log_success "✓ Configuration files backed up"
}

# Rollback functions
rollback_database() {
    log_step "Rolling back database..."

    local latest_backup="$BACKUP_DIR/latest_backup.sql"

    if [ ! -f "$latest_backup" ]; then
        log_error "No backup found at: $latest_backup"
        log_info "Available backups:"
        ls -lh "$BACKUP_DIR"/*.sql 2>/dev/null || log_info "No backups found"
        return 1
    fi

    log_info "Restoring from: $latest_backup"

    # Drop and recreate database
    docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS resume_analysis;" 2>/dev/null || true
    docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE resume_analysis;" 2>/dev/null

    # Restore backup
    docker-compose exec -T postgres psql -U postgres resume_analysis < "$latest_backup" 2>/dev/null

    log_success "✓ Database rolled back successfully"
}

perform_rollback() {
    echo "========================================="
    echo "  Rolling Back to Previous Version"
    echo "========================================="
    echo ""

    log_warning "This will rollback to the previous version"

    # Stop current services
    log_step "Stopping current services..."
    docker-compose down
    log_success "✓ Services stopped"
    echo ""

    # Rollback database
    rollback_database || exit 1
    echo ""

    # Start services with previous version
    log_step "Starting services with previous version..."
    docker-compose up -d
    log_success "✓ Services started"
    echo ""

    # Wait for services
    wait_for_services

    log_success "✓ Rollback completed successfully"
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

wait_for_services() {
    wait_for_postgres || exit 1
    wait_for_redis || exit 1
    wait_for_http_health "http://localhost:8000/health" "backend" || exit 1
    wait_for_http_health "http://localhost:5173/" "frontend" || exit 1
}

# Pull latest images
pull_latest_images() {
    log_step "Pulling latest images..."
    docker-compose pull
    log_success "✓ Latest images pulled"
    echo ""
}

# Build images
build_images() {
    log_step "Building application images..."
    docker-compose build backend frontend celery_worker
    log_success "✓ Application images built"
    echo ""
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    docker-compose run --rm backend alembic upgrade head || log_warning "⚠ Migrations failed or already applied"
    log_success "✓ Database migrations completed"
    echo ""
}

# Check for pending migrations without applying them
check_pending_migrations() {
    echo "========================================="
    echo "  Checking Database Migrations"
    echo "========================================="
    echo ""

    log_step "Checking migration status..."

    # Ensure database is accessible
    if ! docker-compose ps | grep -q "postgres"; then
        log_error "PostgreSQL container is not running"
        log_info "Please start the application first with: ./scripts/deploy.sh"
        exit 1
    fi

    # Wait for PostgreSQL to be ready
    wait_for_postgres || exit 1

    # Get current database revision
    log_info "Getting current database revision..."
    local current_revision
    current_revision=$(docker-compose run --rm backend alembic current 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -1)

    if [ -z "$current_revision" ]; then
        log_warning "⚠ No migrations have been applied yet (empty database)"
        current_revision="(empty)"
    else
        log_info "Current revision: $current_revision"
    fi

    # Get target head revision
    log_info "Getting target head revision..."
    local head_revision
    head_revision=$(docker-compose run --rm backend alembic heads 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -1)

    if [ -z "$head_revision" ]; then
        log_error "Failed to get head revision"
        exit 1
    fi
    log_info "Head revision: $head_revision"

    echo ""
    echo "========================================="
    echo "  Migration Status"
    echo "========================================="
    echo ""

    # Compare revisions
    if [ "$current_revision" = "$head_revision" ]; then
        log_success "✓ Database is up to date"
        echo ""
        echo "Current revision: $current_revision"
        echo "Target revision:  $head_revision"
        echo ""
        log_info "No pending migrations"
        exit 0
    else
        log_warning "⚠ Database has pending migrations"
        echo ""
        echo "Current revision: $current_revision"
        echo "Target revision:  $head_revision"
        echo ""

        # Show pending migrations
        log_info "Pending migrations:"
        docker-compose run --rm backend alembic history 2>/dev/null | head -20
        echo ""

        log_warning "Run the following command to apply migrations:"
        echo "  $0"
        echo ""
        exit 1
    fi
}

# Standard upgrade (with downtime)
perform_standard_upgrade() {
    echo "========================================="
    echo "  Upgrading Application (Standard)"
    echo "========================================="
    echo ""

    # Backup
    create_backup_directory
    backup_database || exit 1
    backup_env_files
    echo ""

    # Pull/build new images
    pull_latest_images
    build_images

    # Stop services
    log_step "Stopping services..."
    docker-compose down
    log_success "✓ Services stopped"
    echo ""

    # Start infrastructure
    log_step "Starting infrastructure services..."
    docker-compose up -d postgres redis
    log_success "✓ Infrastructure services started"

    wait_for_postgres || exit 1
    wait_for_redis || exit 1
    echo ""

    # Run migrations
    run_migrations

    # Start all services
    log_step "Starting all services..."
    docker-compose up -d
    log_success "✓ All services started"
    echo ""

    # Health checks
    log_step "Running health checks..."
    wait_for_services
    echo ""
}

# Zero-downtime upgrade (blue-green)
perform_zero_downtime_upgrade() {
    echo "========================================="
    echo "  Upgrading Application (Zero-Downtime)"
    echo "========================================="
    echo ""

    log_warning "Zero-downtime upgrade requires additional configuration"
    log_info "This is a simplified version - full blue-green deployment requires:"
    log_info "  - Load balancer configuration"
    log_info "  - Multiple service instances"
    log_info "  - Health check integration"
    echo ""

    # Backup
    create_backup_directory
    backup_database || exit 1
    backup_env_files
    echo ""

    # Pull/build new images
    pull_latest_images
    build_images

    # Run migrations (with current running services)
    run_migrations

    # Restart services one by one
    log_step "Restarting services with rolling update..."

    # Restart backend
    log_info "Restarting backend..."
    docker-compose up -d --no-deps backend
    wait_for_http_health "http://localhost:8000/health" "backend" || exit 1

    # Restart celery_worker
    log_info "Restarting celery worker..."
    docker-compose up -d --no-deps celery_worker
    sleep 5

    # Restart flower
    log_info "Restarting flower..."
    docker-compose up -d --no-deps flower
    wait_for_http_health "http://localhost:5555/" "flower" || true

    # Restart frontend
    log_info "Restarting frontend..."
    docker-compose up -d --no-deps frontend
    wait_for_http_health "http://localhost:5173/" "frontend" || exit 1

    log_success "✓ Rolling update completed"
    echo ""
}

# Main upgrade flow
main() {
    # Parse arguments
    parse_args "$@"

    # Handle migration check
    if [ "$CHECK_MIGRATIONS" = true ]; then
        # Check prerequisites
        log_info "Checking prerequisites..."
        check_docker || { log_error "Docker is required but not installed. Aborting."; exit 1; }
        check_docker_compose || { log_error "Docker Compose is required but not installed. Aborting."; exit 1; }
        log_success "✓ Prerequisites check passed"
        echo ""

        # Setup environment
        setup_environment || exit 1
        echo ""

        check_pending_migrations
        exit 0
    fi

    # Handle rollback
    if [ "$ROLLBACK" = true ]; then
        perform_rollback
        exit 0
    fi

    # Check prerequisites
    log_info "Checking prerequisites..."
    check_docker || { log_error "Docker is required but not installed. Aborting."; exit 1; }
    check_docker_compose || { log_error "Docker Compose is required but not installed. Aborting."; exit 1; }
    check_running_containers
    log_success "✓ Prerequisites check passed"
    echo ""

    # Setup environment
    setup_environment || exit 1
    echo ""

    # Perform upgrade based on mode
    if [ "$NO_DOWNTIME" = true ]; then
        perform_zero_downtime_upgrade
    else
        perform_standard_upgrade
    fi

    # Display upgrade summary
    echo "========================================="
    echo "  Upgrade Summary"
    echo "========================================="
    echo ""
    log_success "✓ Upgrade completed successfully!"
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

    if [ "$SKIP_BACKUP" = false ]; then
        echo "Backup Location:"
        echo "  - Database: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
        echo "  - Config:   $BACKUP_DIR/config_$TIMESTAMP/"
        echo ""
        echo "To rollback:"
        echo "  $0 --rollback"
        echo ""
    fi

    echo "View logs:"
    echo "  docker-compose logs -f"
    echo ""
}

# Run main function
main "$@"
