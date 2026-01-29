#!/bin/bash
# Load test data (resumes and vacancies) into the application

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
TEST_DATA_DIR="${TEST_DATA_DIR:-./testdata/vacancy-resume-matching-dataset-main}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Loading Test Data${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if backend is running
echo -e "${YELLOW}Checking if backend is running...${NC}"
if ! curl -sf "${BACKEND_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}Backend is not running at ${BACKEND_URL}${NC}"
    echo "Please start the application first: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}Backend is running${NC}"
echo ""

# Check test data directory
if [ ! -d "$TEST_DATA_DIR" ]; then
    echo -e "${RED}Test data directory not found: $TEST_DATA_DIR${NC}"
    exit 1
fi

RESUME_DIR="$TEST_DATA_DIR/CV"
VACANCY_CSV="$TEST_DATA_DIR/5_vacancies.csv"

if [ ! -d "$RESUME_DIR" ]; then
    echo -e "${RED}Resume directory not found: $RESUME_DIR${NC}"
    exit 1
fi

if [ ! -f "$VACANCY_CSV" ]; then
    echo -e "${RED}Vacancy file not found: $VACANCY_CSV${NC}"
    exit 1
fi

# Count files
RESUME_COUNT=$(find "$RESUME_DIR" -name "*.docx" -o -name "*.pdf" | wc -l)
echo -e "${GREEN}Found $RESUME_COUNT resume files${NC}"

# 1. Upload Resumes
echo ""
echo -e "${YELLOW}[1/2] Uploading resumes...${NC}"

RESUME_UPLOADED=0
RESUME_FAILED=0

for resume in "$RESUME_DIR"/*.{docx,pdf,DOCX,PDF}; do
    # Check if file exists (glob may return pattern itself if no matches)
    [ -f "$resume" ] || continue

    filename=$(basename "$resume")
    echo -ne "   Uploading: $filename... "

    response=$(curl -s -X POST "${BACKEND_URL}/api/resumes/upload" \
        -F "file=@$resume" \
        -w "\n%{http_code}" 2>/dev/null)

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}OK${NC}"
        ((RESUME_UPLOADED++))
    else
        echo -e "${RED}FAILED ($http_code)${NC}"
        ((RESUME_FAILED++))
    fi

    # Small delay to avoid overwhelming the backend
    sleep 0.2
done

echo ""
echo -e "${GREEN}Resumes uploaded: $RESUME_UPLOADED${NC}"
if [ $RESUME_FAILED -gt 0 ]; then
    echo -e "${YELLOW}Resumes failed: $RESUME_FAILED${NC}"
fi
echo ""

# 2. Create Vacancies from CSV
echo -e "${YELLOW}[2/2] Creating vacancies from CSV...${NC}"

VACANCY_CREATED=0
VACANCY_FAILED=0

# Skip header and parse CSV
tail -n +2 "$VACANCY_CSV" | while IFS=',' read -r id job_description job_title uid rest; do
    # Remove quotes from fields
    job_title=$(echo "$job_title" | sed 's/^"//;s/"$//')
    job_description=$(echo "$job_description" | sed 's/^"//;s/"$//')

    # Create JSON payload
    json_payload=$(cat <<EOF
{
  "title": "$job_title",
  "description": "$job_description",
  "location": "Remote",
  "salary_min": 80000,
  "salary_max": 150000,
  "currency": "USD"
}
EOF
)

    echo -ne "   Creating: $job_title... "

    response=$(curl -s -X POST "${BACKEND_URL}/api/vacancies/" \
        -H "Content-Type: application/json" \
        -d "$json_payload" \
        -w "\n%{http_code}" 2>/dev/null)

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}OK${NC}"
        ((VACANCY_CREATED++))
    else
        echo -e "${RED}FAILED ($http_code)${NC}"
        ((VACANCY_FAILED++))
    fi

    sleep 0.2
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Test Data Loading Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Resumes uploaded: ${GREEN}$RESUME_UPLOADED${NC}"
echo "  - Vacancies created: ${GREEN}~5${NC} (from CSV)"
echo ""
echo "Next steps:"
echo "  - Open frontend: ${BLUE}http://localhost:5173${NC}"
echo "  - Browse resumes: ${BLUE}http://localhost:5173/resume-database${NC}"
echo "  - Browse vacancies: ${BLUE}http://localhost:5173/vacancies${NC}"
echo "  - Try matching: ${BLUE}http://localhost:5173/compare-vacancy${NC}"
echo ""
