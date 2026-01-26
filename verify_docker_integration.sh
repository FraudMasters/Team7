#!/bin/bash
# Docker Integration Verification Script
# This script verifies that all Docker containers start correctly and are healthy
# Usage: ./verify_docker_integration.sh

set -e  # Exit on error

echo "======================================"
echo "Docker Integration Verification"
echo "======================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check if docker-compose is installed
print_info "Checking docker-compose installation..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi
print_success "docker-compose is installed"

# Determine which docker-compose command to use
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Stop any existing containers
print_info "Stopping any existing containers..."
$DOCKER_COMPOSE down 2>/dev/null || true
print_success "Containers stopped"

# Start Docker containers
print_info "Starting Docker containers..."
$DOCKER_COMPOSE up -d

# Wait for containers to start
print_info "Waiting for containers to initialize..."
sleep 10

# Check container status
print_info "Checking container status..."
echo ""

# Function to check container health
check_container() {
    local container_name=$1
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if $DOCKER_COMPOSE ps | grep -q "$container_name.*Up.*healthy"; then
            print_success "$container_name is healthy"
            return 0
        elif $DOCKER_COMPOSE ps | grep -q "$container_name.*Up"; then
            # Container is up but not yet healthy
            attempt=$((attempt + 1))
            sleep 2
        else
            print_error "$container_name is not running"
            $DOCKER_COMPOSE ps
            return 1
        fi
    done

    print_error "$container_name did not become healthy in time"
    $DOCKER_COMPOSE ps
    return 1
}

# Check each critical container
echo "Checking critical containers..."
check_container "resume_analysis_db" || exit 1
check_container "resume_analysis_redis" || exit 1
check_container "resume_analysis_backend" || exit 1

print_success "All critical containers are healthy"
echo ""

# Verify backend health endpoint
print_info "Verifying backend health endpoint..."
sleep 5  # Give backend extra time
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend health endpoint is accessible"
    echo ""
    print_info "Backend health response:"
    curl -s http://localhost:8000/health | head -20
else
    print_error "Backend health endpoint is not accessible"
    print_info "Backend logs:"
    $DOCKER_COMPOSE logs backend | tail -50
    exit 1
fi
echo ""

# Verify frontend is accessible
print_info "Verifying frontend accessibility..."
sleep 3  # Give frontend time to start
if curl -f -s http://localhost:5173 > /dev/null 2>&1; then
    print_success "Frontend is accessible"
else
    print_error "Frontend is not accessible"
    print_info "Frontend logs:"
    $DOCKER_COMPOSE logs frontend | tail -50
    exit 1
fi
echo ""

# Check all containers
print_info "Final container status:"
$DOCKER_COMPOSE ps
echo ""

# Verify API docs endpoint
print_info "Verifying API documentation endpoint..."
if curl -f -s http://localhost:8000/docs > /dev/null 2>&1; then
    print_success "API documentation is accessible at http://localhost:8000/docs"
else
    print_error "API documentation is not accessible"
fi
echo ""

# Verify Flower (Celery monitoring)
print_info "Verifying Celery monitoring (Flower)..."
if curl -f -s http://localhost:5555 > /dev/null 2>&1; then
    print_success "Flower monitoring UI is accessible at http://localhost:5555"
else
    print_info "Flower is not yet accessible (may still be starting)"
fi
echo ""

# Display service URLs
echo "======================================"
echo "Service URLs"
echo "======================================"
echo "Backend API:      http://localhost:8000"
echo "API Docs:         http://localhost:8000/docs"
echo "Frontend:         http://localhost:5173"
echo "Flower (Celery):  http://localhost:5555"
echo ""

# Display logs command
echo "To view logs, use:"
echo "  $DOCKER_COMPOSE logs -f [service-name]"
echo ""

print_success "Docker integration verification complete!"
echo ""
echo "All services are running and healthy."
echo ""
