#!/bin/bash
# Скрипт для сканирования безопасности микросервисов
# Security scan script for microservices

set -e

echo "Starting security scan for microservices..."
echo "=========================================="

# Run bandit on all microservices
echo "Running bandit security scanner..."
bandit -r services/ -f json -o security-report.json || true

# Also scan backend directory
echo "Scanning backend directory..."
bandit -r backend/ -f json -o backend-security-report.json || true

# Check results
echo ""
echo "=========================================="
echo "Security scan complete!"
echo "Reports saved:"
echo "  - security-report.json (services)"
echo "  - backend-security-report.json (backend)"
echo ""
echo "To view full results:"
echo "  cat security-report.json | jq '.results'"
echo ""
echo "To check for high severity issues:"
echo "  bandit -r services/ -f json | grep -q 'no high severity issues' && echo 'Security scan passed'"

# Exit with error if high severity issues found
if grep -q '"severity": "HIGH"' security-report.json 2>/dev/null; then
    echo ""
    echo "❌ HIGH SEVERITY ISSUES FOUND!"
    exit 1
else
    echo ""
    echo "✓ No high severity issues detected"
    exit 0
fi
