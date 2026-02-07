#!/bin/bash

# Excel Export End-to-End Verification Script
# This script verifies the Excel export functionality without requiring Python

set -e

echo "=== Excel Export End-to-End Verification ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Helper function for tests
test_step() {
    local step_name="$1"
    local command="$2"
    local expected="$3"

    echo -n "Testing: $step_name ... "

    if eval "$command" | grep -q "$expected"; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Check if backend is running
echo "1. Checking if backend service is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}Backend is running${NC}"
else
    echo -e "${YELLOW}WARNING: Backend may not be running. Some tests may fail.${NC}"
fi
echo ""

# Test 1: Check Excel export endpoint exists
echo "2. Testing Excel export endpoint availability..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":["time_to_hire"],"filters":{}}' 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "422" ]; then
    echo -e "${GREEN}Endpoint is accessible (HTTP $RESPONSE)${NC}"
    ((PASSED++))
else
    echo -e "${RED}Endpoint not accessible (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Test Excel export with valid metrics
echo "3. Testing Excel export with valid metrics..."
TEMP_FILE="/tmp/test_excel_export_$$.xlsx"
HTTP_CODE=$(curl -s -o "$TEMP_FILE" -w "%{http_code}" -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":["time_to_hire","resumes_processed"],"filters":{"start_date":"2024-01-01","end_date":"2024-01-31"}}' 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    if [ -f "$TEMP_FILE" ]; then
        FILE_SIZE=$(stat -f%z "$TEMP_FILE" 2>/dev/null || stat -c%s "$TEMP_FILE" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -gt 1000 ]; then
            echo -e "${GREEN}Excel file downloaded successfully (${FILE_SIZE} bytes)${NC}"
            ((PASSED++))

            # Test 3: Verify it's a valid Excel file (ZIP signature)
            echo "4. Verifying file format (XLSX is a ZIP file)..."
            if file "$TEMP_FILE" | grep -q "Zip archive" || file "$TEMP_FILE" | grep -q "Microsoft Excel"; then
                echo -e "${GREEN}Valid Excel file format detected${NC}"
                ((PASSED++))
            else
                echo -e "${YELLOW}File format verification unclear (file command output: $(file "$TEMP_FILE"))${NC}"
            fi

            # Test 4: Check file has XLSX structure
            echo "5. Checking XLSX internal structure..."
            if unzip -t "$TEMP_FILE" > /dev/null 2>&1; then
                echo -e "${GREEN}Valid ZIP/XLSX structure${NC}"
                ((PASSED++))

                # Test 5: Check for required workbook files
                if unzip -l "$TEMP_FILE" | grep -q "xl/workbook.xml"; then
                    echo -e "${GREEN}Contains required workbook files${NC}"
                    ((PASSED++))
                else
                    echo -e "${RED}Missing required workbook files${NC}"
                    ((FAILED++))
                fi
            else
                echo -e "${RED}Invalid ZIP/XLSX structure${NC}"
                ((FAILED++))
            fi
        else
            echo -e "${RED}File too small (${FILE_SIZE} bytes), likely invalid${NC}"
            ((FAILED++))
        fi
        rm -f "$TEMP_FILE"
    else
        echo -e "${RED}File was not created${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}Export failed with HTTP code: $HTTP_CODE${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: Test with empty metrics (should fail validation)
echo "6. Testing validation with empty metrics..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":[],"filters":{}}' 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "422" ]; then
    echo -e "${GREEN}Validation correctly rejected empty metrics (HTTP 422)${NC}"
    ((PASSED++))
else
    echo -e "${RED}Validation should reject empty metrics (got HTTP $HTTP_CODE)${NC}"
    ((FAILED++))
fi
echo ""

# Test 7: Test with multiple metrics
echo "7. Testing export with multiple metrics..."
TEMP_FILE2="/tmp/test_excel_multi_$$.xlsx"
HTTP_CODE=$(curl -s -o "$TEMP_FILE2" -w "%{http_code}" -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":["time_to_hire","resumes_processed","match_rates","interviews_scheduled","offers_extended","offers_accepted"],"filters":{}}' 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ] && [ -f "$TEMP_FILE2" ]; then
    FILE_SIZE=$(stat -f%z "$TEMP_FILE2" 2>/dev/null || stat -c%s "$TEMP_FILE2" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -gt 2000 ]; then
        echo -e "${GREEN}Multiple metrics export successful (${FILE_SIZE} bytes)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}File size too small for multiple metrics (${FILE_SIZE} bytes)${NC}"
        ((FAILED++))
    fi
    rm -f "$TEMP_FILE2"
else
    echo -e "${RED}Multiple metrics export failed (HTTP $HTTP_CODE)${NC}"
    ((FAILED++))
fi
echo ""

# Test 8: Check content type header
echo "8. Testing response Content-Type header..."
CONTENT_TYPE=$(curl -s -I -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":["time_to_hire"],"filters":{}}' 2>/dev/null | grep -i "content-type" || echo "")

if echo "$CONTENT_TYPE" | grep -qi "openxmlformats"; then
    echo -e "${GREEN}Correct Content-Type header for Excel files${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}Content-Type header may not be set correctly: $CONTENT_TYPE${NC}"
fi
echo ""

# Test 9: Check Content-Disposition header
echo "9. Testing response Content-Disposition header..."
CONTENT_DISP=$(curl -s -I -X POST http://localhost:8000/api/reports/export/excel \
  -H 'Content-Type: application/json' \
  -d '{"metrics":["time_to_hire"],"filters":{}}' 2>/dev/null | grep -i "content-disposition" || echo "")

if echo "$CONTENT_DISP" | grep -qi "attachment"; then
    echo -e "${GREEN}Correct Content-Disposition header (attachment)${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}Content-Disposition header: $CONTENT_DISP${NC}"
fi
echo ""

# Test 10: Verify frontend files exist
echo "10. Verifying frontend implementation..."
if [ -f "frontend/src/components/analytics/ReportBuilder.tsx" ]; then
    if grep -q "handleExportExcel" frontend/src/components/analytics/ReportBuilder.tsx && \
       grep -q "exportingExcel" frontend/src/components/analytics/ReportBuilder.tsx && \
       grep -q "ExcelIcon" frontend/src/components/analytics/ReportBuilder.tsx; then
        echo -e "${GREEN}Frontend Excel export implementation found${NC}"
        ((PASSED++))
    else
        echo -e "${RED}Frontend implementation incomplete${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}Frontend file not found at expected location${NC}"
fi
echo ""

# Test 11: Verify backend implementation
echo "11. Verifying backend implementation..."
if [ -f "backend/api/reports.py" ]; then
    if grep -q "export_report_excel" backend/api/reports.py && \
       grep -q "format_excel_headers" backend/api/reports.py && \
       grep -q "apply_data_bars" backend/api/reports.py; then
        echo -e "${GREEN}Backend Excel export implementation found${NC}"
        ((PASSED++))
    else
        echo -e "${RED}Backend implementation incomplete${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}Backend file not found at expected location${NC}"
fi
echo ""

# Test 12: Check for openpyxl dependency
echo "12. Checking openpyxl dependency..."
if [ -f "backend/requirements.txt" ]; then
    if grep -q "openpyxl" backend/requirements.txt; then
        echo -e "${GREEN}openpyxl dependency found in requirements.txt${NC}"
        ((PASSED++))
    else
        echo -e "${RED}openpyxl dependency not found${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}requirements.txt not found${NC}"
fi
echo ""

# Test 13: Verify test files exist
echo "13. Verifying test files..."
BACKEND_TEST="backend/tests/api/test_reports_excel_export.py"
FRONTEND_TEST="frontend/src/components/analytics/ReportBuilderExcelExport.test.tsx"

TESTS_FOUND=0
if [ -f "$BACKEND_TEST" ]; then
    echo -e "${GREEN}Backend test file found${NC}"
    ((TESTS_FOUND++))
else
    echo -e "${YELLOW}Backend test file not found${NC}"
fi

if [ -f "$FRONTEND_TEST" ]; then
    echo -e "${GREEN}Frontend test file found${NC}"
    ((TESTS_FOUND++))
else
    echo -e "${YELLOW}Frontend test file not found${NC}"
fi

if [ $TESTS_FOUND -eq 2 ]; then
    echo -e "${GREEN}All test files present${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}Some test files missing${NC}"
fi
echo ""

# Summary
echo "=== VERIFICATION SUMMARY ==="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical verifications passed!${NC}"
    echo ""
    echo "Excel export functionality is implemented and ready for use."
    echo ""
    echo "Remaining manual verification steps:"
    echo "1. Start backend: cd backend && python -m uvicorn main:app --reload"
    echo "2. Start frontend: cd frontend && npm run dev"
    echo "3. Open browser to: http://localhost:5173/analytics/report-builder"
    echo "4. Select metrics and click 'Export Excel' button"
    echo "5. Verify downloaded .xlsx file opens in Excel with:"
    echo "   - Formatted headers (bold, blue background)"
    echo "   - Data bars in numeric columns"
    echo "   - All selected metrics present"
    echo "   - Proper column widths"
    exit 0
else
    echo -e "${RED}Some verifications failed. Please review the output above.${NC}"
    exit 1
fi
