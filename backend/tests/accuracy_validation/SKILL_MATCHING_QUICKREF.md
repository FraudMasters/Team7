# Skill Matching Validation - Quick Reference

## TL;DR

```bash
cd backend
python tests/accuracy_validation/validate_skill_matching.py
```

**Target:** ≥90% accuracy
**Output:** Console report + `skill_matching_validation_report.json`
**Exit Code:** 0=pass, 1=fail, 2=error

## Files Created

```
backend/tests/accuracy_validation/
├── test_resume_vacancy_pairs.json         # 20 test pairs (118 skill matches)
├── validate_skill_matching.py             # Validation script (500+ lines)
├── SKILL_MATCHING_README.md               # Full documentation
├── SKILL_MATCHING_EXECUTION_GUIDE.md      # Step-by-step guide
└── SKILL_MATCHING_QUICKREF.md             # This file
```

## Test Dataset Summary

| Metric | Value |
|--------|-------|
| Total Pairs | 20 |
| Expected Matches | 118 skills |
| Unique Skills | 45 |
| Synonym Matches | 15 |
| Perfect Match Cases | 8 |
| Partial Match Cases | 6 |
| Synonym Test Cases | 10 |
| No Match Cases | 1 |

## Key Features Tested

✅ **Direct Skill Matching**
- Java, Python, JavaScript, Go, C#, etc.

✅ **Synonym Matching**
- ReactJS → React
- PostgreSQL → SQL
- AngularJS → Angular
- Vue.js → Vue
- Spring Boot → Spring
- TS → TypeScript
- K8s → Kubernetes

✅ **Multi-Word Skills**
- Machine Learning
- Spring Boot
- CI/CD
- REST API

✅ **Case-Insensitive Matching**
- java → Java
- react → React
- sql → SQL

✅ **Partial Scenarios**
- Missing required skills
- Extra skills not in vacancy
- Mixed presence/absence

## Metrics Explained

| Metric | Formula | Target | Meaning |
|--------|---------|--------|---------|
| **Accuracy** | TP / Total Expected | ≥90% | Primary metric - correct matches |
| **Precision** | TP / (TP + FP) | ≥90% | Of detected matches, how many are correct |
| **Recall** | TP / (TP + FN) | ≥90% | Of expected matches, how many detected |
| **F1 Score** | 2×P×R/(P+R) | ≥90% | Harmonic mean of precision & recall |

**Legend:** TP=True Positive, FP=False Positive, FN=False Negative

## Common Exit Codes

```bash
0 # ✅ PASSED - Accuracy ≥90%
1 # ❌ FAILED - Accuracy <90%
2 # ⚠️  ERROR - Exception occurred
```

## Quick Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| ImportError | Wrong directory | `cd backend` first |
| Low accuracy (85-90%) | Missing synonyms | Add to `skill_synonyms.json` |
| Low accuracy (70-85%) | Extraction issues | Adjust KeyBERT params |
| Low accuracy (<70%) | Configuration error | Reinstall dependencies |
| Slow first run | Models downloading | Wait for completion |
| Accuracy varies | Random seed issues | Check determinism |

## Manual Test Commands

```bash
# Test imports
cd backend
python -c "from analyzers.keyword_extractor import extract_resume_keywords; print('OK')"
python -c "from analyzers.ner_extractor import extract_resume_entities; print('OK')"
python -c "from api.matching import check_skill_match; print('OK')"

# Test synonym loading
python -c "from api.matching import load_skill_synonyms; print(len(load_skill_synonyms()), 'mappings')"

# Test skill extraction
python -c "
from analyzers.keyword_extractor import extract_resume_keywords
from analyzers.ner_extractor import extract_resume_entities
text = 'Java Developer with Spring Boot and PostgreSQL'
kw = extract_resume_keywords(text, 'en', 20)
ent = extract_resume_entities(text, 'en')
print('Keywords:', kw.get('keywords', [])[:5])
print('Skills:', ent.get('technical_skills', [])[:5])
"

# Run validation
python tests/accuracy_validation/validate_skill_matching.py
```

## Expected Output (Success)

```
================================================================================
SKILL MATCHING ACCURACY VALIDATION REPORT
================================================================================

SUMMARY METRICS
--------------------------------------------------------------------------------
Total Test Pairs:                20
Total Expected Skill Matches:    118
True Positives (Correct):        108
False Positives (Over-matched):  5
False Negatives (Missed):        5

ACCURACY METRICS
--------------------------------------------------------------------------------
Accuracy:       91.53% (Target: 90.00%)
Precision:      95.58%
Recall:         91.53%
F1 Score:       93.51%

Status: ✅ PASSED
```

## Expected Output (Failure)

```
ACCURACY METRICS
--------------------------------------------------------------------------------
Accuracy:       87.29% (Target: 90.00%)
Precision:      89.13%
Recall:         87.29%
F1 Score:       88.20%

Status: ❌ FAILED

FAILED CASES
--------------------------------------------------------------------------------

pair_003: Partial Match - Python Developer Missing Key Skills
  TP: 1, FP: 0, FN: 2
    - FN: 'Django' should be matched but detected as missing
    - FN: 'FastAPI' should be matched but detected as missing

RECOMMENDATIONS
--------------------------------------------------------------------------------
1. Review skill extraction accuracy - may need tuning KeyBERT parameters
2. Expand skill synonym mappings in skill_synonyms.json
3. Improve NER patterns for technical skills in ner_extractor.py
```

## Integration Points

**Uses:**
- `analyzers/keyword_extractor.py` - KeyBERT skill extraction
- `analyzers/ner_extractor.py` - SpaCy technical skill NER
- `api/matching.py` - Skill matching logic with synonyms
- `models/skill_synonyms.json` - 200+ synonym mappings

**Outputs:**
- Console report (human-readable)
- JSON report (machine-readable for CI/CD)

## Related Documentation

- **Full Documentation:** `SKILL_MATCHING_README.md`
- **Step-by-Step Guide:** `SKILL_MATCHING_EXECUTION_GUIDE.md`
- **Error Detection Validation:** `ERROR_DETECTION_README.md` (similar framework)
- **Implementation:** `backend/api/matching.py`
- **Synonym Mappings:** `backend/models/skill_synonyms.json`

## Fast Commands

```bash
# Run validation
make test-skill-matching  # if Makefile exists
# OR
python backend/tests/accuracy_validation/validate_skill_matching.py

# View results
cat backend/tests/accuracy_validation/skill_matching_validation_report.json | jq '.metrics'

# Check accuracy only
python backend/tests/accuracy_validation/validate_skill_matching.py 2>&1 | grep "Accuracy:"

# Count failed cases
python backend/tests/accuracy_validation/validate_skill_matching.py 2>&1 | grep -c "FN:"
```

## Validation Checklist

Before marking subtask-7-5 as complete, verify:

- [ ] Test dataset created (20 pairs, 118 matches)
- [ ] Validation script implemented
- [ ] Documentation created (3 files)
- [ ] Validation script runs without errors
- [ ] Accuracy ≥90% achieved
- [ ] JSON report generated successfully
- [ ] Exit code correct (0=pass, 1=fail)
- [ ] Documentation reviewed and complete

## Contact & Support

**Issues:**
1. Check `SKILL_MATCHING_EXECUTION_GUIDE.md` troubleshooting section
2. Review failed cases in console output
3. Enable DEBUG mode for detailed logs
4. Verify all ML models installed

**Enhancement Requests:**
- Add test cases for new job types
- Expand synonym mappings
- Improve skill extraction patterns
- Add non-English test cases

---

**Version:** 1.0
**Last Updated:** 2026-01-24
**Status:** Ready for manual execution
