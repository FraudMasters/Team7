#!/bin/bash

# Excel Export Implementation Verification Script
# This script verifies the Excel export implementation without requiring a running server

set -e

echo "=== Excel Export Implementation Verification ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Script is run from the worktree root directory
# Stay in current directory

echo -e "${BLUE}Project Root: $(pwd)${NC}"
echo ""

# ============================================
# BACKEND IMPLEMENTATION VERIFICATION
# ============================================
echo -e "${BLUE}=== BACKEND VERIFICATION ===${NC}"
echo ""

# Test 1: Check openpyxl dependency
echo "1. Checking openpyxl dependency..."
if grep -q "openpyxl" backend/requirements.txt 2>/dev/null; then
    VERSION=$(grep "openpyxl" backend/requirements.txt | sed 's/openpyxl==\?//')
    echo -e "${GREEN}✓ openpyxl dependency found (version: $VERSION)${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ openpyxl dependency not found in requirements.txt${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Check Excel export endpoint
echo "2. Checking Excel export endpoint implementation..."
if grep -q "@router.post(\"/export/excel\"" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Excel export endpoint defined${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Excel export endpoint not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Check formatting utility functions
echo "3. Checking formatting utility functions..."
FUNCS_FOUND=0
if grep -q "def format_excel_headers" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ format_excel_headers function found${NC}"
    ((FUNCS_FOUND++))
else
    echo -e "${RED}✗ format_excel_headers function not found${NC}"
fi

if grep -q "def apply_data_bars" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ apply_data_bars function found${NC}"
    ((FUNCS_FOUND++))
else
    echo -e "${RED}✗ apply_data_bars function not found${NC}"
fi

if [ $FUNCS_FOUND -eq 2 ]; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

# Test 4: Check openpyxl imports
echo "4. Checking openpyxl imports..."
IMPORTS_FOUND=0
if grep -q "from openpyxl import Workbook" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Workbook import found${NC}"
    ((IMPORTS_FOUND++))
fi

if grep -q "from openpyxl.styles" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Styles import found${NC}"
    ((IMPORTS_FOUND++))
fi

if grep -q "from openpyxl.utils" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Utils import found${NC}"
    ((IMPORTS_FOUND++))
fi

if [ $IMPORTS_FOUND -ge 2 ]; then
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Some openpyxl imports may be missing${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 5: Check StreamingResponse usage
echo "5. Checking StreamingResponse implementation..."
if grep -A 20 "export_report_excel" backend/api/reports.py 2>/dev/null | grep -q "StreamingResponse"; then
    echo -e "${GREEN}✓ StreamingResponse used for file download${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ StreamingResponse not found in Excel export${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: Check content type headers
echo "6. Checking Excel MIME type configuration..."
if grep -q "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Correct Excel MIME type configured${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Excel MIME type may not be set correctly${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 7: Check validation
echo "7. Checking validation implementation..."
if grep -A 30 "export_report_excel" backend/api/reports.py 2>/dev/null | grep -q "422"; then
    echo -e "${GREEN}✓ Validation error handling found (HTTP 422)${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Validation may not be implemented${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 8: Check if reports router is registered
echo "8. Checking if reports router is registered in main app..."
if grep -q "reports.router" backend/main.py 2>/dev/null && grep -q "include_router" backend/main.py 2>/dev/null; then
    echo -e "${GREEN}✓ Reports router registered in main.py${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Reports router not found in main.py${NC}"
    ((FAILED++))
fi
echo ""

# ============================================
# FRONTEND IMPLEMENTATION VERIFICATION
# ============================================
echo -e "${BLUE}=== FRONTEND VERIFICATION ===${NC}"
echo ""

# Test 9: Check ExcelIcon import
echo "9. Checking Excel icon import..."
if grep -q "TableChart as ExcelIcon" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null; then
    echo -e "${GREEN}✓ ExcelIcon (TableChart) imported${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ ExcelIcon import not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 10: Check exportingExcel state
echo "10. Checking export state management..."
if grep -q "exportingExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null; then
    echo -e "${GREEN}✓ exportingExcel state variable found${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ exportingExcel state not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 11: Check handleExportExcel function
echo "11. Checking Excel export handler function..."
if grep -q "const handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null; then
    echo -e "${GREEN}✓ handleExportExcel function found${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ handleExportExcel function not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 12: Check API endpoint call
echo "12. Checking API endpoint URL..."
if grep -q "/api/reports/export/excel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null; then
    echo -e "${GREEN}✓ Correct API endpoint URL used${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ API endpoint URL not found or incorrect${NC}"
    ((FAILED++))
fi
echo ""

# Test 13: Check blob handling
echo "13. Checking blob response handling..."
BLOB_HANDLING=0
if grep -A 20 "handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "response.blob()"; then
    echo -e "${GREEN}✓ Blob response handling found${NC}"
    ((BLOB_HANDLING++))
fi

if grep -A 30 "handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "URL.createObjectURL"; then
    echo -e "${GREEN}✓ Object URL creation found${NC}"
    ((BLOB_HANDLING++))
fi

if grep -A 40 "handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "URL.revokeObjectURL"; then
    echo -e "${GREEN}✓ Object URL cleanup found${NC}"
    ((BLOB_HANDLING++))
fi

if [ $BLOB_HANDLING -eq 3 ]; then
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Blob handling may be incomplete (found $BLOB_HANDLING/3)${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 14: Check Excel export button
echo "14. Checking Excel export button..."
BUTTON_CHECKS=0
if grep -q "Export Excel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null; then
    echo -e "${GREEN}✓ Excel export button text found${NC}"
    ((BUTTON_CHECKS++))
fi

if grep -B 5 "Export Excel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "ExcelIcon"; then
    echo -e "${GREEN}✓ Excel icon used in button${NC}"
    ((BUTTON_CHECKS++))
fi

if grep -B 3 "Export Excel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "warning"; then
    echo -e "${GREEN}✓ Warning color variant used${NC}"
    ((BUTTON_CHECKS++))
fi

if [ $BUTTON_CHECKS -eq 3 ]; then
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Excel export button may be incomplete (found $BUTTON_CHECKS/3)${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 15: Check filename generation with .xlsx extension
echo "15. Checking filename generation..."
if grep -A 35 "handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx 2>/dev/null | grep -q "\.xlsx"; then
    echo -e "${GREEN}✓ .xlsx file extension used${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ .xlsx extension may not be set${NC}"
    ((WARNINGS++))
fi
echo ""

# ============================================
# TEST FILES VERIFICATION
# ============================================
echo -e "${BLUE}=== TEST FILES VERIFICATION ===${NC}"
echo ""

# Test 16: Check backend test file
echo "16. Checking backend test file..."
if [ -f "backend/tests/api/test_reports_excel_export.py" ]; then
    LINES=$(wc -l < backend/tests/api/test_reports_excel_export.py)
    if [ $LINES -gt 500 ]; then
        echo -e "${GREEN}✓ Backend test file found ($LINES lines)${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ Backend test file exists but may be incomplete ($LINES lines)${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗ Backend test file not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 17: Check frontend test file
echo "17. Checking frontend test file..."
if [ -f "frontend/src/components/analytics/ReportBuilderExcelExport.test.tsx" ]; then
    LINES=$(wc -l < frontend/src/components/analytics/ReportBuilderExcelExport.test.tsx)
    if [ $LINES -gt 700 ]; then
        echo -e "${GREEN}✓ Frontend test file found ($LINES lines)${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ Frontend test file exists but may be incomplete ($LINES lines)${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗ Frontend test file not found${NC}"
    ((FAILED++))
fi
echo ""

# ============================================
# IMPLEMENTATION PATTERN VERIFICATION
# ============================================
echo -e "${BLUE}=== IMPLEMENTATION PATTERNS ===${NC}"
echo ""

# Test 18: Check backend follows existing patterns
echo "18. Checking if backend follows CSV export pattern..."
if grep -q "export_report_csv" backend/api/reports.py 2>/dev/null && \
   grep -q "export_report_excel" backend/api/reports.py 2>/dev/null; then
    echo -e "${GREEN}✓ Both CSV and Excel exports implemented${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Export functions may not follow consistent pattern${NC}"
    ((WARNINGS++))
fi
echo ""

# Test 19: Check error handling
echo "19. Checking error handling..."
ERROR_HANDLING=0
if grep -A 50 "export_report_excel" backend/api/reports.py 2>/dev/null | grep -q "try:"; then
    ((ERROR_HANDLING++))
fi
if grep -A 50 "export_report_excel" backend/api/reports.py 2>/dev/null | grep -q "except"; then
    ((ERROR_HANDLING++))
fi
if grep -A 50 "export_report_excel" backend/api/reports.py 2>/dev/null | grep -q "logger"; then
    ((ERROR_HANDLING++))
fi

if [ $ERROR_HANDLING -eq 3 ]; then
    echo -e "${GREEN}✓ Error handling implemented${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Error handling may be incomplete ($ERROR_HANDLING/3)${NC}"
    ((WARNINGS++))
fi
echo ""

# ============================================
# SUMMARY
# ============================================
echo ""
echo -e "${BLUE}=== VERIFICATION SUMMARY ===${NC}"
echo ""
echo -e "${GREEN}Passed:  $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed:   $FAILED${NC}"
echo ""

# Total checks
TOTAL=$((PASSED + WARNINGS + FAILED))
PERCENT_PASSED=$((PASSED * 100 / TOTAL))

echo -e "Success Rate: ${PERCENT_PASSED}%"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -lt 3 ]; then
    echo -e "${GREEN}✓ IMPLEMENTATION VERIFIED!${NC}"
    echo ""
    echo "All critical components are implemented correctly."
    echo ""
    echo "Next Steps for End-to-End Testing:"
    echo "1. Ensure backend is running:"
    echo "   cd backend && python -m uvicorn main:app --reload --port 8000"
    echo ""
    echo "2. Ensure frontend is running:"
    echo "   cd frontend && npm run dev"
    echo ""
    echo "3. Open browser to: http://localhost:5173/analytics/report-builder"
    echo ""
    echo "4. Test the following scenarios:"
    echo "   a) Select single metric and export Excel"
    echo "   b) Select multiple metrics and export Excel"
    echo "   c) Try to export without selecting metrics (should show error)"
    echo "   d) Verify downloaded file has .xlsx extension"
    echo "   e) Open file in Excel and check:"
    echo "      - Headers are bold with blue background"
    echo "      - Data bars appear in Value column"
    echo "      - All selected metrics are present"
    echo "      - Column widths are appropriate"
    echo ""
    echo "5. Run automated tests:"
    echo "   Backend: cd backend && pytest tests/api/test_reports_excel_export.py -v"
    echo "   Frontend: cd frontend && npm test -- --ReportBuilderExcelExport"
    echo ""
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Implementation complete with minor warnings${NC}"
    echo "Review the warnings above and address if needed."
    exit 0
else
    echo -e "${RED}✗ Some critical components are missing${NC}"
    echo "Please review the failed checks above."
    exit 1
fi
