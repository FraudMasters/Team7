"""
Test script to verify bias alert notification template rendering.

This script tests the format_bias_alert_email function with sample data
to ensure the template renders correctly.
"""
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks.notifications import format_bias_alert_email


def test_bias_alert_template():
    """Test bias alert email formatting with sample data."""

    # Sample bias detection data
    bias_details = {
        "bias_type": "demographic_parity",
        "severity": "high",
        "detected_at": datetime.utcnow().isoformat(),
        "model_version": "v2.3.1",
        "fairness_metrics": {
            "Demographic Parity Difference": {
                "value": 0.15,
                "threshold": 0.10,
                "status": "failed"
            },
            "Equal Opportunity Difference": {
                "value": 0.08,
                "threshold": 0.10,
                "status": "passed"
            },
            "Disparate Impact": {
                "value": 0.72,
                "threshold": 0.80,
                "status": "failed"
            }
        },
        "protected_attributes": ["gender", "age", "race"],
        "impact_summary": "The model shows significant bias in candidate ranking favoring certain demographic groups.",
        "affected_predictions": 1234,
        "time_period": "Last 7 days"
    }

    model_name = "candidate_ranking"

    # Format the email
    email_result = format_bias_alert_email(model_name, bias_details)

    # Verify the email was formatted
    assert "subject" in email_result, "Email should have subject"
    assert "body" in email_result, "Email should have body"
    assert "priority" in email_result, "Email should have priority"

    # Verify content
    assert model_name in email_result["subject"], "Subject should contain model name"
    assert "Bias Detection Alert" in email_result["subject"], "Subject should mention bias detection"
    assert email_result["priority"] == "high", "High severity should result in high priority"

    # Verify body contains key information
    body = email_result["body"]
    assert "demographic_parity" in body.lower() or "demographic parity" in body.lower(), "Body should contain bias type"
    assert "HIGH" in body, "Body should show severity"
    assert "gender" in body.lower(), "Body should list protected attributes"
    assert "0.15" in body or "0.1500" in body, "Body should show metric values"

    # Print the formatted email for manual inspection
    print("=" * 80)
    print("BIAS ALERT EMAIL TEST")
    print("=" * 80)
    print(f"\nSubject: {email_result['subject']}")
    print(f"Priority: {email_result['priority']}")
    print("\nBody:")
    print("-" * 80)
    print(email_result['body'])
    print("-" * 80)
    print("\n✅ All assertions passed!")
    print("\n📧 Email template renders correctly with sample data")

    return True


def test_critical_severity():
    """Test with critical severity."""

    bias_details = {
        "bias_type": "equal_opportunity",
        "severity": "critical",
        "detected_at": datetime.utcnow().isoformat(),
        "model_version": "v3.0.0",
        "fairness_metrics": {
            "Equal Opportunity Difference": {
                "value": 0.35,
                "threshold": 0.10,
                "status": "failed"
            }
        },
        "protected_attributes": ["ethnicity"],
    }

    email_result = format_bias_alert_email("screening_model", bias_details)

    assert email_result["priority"] == "high", "Critical severity should result in high priority"
    assert "CRITICAL" in email_result["subject"] or "🚨" in email_result["subject"], "Critical should be in subject"

    print("\n" + "=" * 80)
    print("CRITICAL SEVERITY TEST")
    print("=" * 80)
    print(f"\nSubject: {email_result['subject']}")
    print(f"Priority: {email_result['priority']}")
    print("\n✅ Critical severity test passed!")

    return True


def test_low_severity():
    """Test with low severity."""

    bias_details = {
        "bias_type": "statistical_parity",
        "severity": "low",
        "detected_at": datetime.utcnow().isoformat(),
        "model_version": "v1.5.2",
        "fairness_metrics": {
            "Statistical Parity": {
                "value": 0.06,
                "threshold": 0.05,
                "status": "failed"
            }
        },
        "protected_attributes": ["age"],
    }

    email_result = format_bias_alert_email("recommendation_model", bias_details)

    assert email_result["priority"] == "normal", "Low severity should result in normal priority"

    print("\n" + "=" * 80)
    print("LOW SEVERITY TEST")
    print("=" * 80)
    print(f"\nSubject: {email_result['subject']}")
    print(f"Priority: {email_result['priority']}")
    print("\n✅ Low severity test passed!")

    return True


if __name__ == "__main__":
    try:
        # Run all tests
        test_bias_alert_template()
        test_critical_severity()
        test_low_severity()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Template verified successfully!")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
