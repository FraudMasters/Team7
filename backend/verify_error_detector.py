#!/usr/bin/env python3
"""
Verification script for error_detector module.

This script verifies that the error_detector module is correctly implemented
by testing key functionality.

Note: This script is for documentation purposes. Actual test execution is
blocked by system policy preventing Python commands.
"""

def verify_imports():
    """Verify that error_detector functions can be imported."""
    print("✓ Checking imports...")
    try:
        from analyzers.error_detector import (
            detect_resume_errors,
            get_error_summary,
            format_errors_for_display,
        )
        print("  ✓ All main functions can be imported")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def verify_constants():
    """Verify that constants are defined correctly."""
    print("✓ Checking constants...")
    from analyzers.error_detector import (
        MAX_RESUME_LENGTH_CHARS,
        MIN_RESUME_LENGTH_CHARS,
        ENTRY_LEVEL_EXPERIENCE_MONTHS,
    )

    assert MAX_RESUME_LENGTH_CHARS == 10000, "MAX_RESUME_LENGTH_CHARS should be 10000"
    assert MIN_RESUME_LENGTH_CHARS == 500, "MIN_RESUME_LENGTH_CHARS should be 500"
    assert ENTRY_LEVEL_EXPERIENCE_MONTHS == 12, "ENTRY_LEVEL_EXPERIENCE_MONTHS should be 12"

    print("  ✓ All constants are correctly defined")
    return True


def test_detect_resume_errors_basic():
    """Test basic error detection functionality."""
    print("✓ Testing detect_resume_errors basic functionality...")
    from analyzers.error_detector import detect_resume_errors

    # Test with minimal resume
    text = "Short resume"
    result = detect_resume_errors(text)

    assert "errors" in result, "Result should have 'errors' key"
    assert "total_errors" in result, "Result should have 'total_errors' key"
    assert "critical_count" in result, "Result should have 'critical_count' key"
    assert "warning_count" in result, "Result should have 'warning_count' key"
    assert "info_count" in result, "Result should have 'info_count' key"
    assert "error" in result, "Result should have 'error' key"

    print("  ✓ detect_resume_errors returns correct structure")
    return True


def test_missing_email_detection():
    """Test that missing email is detected."""
    print("✓ Testing missing email detection...")
    from analyzers.error_detector import detect_resume_errors

    text = "John Doe\nSoftware Developer"
    result = detect_resume_errors(text)

    # Should detect missing email
    email_errors = [e for e in result["errors"] if e["type"] == "missing_email"]
    assert len(email_errors) > 0, "Should detect missing email"
    assert email_errors[0]["severity"] == "critical", "Missing email should be critical"

    print("  ✓ Missing email detected correctly")
    return True


def test_resume_length_detection():
    """Test that resume length issues are detected."""
    print("✓ Testing resume length detection...")
    from analyzers.error_detector import detect_resume_errors, MAX_RESUME_LENGTH_CHARS

    # Too long
    long_text = "x" * (MAX_RESUME_LENGTH_CHARS + 1000)
    result = detect_resume_errors(long_text)
    length_errors = [e for e in result["errors"] if e["type"] == "resume_too_long"]
    assert len(length_errors) > 0, "Should detect resume too long"

    # Too short
    short_text = "x" * 100
    result = detect_resume_errors(short_text)
    short_errors = [e for e in result["errors"] if e["type"] == "resume_too_short"]
    assert len(short_errors) > 0, "Should detect resume too short"

    print("  ✓ Resume length issues detected correctly")
    return True


def test_portfolio_requirement():
    """Test portfolio requirement for entry-level candidates."""
    print("✓ Testing portfolio requirement for entry-level...")
    from analyzers.error_detector import detect_resume_errors

    text = "Junior developer"
    data = {"total_experience_months": 6}  # Less than 1 year
    result = detect_resume_errors(text, data)

    # Should suggest portfolio for entry-level
    portfolio_errors = [e for e in result["errors"] if e["type"] == "missing_portfolio"]
    assert len(portfolio_errors) > 0, "Should suggest portfolio for entry-level"

    # With portfolio, should not error
    data_with_portfolio = {
        "total_experience_months": 6,
        "portfolio": ["github.com/johndoe"]
    }
    result = detect_resume_errors(text, data_with_portfolio)
    portfolio_errors = [e for e in result["errors"] if e["type"] == "missing_portfolio"]
    assert len(portfolio_errors) == 0, "Should not error with portfolio"

    print("  ✓ Portfolio requirement checked correctly")
    return True


def test_missing_sections():
    """Test that missing sections are detected."""
    print("✓ Testing missing sections detection...")
    from analyzers.error_detector import detect_resume_errors

    text = "John Doe\nSome random text"
    result = detect_resume_errors(text)

    # Should detect missing skills and experience (both critical)
    skills_errors = [e for e in result["errors"] if e["type"] == "missing_skills_section"]
    exp_errors = [e for e in result["errors"] if e["type"] == "missing_experience_section"]

    assert len(skills_errors) > 0, "Should detect missing skills"
    assert len(exp_errors) > 0, "Should detect missing experience"
    assert skills_errors[0]["severity"] == "critical", "Missing skills should be critical"
    assert exp_errors[0]["severity"] == "critical", "Missing experience should be critical"

    print("  ✓ Missing sections detected correctly")
    return True


def test_error_summary():
    """Test error summary functionality."""
    print("✓ Testing error summary...")
    from analyzers.error_detector import get_error_summary

    errors = [
        {"type": "missing_email", "severity": "critical", "category": "contact"},
        {"type": "missing_phone", "severity": "warning", "category": "contact"},
        {"type": "resume_too_long", "severity": "warning", "category": "length"}
    ]

    summary = get_error_summary(errors)

    assert summary["total"] == 3, "Total should be 3"
    assert "contact" in summary["by_category"], "Should have contact category"
    assert "length" in summary["by_category"], "Should have length category"
    assert len(summary["by_severity"]["critical"]) == 1, "Should have 1 critical"
    assert len(summary["by_severity"]["warning"]) == 2, "Should have 2 warnings"

    print("  ✓ Error summary calculated correctly")
    return True


def test_format_errors():
    """Test error formatting for display."""
    print("✓ Testing error formatting...")
    from analyzers.error_detector import format_errors_for_display

    errors = [
        {
            "type": "missing_email",
            "severity": "critical",
            "message": "Email is missing",
            "suggestions": ["Add email"]
        }
    ]

    formatted = format_errors_for_display(errors)

    assert "RESUME ERROR REPORT" in formatted, "Should have report title"
    assert "Email is missing" in formatted, "Should show error message"
    assert "CRITICAL ISSUES" in formatted, "Should show critical section"
    assert "Add email" in formatted, "Should show suggestions"

    print("  ✓ Errors formatted correctly for display")
    return True


def test_valid_resume():
    """Test that valid resume passes all checks."""
    print("✓ Testing valid resume...")
    from analyzers.error_detector import detect_resume_errors

    text = """
    John Doe
    Email: john@example.com
    Phone: 555-123-4567
    LinkedIn: linkedin.com/in/johndoe

    Skills: Python, Java

    Experience: Software Developer

    Education: BS Computer Science
    """

    data = {
        "contact": {
            "email": "john@example.com",
            "phone": "555-123-4567"
        },
        "total_experience_months": 60,
        "portfolio": ["github.com/john"]
    }

    result = detect_resume_errors(text, data)

    # Should have minimal errors (maybe info about LinkedIn)
    assert result["critical_count"] == 0, "Valid resume should have no critical errors"

    print("  ✓ Valid resume passes critical checks")
    return True


def main():
    """Run all verification tests."""
    print("=" * 80)
    print("ERROR DETECTOR VERIFICATION")
    print("=" * 80)
    print()

    tests = [
        verify_imports,
        verify_constants,
        test_detect_resume_errors_basic,
        test_missing_email_detection,
        test_resume_length_detection,
        test_portfolio_requirement,
        test_missing_sections,
        test_error_summary,
        test_format_errors,
        test_valid_resume,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            failed += 1
        print()

    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
