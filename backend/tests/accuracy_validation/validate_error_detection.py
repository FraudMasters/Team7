#!/usr/bin/env python3
"""
Error Detection Accuracy Validation Script

This script validates the accuracy of the error detection system by running
it on a test dataset of 20 resumes with known errors (ground truth).

Target: 80%+ accuracy

Usage:
    python tests/accuracy_validation/validate_error_detection.py

Output:
    - Console output with detailed metrics
    - JSON report file with results
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load the test dataset from JSON file."""
    logger.info(f"Loading test dataset from {dataset_path}")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        logger.info(f"Loaded {dataset['summary']['total_resumes']} test resumes")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def import_error_detector() -> Any:
    """Import the error detector module."""
    try:
        # Add backend to path if needed
        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        from analyzers.error_detector import detect_resume_errors
        logger.info("Successfully imported error detector")
        return detect_resume_errors
    except ImportError as e:
        logger.error(f"Failed to import error detector: {e}")
        raise


def normalize_error_type(error_type: str) -> str:
    """Normalize error type names for comparison."""
    # Map variations to standard names
    mappings = {
        'missing_email': 'missing_email',
        'missing_phone': 'missing_phone',
        'invalid_email': 'invalid_email_format',
        'invalid_email_format': 'invalid_email_format',
        'resume_too_short': 'resume_too_short',
        'resume_too_long': 'resume_too_long',
        'missing_portfolio': 'missing_portfolio',
        'suggest_portfolio': 'suggest_portfolio',
        'missing_skills': 'missing_skills_section',
        'missing_skills_section': 'missing_skills_section',
        'missing_experience': 'missing_experience_section',
        'missing_experience_section': 'missing_experience_section',
        'missing_education': 'missing_education_section',
        'missing_education_section': 'missing_education_section',
    }
    return mappings.get(error_type.lower().replace('-', '_'), error_type.lower())


def compare_errors(
    detected_errors: List[Dict[str, Any]],
    expected_errors: List[Dict[str, Any]]
) -> Tuple[int, int, int, int, List[str]]:
    """
    Compare detected errors with expected errors.

    Returns:
        Tuple of (true_positives, false_positives, false_negatives, true_negatives, mismatches)
    """
    detected_types = set()
    for error in detected_errors:
        error_type = normalize_error_type(error.get('type', ''))
        detected_types.add(error_type)

    expected_types = set()
    for error in expected_errors:
        error_type = normalize_error_type(error.get('type', ''))
        expected_types.add(error_type)

    true_positives = len(detected_types & expected_types)
    false_positives = len(detected_types - expected_types)
    false_negatives = len(expected_types - detected_types)

    # True negatives are tricky - we consider expected errors that weren't detected
    # as false negatives, and errors we didn't expect but detected as false positives
    # True negatives would be errors we correctly didn't detect (hard to count)
    true_negatives = 0  # Not applicable for error detection

    mismatches = []
    if false_positives > 0:
        mismatches.append(f"False positives: {detected_types - expected_types}")
    if false_negatives > 0:
        mismatches.append(f"False negatives: {expected_types - detected_types}")

    return true_positives, false_positives, false_negatives, true_negatives, mismatches


def calculate_metrics(
    total_true_positives: int,
    total_false_positives: int,
    total_false_negatives: int,
    total_test_cases: int
) -> Dict[str, float]:
    """Calculate accuracy metrics."""
    precision = 0.0
    recall = 0.0
    f1 = 0.0
    accuracy = 0.0

    if total_true_positives + total_false_positives > 0:
        precision = total_true_positives / (total_true_positives + total_false_positives)

    if total_true_positives + total_false_negatives > 0:
        recall = total_true_positives / (total_true_positives + total_false_negatives)

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)

    if total_test_cases > 0:
        accuracy = total_true_positives / total_test_cases

    return {
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1_score': round(f1 * 100, 2),
        'accuracy': round(accuracy * 100, 2)
    }


def validate_resume(
    detect_resume_errors: Any,
    resume: Dict[str, Any],
    index: int
) -> Dict[str, Any]:
    """Validate a single resume against expected errors."""
    logger.info(f"[{index+1}/20] Validating {resume['id']}: {resume['name']}")

    try:
        # Run error detection
        result = detect_resume_errors(
            resume['resume_text'],
            resume.get('resume_data')
        )

        detected_errors = result.get('errors', [])
        expected_errors = resume.get('expected_errors', [])

        # Compare errors
        tp, fp, fn, tn, mismatches = compare_errors(detected_errors, expected_errors)

        return {
            'id': resume['id'],
            'name': resume['name'],
            'detected_count': len(detected_errors),
            'expected_count': resume.get('expected_error_count', len(expected_errors)),
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'true_negatives': tn,
            'mismatches': mismatches,
            'detected_errors': [e['type'] for e in detected_errors],
            'expected_errors': [e['type'] for e in expected_errors],
            'passed': fp == 0 and fn == 0
        }

    except Exception as e:
        logger.error(f"Error validating {resume['id']}: {e}")
        return {
            'id': resume['id'],
            'name': resume['name'],
            'error': str(e),
            'passed': False
        }


def generate_report(
    results: List[Dict[str, Any]],
    metrics: Dict[str, float],
    target_accuracy: float
) -> Dict[str, Any]:
    """Generate validation report."""
    passed = sum(1 for r in results if r.get('passed', False))
    failed = len(results) - passed

    report = {
        'validation_date': datetime.now().isoformat(),
        'target_accuracy': target_accuracy,
        'target_met': metrics['accuracy'] >= target_accuracy,
        'metrics': metrics,
        'summary': {
            'total_resumes': len(results),
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / len(results)) * 100, 2)
        },
        'detailed_results': results,
        'recommendations': []
    }

    # Generate recommendations
    if metrics['accuracy'] < target_accuracy:
        report['recommendations'].append(
            f"Accuracy ({metrics['accuracy']}%) is below target ({target_accuracy}%). "
            "Review error detection logic and test cases."
        )

    if metrics['recall'] < 85:
        report['recommendations'].append(
            f"Recall ({metrics['recall']}%) is low. Some errors are being missed. "
            "Review error detection rules."
        )

    if metrics['precision'] < 85:
        report['recommendations'].append(
            f"Precision ({metrics['precision']}%) is low. Too many false positives. "
            "Review error detection thresholds."
        )

    if failed > 0:
        failed_cases = [r for r in results if not r.get('passed', False)]
        report['failed_cases'] = [
            {'id': r['id'], 'name': r['name'], 'mismatches': r.get('mismatches', [])}
            for r in failed_cases
        ]

    return report


def print_console_report(report: Dict[str, Any]):
    """Print formatted report to console."""
    print("\n" + "=" * 80)
    print("ERROR DETECTION ACCURACY VALIDATION REPORT")
    print("=" * 80 + "\n")

    # Summary
    print(f"Validation Date: {report['validation_date']}")
    print(f"Target Accuracy: {report['target_accuracy']}%")
    print(f"Target Met: {'✓ YES' if report['target_met'] else '✗ NO'}")
    print()

    # Metrics
    print("METRICS:")
    print(f"  Accuracy:    {report['metrics']['accuracy']}%")
    print(f"  Precision:   {report['metrics']['precision']}%")
    print(f"  Recall:      {report['metrics']['recall']}%")
    print(f"  F1 Score:    {report['metrics']['f1_score']}%")
    print()

    # Summary
    summary = report['summary']
    print("SUMMARY:")
    print(f"  Total Resumes:     {summary['total_resumes']}")
    print(f"  Passed:            {summary['passed']}")
    print(f"  Failed:            {summary['failed']}")
    print(f"  Pass Rate:         {summary['pass_rate']}%")
    print()

    # Failed Cases
    if report.get('failed_cases'):
        print("FAILED CASES:")
        for case in report['failed_cases'][:5]:  # Show first 5
            print(f"  ✗ {case['id']}: {case['name']}")
            if case.get('mismatches'):
                for mismatch in case['mismatches']:
                    print(f"    - {mismatch}")
        print()

    # Recommendations
    if report.get('recommendations'):
        print("RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        print()

    print("=" * 80)
    print()


def save_report(report: Dict[str, Any], output_path: str):
    """Save report to JSON file."""
    logger.info(f"Saving report to {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info("Report saved successfully")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")


def main():
    """Main validation function."""
    print("\n" + "=" * 80)
    print("ERROR DETECTION ACCURACY VALIDATION")
    print("=" * 80 + "\n")

    # Configuration
    dataset_path = Path(__file__).parent / 'test_resumes.json'
    output_path = Path(__file__).parent / 'validation_report.json'
    target_accuracy = 80.0

    # Load dataset
    dataset = load_test_dataset(str(dataset_path))

    # Import error detector
    detect_resume_errors = import_error_detector()

    # Validate all resumes
    results = []
    for index, resume in enumerate(dataset['resumes']):
        result = validate_resume(detect_resume_errors, resume, index)
        results.append(result)

    # Calculate metrics
    total_tp = sum(r.get('true_positives', 0) for r in results)
    total_fp = sum(r.get('false_positives', 0) for r in results)
    total_fn = sum(r.get('false_negatives', 0) for r in results)

    # Total test cases = total expected errors across all resumes
    total_test_cases = sum(r.get('expected_count', 0) for r in results)

    metrics = calculate_metrics(total_tp, total_fp, total_fn, total_test_cases)

    # Generate report
    report = generate_report(results, metrics, target_accuracy)

    # Print to console
    print_console_report(report)

    # Save to file
    save_report(report, str(output_path))

    # Exit with appropriate code
    if report['target_met']:
        print("✓ Validation PASSED - Accuracy target met!")
        return 0
    else:
        print("✗ Validation FAILED - Accuracy target not met!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
