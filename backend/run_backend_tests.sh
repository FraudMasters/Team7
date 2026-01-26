#!/bin/bash
# Backend Unit Tests Runner
# Script to run all backend unit tests with proper configuration

set -e  # Exit on error

echo "================================"
echo "Backend Unit Tests Runner"
echo "================================"
echo ""

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Check we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found"
    echo "Please run this script from the backend directory"
    echo "Usage: cd backend && ./run_backend_tests.sh"
    exit 1
fi

# Check pytest is installed
echo "📦 Checking dependencies..."
if ! python3 -m pytest --version &> /dev/null; then
    echo "❌ Error: pytest not installed"
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

echo "✅ Dependencies OK"
echo ""

# Parse command line arguments
VERBOSE=""
COVERAGE=""
PARALLEL=""
SPECIFIC_TEST=""

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
        -p|--parallel)
            PARALLEL="-n auto"
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run_backend_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Verbose output with print statements"
            echo "  -c, --coverage     Generate coverage report"
            echo "  -p, --parallel     Run tests in parallel (requires pytest-xdist)"
            echo "  -t, --test FILE    Run specific test file"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_backend_tests.sh                    # Run all tests"
            echo "  ./run_backend_tests.sh -v                 # Verbose output"
            echo "  ./run_backend_tests.sh -c                 # With coverage"
            echo "  ./run_backend_tests.sh -p -c              # Parallel + coverage"
            echo "  ./run_backend_tests.sh -t test_synonyms.py # Specific file"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Determine what to run
if [ -n "$SPECIFIC_TEST" ]; then
    TEST_TARGET="$SPECIFIC_TEST"
    echo "🎯 Running specific test: $SPECIFIC_TEST"
else
    TEST_TARGET="tests/"
    echo "🚀 Running all backend tests"
fi

echo ""
echo "================================"
echo "Test Configuration"
echo "================================"
echo "Test Target: $TEST_TARGET"
echo "Verbose: $([ -n "$VERBOSE" ] && echo 'Yes' || echo 'No')"
echo "Coverage: $([ -n "$COVERAGE" ] && echo 'Yes' || echo 'No')"
echo "Parallel: $([ -n "$PARALLEL" ] && echo 'Yes' || echo 'No')"
echo ""
echo "Starting tests..."
echo "================================"
echo ""

# Run pytest
PYTHONPATH="$PYTHONPATH:." python3 -m pytest \
    $TEST_TARGET \
    $VERBOSE \
    $COVERAGE \
    $PARALLEL \
    --tb=short \
    --strict-markers \
    -W ignore::DeprecationWarning

TEST_EXIT_CODE=$?

echo ""
echo "================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests PASSED!"
    echo "================================"
    if [ -n "$COVERAGE" ]; then
        echo ""
        echo "📊 Coverage report generated:"
        echo "  - HTML: htmlcov/index.html"
        echo "  - Terminal: See summary above"
        echo ""
        echo "Open coverage report:"
        echo "  open htmlcov/index.html"
    fi
else
    echo "❌ Some tests FAILED"
    echo "================================"
    echo ""
    echo "Check the output above for details"
    echo "Run with -v for more verbose output"
fi

exit $TEST_EXIT_CODE
