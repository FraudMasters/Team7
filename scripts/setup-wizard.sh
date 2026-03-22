#!/bin/bash
# TEAM7 Resume Analysis Platform - Interactive Setup Wizard
# Guides users through complete deployment configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration defaults
PROFILE="core"
NON_INTERACTIVE=false
VALIDATE_ONLY=false
DRY_RUN=false
SKIP_HEALTH_CHECK=false
ENABLE_MONITORING=false
ENABLE_BACKUPS=false
ENABLE_NEO4J=false

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
    echo -e "${CYAN}=====================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=====================================${NC}"
}

# Show help message
show_help() {
    cat << EOF
${GREEN}TEAM7 Resume Analysis Platform - Interactive Setup Wizard${NC}

${BLUE}USAGE:${NC}
    bash scripts/setup-wizard.sh [OPTIONS]

${BLUE}OPTIONS:${NC}
    --profile <name>         Select deployment profile
                             Available: minimal, core, full, monitoring-only
                             Default: core
    --non-interactive        Run without prompts (uses defaults or flags)
    --validate-only          Only validate configuration, don't start services
    --dry-run                Show what would be done without executing
    --skip-health-check      Skip health check after deployment
    --enable-monitoring      Enable monitoring stack (Prometheus, Grafana)
    --enable-backups         Enable automated backups
    --enable-neo4j           Enable Neo4j graph database
    -h, --help               Show this help message

${BLUE}PROFILES:${NC}
    minimal          - Database and Redis only (postgres, redis)
    core (default)   - Essential services (minimal + backend, frontend, celery)
    full             - Complete stack (core + monitoring, backups)
    monitoring-only  - Monitoring services only (Prometheus, Grafana, Flower)

${BLUE}EXAMPLES:${NC}
    # Interactive mode (prompts for configuration)
    bash scripts/setup-wizard.sh

    # Non-interactive with core profile
    bash scripts/setup-wizard.sh --non-interactive --profile core

    # Full deployment with monitoring
    bash scripts/setup-wizard.sh --profile full --enable-monitoring

    # Validate configuration only
    bash scripts/setup-wizard.sh --validate-only

    # Dry run to preview actions
    bash scripts/setup-wizard.sh --dry-run

${BLUE}WORKFLOW:${NC}
    1. Check prerequisites (Docker, Docker Compose)
    2. Select deployment profile
    3. Configure environment variables
    4. Validate configuration
    5. Start services
    6. Run health checks
    7. Display access information

${BLUE}EXIT CODES:${NC}
    0  Setup completed successfully
    1  Setup failed or validation error
    2  User cancelled setup

EOF
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-health-check)
                SKIP_HEALTH_CHECK=true
                shift
                ;;
            --enable-monitoring)
                ENABLE_MONITORING=true
                shift
                ;;
            --enable-backups)
                ENABLE_BACKUPS=true
                shift
                ;;
            --enable-neo4j)
                ENABLE_NEO4J=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Validate profile selection
validate_profile() {
    case $PROFILE in
        minimal|core|full|monitoring-only)
            return 0
            ;;
        *)
            log_error "Invalid profile: $PROFILE"
            echo "Valid profiles: minimal, core, full, monitoring-only"
            return 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_step "Step 1/7: Checking Prerequisites"

    local all_good=true

    # Check Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log_success "✓ Docker installed (version $docker_version)"

        # Check if Docker daemon is running
        if docker ps &> /dev/null; then
            log_success "✓ Docker daemon is running"
        else
            log_error "✗ Docker daemon is not running"
            log_info "Please start Docker Desktop or the Docker daemon"
            all_good=false
        fi
    else
        log_error "✗ Docker is not installed"
        log_info "Install from: https://www.docker.com/products/docker-desktop"
        all_good=false
    fi

    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        local compose_version=""
        if docker compose version &> /dev/null; then
            compose_version=$(docker compose version --short 2>/dev/null || echo "unknown")
        else
            compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        fi
        log_success "✓ Docker Compose installed (version $compose_version)"
    else
        log_error "✗ Docker Compose is not available"
        log_info "Install Docker Desktop which includes Compose"
        all_good=false
    fi

    # Check curl
    if command -v curl &> /dev/null; then
        log_success "✓ curl is available"
    else
        log_warning "⚠ curl not found (recommended for health checks)"
    fi

    # Check disk space (require at least 5GB free)
    local available_space=$(df -k . | tail -1 | awk '{print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    if [ $available_gb -ge 5 ]; then
        log_success "✓ Sufficient disk space (${available_gb}GB available)"
    else
        log_warning "⚠ Low disk space (${available_gb}GB available, 5GB recommended)"
    fi

    if [ "$all_good" = false ]; then
        log_error "Prerequisites check failed"
        return 1
    fi

    log_success "All prerequisites satisfied"
    return 0
}

# Interactive profile selection
select_profile_interactive() {
    log_step "Step 2/7: Select Deployment Profile"

    echo ""
    echo "Available profiles:"
    echo ""
    echo -e "${GREEN}1) minimal${NC}          - Database and Redis only"
    echo "                      Services: postgres, redis"
    echo "                      Use case: External application integration"
    echo ""
    echo -e "${GREEN}2) core (default)${NC}   - Essential application services"
    echo "                      Services: minimal + backend, frontend, celery"
    echo "                      Use case: Standard production deployment"
    echo ""
    echo -e "${GREEN}3) full${NC}             - Complete stack with all features"
    echo "                      Services: core + monitoring, backups, neo4j"
    echo "                      Use case: Full-featured production environment"
    echo ""
    echo -e "${GREEN}4) monitoring-only${NC}  - Monitoring services only"
    echo "                      Services: prometheus, grafana, flower"
    echo "                      Use case: Add monitoring to existing deployment"
    echo ""

    read -p "Select profile [1-4] (default: 2): " choice

    case $choice in
        1) PROFILE="minimal" ;;
        2|"") PROFILE="core" ;;
        3) PROFILE="full" ;;
        4) PROFILE="monitoring-only" ;;
        *)
            log_error "Invalid choice: $choice"
            return 1
            ;;
    esac

    log_info "Selected profile: ${GREEN}$PROFILE${NC}"

    # Ask about optional features for core profile
    if [ "$PROFILE" = "core" ]; then
        echo ""
        read -p "Enable monitoring? (Prometheus, Grafana, Flower) [y/N]: " enable_mon
        if [[ "$enable_mon" =~ ^[Yy]$ ]]; then
            ENABLE_MONITORING=true
            log_info "Monitoring enabled"
        fi

        read -p "Enable automated backups? [y/N]: " enable_bak
        if [[ "$enable_bak" =~ ^[Yy]$ ]]; then
            ENABLE_BACKUPS=true
            log_info "Backups enabled"
        fi

        read -p "Enable Neo4j graph database? (for Graphiti features) [y/N]: " enable_neo
        if [[ "$enable_neo" =~ ^[Yy]$ ]]; then
            ENABLE_NEO4J=true
            log_info "Neo4j enabled"
        fi
    fi

    return 0
}

# Configure environment variables
configure_environment() {
    log_step "Step 3/7: Configure Environment"

    if [ -f .env ] && [ "$NON_INTERACTIVE" = false ]; then
        log_warning ".env file already exists"
        read -p "Overwrite existing .env file? [y/N]: " overwrite
        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            log_info "Using existing .env file"
            return 0
        fi
    fi

    # Copy from example
    if [ -f .env.example ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY RUN] Would copy .env.example to .env"
        else
            cp .env.example .env
            log_success "Created .env from .env.example"
        fi
    else
        log_error ".env.example not found"
        return 1
    fi

    # In non-interactive mode, use defaults
    if [ "$NON_INTERACTIVE" = true ]; then
        log_info "Using default configuration from .env.example"
        return 0
    fi

    # Interactive configuration
    echo ""
    log_info "Configure database credentials (press Enter for defaults):"

    read -p "PostgreSQL database name [resume_analysis]: " db_name
    db_name=${db_name:-resume_analysis}

    read -p "PostgreSQL username [postgres]: " db_user
    db_user=${db_user:-postgres}

    read -sp "PostgreSQL password [postgres]: " db_password
    echo ""
    db_password=${db_password:-postgres}

    # Update .env file
    if [ "$DRY_RUN" = false ]; then
        sed -i.bak "s/POSTGRES_DB=.*/POSTGRES_DB=$db_name/" .env
        sed -i.bak "s/POSTGRES_USER=.*/POSTGRES_USER=$db_user/" .env
        sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$db_password/" .env
        sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$db_user:$db_password@localhost:5432/$db_name|" .env
        rm -f .env.bak
        log_success "Updated database configuration"
    fi

    # Configure Neo4j if enabled
    if [ "$ENABLE_NEO4J" = true ]; then
        echo ""
        log_info "Configure Neo4j credentials:"

        read -sp "Neo4j password [graphiti_password]: " neo4j_password
        echo ""
        neo4j_password=${neo4j_password:-graphiti_password}

        if [ "$DRY_RUN" = false ]; then
            sed -i.bak "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=$neo4j_password/" .env
            rm -f .env.bak
            log_success "Updated Neo4j configuration"
        fi
    fi

    # Configure monitoring if enabled
    if [ "$ENABLE_MONITORING" = true ]; then
        echo ""
        log_info "Configure monitoring (Grafana):"

        read -p "Grafana admin password [admin]: " grafana_password
        grafana_password=${grafana_password:-admin}

        if [ "$DRY_RUN" = false ]; then
            sed -i.bak "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=$grafana_password/" .env
            rm -f .env.bak
            log_success "Updated monitoring configuration"
        fi
    fi

    # Configure backups if enabled
    if [ "$ENABLE_BACKUPS" = true ]; then
        echo ""
        read -p "Enable S3 backups? [y/N]: " enable_s3
        if [[ "$enable_s3" =~ ^[Yy]$ ]]; then
            read -p "S3 bucket name: " s3_bucket
            read -p "S3 region [us-east-1]: " s3_region
            s3_region=${s3_region:-us-east-1}
            read -p "S3 access key: " s3_access_key
            read -sp "S3 secret key: " s3_secret_key
            echo ""

            if [ "$DRY_RUN" = false ]; then
                sed -i.bak "s/BACKUP_S3_ENABLED=.*/BACKUP_S3_ENABLED=true/" .env
                sed -i.bak "s/BACKUP_S3_BUCKET=.*/BACKUP_S3_BUCKET=$s3_bucket/" .env
                sed -i.bak "s/BACKUP_S3_REGION=.*/BACKUP_S3_REGION=$s3_region/" .env
                sed -i.bak "s/BACKUP_S3_ACCESS_KEY=.*/BACKUP_S3_ACCESS_KEY=$s3_access_key/" .env
                sed -i.bak "s/BACKUP_S3_SECRET_KEY=.*/BACKUP_S3_SECRET_KEY=$s3_secret_key/" .env
                rm -f .env.bak
                log_success "Updated S3 backup configuration"
            fi
        fi
    fi

    log_success "Environment configuration complete"
    return 0
}

# Validate .env file exists and is readable
validate_env_file() {
    if [ ! -f .env ]; then
        log_error ".env file not found"
        return 1
    fi

    if [ ! -r .env ]; then
        log_error ".env file is not readable"
        return 1
    fi

    log_success "✓ .env file exists"
    return 0
}

# Validate required environment variables
validate_required_variables() {
    local all_valid=true

    # Source environment variables
    set -a
    source .env 2>/dev/null || true
    set +a

    # Define required variables based on profile
    local required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "REDIS_HOST")

    # Add profile-specific required variables
    if [[ "$PROFILE" =~ ^(core|full)$ ]]; then
        required_vars+=("BACKEND_PORT" "FRONTEND_PORT" "DATABASE_URL")
    fi

    if [ "$ENABLE_NEO4J" = true ] || [ "$PROFILE" = "full" ]; then
        required_vars+=("NEO4J_URI" "NEO4J_USER" "NEO4J_PASSWORD")
    fi

    if [ "$ENABLE_MONITORING" = true ] || [ "$PROFILE" = "full" ]; then
        required_vars+=("GRAFANA_USER" "GRAFANA_PASSWORD")
    fi

    if [ "$ENABLE_BACKUPS" = true ] || [ "$PROFILE" = "full" ]; then
        required_vars+=("BACKUP_ENABLED")
    fi

    # Validate each required variable
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "✗ Required variable $var is not set"
            all_valid=false
        else
            log_success "✓ $var is configured"
        fi
    done

    if [ "$all_valid" = false ]; then
        return 1
    fi

    return 0
}

# Validate port availability
validate_port_availability() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "⚠ Port $port is already in use ($service_name)"

        if [ "$NON_INTERACTIVE" = false ]; then
            read -p "Continue anyway? [y/N]: " continue
            if [[ ! "$continue" =~ ^[Yy]$ ]]; then
                log_error "Setup cancelled by user"
                exit 2
            fi
        fi
        return 1
    fi

    log_success "✓ Port $port is available ($service_name)"
    return 0
}

# Validate Docker Compose configuration
validate_docker_compose_config() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would validate Docker Compose configuration"
        return 0
    fi

    # Check if docker-compose.yml exists
    if [ ! -f docker-compose.yml ]; then
        log_error "docker-compose.yml not found"
        return 1
    fi

    # Validate docker-compose configuration syntax
    if docker compose --profile $PROFILE config > /dev/null 2>&1; then
        log_success "✓ Docker Compose configuration is valid for profile: $PROFILE"
        return 0
    else
        log_error "✗ Docker Compose configuration is invalid"
        return 1
    fi
}

# Validate database URL format
validate_database_url() {
    local db_url="${DATABASE_URL:-}"

    if [ -z "$db_url" ]; then
        log_warning "⚠ DATABASE_URL is not set"
        return 1
    fi

    # Check if URL starts with postgresql://
    if [[ ! "$db_url" =~ ^postgresql:// ]]; then
        log_error "✗ DATABASE_URL must start with postgresql://"
        return 1
    fi

    log_success "✓ DATABASE_URL format is valid"
    return 0
}

# Validate configuration
validate_configuration() {
    log_step "Step 4/7: Validate Configuration"

    local all_valid=true

    # Validate .env file
    if ! validate_env_file; then
        all_valid=false
    fi

    # Validate required variables
    if ! validate_required_variables; then
        all_valid=false
    fi

    # Validate database URL format
    if ! validate_database_url; then
        log_warning "⚠ DATABASE_URL validation failed (non-fatal)"
    fi

    # Check port availability for profile-specific services
    local ports=()
    local port_names=()

    # Add ports based on profile
    if [[ "$PROFILE" =~ ^(minimal|core|full)$ ]]; then
        ports+=(5432 6379)
        port_names+=("PostgreSQL" "Redis")
    fi

    if [[ "$PROFILE" =~ ^(core|full)$ ]]; then
        ports+=(8000 5173)
        port_names+=("Backend" "Frontend")
    fi

    if [ "$ENABLE_MONITORING" = true ] || [ "$PROFILE" = "full" ] || [ "$PROFILE" = "monitoring-only" ]; then
        ports+=(9090 3001 5555)
        port_names+=("Prometheus" "Grafana" "Flower")
    fi

    if [ "$ENABLE_NEO4J" = true ] || [ "$PROFILE" = "full" ]; then
        ports+=(7474 7687)
        port_names+=("Neo4j Browser" "Neo4j Bolt")
    fi

    # Validate each port
    for i in "${!ports[@]}"; do
        validate_port_availability "${ports[$i]}" "${port_names[$i]}" || true
    done

    # Validate Docker Compose configuration
    if ! validate_docker_compose_config; then
        all_valid=false
    fi

    if [ "$all_valid" = false ]; then
        log_error "Configuration validation failed"
        return 1
    fi

    log_success "Configuration validation passed"
    return 0
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    local dirs=(
        "backend/models_cache"
        "backend/data/uploads"
        "backend/data/backups"
    )

    for dir in "${dirs[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY RUN] Would create directory: $dir"
        else
            mkdir -p "$dir"
            log_success "✓ Created $dir"
        fi
    done
}

# Start services
start_services() {
    log_step "Step 5/7: Starting Services"

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would execute: docker-compose --profile $PROFILE up -d"
        return 0
    fi

    # Stop any existing containers
    log_info "Stopping existing containers..."
    docker-compose down --remove-orphans 2>/dev/null || true

    # Build profile arguments
    local compose_args="--profile $PROFILE"

    # Add monitoring if enabled
    if [ "$ENABLE_MONITORING" = true ] && [ "$PROFILE" != "full" ]; then
        compose_args="$compose_args --profile monitoring"
    fi

    log_info "Building images..."
    docker-compose $compose_args build

    log_info "Starting services with profile: $PROFILE"
    docker-compose $compose_args up -d

    log_success "Services started"

    # Wait for database
    if [[ "$PROFILE" =~ ^(minimal|core|full)$ ]]; then
        log_info "Waiting for database to be ready..."

        local db_ready=false
        for i in {1..30}; do
            if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
                log_success "✓ Database is ready"
                db_ready=true
                break
            fi
            sleep 1
            echo -n "."
        done
        echo ""

        if [ "$db_ready" = false ]; then
            log_warning "Database did not become ready in time, but services are starting"
        fi
    fi

    return 0
}

# Run health checks
run_health_checks() {
    log_step "Step 6/7: Running Health Checks"

    if [ "$SKIP_HEALTH_CHECK" = true ]; then
        log_info "Health checks skipped (--skip-health-check)"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would execute: bash scripts/health-check.sh"
        return 0
    fi

    # Check if health check script exists
    if [ ! -f scripts/health-check.sh ]; then
        log_warning "Health check script not found, performing basic checks..."

        # Basic health checks
        sleep 10

        if [[ "$PROFILE" =~ ^(core|full)$ ]]; then
            # Check backend
            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                log_success "✓ Backend is healthy"
            else
                log_warning "⚠ Backend may still be starting..."
            fi

            # Check frontend
            if curl -sf http://localhost:5173/ > /dev/null 2>&1; then
                log_success "✓ Frontend is healthy"
            else
                log_warning "⚠ Frontend may still be starting..."
            fi
        fi

        return 0
    fi

    # Run comprehensive health check
    log_info "Running comprehensive health checks..."
    if bash scripts/health-check.sh; then
        log_success "All health checks passed"
        return 0
    else
        log_warning "Some health checks failed - services may still be starting"
        log_info "Run 'bash scripts/health-check.sh' to check status again"
        return 0
    fi
}

# Display deployment summary
display_summary() {
    log_step "Step 7/7: Deployment Summary"

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Profile:${NC} $PROFILE"
    echo ""

    if [[ "$PROFILE" =~ ^(core|full)$ ]]; then
        echo -e "${BLUE}Services:${NC}"
        echo -e "  - Frontend:        ${CYAN}http://localhost:5173${NC}"
        echo -e "  - Backend API:     ${CYAN}http://localhost:8000${NC}"
        echo -e "  - API Docs:        ${CYAN}http://localhost:8000/docs${NC}"
    fi

    if [ "$ENABLE_MONITORING" = true ] || [ "$PROFILE" = "full" ]; then
        echo -e "  - Prometheus:      ${CYAN}http://localhost:9090${NC}"
        echo -e "  - Grafana:         ${CYAN}http://localhost:3001${NC}"
        echo -e "  - Flower:          ${CYAN}http://localhost:5555${NC}"
    fi

    if [ "$ENABLE_NEO4J" = true ] || [ "$PROFILE" = "full" ]; then
        echo -e "  - Neo4j Browser:   ${CYAN}http://localhost:7474${NC}"
    fi

    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo -e "  - View logs:       ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  - Stop services:   ${YELLOW}docker-compose down${NC}"
    echo -e "  - Restart:         ${YELLOW}docker-compose restart${NC}"
    echo -e "  - Health check:    ${YELLOW}bash scripts/health-check.sh${NC}"
    echo ""

    if [ -f scripts/load_test_data.sh ]; then
        echo -e "${BLUE}Next steps:${NC}"
        echo -e "  - Load test data:  ${YELLOW}bash scripts/load_test_data.sh${NC}"
        echo ""
    fi
}

# Main execution flow
main() {
    # Parse arguments
    parse_args "$@"

    # Show banner
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  TEAM7 Resume Analysis Platform${NC}"
    echo -e "${CYAN}  Interactive Setup Wizard${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY RUN mode - no changes will be made"
    fi

    # Step 1: Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        exit 1
    fi

    # Step 2: Select profile
    if [ "$NON_INTERACTIVE" = false ]; then
        if ! select_profile_interactive; then
            log_error "Profile selection failed"
            exit 1
        fi
    else
        log_step "Step 2/7: Using Profile: $PROFILE"
        if ! validate_profile; then
            exit 1
        fi
    fi

    # Step 3: Configure environment
    if ! configure_environment; then
        log_error "Environment configuration failed"
        exit 1
    fi

    # Step 4: Validate configuration
    if ! validate_configuration; then
        log_error "Configuration validation failed"
        exit 1
    fi

    # If validate-only mode, stop here
    if [ "$VALIDATE_ONLY" = true ]; then
        log_success "Validation complete (--validate-only mode)"
        exit 0
    fi

    # Create directories
    create_directories

    # Step 5: Start services
    if ! start_services; then
        log_error "Failed to start services"
        exit 1
    fi

    # Step 6: Run health checks
    if ! run_health_checks; then
        log_warning "Health checks had warnings, but setup continued"
    fi

    # Step 7: Display summary
    display_summary

    log_success "Setup wizard completed successfully!"
    exit 0
}

# Run main function
main "$@"
