# Skill Matching Accuracy Validation

## Overview

This validation framework tests the accuracy of the skill matching system by comparing extracted resume skills against job vacancy requirements. The system uses a test dataset of 20 resume-vacancy pairs with known ground truth matches.

## Target Accuracy

**Minimum Required: 90% accuracy**

The skill matching system must correctly identify at least 90% of expected skill matches (true positives) across all test cases.

## Test Dataset

### Statistics

- **Total Pairs:** 20 resume-vacancy pairs
- **Total Expected Matches:** 118 skill matches
- **Unique Skills Tested:** 45 different skills
- **Synonym Matches Tested:** 15 synonym variations

### Test Coverage

The dataset includes:

1. **Perfect Match Scenarios** (8 pairs)
   - All required and additional skills present in resume
   - Examples: Java Developer, DevOps Engineer, QA Engineer

2. **Partial Match Scenarios** (6 pairs)
   - Some skills missing from resume
   - Examples: Python Developer missing Django/FastAPI
   - Examples: .NET Developer missing Entity Framework

3. **Synonym Match Scenarios** (10 pairs)
   - Testing skill synonym recognition
   - Examples:
     - ReactJS → React
     - PostgreSQL → SQL
     - AngularJS → Angular
     - Vue.js → Vue
     - Spring Boot → Spring
     - TS → TypeScript

4. **No Match Scenarios** (1 pair)
   - Completely wrong skill set (e.g., Python dev applying for Go role)

5. **Edge Cases** (2 pairs)
   - Entry-level developers with minimal skills
   - Mixed match scenarios (some present, some missing)

## Metrics Calculated

### Primary Metrics

1. **Accuracy** (Most Important)
   - Formula: `True Positives / Total Expected Matches × 100`
   - Measures: How many expected skills were correctly identified
   - Target: ≥90%

2. **Precision**
   - Formula: `True Positives / (True Positives + False Positives) × 100`
   - Measures: Of skills detected as matched, how many were correct
   - Target: ≥90%

3. **Recall**
   - Formula: `True Positives / (True Positives + False Negatives) × 100`
   - Measures: Of expected matches, how many were detected
   - Target: ≥90%

4. **F1 Score**
   - Formula: `2 × (Precision × Recall) / (Precision + Recall)`
   - Measures: Harmonic mean of precision and recall
   - Target: ≥90%

### Error Types

- **True Positive (TP):** Correctly identified a skill as matched
- **False Positive (FP):** Incorrectly identified a skill as matched (should be missing)
- **False Negative (FN):** Failed to identify a skill as matched (should be present)

## Usage

### Running Validation

```bash
cd backend
python tests/accuracy_validation/validate_skill_matching.py
```

### Expected Output

1. **Console Output**
   - Summary metrics (accuracy, precision, recall, F1)
   - Pass/fail status
   - List of failed cases with mismatches
   - Recommendations if failed

2. **JSON Report** (`skill_matching_validation_report.json`)
   - All metrics in machine-readable format
   - Detailed results for each test pair
   - Mismatches with explanations
   - Timestamp for tracking

### Exit Codes

- `0`: Validation passed (accuracy ≥90%)
- `1`: Validation failed (accuracy <90%)
- `2`: Error occurred during validation

## File Structure

```
backend/tests/accuracy_validation/
├── validate_skill_matching.py          # Main validation script
├── test_resume_vacancy_pairs.json      # Test dataset (20 pairs)
├── skill_matching_validation_report.json  # Generated report
└── SKILL_MATCHING_README.md            # This file
```

## Test Dataset Format

Each test pair includes:

```json
{
  "id": "pair_001",
  "name": "Perfect Java Developer Match",
  "resume_text": "...",
  "vacancy": {
    "title": "Senior Java Developer",
    "required_skills": ["Java", "Spring Boot", "PostgreSQL"],
    "additional_skills": ["Docker", "Kubernetes"],
    "min_experience_months": 36
  },
  "expected_matches": {
    "matched_skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes"],
    "missing_skills": [],
    "expected_match_percentage": 100.0,
    "synonym_matches": [
      {"required": "SQL", "matched_as": "PostgreSQL"}
    ]
  }
}
```

## How Skill Matching Works

### 1. Skill Extraction

Resume skills are extracted using:
- **KeyBERT**: Contextual keyword extraction
- **SpaCy NER**: Named entity recognition for technical skills
- **Custom Patterns**: Regex for programming languages, frameworks, tools

### 2. Skill Normalization

All skills are normalized:
- Convert to lowercase
- Remove extra whitespace
- Apply standard formatting

### 3. Synonym Matching

The system uses `skill_synonyms.json` with 200+ mappings:
- **Databases**: PostgreSQL ≈ SQL, MySQL ≈ SQL
- **Web Frameworks**: ReactJS ≈ React, AngularJS ≈ Angular
- **Programming Languages**: TS ≈ TypeScript, JS ≈ JavaScript
- **DevOps**: K8s ≈ Kubernetes, IaC ≈ Terraform

### 4. Matching Algorithm

For each required skill:
1. Check direct match (case-insensitive)
2. Check synonym mappings
3. Determine status: matched or missing
4. Track which variant was found

## Troubleshooting

### Low Accuracy (<90%)

**Check:**
1. Are skills being extracted from resumes?
   - Review KeyBERT parameters in `keyword_extractor.py`
   - Verify NER patterns in `ner_extractor.py`

2. Are synonym mappings working?
   - Review `skill_synonyms.json` for missing mappings
   - Test specific synonyms manually

3. Are there too many false positives?
   - Skill extraction may be too permissive
   - Increase `min_score` in KeyBERT extraction

4. Are there too many false negatives?
   - Skill extraction may be too strict
   - Decrease `min_score` or expand synonym mappings

### Adding New Test Cases

To add a new test pair to `test_resume_vacancy_pairs.json`:

1. Manually determine which skills should match
2. Include realistic resume text with those skills
3. Create vacancy with required and additional skills
4. Document expected matches and synonym variations
5. Update summary statistics at top of file

### Common Issues

**Issue**: "ImportError: No module named 'analyzers'"
**Solution**: Run from backend directory: `cd backend && python tests/...`

**Issue**: "KeyError: 'matched_skills'"
**Solution**: Ensure each test pair has `expected_matches` object with all required fields

**Issue**: "False positives for generic skills"
**Solution**: Add stop words or increase min_score in keyword extraction

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Validate Skill Matching Accuracy
  run: |
    cd backend
    python tests/accuracy_validation/validate_skill_matching.py

- name: Upload Validation Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: skill-matching-report
    path: backend/tests/accuracy_validation/skill_matching_validation_report.json
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
cd backend
python tests/accuracy_validation/validate_skill_matching.py
if [ $? -ne 0 ]; then
  echo "Skill matching accuracy validation failed"
  exit 1
fi
```

## Continuous Improvement

### Regular Review

Schedule quarterly reviews of:
1. Test dataset relevance (are skills current?)
2. Synonym mappings completeness
3. Accuracy trends over time
4. New skills to add (AI/ML, cloud-native, etc.)

### Expanding Coverage

To improve test coverage:
1. Add more job types (DevSecOps, SRE, Mobile, etc.)
2. Include more specialized skills (Blockchain, IoT, AR/VR)
3. Add non-English resume samples (Russian, Spanish)
4. Test multi-word skill variations (Machine Learning, NLP)

## References

- **Skill Matching Implementation**: `backend/api/matching.py`
- **Skill Synonyms**: `backend/models/skill_synonyms.json`
- **Skill Extraction**: `backend/analyzers/keyword_extractor.py`, `ner_extractor.py`
- **Error Detection Validation**: See `ERROR_DETECTION_README.md` for similar framework

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review validation report JSON for detailed error breakdown
3. Enable DEBUG logging in validation script for more details
4. Test individual pairs by modifying dataset temporarily
