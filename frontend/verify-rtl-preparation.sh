#!/bin/bash

# RTL Preparation Verification Script
#
# This script helps verify that the application is properly prepared
# for future RTL (Right-to-Left) language support (Arabic, Hebrew, etc.)
#
# Usage:
#   1. Start both backend and frontend servers
#   2. Open browser to http://localhost:5173
#   3. Run this script for step-by-step verification instructions

set -e

echo "================================"
echo "RTL Preparation Verification"
echo "================================"
echo ""

# Check if servers are running
echo "Checking server availability..."

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ Frontend server is running (http://localhost:5173)"
else
    echo "✗ Frontend server is NOT running"
    echo "  Please start it with: cd frontend && npm run dev"
    exit 1
fi

if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✓ Backend server is running (http://localhost:8000)"
else
    echo "⚠ Backend server is NOT running (optional for this test)"
fi

echo ""
echo "================================"
echo "Verification Steps"
echo "================================"
echo ""

# Step 1: Check initial dir attribute
echo "Step 1: Verify initial HTML dir attribute"
echo "  1. Open browser DevTools (F12 or Cmd+Option+I)"
echo "  2. Go to Elements/Inspector tab"
echo "  3. Find the <html> element"
echo "  4. Verify it has dir='ltr' attribute"
echo "  5. Verify it has lang='en' or lang='ru' attribute"
echo ""
read -p "Press Enter after verifying initial dir attribute..."

# Step 2: Switch language and verify dir updates
echo ""
echo "Step 2: Verify dir attribute updates on language switch"
echo "  1. Use the language switcher in the navigation bar"
echo "  2. Switch from English to Russian (or vice versa)"
echo "  3. Check the <html> element again"
echo "  4. Verify dir attribute is still 'ltr' (both EN and RU are LTR)"
echo ""
read -p "Press Enter after verifying dir attribute persists..."

# Step 3: Check CSS for RTL hooks
echo ""
echo "Step 3: Verify CSS has RTL preparation"
echo "  1. Open frontend/src/index.css in your editor"
echo "  2. Verify there is an RTL Support section with comments"
echo "  3. Verify the comments explain logical properties"
echo "  4. Check for examples like: margin-inline-start, text-align: start"
echo ""
read -p "Press Enter after verifying CSS RTL hooks..."

# Step 4: Verify LanguageContext has direction support
echo ""
echo "Step 4: Verify LanguageContext has direction field"
echo "  1. Open frontend/src/contexts/LanguageContext.tsx"
echo "  2. Verify LanguageConfig interface has 'direction: TextDirection' field"
echo "  3. Verify SUPPORTED_LANGUAGES has direction: 'ltr' for both en and ru"
echo "  4. Verify useEffect sets documentElement dir attribute"
echo ""
read -p "Press Enter after verifying LanguageContext..."

# Step 5: Test in browser console
echo ""
echo "Step 5: Test dir attribute via browser console"
echo "  1. Open browser DevTools Console"
echo "  2. Run: document.documentElement.getAttribute('dir')"
echo "  Expected output: 'ltr'"
echo "  3. Run: document.documentElement.getAttribute('lang')"
echo "  Expected output: 'en' or 'ru'"
echo "  4. Switch language using the UI"
echo "  5. Run: document.documentElement.getAttribute('lang')"
echo "  Expected output: updated to 'en' or 'ru'"
echo ""
read -p "Press Enter after console verification..."

# Summary
echo ""
echo "================================"
echo "Verification Summary"
echo "================================"
echo ""
echo "✓ RTL Preparation Checklist:"
echo ""
echo "  [✓] HTML dir attribute is set on page load"
echo "  [✓] HTML lang attribute is set on page load"
echo "  [✓] dir attribute updates when language changes"
echo "  [✓] lang attribute updates when language changes"
echo "  [✓] CSS includes RTL support documentation"
echo "  [✓] LanguageContext includes direction field"
echo "  [✓] LanguageConfig has direction: 'ltr' for en/ru"
echo "  [✓] useEffect manages dir attribute on language change"
echo ""
echo "Future RTL Support:"
echo "  • To add Arabic (ar): Set direction: 'rtl' in SUPPORTED_LANGUAGES"
echo "  • To add Hebrew (he): Set direction: 'rtl' in SUPPORTED_LANGUAGES"
echo "  • CSS logical properties will automatically flip layout"
echo "  • Use [dir=\"rtl\"] selectors for RTL-specific overrides"
echo ""
echo "================================"
echo "Verification Complete!"
echo "================================"
