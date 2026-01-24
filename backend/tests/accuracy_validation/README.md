# Error Detection Accuracy Validation

This directory contains the accuracy validation framework for the error detection system.

## Purpose

Validate that the error detection system achieves **80%+ accuracy** on a test dataset of 20 resumes with known errors (ground truth).

## Files

- **test_resumes.json** - Test dataset with 20 resumes and expected errors
- **validate_error_detection.py** - Validation script that runs error detection and calculates metrics
- **validation_report.json** - Generated report (after running validation)
- **README.md** - This file

## Usage

### Run Validation

```bash
cd backend
python tests/accuracy_validation/validate_error_detection.py
```

### Expected Output

The script will:
1. Load 20 test resumes from `test_resumes.json`
2. Run error detection on each resume
3. Compare detected errors with expected errors (ground truth)
4. Calculate accuracy metrics (precision, recall, F1, accuracy)
5. Display results to console
6. Save detailed report to `validation_report.json`

## Metrics

### Accuracy

```
Accuracy = True Positives / Total Test Cases
```

Where:
- **True Positives**: Errors correctly detected
- **False Positives**: Errors detected but not expected
- **False Negatives**: Expected errors not detected

### Target

- **Minimum Accuracy**: 80%
- **Recommended Precision**: 85%+ (avoid false positives)
- **Recommended Recall**: 85%+ (avoid missing errors)

## Test Dataset

The test dataset includes 20 resumes covering various scenarios:

| Category | Count | Examples |
|----------|-------|----------|
| Perfect Resumes (No Errors) | 8 | Senior dev with all sections, entry-level with portfolio |
| Contact Issues | 4 | Missing email, missing phone, invalid email format |
| Length Issues | 2 | Too short, too long |
| Missing Sections | 4 | Missing skills, experience, education |
| Portfolio Issues | 2 | Entry-level missing portfolio |

### Error Types Detected

1. **Contact Errors** (Critical/Warning)
   - Missing email (critical)
   - Missing phone (warning)
   - Invalid email format (critical)

2. **Length Errors** (Warning)
   - Resume too short (< 500 chars)
   - Resume too long (> 10000 chars)

3. **Section Errors** (Critical/Warning/Info)
   - Missing skills section (critical)
   - Missing experience section (critical)
   - Missing education section (info)

4. **Portfolio Errors** (Warning/Info)
   - Missing portfolio for entry-level (warning)
   - Suggest portfolio for mid-level (info)

## Interpreting Results

### Success Criteria

```
✓ PASSED if accuracy >= 80%
✗ FAILED if accuracy < 80%
```

### Improving Accuracy

If validation fails:

1. **Low Recall (< 85%)**: Errors are being missed
   - Review error detection rules in `analyzers/error_detector.py`
   - Add or adjust detection logic for missing error types
   - Check regex patterns and validation logic

2. **Low Precision (< 85%)**: Too many false positives
   - Adjust thresholds (e.g., min/max length)
   - Make error detection more specific
   - Review edge cases

3. **Specific Test Failures**:
   - Review `failed_cases` in validation report
   - Manually check each failed resume
   - Update expected errors if ground truth is incorrect
   - Fix detection logic if errors are legitimate

## Example Report

```json
{
  "validation_date": "2026-01-24T12:00:00",
  "target_accuracy": 80.0,
  "target_met": true,
  "metrics": {
    "accuracy": 85.5,
    "precision": 88.2,
    "recall": 87.5,
    "f1_score": 87.8
  },
  "summary": {
    "total_resumes": 20,
    "passed": 18,
    "failed": 2,
    "pass_rate": 90.0
  }
}
```

## Continuous Validation

Run this validation:
- After modifying error detection logic
- Before deploying to production
- As part of CI/CD pipeline
- When adding new error types

## Integration with QA

This validation script is part of **subtask-7-4** (Error Detection Accuracy Validation).

Results should be documented in:
1. `validation_report.json` (machine-readable)
2. `build-progress.txt` (manual notes)
3. QA sign-off in `implementation_plan.json`

## Notes

- Test dataset represents common real-world scenarios
- Ground truth errors are manually verified
- Validation is deterministic (same inputs = same outputs)
- Can be automated in CI/CD pipeline
