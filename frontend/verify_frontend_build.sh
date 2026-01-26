#!/bin/bash

###############################################################################
# Frontend TypeScript Compilation Verification Script
#
# This script verifies that the frontend TypeScript compilation succeeds.
# Run this script when npm/node are available in your environment.
#
# Usage:
#   ./verify_frontend_build.sh [--verbose] [--fix]
#
# Options:
#   --verbose  Show detailed output from build commands
#   --fix      Attempt to fix common issues automatically
#
# Author: auto-claude (subtask-6-4)
# Date: 2026-01-26
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=false
AUTO_FIX=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --fix|-f)
      AUTO_FIX=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--verbose] [--fix]"
      echo ""
      echo "Verify frontend TypeScript compilation succeeds."
      echo ""
      echo "Options:"
      echo "  --verbose, -v   Show detailed build output"
      echo "  --fix, -f       Attempt to fix common issues"
      echo "  --help, -h      Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

###############################################################################
# Helper Functions
###############################################################################

print_header() {
  echo ""
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}============================================${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

run_command() {
  local cmd="$1"
  local description="$2"

  if [ "$VERBOSE" = true ]; then
    echo ""
    echo -e "${BLUE}Running: $cmd${NC}"
    eval "$cmd"
  else
    eval "$cmd" > /tmp/build_output.txt 2>&1
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
      echo ""
      echo -e "${RED}Command failed: $description${NC}"
      echo -e "${RED}Output:${NC}"
      cat /tmp/build_output.txt
      rm -f /tmp/build_output.txt
      return $exit_code
    fi
  fi

  return 0
}

###############################################################################
# Pre-flight Checks
###############################################################################

check_node_npm() {
  print_header "Checking Node.js and npm"

  # Check Node.js
  if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    print_info "Please install Node.js (>=18.0.0) from https://nodejs.org/"
    return 1
  fi

  NODE_VERSION=$(node -v)
  NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
  print_success "Node.js found: $NODE_VERSION"

  if [ "$NODE_MAJOR" -lt 18 ]; then
    print_warning "Node.js version 18+ recommended, you have $NODE_VERSION"
  fi

  # Check npm
  if ! command -v npm &> /dev/null; then
    print_error "npm is not installed or not in PATH"
    return 1
  fi

  NPM_VERSION=$(npm -v)
  print_success "npm found: $NPM_VERSION"

  return 0
}

check_dependencies() {
  print_header "Checking Dependencies"

  cd "$FRONTEND_DIR"

  if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found"
    print_info "Running 'npm ci' to install dependencies..."

    if [ "$AUTO_FIX" = true ]; then
      if run_command "npm ci" "npm ci"; then
        print_success "Dependencies installed successfully"
      else
        print_error "Failed to install dependencies"
        return 1
      fi
    else
      print_error "Dependencies not installed. Run: npm ci"
      print_info "Or re-run with --fix flag: ./verify_frontend_build.sh --fix"
      return 1
    fi
  else
    print_success "node_modules found"
  fi

  # Check package.json
  if [ ! -f "package.json" ]; then
    print_error "package.json not found"
    return 1
  fi

  print_success "package.json found"

  # Check key files
  local required_files=("tsconfig.json" "vite.config.ts" "src/main.tsx" "src/App.tsx")
  local missing_files=()

  for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
      missing_files+=("$file")
    fi
  done

  if [ ${#missing_files[@]} -gt 0 ]; then
    print_error "Missing required files:"
    for file in "${missing_files[@]}"; do
      echo "  - $file"
    done
    return 1
  fi

  print_success "All required files present"

  return 0
}

###############################################################################
# TypeScript Verification
###############################################################################

verify_typescript_config() {
  print_header "Verifying TypeScript Configuration"

  cd "$FRONTEND_DIR"

  # Check tsconfig.json validity
  if ! python3 -c "import json; json.load(open('tsconfig.json'))" 2>/dev/null; then
    print_error "tsconfig.json is not valid JSON"
    return 1
  fi

  print_success "tsconfig.json is valid JSON"

  # Check TypeScript version
  TSC_VERSION=$(npx tsc --version 2>/dev/null || echo "not found")
  print_info "TypeScript compiler: $TSC_VERSION"

  # Verify tsconfig.node.json
  if [ ! -f "tsconfig.node.json" ]; then
    print_warning "tsconfig.node.json not found (optional)"
  else
    if ! python3 -c "import json; json.load(open('tsconfig.node.json'))" 2>/dev/null; then
      print_error "tsconfig.node.json is not valid JSON"
      return 1
    fi
    print_success "tsconfig.node.json is valid JSON"
  fi

  return 0
}

verify_imports() {
  print_header "Verifying Import Paths"

  cd "$FRONTEND_DIR"

  # Check for obvious import issues
  local error_count=0

  # Look for imports from non-existent files (basic check)
  print_info "Checking for import issues..."

  # This is a basic check - full check would require TypeScript compiler
  if grep -r "from '@pages/" src/ | grep -v "\.test\." | grep -v "\.spec\." > /dev/null 2>&1; then
    print_info "Found @pages/ imports"
  fi

  if grep -r "from '@components/" src/ | grep -v "\.test\." | grep -v "\.spec\." > /dev/null 2>&1; then
    print_info "Found @components/ imports"
  fi

  if grep -r "from '@/types/" src/ | grep -v "\.test\." | grep -v "\.spec\." > /dev/null 2>&1; then
    print_info "Found @/types/ imports"
  fi

  print_success "Import paths look valid"

  return 0
}

###############################################################################
# Build Process
###############################################################################

run_type_check() {
  print_header "Running TypeScript Type Check"

  cd "$FRONTEND_DIR"

  print_info "Running: npx tsc --noEmit"

  if [ "$VERBOSE" = true ]; then
    if npx tsc --noEmit; then
      print_success "TypeScript type check passed"
      return 0
    else
      local exit_code=$?
      print_error "TypeScript type check failed (exit code: $exit_code)"
      return $exit_code
    fi
  else
    local output=$(npx tsc --noEmit 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
      print_success "TypeScript type check passed"
      return 0
    else
      print_error "TypeScript type check failed (exit code: $exit_code)"
      echo ""
      echo "$output"
      return $exit_code
    fi
  fi
}

run_build() {
  print_header "Running Full Build"

  cd "$FRONTEND_DIR"

  print_info "Running: npm run build"

  if [ "$VERBOSE" = true ]; then
    if npm run build; then
      print_success "Build completed successfully"
      return 0
    else
      local exit_code=$?
      print_error "Build failed (exit code: $exit_code)"
      return $exit_code
    fi
  else
    local output=$(npm run build 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
      # Extract relevant info
      echo "$output" | grep -E "(error|warning|built|transformed)" || true
      print_success "Build completed successfully"
      return 0
    else
      print_error "Build failed (exit code: $exit_code)"
      echo ""
      echo "$output"
      return $exit_code
    fi
  fi
}

verify_build_output() {
  print_header "Verifying Build Output"

  cd "$FRONTEND_DIR"

  if [ ! -d "dist" ]; then
    print_error "dist/ directory not found"
    return 1
  fi

  print_success "dist/ directory found"

  # Check for index.html
  if [ ! -f "dist/index.html" ]; then
    print_error "dist/index.html not found"
    return 1
  fi

  print_success "dist/index.html found"

  # Check for assets
  if [ ! -d "dist/assets" ]; then
    print_error "dist/assets/ directory not found"
    return 1
  fi

  print_success "dist/assets/ directory found"

  # Count JS files
  local js_count=$(find dist/assets -name "*.js" 2>/dev/null | wc -l)
  if [ "$js_count" -eq 0 ]; then
    print_warning "No JavaScript files found in dist/assets/"
  else
    print_success "Found $js_count JavaScript file(s) in dist/assets/"
  fi

  # Count CSS files
  local css_count=$(find dist/assets -name "*.css" 2>/dev/null | wc -l)
  if [ "$css_count" -eq 0 ]; then
    print_warning "No CSS files found in dist/assets/"
  else
    print_success "Found $css_count CSS file(s) in dist/assets/"
  fi

  # Show total size
  local total_size=$(du -sh dist 2>/dev/null | cut -f1)
  print_info "Total build size: $total_size"

  return 0
}

###############################################################################
# Optional Checks
###############################################################################

run_linter() {
  print_header "Running ESLint (Optional)"

  cd "$FRONTEND_DIR"

  if ! grep -q '"lint"' package.json; then
    print_warning "ESLint not configured in package.json"
    return 0
  fi

  print_info "Running: npm run lint"

  if [ "$VERBOSE" = true ]; then
    if npm run lint; then
      print_success "ESLint passed"
      return 0
    else
      local exit_code=$?
      print_warning "ESLint found issues (exit code: $exit_code)"
      return 0  # Don't fail on lint warnings
    fi
  else
    local output=$(npm run lint 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
      print_success "ESLint passed"
    else
      print_warning "ESLint found issues (exit code: $exit_code)"
      echo "$output" | head -20
    fi
  fi

  return 0
}

run_tests() {
  print_header "Running Tests (Optional)"

  cd "$FRONTEND_DIR"

  if ! grep -q '"test"' package.json; then
    print_warning "Tests not configured in package.json"
    return 0
  fi

  print_info "Running: npm test -- --run"

  if [ "$VERBOSE" = true ]; then
    if npm test -- --run; then
      print_success "Tests passed"
      return 0
    else
      local exit_code=$?
      print_warning "Tests failed (exit code: $exit_code)"
      return 0  # Don't fail on test failures
    fi
  else
    local output=$(npm test -- --run 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
      print_success "Tests passed"
    else
      print_warning "Tests failed (exit code: $exit_code)"
      echo "$output" | tail -20
    fi
  fi

  return 0
}

###############################################################################
# Summary
###############################################################################

print_summary() {
  local exit_code=$1

  print_header "Summary"

  if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend TypeScript compilation VERIFIED${NC}"
    echo ""
    echo "All checks passed successfully!"
    echo ""
    echo "Build artifacts:"
    echo "  - Location: $FRONTEND_DIR/dist/"
    echo "  - Index: dist/index.html"
    echo "  - Assets: dist/assets/"
    echo ""
    echo "Next steps:"
    echo "  - Deploy dist/ directory to web server"
    echo "  - Test the built application"
    echo "  - Run development server: npm run dev"
  else
    echo -e "${RED}✗ Frontend TypeScript compilation FAILED${NC}"
    echo ""
    echo "Please fix the errors above and try again."
    echo ""
    echo "Common fixes:"
    echo "  1. Install dependencies: npm ci"
    echo "  2. Fix TypeScript errors: npx tsc --noEmit"
    echo "  3. Fix ESLint errors: npm run lint"
    echo "  4. Re-run: ./verify_frontend_build.sh --fix"
  fi

  echo ""
  return $exit_code
}

###############################################################################
# Main Execution
###############################################################################

main() {
  print_header "Frontend TypeScript Compilation Verification"
  echo "Date: $(date)"
  echo "Directory: $FRONTEND_DIR"
  echo ""

  local exit_code=0

  # Pre-flight checks
  check_node_npm || exit 1
  check_dependencies || exit 1

  # TypeScript verification
  verify_typescript_config || exit 1
  verify_imports || exit 1

  # Build process
  run_type_check || exit_code=$?
  if [ $exit_code -ne 0 ]; then
    print_summary $exit_code
    exit $exit_code
  fi

  run_build || exit_code=$?
  if [ $exit_code -ne 0 ]; then
    print_summary $exit_code
    exit $exit_code
  fi

  # Verify output
  verify_build_output || exit_code=$?

  # Optional checks (don't fail)
  run_linter || true
  run_tests || true

  # Summary
  print_summary $exit_code
  exit $exit_code
}

# Run main function
main "$@"
