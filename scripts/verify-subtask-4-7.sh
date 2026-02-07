#!/bin/bash

###############################################################################
# Verification Script for Subtask 4-7: Verify All Existing Tests Still Pass
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

print_failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

###############################################################################
# 1. Environment Check
###############################################################################

print_header "1. Environment Check"

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_failure "Not in project root directory"
    exit 1
else
    print_success "In project root directory"
fi

# Check for backend
if [ -d "backend" ]; then
    print_success "Backend directory exists"
else
    print_failure "Backend directory not found"
fi

# Check for frontend
if [ -d "frontend" ]; then
    print_success "Frontend directory exists"
else
    print_failure "Frontend directory not found"
fi

###############################################################################
# 2. Backend Test Structure Check
###############################################################################

print_header "2. Backend Test Structure"

# Check for pytest
if command -v pytest &> /dev/null; then
    print_success "pytest is available"
    PYTEST_VERSION=$(pytest --version | head -n 1)
    print_info "Version: $PYTEST_VERSION"
else
    print_failure "pytest is not installed or not in PATH"
    print_info "Install with: cd backend && pip install -r requirements.txt"
fi

# Check for test directory
if [ -d "backend/tests" ]; then
    print_success "Backend tests directory exists"

    # Count test files
    TEST_COUNT=$(find backend/tests -name "test_*.py" -type f | wc -l)
    print_info "Found $TEST_COUNT test files"

    # List test modules
    print_info "Test modules:"
    find backend/tests -name "test_*.py" -type f | sed 's|backend/tests/||' | sed 's|__init__.py||' | grep -v "__init__" | sort | while read file; do
        echo -e "  - ${file%.*}"
    done
else
    print_failure "Backend tests directory not found"
fi

# Check for pytest.ini
if [ -f "backend/pytest.ini" ]; then
    print_success "pytest.ini configuration exists"
else
    print_warning "pytest.ini not found (using default configuration)"
fi

###############################################################################
# 3. Frontend Test Structure Check
###############################################################################

print_header "3. Frontend Test Structure"

# Check for npm
if command -v npm &> /dev/null; then
    print_success "npm is available"
    NPM_VERSION=$(npm --version)
    print_info "Version: $NPM_VERSION"
else
    print_failure "npm is not installed or not in PATH"
fi

# Check for vitest
if [ -f "frontend/package.json" ]; then
    if grep -q '"vitest"' frontend/package.json; then
        print_success "vitest is in package.json dependencies"
    else
        print_failure "vitest not found in package.json"
    fi

    # Check test script
    if grep -q '"test".*"vitest"' frontend/package.json; then
        print_success "Test script configured in package.json"
    else
        print_warning "Test script may not be properly configured"
    fi
else
    print_failure "package.json not found"
fi

# Count test files
if [ -d "frontend/src" ]; then
    TEST_COUNT=$(find frontend/src -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" 2>/dev/null | wc -l)
    print_success "Found $TEST_COUNT frontend test files"

    if [ "$TEST_COUNT" -gt 0 ]; then
        print_info "Sample test files:"
        find frontend/src -name "*.test.*" -o -name "*.spec.*" 2>/dev/null | head -5 | while read file; do
            echo -e "  - ${file#frontend/src/}"
        done
    fi
fi

###############################################################################
# 4. Authentication Impact Analysis
###############################################################################

print_header "4. Authentication Impact Analysis"

# Check if auth middleware exists
if [ -f "backend/middleware/auth.py" ]; then
    print_success "Authentication middleware exists"

    # Check for auth dependencies in API files
    AUTH_USAGE=$(grep -r "require_role\|require_any_role\|get_current_token" backend/api/*.py 2>/dev/null | wc -l)
    if [ "$AUTH_USAGE" -gt 0 ]; then
        print_warning "Found $AUTH_USAGE authentication requirements in API endpoints"
        print_info "Existing tests may need authentication tokens to pass"

        # List files with auth
        print_info "API files using authentication:"
        grep -l "require_role\|require_any_role\|get_current_token" backend/api/*.py 2>/dev/null | while read file; do
            echo -e "  - ${file#backend/}"
        done
    fi
else
    print_warning "Authentication middleware not found"
fi

# Check for AuthContext in frontend
if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
    print_success "AuthContext exists"

    # Check if tests might need AuthContext mocking
    if [ -d "frontend/src" ]; then
        COMPONENT_TESTS=$(find frontend/src/components -name "*.test.tsx" 2>/dev/null | wc -l)
        if [ "$COMPONENT_TESTS" -gt 0 ]; then
            print_info "Found $COMPONENT_TESTS component tests"
            print_warning "Component tests may need AuthContext mocked"
        fi
    fi
else
    print_warning "AuthContext not found"
fi

###############################################################################
# 5. Run Backend Tests (if pytest available)
###############################################################################

print_header "5. Backend Tests"

if command -v pytest &> /dev/null; then
    print_info "Running backend tests with pytest..."
    echo ""

    if cd backend 2>/dev/null; then
        if pytest tests/ --tb=short -v 2>&1 | tee /tmp/backend-test-output.txt; then
            print_success "All backend tests passed"
            PASSED=$(grep -oP '\d+ passed' /tmp/backend-test-output.txt | head -1)
            if [ -n "$PASSED" ]; then
                print_info "Results: $PASSED"
            fi
        else
            EXIT_CODE=$?
            print_failure "Backend tests failed with exit code $EXIT_CODE"
            print_info "Check output above for details"
            print_info "Common issues:"
            echo -e "  - Tests calling protected API endpoints need authentication tokens"
            echo -e "  - Tests may need to mock JWT dependencies"
            echo -e "  - Database connection issues"
        fi
        cd - > /dev/null
    else
        print_failure "Could not access backend directory"
    fi
else
    print_warning "Cannot run backend tests - pytest not available"
    print_info "To run manually: cd backend && pytest tests/ --tb=short"
fi

###############################################################################
# 6. Run Frontend Tests (if npm available)
###############################################################################

print_header "6. Frontend Tests"

if command -v npm &> /dev/null; then
    print_info "Running frontend tests with vitest..."
    echo ""

    if cd frontend 2>/dev/null; then
        if npm test -- --run 2>&1 | tee /tmp/frontend-test-output.txt; then
            print_success "All frontend tests passed"
            PASSED=$(grep -oP '\d+ passed' /tmp/frontend-test-output.txt | head -1)
            if [ -n "$PASSED" ]; then
                print_info "Results: $PASSED"
            fi
        else
            EXIT_CODE=$?
            print_failure "Frontend tests failed with exit code $EXIT_CODE"
            print_info "Check output above for details"
            print_info "Common issues:"
            echo -e "  - Component tests may need AuthContext mocked"
            echo -e "  - Tests using API client may need auth mocking"
            echo -e "  - Missing test dependencies"
        fi
        cd - > /dev/null
    else
        print_failure "Could not access frontend directory"
    fi
else
    print_warning "Cannot run frontend tests - npm not available"
    print_info "To run manually: cd frontend && npm test"
fi

###############################################################################
# 7. Test Coverage Analysis
###############################################################################

print_header "7. Test Coverage Analysis"

# Backend coverage
if command -v pytest &> /dev/null && [ -d "backend" ]; then
    print_info "Backend test modules:"
    find backend/tests -name "test_*.py" -type f | while read file; do
        module=$(basename "$file" .py)
        count=$(grep -c "def test_" "$file" 2>/dev/null || echo "0")
        echo -e "  - $module: $count tests"
    done
fi

# Frontend coverage
if [ -d "frontend/src" ]; then
    print_info "Frontend test files:"
    find frontend/src -name "*.test.*" -o -name "*.spec.*" 2>/dev/null | while read file; do
        filename=$(basename "$file")
        count=$(grep -c "test(\|it(" "$file" 2>/dev/null || echo "0")
        echo -e "  - $filename: $count tests"
    done
fi

###############################################################################
# 8. Summary and Recommendations
###############################################################################

print_header "8. Summary and Recommendations"

echo -e "Test Status:"
echo -e "  Checks Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "  Checks Failed: ${RED}$FAIL_COUNT${NC}"
echo -e "  Warnings:      ${YELLOW}$WARN_COUNT${NC}"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    print_success "All verification checks passed!"
    echo ""
    print_info "Next Steps:"
    echo -e "  1. Run full backend test suite: cd backend && pytest tests/ -v"
    echo -e "  2. Run full frontend test suite: cd frontend && npm test"
    echo -e "  3. If tests fail due to authentication:"
    echo -e "     - Backend: Add JWT token mocking to test fixtures"
    echo -e "     - Frontend: Mock AuthContext in component tests"
    echo -e "  4. Update tests to use authentication dependencies where needed"
else
    print_failure "Some verification checks failed"
    echo ""
    print_info "Required Actions:"
    echo -e "  1. Install missing dependencies (pytest, npm, etc.)"
    echo -e "  2. Ensure all test files are present"
    echo -e "  3. Fix any configuration issues"
    echo -e "  4. Re-run this verification script"
fi

echo ""
print_info "Authentication Testing Notes:"
echo -e "  - Protected endpoints now require JWT tokens"
echo -e "  - Tests for protected endpoints need authentication fixtures"
echo -e "  - Public endpoints should work without authentication"
echo -e "  - Role-based access control requires specific user roles"

echo ""
print_info "For detailed test execution and debugging:"
echo -e "  Backend: cd backend && pytest tests/ -v --tb=long"
echo -e "  Frontend: cd frontend && npm test -- --run --reporter=verbose"

echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    exit 0
else
    exit 1
fi
