#!/bin/bash
# Microservices Integration Tests Runner
# Script to run all tests against microservices via API Gateway
# This verifies zero functionality loss after the refactoring

set -e  # Exit on error

echo "================================"
echo "Microservices Integration Tests"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
GATEWAY_HOST="${GATEWAY_HOST:-localhost}"
GATEWAY_PORT="${GATEWAY_PORT:-8888}"
VERBOSE=""
COVERAGE=""
SKIP_SLOW=""
SPECIFIC_TEST=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v -s"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        -s|--skip-slow)
            SKIP_SLOW="-m 'not slow'"
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run_microservices_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Verbose output with print statements"
            echo "  -c, --coverage     Generate coverage report"
            echo "  -s, --skip-slow    Skip slow tests"
            echo "  -t, --test PATH    Run specific test file"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  GATEWAY_HOST       API Gateway host (default: localhost)"
            echo "  GATEWAY_PORT       API Gateway port (default: 8888)"
            echo ""
            echo "Examples:"
            echo "  ./run_microservices_tests.sh                    # Run all tests"
            echo "  ./run_microservices_tests.sh -v                 # Verbose output"
            echo "  ./run_microservices_tests.sh -s                 # Skip slow tests"
            echo "  ./run_microservices_tests.sh -t test_gateway.py  # Specific file"
            echo ""
            echo "Test Suites:"
            echo "  1. Gateway Integration Tests (tests/integration/test_gateway.py)"
            echo "  2. Microservices Tests (tests/integration/test_microservices.py)"
            echo "  3. Backend Unit Tests (backend/tests/)"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Configuration:${NC}"
echo "  Gateway URL: http://${GATEWAY_HOST}:${GATEWAY_PORT}"
echo "  Verbose: $([ -n "$VERBOSE" ] && echo 'Yes' || echo 'No')"
echo "  Coverage: $([ -n "$COVERAGE" ] && echo 'Yes' || echo 'No')"
echo "  Skip Slow: $([ -n "$SKIP_SLOW" ] && echo 'Yes' || echo 'No')"
echo ""

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not running"
        return 1
    fi
}

# Check if API Gateway is running
echo "================================"
echo "Checking Services"
echo "================================"
echo ""

if ! check_service "http://${GATEWAY_HOST}:${GATEWAY_PORT}/health" "API Gateway"; then
    echo ""
    echo -e "${YELLOW}⚠ API Gateway is not running${NC}"
    echo ""
    echo "Please start the microservices:"
    echo "  docker-compose -f docker-compose.microservices.yml up -d"
    echo ""
    echo "Or start the gateway only:"
    echo "  docker-compose -f docker-compose.microservices.yml up api_gateway"
    echo ""
    exit 1
fi

echo ""

# Check if microservices are running
SERVICES_UP=0
SERVICES_DOWN=0

for service_port in 8001 8002 8003 8004 8005 8006 8007 8008 8009; do
    if curl -s -f "http://localhost:${service_port}/health" > /dev/null 2>&1; then
        SERVICES_UP=$((SERVICES_UP + 1))
    else
        SERVICES_DOWN=$((SERVICES_DOWN + 1))
    fi
done

echo "Microservices Status:"
echo "  Running: $SERVICES_UP/9"
echo "  Not Running: $SERVICES_DOWN/9"

if [ $SERVICES_DOWN -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠ Some microservices are not running${NC}"
    echo ""
    echo "Start all microservices:"
    echo "  docker-compose -f docker-compose.microservices.yml up -d"
    echo ""
fi

echo ""
echo "================================"
echo "Running Tests"
echo "================================"
echo ""

# Determine what to run
if [ -n "$SPECIFIC_TEST" ]; then
    TEST_TARGET="$SPECIFIC_TEST"
    echo -e "${BLUE}🎯 Running specific test:${NC} $SPECIFIC_TEST"
else
    TEST_TARGET="tests/"
    echo -e "${BLUE}🚀 Running all integration tests${NC}"
fi

echo ""

# Run pytest
echo -e "${BLUE}Executing pytest...${NC}"
echo ""

PYTHONPATH="$PYTHONPATH:." python3 -m pytest \
    $TEST_TARGET \
    $VERBOSE \
    $COVERAGE \
    $SKIP_SLOW \
    --tb=short \
    --strict-markers \
    -W ignore::DeprecationWarning \
    --color=yes

TEST_EXIT_CODE=$?

echo ""
echo "================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests PASSED!${NC}"
    echo "================================"
    echo ""
    echo "Zero functionality loss verified!"
    echo ""
    if [ -n "$COVERAGE" ]; then
        echo ""
        echo -e "${BLUE}📊 Coverage report generated:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - Terminal: See summary above"
        echo ""
        echo "Open coverage report:"
        echo "  open htmlcov/index.html"
    fi
else
    echo -e "${RED}❌ Some tests FAILED${NC}"
    echo "================================"
    echo ""
    echo "Check the output above for details"
    echo "Run with -v for more verbose output"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure all microservices are running"
    echo "  2. Check API Gateway configuration"
    echo "  3. Verify network connectivity"
    echo "  4. Review service logs"
fi

exit $TEST_EXIT_CODE
