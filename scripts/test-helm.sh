#!/bin/bash
# AgentHR - Helm Chart Validation Script
# Validates Helm chart structure and templates without requiring a Kubernetes cluster

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

# Record test result
record_test_result() {
    local test_name=$1
    local result=$2

    if [ "$result" -eq 0 ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "✓ $test_name"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
        log_error "✗ $test_name"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_step "Step 1: Checking Prerequisites"

    local all_good=true

    # Check if helm directory exists
    if [ ! -d "helm/agenthr" ]; then
        log_error "helm/agenthr directory not found"
        all_good=false
    else
        log_success "✓ helm/agenthr directory found"
    fi

    # Check Chart.yaml
    if [ ! -f "helm/agenthr/Chart.yaml" ]; then
        log_error "helm/agenthr/Chart.yaml not found"
        all_good=false
    else
        log_success "✓ Chart.yaml found"
    fi

    # Check values.yaml
    if [ ! -f "helm/agenthr/values.yaml" ]; then
        log_error "helm/agenthr/values.yaml not found"
        all_good=false
    else
        log_success "✓ values.yaml found"
    fi

    # Check templates directory
    if [ ! -d "helm/agenthr/templates" ]; then
        log_error "helm/agenthr/templates directory not found"
        all_good=false
    else
        log_success "✓ templates directory found"
    fi

    if [ "$all_good" = false ]; then
        log_error "Prerequisites check failed"
        exit 1
    fi
}

# Validate Chart.yaml structure
validate_chart_yaml() {
    log_step "Step 2: Validating Chart.yaml"

    local chart_file="helm/agenthr/Chart.yaml"
    local test_failed=false

    # Check required fields
    if ! grep -q "^apiVersion:" "$chart_file"; then
        log_error "Missing apiVersion in Chart.yaml"
        test_failed=true
    else
        record_test_result "Chart.yaml has apiVersion" 0
    fi

    if ! grep -q "^name:" "$chart_file"; then
        log_error "Missing name in Chart.yaml"
        test_failed=true
    else
        record_test_result "Chart.yaml has name" 0
    fi

    if ! grep -q "^version:" "$chart_file"; then
        log_error "Missing version in Chart.yaml"
        test_failed=true
    else
        record_test_result "Chart.yaml has version" 0
    fi

    if ! grep -q "^description:" "$chart_file"; then
        log_error "Missing description in Chart.yaml"
        test_failed=true
    else
        record_test_result "Chart.yaml has description" 0
    fi

    # Check dependencies
    if grep -q "^dependencies:" "$chart_file"; then
        log_success "✓ Chart.yaml defines dependencies"

        if grep -q "name: postgresql" "$chart_file"; then
            record_test_result "PostgreSQL dependency defined" 0
        else
            log_error "PostgreSQL dependency not found"
            test_failed=true
        fi

        if grep -q "name: redis" "$chart_file"; then
            record_test_result "Redis dependency defined" 0
        else
            log_error "Redis dependency not found"
            test_failed=true
        fi
    else
        log_error "No dependencies defined in Chart.yaml"
        test_failed=true
    fi

    if [ "$test_failed" = true ]; then
        return 1
    fi
}

# Validate values.yaml structure
validate_values_yaml() {
    log_step "Step 3: Validating values.yaml"

    local values_file="helm/agenthr/values.yaml"
    local test_failed=false

    # Check backend configuration
    if grep -q "^backend:" "$values_file"; then
        record_test_result "Backend configuration exists" 0

        if grep -A 20 "^backend:" "$values_file" | grep -q "replicaCount:"; then
            record_test_result "Backend replicaCount defined" 0
        else
            log_error "Backend replicaCount not defined"
            test_failed=true
        fi

        if grep -A 20 "^backend:" "$values_file" | grep -q "image:"; then
            record_test_result "Backend image defined" 0
        else
            log_error "Backend image not defined"
            test_failed=true
        fi
    else
        log_error "Backend configuration missing"
        test_failed=true
    fi

    # Check frontend configuration
    if grep -q "^frontend:" "$values_file"; then
        record_test_result "Frontend configuration exists" 0
    else
        log_error "Frontend configuration missing"
        test_failed=true
    fi

    # Check celeryWorker configuration
    if grep -q "^celeryWorker:" "$values_file"; then
        record_test_result "Celery worker configuration exists" 0
    else
        log_error "Celery worker configuration missing"
        test_failed=true
    fi

    # Check celeryBeat configuration
    if grep -q "^celeryBeat:" "$values_file"; then
        record_test_result "Celery beat configuration exists" 0
    else
        log_error "Celery beat configuration missing"
        test_failed=true
    fi

    # Check ingress configuration
    if grep -q "^ingress:" "$values_file"; then
        record_test_result "Ingress configuration exists" 0
    else
        log_error "Ingress configuration missing"
        test_failed=true
    fi

    # Check persistence configuration
    if grep -q "^persistence:" "$values_file"; then
        record_test_result "Persistence configuration exists" 0
    else
        log_error "Persistence configuration missing"
        test_failed=true
    fi

    if [ "$test_failed" = true ]; then
        return 1
    fi
}

# Validate template files exist
validate_template_files() {
    log_step "Step 4: Validating Template Files"

    local templates_dir="helm/agenthr/templates"
    local required_templates=(
        "_helpers.tpl"
        "backend-deployment.yaml"
        "backend-service.yaml"
        "frontend-deployment.yaml"
        "frontend-service.yaml"
        "celery-worker-deployment.yaml"
        "celery-beat-deployment.yaml"
        "configmap.yaml"
        "secrets.yaml"
        "serviceaccount.yaml"
        "ingress.yaml"
        "pvc.yaml"
    )

    for template in "${required_templates[@]}"; do
        if [ -f "$templates_dir/$template" ]; then
            record_test_result "Template $template exists" 0
        else
            log_error "Template $template not found"
            record_test_result "Template $template exists" 1
        fi
    done
}

# Validate template YAML syntax
validate_template_syntax() {
    log_step "Step 5: Validating Template YAML Syntax"

    local templates_dir="helm/agenthr/templates"
    local test_failed=false

    # Find all YAML files (excluding _helpers.tpl)
    for template in "$templates_dir"/*.yaml; do
        local template_name=$(basename "$template")

        # Check if file has basic YAML structure
        if grep -q "^apiVersion:" "$template" || grep -q "^---" "$template"; then
            # Basic YAML structure validation
            if grep -q "^kind:" "$template"; then
                record_test_result "Template $template_name has valid structure" 0
            else
                log_warning "Template $template_name missing 'kind' field"
            fi
        else
            log_warning "Template $template_name may be empty or conditional"
        fi
    done

    # Check _helpers.tpl exists and has content
    if [ -f "$templates_dir/_helpers.tpl" ]; then
        if grep -q "agenthr.name" "$templates_dir/_helpers.tpl"; then
            record_test_result "_helpers.tpl has template functions" 0
        else
            log_error "_helpers.tpl appears to be empty or invalid"
            test_failed=true
        fi
    fi

    if [ "$test_failed" = true ]; then
        return 1
    fi
}

# Validate deployment templates
validate_deployments() {
    log_step "Step 6: Validating Deployment Templates"

    local templates_dir="helm/agenthr/templates"
    local deployments=(
        "backend-deployment.yaml"
        "frontend-deployment.yaml"
        "celery-worker-deployment.yaml"
        "celery-beat-deployment.yaml"
    )

    for deployment in "${deployments[@]}"; do
        local deployment_file="$templates_dir/$deployment"
        local deployment_name=$(basename "$deployment" .yaml)

        if [ ! -f "$deployment_file" ]; then
            log_error "$deployment not found"
            record_test_result "$deployment_name exists" 1
            continue
        fi

        # Check for required fields
        if grep -q "kind: Deployment" "$deployment_file"; then
            record_test_result "$deployment_name has kind: Deployment" 0
        else
            log_error "$deployment missing 'kind: Deployment'"
            record_test_result "$deployment_name has kind: Deployment" 1
        fi

        if grep -q "replicas:" "$deployment_file"; then
            record_test_result "$deployment_name defines replicas" 0
        else
            log_warning "$deployment missing replicas configuration"
        fi

        if grep -q "containers:" "$deployment_file"; then
            record_test_result "$deployment_name defines containers" 0
        else
            log_error "$deployment missing containers specification"
            record_test_result "$deployment_name defines containers" 1
        fi

        # Check for health probes (optional but recommended)
        if grep -q "livenessProbe:" "$deployment_file"; then
            log_success "✓ $deployment_name has liveness probe"
        fi

        if grep -q "readinessProbe:" "$deployment_file"; then
            log_success "✓ $deployment_name has readiness probe"
        fi

        # Check for resource limits
        if grep -q "resources:" "$deployment_file"; then
            log_success "✓ $deployment_name defines resource limits"
        else
            log_warning "$deployment_name missing resource limits"
        fi
    done
}

# Validate service templates
validate_services() {
    log_step "Step 7: Validating Service Templates"

    local templates_dir="helm/agenthr/templates"
    local services=(
        "backend-service.yaml"
        "frontend-service.yaml"
    )

    for service in "${services[@]}"; do
        local service_file="$templates_dir/$service"
        local service_name=$(basename "$service" .yaml)

        if [ ! -f "$service_file" ]; then
            log_error "$service not found"
            record_test_result "$service_name exists" 1
            continue
        fi

        # Check for required fields
        if grep -q "kind: Service" "$service_file"; then
            record_test_result "$service_name has kind: Service" 0
        else
            log_error "$service missing 'kind: Service'"
            record_test_result "$service_name has kind: Service" 1
        fi

        if grep -q "type:" "$service_file"; then
            record_test_result "$service_name defines service type" 0
        else
            log_error "$service missing service type"
            record_test_result "$service_name defines service type" 1
        fi

        if grep -q "ports:" "$service_file"; then
            record_test_result "$service_name defines ports" 0
        else
            log_error "$service missing ports specification"
            record_test_result "$service_name defines ports" 1
        fi
    done
}

# Validate ingress template
validate_ingress() {
    log_step "Step 8: Validating Ingress Template"

    local ingress_file="helm/agenthr/templates/ingress.yaml"

    if [ ! -f "$ingress_file" ]; then
        log_error "ingress.yaml not found"
        record_test_result "Ingress template exists" 1
        return 1
    fi

    record_test_result "Ingress template exists" 0

    # Check for conditional rendering
    if grep -q "{{- if .Values.ingress.enabled }}" "$ingress_file"; then
        record_test_result "Ingress has conditional rendering" 0
    else
        log_warning "Ingress missing conditional rendering"
    fi

    # Check for TLS configuration
    if grep -q "tls:" "$ingress_file"; then
        log_success "✓ Ingress supports TLS configuration"
    fi

    # Check for path routing
    if grep -q "paths:" "$ingress_file"; then
        record_test_result "Ingress defines path routing" 0
    else
        log_error "Ingress missing path routing"
        record_test_result "Ingress defines path routing" 1
    fi
}

# Validate PVC template
validate_pvcs() {
    log_step "Step 9: Validating PersistentVolumeClaim Template"

    local pvc_file="helm/agenthr/templates/pvc.yaml"

    if [ ! -f "$pvc_file" ]; then
        log_error "pvc.yaml not found"
        record_test_result "PVC template exists" 1
        return 1
    fi

    record_test_result "PVC template exists" 0

    # Check for PVC definitions
    if grep -q "kind: PersistentVolumeClaim" "$pvc_file"; then
        record_test_result "PVC template has valid kind" 0
    else
        log_error "PVC template missing 'kind: PersistentVolumeClaim'"
        record_test_result "PVC template has valid kind" 1
    fi

    # Check for storage size configuration
    if grep -q "storage:" "$pvc_file"; then
        log_success "✓ PVC defines storage size"
    fi

    # Check for access modes
    if grep -q "accessModes:" "$pvc_file"; then
        log_success "✓ PVC defines access modes"
    fi
}

# Validate ConfigMap and Secrets
validate_config_and_secrets() {
    log_step "Step 10: Validating ConfigMap and Secrets"

    local templates_dir="helm/agenthr/templates"

    # Check ConfigMap
    if [ -f "$templates_dir/configmap.yaml" ]; then
        record_test_result "ConfigMap template exists" 0

        if grep -q "kind: ConfigMap" "$templates_dir/configmap.yaml"; then
            record_test_result "ConfigMap has valid kind" 0
        else
            log_error "ConfigMap missing 'kind: ConfigMap'"
            record_test_result "ConfigMap has valid kind" 1
        fi
    else
        log_error "configmap.yaml not found"
        record_test_result "ConfigMap template exists" 1
    fi

    # Check Secrets
    if [ -f "$templates_dir/secrets.yaml" ]; then
        record_test_result "Secrets template exists" 0

        if grep -q "kind: Secret" "$templates_dir/secrets.yaml"; then
            record_test_result "Secrets has valid kind" 0
        else
            log_error "Secrets missing 'kind: Secret'"
            record_test_result "Secrets has valid kind" 1
        fi
    else
        log_error "secrets.yaml not found"
        record_test_result "Secrets template exists" 1
    fi
}

# Check for Helm best practices
validate_best_practices() {
    log_step "Step 11: Checking Helm Best Practices"

    local templates_dir="helm/agenthr/templates"

    # Check for helper templates
    if [ -f "$templates_dir/_helpers.tpl" ]; then
        log_success "✓ Helper templates file exists"

        # Check for common helpers
        if grep -q "agenthr.name" "$templates_dir/_helpers.tpl"; then
            record_test_result "Helper: agenthr.name defined" 0
        fi

        if grep -q "agenthr.fullname" "$templates_dir/_helpers.tpl"; then
            record_test_result "Helper: agenthr.fullname defined" 0
        fi

        if grep -q "agenthr.labels" "$templates_dir/_helpers.tpl"; then
            record_test_result "Helper: agenthr.labels defined" 0
        fi

        if grep -q "agenthr.selectorLabels" "$templates_dir/_helpers.tpl"; then
            record_test_result "Helper: agenthr.selectorLabels defined" 0
        fi
    else
        log_error "Helper templates file missing"
        record_test_result "Helper templates exist" 1
    fi

    # Check README exists
    if [ -f "helm/agenthr/README.md" ]; then
        record_test_result "Chart README.md exists" 0
    else
        log_warning "Chart README.md not found (recommended)"
    fi

    # Check for .helmignore
    if [ -f "helm/agenthr/.helmignore" ]; then
        log_success "✓ .helmignore file exists"
    else
        log_warning ".helmignore file not found (optional)"
    fi
}

# Display summary
display_summary() {
    log_step "Test Summary"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))

    echo ""
    echo "======================================"
    echo "  Test Results"
    echo "======================================"
    echo ""
    echo -e "Total Tests:  $total_tests"
    echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
    echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo ""
    fi

    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "✓ All validation tests passed!"
        echo ""
        echo "The Helm chart structure is valid and ready for deployment."
        echo ""
        echo "Next steps:"
        echo "1. Install Helm dependencies: helm dependency update helm/agenthr"
        echo "2. Render templates: helm template agenthr helm/agenthr"
        echo "3. Deploy to Kubernetes: helm install agenthr helm/agenthr"
        echo "4. See scripts/HELM_TESTING.md for detailed testing procedures"
        echo ""
        return 0
    else
        log_error "Some validation tests failed. Please review the errors above."
        echo ""
        echo "Common fixes:"
        echo "- Ensure all required template files exist"
        echo "- Check YAML syntax in template files"
        echo "- Verify values.yaml has all required configurations"
        echo "- Review Chart.yaml for missing fields"
        echo ""
        return 1
    fi
}

# Main execution
main() {
    log_step "AgentHR Helm Chart Validation"

    echo "This script validates the Helm chart structure without requiring Kubernetes."
    echo "For full deployment testing, see scripts/HELM_TESTING.md"
    echo ""

    check_prerequisites
    validate_chart_yaml
    validate_values_yaml
    validate_template_files
    validate_template_syntax
    validate_deployments
    validate_services
    validate_ingress
    validate_pvcs
    validate_config_and_secrets
    validate_best_practices

    display_summary
}

# Run main function
main
exit $?
