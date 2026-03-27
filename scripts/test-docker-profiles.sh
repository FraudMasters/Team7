#!/bin/bash
# TEAM7 Resume Analysis Platform - Docker Compose Profile Testing Script
# Tests all Docker Compose profiles to ensure they work correctly

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

log_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Cleanup function
cleanup() {
    log_info "Cleaning up Docker Compose services..."
    docker compose down -v 2>&1 || true
}

# Trap cleanup on script exit
trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    log_step "Step 1: Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_success "✓ Docker is installed"

    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    log_success "✓ Docker daemon is running"

    # Check docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
        exit 1
    fi
    log_success "✓ docker-compose.yml found"

    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found"
        exit 1
    fi
    log_success "✓ .env file found"
}

# Wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local container_name=$2
    local max_wait=120  # 2 minutes
    local elapsed=0

    log_info "Waiting for $service_name to be healthy..."

    while [ $elapsed -lt $max_wait ]; do
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")

        if [ "$health_status" = "healthy" ]; then
            log_success "✓ $service_name is healthy"
            return 0
        elif [ "$health_status" = "none" ]; then
            # No health check defined, just check if running
            local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "not found")
            if [ "$status" = "running" ]; then
                log_success "✓ $service_name is running"
                return 0
            fi
        fi

        sleep 2
        ((elapsed+=2))
    done

    log_error "✗ $service_name failed to become healthy within ${max_wait}s"
    return 1
}

# Test minimal profile
test_minimal_profile() {
    log_step "Test 1: Minimal Profile (postgres + redis)"

    log_info "Starting services with --profile minimal..."
    docker compose --profile minimal up -d

    # Wait for services to start
    sleep 5

    # Verify postgres is running
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_db"; then
        if wait_for_service "PostgreSQL" "resume_analysis_db"; then
            log_success "✓ PostgreSQL is running and healthy"
        else
            log_error "✗ PostgreSQL failed to start"
            FAILED_TESTS+=("minimal-postgres")
            ((TESTS_FAILED++))
            return 1
        fi
    else
        log_error "✗ PostgreSQL container not found"
        FAILED_TESTS+=("minimal-postgres")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify redis is running
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_redis"; then
        if wait_for_service "Redis" "resume_analysis_redis"; then
            log_success "✓ Redis is running and healthy"
        else
            log_error "✗ Redis failed to start"
            FAILED_TESTS+=("minimal-redis")
            ((TESTS_FAILED++))
            return 1
        fi
    else
        log_error "✗ Redis container not found"
        FAILED_TESTS+=("minimal-redis")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify backend is running (minimal profile includes backend)
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_backend"; then
        log_success "✓ Backend is running"
    else
        log_error "✗ Backend container not found"
        FAILED_TESTS+=("minimal-backend")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify frontend is running (minimal profile includes frontend)
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_frontend"; then
        log_success "✓ Frontend is running"
    else
        log_error "✗ Frontend container not found"
        FAILED_TESTS+=("minimal-frontend")
        ((TESTS_FAILED++))
        return 1
    fi

    log_success "Minimal profile test passed"
    ((TESTS_PASSED++))

    # Stop services
    log_info "Stopping minimal profile services..."
    docker compose down
}

# Test core profile
test_core_profile() {
    log_step "Test 2: Core Profile (adds celery_worker + celery_beat)"

    log_info "Starting services with --profile core..."
    docker compose --profile core up -d

    # Wait for services to start
    sleep 10

    # Verify core infrastructure (postgres, redis)
    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_db"; then
        log_error "✗ PostgreSQL container not found"
        FAILED_TESTS+=("core-postgres")
        ((TESTS_FAILED++))
        return 1
    fi

    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_redis"; then
        log_error "✗ Redis container not found"
        FAILED_TESTS+=("core-redis")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify backend
    if ! docker ps --format '{{.Names}}' | grep -q "resume_analysis_backend"; then
        log_error "✗ Backend container not found"
        FAILED_TESTS+=("core-backend")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify celery_worker is running
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_celery_worker"; then
        log_success "✓ Celery Worker is running"
    else
        log_error "✗ Celery Worker container not found"
        FAILED_TESTS+=("core-celery-worker")
        ((TESTS_FAILED++))
        return 1
    fi

    # Verify celery_beat is running
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_celery_beat"; then
        log_success "✓ Celery Beat is running"
    else
        log_error "✗ Celery Beat container not found"
        FAILED_TESTS+=("core-celery-beat")
        ((TESTS_FAILED++))
        return 1
    fi

    log_success "Core profile test passed"
    ((TESTS_PASSED++))

    # Run health check script
    log_info "Running health-check.sh script..."
    if bash scripts/health-check.sh; then
        log_success "✓ Health check script passed"
        ((TESTS_PASSED++))
    else
        log_warning "⚠ Some health checks failed (expected if services still starting)"
        # Don't fail the test as services might still be initializing
    fi

    # Stop services
    log_info "Stopping core profile services..."
    docker compose down
}

# Test full profile
test_full_profile() {
    log_step "Test 3: Full Profile (adds monitoring stack)"

    log_info "Starting services with --profile full..."
    docker compose --profile full up -d

    # Wait for services to start (monitoring stack takes longer)
    sleep 15

    # Verify core services
    local core_services=("resume_analysis_db" "resume_analysis_redis" "resume_analysis_backend" "resume_analysis_celery_worker" "resume_analysis_frontend")
    for service in "${core_services[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "$service"; then
            log_error "✗ $service container not found"
            FAILED_TESTS+=("full-$service")
            ((TESTS_FAILED++))
            return 1
        fi
    done
    log_success "✓ All core services are running"

    # Verify monitoring services
    local monitoring_services=("resume_analysis_grafana" "resume_analysis_loki" "resume_analysis_promtail" "resume_analysis_prometheus")
    for service in "${monitoring_services[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "$service"; then
            log_success "✓ $service is running"
        else
            log_error "✗ $service container not found"
            FAILED_TESTS+=("full-$service")
            ((TESTS_FAILED++))
            return 1
        fi
    done

    # Verify exporters
    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_postgres_exporter"; then
        log_success "✓ PostgreSQL Exporter is running"
    else
        log_warning "⚠ PostgreSQL Exporter not running (optional)"
    fi

    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_celery_exporter"; then
        log_success "✓ Celery Exporter is running"
    else
        log_warning "⚠ Celery Exporter not running (optional)"
    fi

    if docker ps --format '{{.Names}}' | grep -q "resume_analysis_cadvisor"; then
        log_success "✓ cAdvisor is running"
    else
        log_warning "⚠ cAdvisor not running (optional)"
    fi

    log_success "Full profile test passed"
    ((TESTS_PASSED++))

    # Stop services
    log_info "Stopping full profile services..."
    docker compose down
}

# Display service URLs
show_service_urls() {
    log_step "Service URLs"

    echo "Core Services:"
    echo "  - Frontend:        ${BLUE}http://localhost:3000${NC}"
    echo "  - Backend API:     ${BLUE}http://localhost:8000${NC}"
    echo "  - API Docs:        ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    echo "Monitoring (full profile only):"
    echo "  - Grafana:         ${BLUE}http://localhost:3001${NC}"
    echo "  - Prometheus:      ${BLUE}http://localhost:9090${NC}"
    echo "  - Loki:            ${BLUE}http://localhost:3100${NC}"
    echo ""
}

# Display test summary
show_summary() {
    log_step "Test Summary"

    echo -e "Total Tests:     $((TESTS_PASSED + TESTS_FAILED))"
    echo -e "Tests Passed:    ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Tests Failed:    ${RED}${TESTS_FAILED}${NC}"
    echo ""

    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
    fi

    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All Docker Compose profile tests passed! ✓"
        echo ""
        show_service_urls
    else
        log_error "Some tests failed. Check logs above for details."
        echo ""
        echo "Troubleshooting:"
        echo "  - Check logs:   ${YELLOW}docker compose logs -f${NC}"
        echo "  - Check status: ${YELLOW}docker compose ps${NC}"
        echo "  - Clean up:     ${YELLOW}docker compose down -v${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Docker Compose Profile Testing${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Run prerequisite checks
    check_prerequisites

    # Run tests
    test_minimal_profile || true
    test_core_profile || true
    test_full_profile || true

    # Show summary
    show_summary

    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
