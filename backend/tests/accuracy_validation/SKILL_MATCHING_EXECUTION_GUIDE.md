# Skill Matching Validation - Execution Guide

## Quick Start

### Prerequisites

1. Python 3.9+ installed
2. All dependencies installed: `pip install -r requirements.txt`
3. ML models downloaded (KeyBERT, SpaCy)
4. Backend project structure intact

### Step-by-Step Execution

#### 1. Navigate to Backend Directory

```bash
cd backend
```

**Why:** The validation script imports from `analyzers` and `api` modules, which are in the backend directory.

#### 2. Verify Dependencies

```bash
python -c "from analyzers.keyword_extractor import extract_resume_keywords; print('✓ Keyword extractor OK')"
python -c "from analyzers.ner_extractor import extract_resume_entities; print('✓ NER extractor OK')"
python -c "from api.matching import load_skill_synonyms; print('✓ Matching module OK')"
```

**Expected Output:**
```
✓ Keyword extractor OK
✓ NER extractor OK
✓ Matching module OK
```

**If errors occur:**
- Reinstall dependencies: `pip install -r requirements.txt`
- Ensure ML models are downloaded: `python -m spacy download en_core_web_sm`

#### 3. Run Validation Script

```bash
python tests/accuracy_validation/validate_skill_matching.py
```

**What happens:**
1. Loads 20 test resume-vacancy pairs from JSON
2. Extracts skills from each resume using KeyBERT + SpaCy
3. Matches skills against vacancy requirements
4. Compares results to ground truth
5. Calculates accuracy metrics
6. Generates console report and JSON file

**Expected duration:** 2-5 minutes (depends on CPU, first run downloads models)

#### 4. Review Console Output

Look for:

```
================================================================================
SKILL MATCHING ACCURACY VALIDATION REPORT
================================================================================

SUMMARY METRICS
--------------------------------------------------------------------------------
Total Test Pairs:                20
Total Expected Skill Matches:    118
True Positives (Correct):        [number]
False Positives (Over-matched):  [number]
False Negatives (Missed):        [number]

ACCURACY METRICS
--------------------------------------------------------------------------------
Accuracy:       [percentage]% (Target: 90.00%)
Precision:      [percentage]%
Recall:         [percentage]%
F1 Score:       [percentage]%

Status: ✅ PASSED (or ❌ FAILED)
```

**Pass criteria:** Accuracy ≥ 90%

#### 5. Check Detailed Results

If validation failed, review:

```
FAILED CASES
--------------------------------------------------------------------------------

pair_003: Partial Match - Python Developer Missing Key Skills
  Expected: 33.33%, Detected: [percentage]%
  TP: [number], FP: [number], FN: [number]
    - FN: 'Django' should be matched but detected as missing
    - FN: 'FastAPI' should be matched but detected as missing
```

#### 6. Review JSON Report

```bash
cat tests/accuracy_validation/skill_matching_validation_report.json | head -50
```

**Key fields:**
```json
{
  "validation_type": "skill_matching_accuracy",
  "timestamp": "2026-01-24T12:00:00",
  "metrics": {
    "accuracy": 92.37,
    "precision": 94.12,
    "recall": 91.26,
    "f1_score": 92.67,
    "passed": true
  },
  "detailed_results": [...]
}
```

## Expected Results

### First Run (Cold Start)

**Duration:** 3-5 minutes
- Downloads KeyBERT model (~200MB)
- Loads SpaCy model (~10MB)
- Processes 20 test pairs

**Expected accuracy:** 88-95%

### Subsequent Runs (Warm Cache)

**Duration:** 30-60 seconds
- Models already cached in memory
- Faster processing

**Expected accuracy:** Same as first run (deterministic)

## What If Validation Fails?

### Scenario 1: Accuracy 85-90% (Close to Target)

**Diagnosis:** Minor issues with skill extraction or synonym coverage

**Actions:**
1. Review failed cases in console output
2. Check if specific skill types are missing:
   - Programming languages? → Check NER patterns in `ner_extractor.py`
   - Frameworks? → Check KeyBERT min_score threshold
   - Tools? → May need to add to technical skills regex

3. Add missing synonym mappings to `skill_synonyms.json`:
   ```json
   {
     "programming_languages": {
       "Rust": ["Rust", "Rust lang"]
     }
   }
   ```

4. Re-run validation

### Scenario 2: Accuracy 70-85% (Below Target)

**Diagnosis:** Systematic issues with skill extraction or matching

**Actions:**
1. **Check skill extraction quality:**
   ```python
   # Test manually
   from analyzers.keyword_extractor import extract_resume_keywords
   from analyzers.ner_extractor import extract_resume_entities

   resume_text = "Java Developer with Spring Boot and PostgreSQL experience"
   keywords = extract_resume_keywords(resume_text, language="en", top_n=20)
   entities = extract_resume_entities(resume_text, language="en")

   print("Keywords:", keywords)
   print("Technical Skills:", entities.get("technical_skills", []))
   ```

2. **If extraction is poor:**
   - Adjust KeyBERT parameters in `extract_resume_keywords()`
   - Lower `min_score` from 0.25 to 0.15
   - Increase `top_n` from 50 to 100

3. **If extraction is good but matching fails:**
   - Review `check_skill_match()` function in `matching.py`
   - Test synonym loading: `load_skill_synonyms()`
   - Verify synonym mappings are comprehensive

### Scenario 3: Accuracy <70% (Major Issues)

**Diagnosis:** Critical problems with system configuration

**Actions:**
1. **Verify imports are working:**
   ```bash
   python -c "from analyzers.keyword_extractor import extract_resume_keywords"
   python -c "from analyzers.ner_extractor import extract_resume_entities"
   python -c "from api.matching import check_skill_match, load_skill_synonyms"
   ```

2. **Check ML models are loaded:**
   ```bash
   python -c "from keybert import KeyBERT; model = KeyBERT(); print('KeyBERT OK')"
   python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('SpaCy OK')"
   ```

3. **Test basic functionality:**
   ```python
   # Test skill matching directly
   from api.matching import check_skill_match, load_skill_synonyms

   synonyms = load_skill_synonyms()
   resume_skills = ["Java", "Spring Boot", "PostgreSQL", "Docker"]
   required = "Java"

   result = check_skill_match(resume_skills, required, synonyms)
   print(f"Skill match result: {result}")  # Should be True
   ```

4. **Reinstall dependencies if needed:**
   ```bash
   pip install --upgrade -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Manual Testing

### Test Single Pair

Create a test script `test_single_pair.py`:

```python
from analyzers.keyword_extractor import extract_resume_keywords
from analyzers.ner_extractor import extract_resume_entities
from api.matching import check_skill_match, load_skill_synonyms

# Load synonyms
synonyms = load_skill_synonyms()

# Test resume
resume_text = """
John Anderson
Senior Software Engineer

SKILLS
Java, Spring Boot, PostgreSQL, Hibernate, Docker, Kubernetes
"""

# Extract skills
keywords = extract_resume_keywords(resume_text, language="en", top_n=50)
entities = extract_resume_entities(resume_text, language="en")

resume_skills = list(set(
    keywords.get("keywords", []) +
    keywords.get("keyphrases", []) +
    entities.get("technical_skills", [])
))

print("Extracted skills:", resume_skills)

# Test matching
required_skills = ["Java", "Spring", "SQL"]
for skill in required_skills:
    matched = check_skill_match(resume_skills, skill, synonyms)
    print(f"{skill}: {'✓ Matched' if matched else '✗ Missing'}")
```

Run with: `python test_single_pair.py`

### Test Specific Synonym

```python
from api.matching import normalize_skill_name, load_skill_synonyms

synonyms = load_skill_synonyms()

# Test synonym matching
required = "React"
resume_skill = "ReactJS"

norm_required = normalize_skill_name(required)
norm_resume = normalize_skill_name(resume_skill)

print(f"Required: {required} → {norm_required}")
print(f"Resume: {resume_skill} → {norm_resume}")
print(f"Direct match: {norm_required == norm_resume}")

# Check if in synonym mappings
for canonical, synonym_list in synonyms.items():
    if norm_required in normalize_skill_name(canonical):
        print(f"Found in category: {canonical}")
        print(f"Synonyms: {synonym_list}")
```

## Debug Mode

### Enable Detailed Logging

Edit `validate_skill_matching.py`:

```python
# Change from INFO to DEBUG
logging.basicConfig(
    level=logging.DEBUG,  # ← Change this
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Now you'll see:
- Each skill being extracted
- Each skill being checked for match
- Synonym lookups
- Processing time for each step

### Add Print Statements

For quick debugging, add prints in `validate_skill_matching.py`:

```python
# In extract_skills_from_resume()
print(f"DEBUG: Resume text length: {len(resume_text)}")
print(f"DEBUG: Extracted {len(resume_skills)} skills: {resume_skills[:10]}")

# In match_skills()
print(f"DEBUG: Required skills: {required_skills}")
print(f"DEBUG: Matched skills: {[m['skill'] for m in required_matches if m['status'] == 'matched']}")
```

## Performance Optimization

### Slow First Run?

**Issue:** ML models downloading on first run

**Solution:** Pre-download models
```bash
# Download KeyBERT model
python -c "from keybert import KeyBERT; KeyBERT()"

# Download SpaCy model
python -m spacy download en_core_web_sm

# Verify
ls -lh ~/.cache/torch/sentence_transformers/
ls -lh ~/.cache/spacy/
```

### Slow Subsequent Runs?

**Issue:** Models not being cached properly

**Solution:** Check environment variables
```bash
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
export SPACY_DATA=/path/to/spacy/cache
```

Or add to `.env` file:
```
SENTENCE_TRANSFORMERS_HOME=./models_cache
SPACY_DATA=./models_cache
```

## Continuous Monitoring

### Track Accuracy Over Time

Create a log file:

```bash
# Run validation and append results to log
python tests/accuracy_validation/validate_skill_matching.py | tee -a accuracy_log.txt

# View history
tail -20 accuracy_log.txt

# Plot trends (if you have many runs)
grep "Accuracy:" accuracy_log.txt | awk '{print $2}' > accuracy_trend.txt
```

### Set Up Automated Testing

Add to `Makefile`:
```makefile
.PHONY: test-skill-matching
test-skill-matching:
	@echo "Running skill matching accuracy validation..."
	@cd backend && python tests/accuracy_validation/validate_skill_matching.py
```

Run with: `make test-skill-matching`

## Next Steps After Validation

### If Passed (≥90%)

✅ **Great!** System is working as expected.

**Next:**
1. Update `implementation_plan.json` with subtask-7-5 status
2. Commit results to Git
3. Proceed to next subtask (security scanning)

### If Failed (<90%)

🔧 **Fix needed.**

**Next:**
1. Diagnose root cause using failed cases
2. Implement fixes (skill extraction, synonyms, matching logic)
3. Re-run validation
4. Repeat until ≥90% achieved
5. Update `implementation_plan.json` with notes

## Common Questions

**Q: Why does accuracy vary between runs?**
A: Should not vary if models are cached. If it does, check for:
- Random seed issues (should be deterministic)
- Model reloading on each run
- Different dependency versions

**Q: Can I use my own test dataset?**
A: Yes! Create a new JSON file following the format in `test_resume_vacancy_pairs.json` and update the path in `validate_skill_matching.py`.

**Q: How do I add new synonym mappings?**
A: Edit `backend/models/skill_synonyms.json` following the existing pattern. Re-run validation to test.

**Q: What if I don't have all ML models installed?**
A: The script will fail with ImportError. Run: `pip install -r backend/requirements.txt` and `python -m spacy download en_core_web_sm`

## Support Checklist

Before requesting support, verify:

- [ ] Running from `backend/` directory
- [ ] All dependencies installed (`pip list | grep -E "(keybert|spacy|sentence)"`)
- [ ] ML models downloaded (`spacy model` and `sentence-transformers`)
- [ ] Test dataset file exists (`test_resume_vacancy_pairs.json`)
- [ ] Python version 3.9+ (`python --version`)
- [ ] No import errors when testing individual modules
- [ ] Console output reviewed for specific error messages
- [ ] JSON report generated (check for parsing errors)

Include all of the above in support requests for faster resolution.
