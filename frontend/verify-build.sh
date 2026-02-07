#!/bin/bash

# Build Verification Script for Route-based Code Splitting
# This script verifies the production build and analyzes bundle splitting results
# Task 090 - Subtask 5-1

set -e  # Exit on error

echo "========================================"
echo "Build Verification - Route-based Code Splitting"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Clean previous build
echo -e "${BLUE}Step 1: Cleaning previous build...${NC}"
if [ -d "dist" ]; then
    rm -rf dist
    echo -e "${GREEN}✓ Removed dist directory${NC}"
else
    echo -e "${YELLOW}No dist directory found, skipping clean${NC}"
fi
echo ""

# Step 2: Build production bundle
echo -e "${BLUE}Step 2: Building production bundle...${NC}"
npm run build
echo ""

# Step 3: Analyze bundle structure
echo -e "${BLUE}Step 3: Analyzing bundle structure...${NC}"
echo ""

# Count total JS files
TOTAL_JS=$(ls -1 dist/assets/js/*.js 2>/dev/null | wc -l | tr -d ' ')
echo -e "Total JavaScript files: ${GREEN}${TOTAL_JS}${NC}"

# Check initial bundle size
INITIAL_BUNDLE=$(ls -lh dist/assets/js/index-*.js 2>/dev/null | awk '{print $5}')
echo -e "Initial bundle (index.js): ${GREEN}${INITIAL_BUNDLE}${NC}"

# List route chunks
echo ""
echo -e "${BLUE}Route-specific chunks:${NC}"
ls -lh dist/assets/js/*.js | grep -E "(LandingPage|JobsBrowse|JobDetail|Dashboard|Vacancies|ApplicationFlow|SavedJobs|MyApplications|CandidateProfile|ResumeUpload|ResumeResults|RecommendedJobs|SkillAssessment|Learning|SalaryCalculator|InterviewTips|JobAlerts|Settings|CandidatesKanban|Search|SavedSearches|VacancyForm|VacancyDetail|CandidateDetail|Weights|Compare|SkillGapAnalysis|Backups|WorkflowBoard|Upload|BatchUpload|Applications|ResumeDatabase|AnalyticsDashboard|Results)" | awk '{print "  " $9 " - " $5}' || echo "  (none found yet)"

# List vendor chunks
echo ""
echo -e "${BLUE}Vendor chunks:${NC}"
ls -lh dist/assets/js/*-vendor-*.js 2>/dev/null | awk '{print "  " $9 " - " $5}' || echo "  (none found)"

# Count route chunks
ROUTE_CHUNKS=$(ls -1 dist/assets/js/*.js 2>/dev/null | grep -v vendor | grep -v index | wc -l | tr -d ' ')
echo ""
echo -e "Route-specific chunks: ${GREEN}${ROUTE_CHUNKS}${NC}"

# Step 4: Verify expected criteria
echo ""
echo -e "${BLUE}Step 4: Verifying success criteria...${NC}"
echo ""

# Check initial bundle size (expecting < 200KB)
INITIAL_SIZE_BYTES=$(du -b dist/assets/js/index-*.js 2>/dev/null | cut -f1)
INITIAL_SIZE_KB=$((INITIAL_SIZE_BYTES / 1024))
if [ $INITIAL_SIZE_KB -lt 200 ]; then
    echo -e "${GREEN}✓ Initial bundle size: ${INITIAL_SIZE_KB}KB (< 200KB)${NC}"
else
    echo -e "${RED}✗ Initial bundle size: ${INITIAL_SIZE_KB}KB (expected < 200KB)${NC}"
fi

# Check route chunks count (expecting 35-40)
if [ $ROUTE_CHUNKS -ge 35 ] && [ $ROUTE_CHUNKS -le 40 ]; then
    echo -e "${GREEN}✓ Route chunks generated: ${ROUTE_CHUNKS} (expected 35-40)${NC}"
else
    echo -e "${YELLOW}⚠ Route chunks generated: ${ROUTE_CHUNKS} (expected 35-40)${NC}"
fi

# Check vendor chunks
VENDOR_CHUNKS=$(ls -1 dist/assets/js/*-vendor-*.js 2>/dev/null | wc -l | tr -d ' ')
if [ $VENDOR_CHUNKS -ge 6 ]; then
    echo -e "${GREEN}✓ Vendor chunks separated: ${VENDOR_CHUNKS} chunks${NC}"
else
    echo -e "${YELLOW}⚠ Vendor chunks: ${VENDOR_CHUNKS} (expected 6+)${NC}"
fi

# Step 5: List all chunks by size
echo ""
echo -e "${BLUE}Step 5: All chunks sorted by size:${NC}"
echo ""
du -h dist/assets/js/*.js 2>/dev/null | sort -h | awk '{printf "  %-60s %s\n", $2, $1}'

echo ""
echo "========================================"
echo -e "${GREEN}Build verification complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review the bundle sizes above"
echo "  2. Run unit tests: npm run test:coverage"
echo "  3. Run E2E tests: npm run test:e2e"
echo "  4. Test in browser at: http://localhost:5173"
echo ""
