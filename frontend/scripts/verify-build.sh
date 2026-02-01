#!/bin/bash

###############################################################################
# Production Build Verification Script
# AgentHR Frontend - Resume Analysis Platform
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
PREVIEW_PORT=${PREVIEW_PORT:-8080}

# Bundle size budgets (in bytes)
BUDGET_TOTAL_JS=2000000       # 2MB total JS
BUDGET_TOTAL_CSS=150000       # 150KB total CSS

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; ((TESTS_PASSED++)); }
log_error() { echo -e "${RED}[✗]${NC} $1"; ((TESTS_FAILED++)); }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; ((TESTS_WARNINGS++)); }
print_header() { echo ""; echo -e "${BLUE}=== $1 ===${NC}"; echo ""; }

format_bytes() {
  local bytes=$1
  if [ "$bytes" -ge 1048576 ]; then
    echo "$(echo "scale=2; $bytes/1048576" | bc)MB"
  elif [ "$bytes" -ge 1024 ]; then
    echo "$(echo "scale=2; $bytes/1024" | bc)KB"
  else
    echo "${bytes}B"
  fi
}

###############################################################################
# Preflight Checks
###############################################################################
preflight_checks() {
  print_header "PREFLIGHT CHECKS"

  if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    log_success "Node.js: $NODE_VERSION"
  else
    log_error "Node.js not found"
    exit 1
  fi

  if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    log_success "npm: $NPM_VERSION"
  else
    log_error "npm not found"
    exit 1
  fi
}

###############################################################################
# Build Verification
###############################################################################
run_build() {
  print_header "PRODUCTION BUILD"

  cd "$PROJECT_ROOT"

  log_info "Cleaning previous build..."
  rm -rf "$DIST_DIR"
  log_success "Build directory cleaned"

  log_info "Running production build..."
  if npm run build 2>&1 | tee /tmp/build.log; then
    log_success "Build completed successfully"
  else
    log_error "Build failed"
    cat /tmp/build.log
    exit 1
  fi

  if [ ! -f "$DIST_DIR/index.html" ]; then
    log_error "index.html not found in build output"
    exit 1
  fi
}

###############################################################################
# Bundle Size Analysis
###############################################################################
analyze_bundle_sizes() {
  print_header "BUNDLE SIZE ANALYSIS"

  TOTAL_JS_SIZE=0
  TOTAL_CSS_SIZE=0

  log_info "Analyzing JavaScript bundles..."
  JS_FILES=$(find "$DIST_DIR" -type f -name "*.js" 2>/dev/null || true)

  if [ -z "$JS_FILES" ]; then
    log_error "No JavaScript files found"
    return 1
  fi

  while IFS= read -r js_file; do
    if [ -f "$js_file" ]; then
      SIZE=$(stat -f%z "$js_file" 2>/dev/null || stat -c%s "$js_file" 2>/dev/null)
      TOTAL_JS_SIZE=$((TOTAL_JS_SIZE + SIZE))
      FILENAME=$(basename "$js_file")
      echo "  $FILENAME: $(format_bytes $SIZE)"
    fi
  done <<< "$JS_FILES"

  log_success "Total JavaScript: $(format_bytes $TOTAL_JS_SIZE)"

  if [ "$TOTAL_JS_SIZE" -gt "$BUDGET_TOTAL_JS" ]; then
    log_warning "Total JS exceeds budget of $(format_bytes $BUDGET_TOTAL_JS)"
  fi

  log_info "Analyzing CSS bundles..."
  CSS_FILES=$(find "$DIST_DIR" -type f -name "*.css" 2>/dev/null || true)

  while IFS= read -r css_file; do
    if [ -f "$css_file" ]; then
      SIZE=$(stat -f%z "$css_file" 2>/dev/null || stat -c%s "$css_file" 2>/dev/null)
      TOTAL_CSS_SIZE=$((TOTAL_CSS_SIZE + SIZE))
      FILENAME=$(basename "$css_file")
      echo "  $FILENAME: $(format_bytes $SIZE)"
    fi
  done <<< "$CSS_FILES"

  log_success "Total CSS: $(format_bytes $TOTAL_CSS_SIZE)"

  TOTAL_SIZE=$((TOTAL_JS_SIZE + TOTAL_CSS_SIZE))
  log_info "Total bundle size: $(format_bytes $TOTAL_SIZE)"
}

###############################################################################
# Console Error Detection
###############################################################################
check_console_errors() {
  print_header "CONSOLE ERROR DETECTION"

  log_info "Checking for console statements in bundle..."

  CONSOLE_LOGS=$(grep -r "console\.log" "$DIST_DIR"/*.js 2>/dev/null | wc -l | tr -d ' ' || echo "0")

  if [ "$CONSOLE_LOGS" -gt 0 ]; then
    log_warning "Found $CONSOLE_LOGS console.log statements"
  else
    log_success "No console.log statements found"
  fi
}

###############################################################################
# Critical User Flow Testing
###############################################################################
test_user_flows() {
  print_header "CRITICAL USER FLOW TESTING"

  # Start preview server
  log_info "Starting preview server..."
  lsof -ti:$PREVIEW_PORT | xargs kill -9 2>/dev/null || true

  cd "$PROJECT_ROOT"
  npm run preview -- --port $PREVIEW_PORT > /tmp/preview.log 2>&1 &
  PREVIEW_PID=$!
  echo "$PREVIEW_PID" > /tmp/preview_server.pid

  sleep 3

  if ! curl -s "http://localhost:$PREVIEW_PORT" > /dev/null 2>&1; then
    log_error "Preview server failed to start"
    cat /tmp/preview.log
    return 1
  fi

  log_success "Preview server started on port $PREVIEW_PORT"

  # Test routes
  local routes=("/" "/jobs" "/recruiter/dashboard" "/recruiter/vacancies" "/recruiter/candidates")

  for route in "${routes[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PREVIEW_PORT$route")
    if [ "$HTTP_CODE" = "200" ]; then
      log_success "Route $route accessible"
    else
      log_error "Route $route returned HTTP $HTTP_CODE"
    fi
  done

  # Cleanup
  kill "$PREVIEW_PID" 2>/dev/null || true
  rm -f /tmp/preview_server.pid
}

###############################################################################
# Summary
###############################################################################
print_summary() {
  print_header "VERIFICATION SUMMARY"

  echo ""
  echo "Test Results:"
  echo "  ✓ Passed: $TESTS_PASSED"
  echo "  ⚠ Warnings: $TESTS_WARNINGS"
  echo "  ✗ Failed: $TESTS_FAILED"
  echo ""

  if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Build verification FAILED${NC}"
    return 1
  else
    echo -e "${GREEN}Build verification PASSED${NC}"
    return 0
  fi
}

###############################################################################
# Main
###############################################################################
main() {
  print_header "AGENTHR PRODUCTION BUILD VERIFICATION"

  preflight_checks
  run_build
  analyze_bundle_sizes
  check_console_errors
  test_user_flows
  print_summary
  exit $?
}

main "$@"
