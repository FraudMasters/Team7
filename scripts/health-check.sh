#!/bin/bash
# TEAM7 Resume Analysis Platform - Health Check Script
# Comprehensive health check for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Global variables for tracking health status
HEALTHY_SERVICES=0
UNHEALTHY_SERVICES=0
TOTAL_SERVICES=6
DRY_RUN=false

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help message
show_help() {
    cat << EOF
TEAM7 Resume Analysis Platform - Health Check Script

Usage: bash scripts/health-check.sh [OPTIONS]

OPTIONS:
    --dry-run    Validate script without checking running services
    -h, --help   Show this help message

DESCRIPTION:
    Performs comprehensive health checks on all platform services:
    - PostgreSQL database
    - Redis cache
    - Backend API
    - Frontend application
    - Celery worker
    - Flower monitoring

EXIT CODES:
    0  All services are healthy
    1  One or more services are unhealthy
    2  Script validation error

EXAMPLES:
    bash scripts/health-check.sh           # Run full health check
    bash scripts/health-check.sh --dry-run # Validate script only

EOF
}

# Dry run mode validation
validate_dry_run() {
    log_info "Running in dry-run mode - validating script..."

    # Check if required commands exist
    local commands=("docker" "docker-compose" "curl")
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            log_success "✓ Command '$cmd' is available"
        else
            log_warning "⚠ Command '$cmd' not found (required for health checks)"
        fi
    done

    # Check if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        log_success "✓ docker-compose.yml found"
    else
        log_error "✗ docker-compose.yml not found"
        return 1
    fi

    # Validate script syntax
    bash -n "$0" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "✓ Script syntax is valid"
    else
        log_error "✗ Script syntax validation failed"
        return 1
    fi

    log_success "Dry-run validation completed successfully"
    return 0
}

# Check if Docker is running
check_docker_running() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi
    return 0
}

# Check PostgreSQL health
check_postgres() {
    local service_name="PostgreSQL"
    local container_name="resume_analysis_db"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check if PostgreSQL is ready
    if docker exec "$container_name" pg_isready -U postgres >/dev/null 2>&1; then
        log_success "✓ $service_name is healthy"
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name is not responding"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Check Redis health
check_redis() {
    local service_name="Redis"
    local container_name="resume_analysis_redis"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check if Redis is responding
    if docker exec "$container_name" redis-cli ping >/dev/null 2>&1; then
        log_success "✓ $service_name is healthy"
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name is not responding"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Check Backend API health
check_backend() {
    local service_name="Backend API"
    local health_url="http://localhost:8000/health"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_backend"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check HTTP health endpoint
    if curl -sf "$health_url" >/dev/null 2>&1; then
        local response=$(curl -s "$health_url")
        log_success "✓ $service_name is healthy"
        if command -v jq &> /dev/null && echo "$response" | jq . >/dev/null 2>&1; then
            echo "   Response: $(echo $response | jq -c .)"
        fi
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name health check failed"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Check Frontend health
check_frontend() {
    local service_name="Frontend"
    local health_url="http://localhost:5173/"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_frontend"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check HTTP health
    if curl -sf "$health_url" >/dev/null 2>&1; then
        log_success "✓ $service_name is healthy"
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name is not responding"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Check Celery Worker health
check_celery_worker() {
    local service_name="Celery Worker"
    local container_name="resume_analysis_celery_worker"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check if container is healthy (not restarting)
    local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null)
    if [ "$status" = "running" ]; then
        log_success "✓ $service_name is healthy"
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name status: $status"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Check Flower monitoring health
check_flower() {
    local service_name="Flower Monitor"
    local health_url="http://localhost:5555/"

    log_info "Checking $service_name..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_flower"; then
        log_error "✗ $service_name container is not running"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi

    # Check HTTP health
    if curl -sf "$health_url" >/dev/null 2>&1; then
        log_success "✓ $service_name is healthy"
        ((HEALTHY_SERVICES++))
        return 0
    else
        log_error "✗ $service_name is not responding"
        ((UNHEALTHY_SERVICES++))
        return 1
    fi
}

# Display health summary
show_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Health Check Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Total Services:     ${TOTAL_SERVICES}"
    echo -e "Healthy Services:   ${GREEN}${HEALTHY_SERVICES}${NC}"
    echo -e "Unhealthy Services: ${RED}${UNHEALTHY_SERVICES}${NC}"
    echo ""

    if [ $UNHEALTHY_SERVICES -eq 0 ]; then
        log_success "All services are healthy! ✓"
        echo ""
        echo "Service URLs:"
        echo "  - Frontend:        ${BLUE}http://localhost:5173${NC}"
        echo "  - Backend API:     ${BLUE}http://localhost:8000${NC}"
        echo "  - API Docs:        ${BLUE}http://localhost:8000/docs${NC}"
        echo "  - Flower Monitor:  ${BLUE}http://localhost:5555${NC}"
        echo ""
    else
        log_error "Some services are unhealthy!"
        echo ""
        echo "Troubleshooting commands:"
        echo "  - View all logs:      ${YELLOW}docker-compose logs -f${NC}"
        echo "  - View service logs:  ${YELLOW}docker-compose logs -f <service-name>${NC}"
        echo "  - Restart services:   ${YELLOW}docker-compose restart${NC}"
        echo "  - Check status:       ${YELLOW}docker-compose ps${NC}"
        echo ""
    fi
}

# Main execution
main() {
    # Parse arguments
    parse_args "$@"

    # Header
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  TEAM7 Platform Health Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # If dry-run mode, validate and exit
    if [ "$DRY_RUN" = true ]; then
        validate_dry_run
        exit $?
    fi

    # Check if Docker is running
    if ! check_docker_running; then
        log_error "Cannot proceed with health checks"
        exit 2
    fi

    # Run all health checks
    check_postgres || true
    check_redis || true
    check_backend || true
    check_frontend || true
    check_celery_worker || true
    check_flower || true

    # Display summary
    show_summary

    # Exit with appropriate code
    if [ $UNHEALTHY_SERVICES -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
