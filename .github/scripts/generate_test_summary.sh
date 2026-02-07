#!/bin/bash
# Generate comprehensive test summary for GitHub Actions
# Usage: ./generate_test_summary.sh <output-file>

set -e

OUTPUT_FILE="${1:-test-summary.md}"

# Get environment variables
GENERATED_TIME="${GENERATED_TIME:-$(date -u +"%Y-%m-%d %H:%M:%S UTC")}"
COMMIT_SHA="${COMMIT_SHA:-${GITHUB_SHA:-unknown}}"
BRANCH_NAME="${BRANCH_NAME:-${GITHUB_REF_NAME:-unknown}}"

# Color codes for console output (not used in markdown)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get status emoji
get_status_emoji() {
    case "$1" in
        success) echo "✅" ;;
        failure) echo "❌" ;;
        cancelled) echo "⏭️" ;;
        *) echo "⚠️" ;;
    esac
}

# Function to get coverage color
get_coverage_status() {
    local pct=$1
    local threshold=${2:-80}
    if awk "BEGIN {exit !($pct >= $threshold)}"; then
        echo "✅"
    else
        echo "❌"
    fi
}

# Create summary file
{
    echo "# 🔬 Comprehensive Test Summary Dashboard"
    echo ""
    echo "**Generated:** ${GENERATED_TIME}"
    echo "**Commit:** ${COMMIT_SHA:0:8}"
    echo "**Branch:** ${BRANCH_NAME}"
    echo ""
    echo "---"
    echo ""

    # Test Results Section
    echo "## 🧪 Test Results"
    echo ""
    echo "| Job | Status |"
    echo "|-----|--------|"

    # Get job statuses from environment (set by workflow)
    FRONTEND_LINT_STATUS="${FRONTEND_LINT_STATUS:-unknown}"
    FRONTEND_TESTS_STATUS="${FRONTEND_TESTS_STATUS:-unknown}"
    BACKEND_LINT_STATUS="${BACKEND_LINT_STATUS:-unknown}"
    BACKEND_TESTS_STATUS="${BACKEND_TESTS_STATUS:-unknown}"
    INTEGRATION_TESTS_STATUS="${INTEGRATION_TESTS_STATUS:-unknown}"

    echo "| Frontend Lint | $(get_status_emoji "$FRONTEND_LINT_STATUS") ${FRONTEND_LINT_STATUS} |"
    echo "| Frontend Tests | $(get_status_emoji "$FRONTEND_TESTS_STATUS") ${FRONTEND_TESTS_STATUS} |"
    echo "| Backend Lint | $(get_status_emoji "$BACKEND_LINT_STATUS") ${BACKEND_LINT_STATUS} |"
    echo "| Backend Tests | $(get_status_emoji "$BACKEND_TESTS_STATUS") ${BACKEND_TESTS_STATUS} |"
    echo "| Integration Tests | $(get_status_emoji "$INTEGRATION_TESTS_STATUS") ${INTEGRATION_TESTS_STATUS} |"
    echo ""

    # Coverage Section
    if [ -n "$FRONTEND_COVERAGE_PCT" ] || [ -n "$BACKEND_COVERAGE_PCT" ]; then
        echo "## 📊 Test Coverage"
        echo ""

        if [ -n "$FRONTEND_COVERAGE_PCT" ]; then
            echo "### Frontend"
            echo ""
            echo "| Metric | Coverage | Status |"
            echo "|--------|----------|--------|"
            echo "| Lines | ${FRONTEND_LINES_PCT:-N/A} | $(get_coverage_status "${FRONTEND_LINES_PCT:-0}" 85) |"
            echo "| Functions | ${FRONTEND_FUNCTIONS_PCT:-N/A} | $(get_coverage_status "${FRONTEND_FUNCTIONS_PCT:-0}" 85) |"
            echo "| Branches | ${FRONTEND_BRANCHES_PCT:-N/A} | $(get_coverage_status "${FRONTEND_BRANCHES_PCT:-0}" 85) |"
            echo "| Statements | ${FRONTEND_COVERAGE_PCT} | $(get_coverage_status "$FRONTEND_COVERAGE_PCT" 85) |"
            echo ""
        fi

        if [ -n "$BACKEND_COVERAGE_PCT" ]; then
            echo "### Backend"
            echo ""
            echo "| Metric | Value |"
            echo "|--------|-------|"
            echo "| Overall Coverage | ${BACKEND_COVERAGE_PCT}% | $(get_coverage_status "$BACKEND_COVERAGE_PCT" 80) |"
            echo "| Lines Covered | ${BACKEND_LINES_COVERED:-N/A} |"
            echo "| Total Statements | ${BACKEND_TOTAL_STATEMENTS:-N/A} |"
            echo ""
        fi

        echo "### Coverage Thresholds"
        echo ""
        echo "| Component | Threshold | Current | Status |"
        echo "|-----------|-----------|---------|--------|"
        if [ -n "$FRONTEND_COVERAGE_PCT" ]; then
            echo "| Frontend | ≥85% | ${FRONTEND_COVERAGE_PCT}% | $(get_coverage_status "$FRONTEND_COVERAGE_PCT" 85) |"
        fi
        if [ -n "$BACKEND_COVERAGE_PCT" ]; then
            echo "| Backend | ≥80% | ${BACKEND_COVERAGE_PCT}% | $(get_coverage_status "$BACKEND_COVERAGE_PCT" 80) |"
        fi
        echo ""
    fi

    # Security Section
    if [ -n "$SECURITY_SCAN_RESULTS" ]; then
        echo "## 🛡️ Security Scan Results"
        echo ""
        echo "| Scan Type | Status | Findings |"
        echo "|-----------|--------|----------|"
        echo "$SECURITY_SCAN_RESULTS"
        echo ""
    fi

    # Performance Section
    if [ -n "$PERFORMANCE_RESULTS" ]; then
        echo "## ⚡ Performance Test Results"
        echo ""
        echo "$PERFORMANCE_RESULTS"
        echo ""
    fi

    # Summary Statistics
    echo "## 📈 Summary Statistics"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"

    # Calculate pass rate
    PASSED=0
    TOTAL=0
    for status in "$FRONTEND_LINT_STATUS" "$FRONTEND_TESTS_STATUS" "$BACKEND_LINT_STATUS" "$BACKEND_TESTS_STATUS" "$INTEGRATION_TESTS_STATUS"; do
        if [ "$status" = "success" ]; then
            ((PASSED++))
        fi
        if [ "$status" != "unknown" ]; then
            ((TOTAL++))
        fi
    done

    if [ $TOTAL -gt 0 ]; then
        PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED / $TOTAL) * 100}")
        echo "| Test Pass Rate | ${PASS_RATE}% (${PASSED}/${TOTAL}) |"
    else
        echo "| Test Pass Rate | N/A |"
    fi

    # Overall coverage
    if [ -n "$FRONTEND_COVERAGE_PCT" ] && [ -n "$BACKEND_COVERAGE_PCT" ]; then
        OVERALL_COV=$(awk "BEGIN {printf \"%.1f\", ($FRONTEND_COVERAGE_PCT + $BACKEND_COVERAGE_PCT) / 2}")
        echo "| Overall Coverage | ${OVERALL_COV}% |"
    fi

    echo ""

    # Overall status
    ALL_PASSED=true
    if [ "$PASS_RATE" != "100" ] || [ "$TOTAL" -eq 0 ]; then
        ALL_PASSED=false
    fi
    if [ -n "$FRONTEND_COVERAGE_PCT" ] && [ "$FRONTEND_COVERAGE_PCT" -lt 85 ]; then
        ALL_PASSED=false
    fi
    if [ -n "$BACKEND_COVERAGE_PCT" ] && [ "$BACKEND_COVERAGE_PCT" -lt 80 ]; then
        ALL_PASSED=false
    fi

    if [ "$ALL_PASSED" = true ]; then
        echo "### 🎉 All Checks Passed!"
        echo ""
        echo "Your changes are ready to merge. All tests pass and coverage is adequate."
    else
        echo "### ⚠️ Action Required"
        echo ""
        if [ "$PASS_RATE" != "100" ]; then
            echo "- ❌ Some tests failed (${PASSED}/${TOTAL} passed)"
        fi
        if [ -n "$FRONTEND_COVERAGE_PCT" ] && [ "$FRONTEND_COVERAGE_PCT" -lt 85 ]; then
            echo "- ❌ Frontend coverage below threshold (${FRONTEND_COVERAGE_PCT}% < 85%)"
        fi
        if [ -n "$BACKEND_COVERAGE_PCT" ] && [ "$BACKEND_COVERAGE_PCT" -lt 80 ]; then
            echo "- ❌ Backend coverage below threshold (${BACKEND_COVERAGE_PCT}% < 80%)"
        fi
    fi

    echo ""
    echo "---"
    echo ""
    echo "<details>"
    echo "<summary>📖 About this report</summary>"
    echo ""
    echo "This comprehensive test summary aggregates results from:"
    echo ""
    echo "- **CI Pipeline**: Unit tests, integration tests, linting"
    echo "- **Coverage Reports**: Frontend and backend code coverage"
    echo "- **Security Scans**: Dependency scans, SAST, secrets detection"
    echo "- **Performance Tests**: Load tests and Lighthouse scores"
    echo ""
    echo "For detailed analysis, download the individual artifacts."
    echo "</details>"
    echo ""

} > "$OUTPUT_FILE"

log_info "Test summary generated: ${OUTPUT_FILE}"

# Also append to GitHub Step Summary if the file exists
if [ -n "$GITHUB_STEP_SUMMARY" ]; then
    cat "$OUTPUT_FILE" >> "$GITHUB_STEP_SUMMARY"
    log_info "Summary added to GitHub Step Summary"
fi

exit 0
