# Vacancy-Resume Matching Dataset Usage Guide

## Executive Summary

This guide provides comprehensive instructions for integrating and using the **vacancy-resume-matching-dataset** with the AI-Powered Resume Analysis Platform. The dataset is **highly relevant** to the project as it directly supports the core job matching functionality.

**Dataset Source**: [NataliaVanetik/vacancy-resume-matching-dataset](https://github.com/NataliaVanetik/vacancy-resume-matching-dataset)

**Compatibility Assessment**: ✅ **EXCELLENT FIT** - Perfect alignment with existing architecture

---

## 1. Dataset Overview

### 1.1 Dataset Composition

The vacancy-resume-matching-dataset-main contains:

| Component | Count | Format | Description |
|-----------|-------|--------|-------------|
| **Vacancies** | 5 | JSON/data.world | Selected job postings with detailed requirements |
| **Resumes** | 65 | .docx | Anonymized candidate resumes |
| **Human Evaluations** | 325+ pairs | Structured data | Expert-labeled match results |

### 1.2 Dataset Structure

Based on the GitHub repository structure, the dataset typically contains:

```
vacancy-resume-matching-dataset-main/
├── vacancies/                    # Job posting data
│   ├── vacancy_001.json
│   ├── vacancy_002.json
│   └── ...
├── resumes/                      # Resume files (.docx format)
│   ├── resume_001.docx
│   ├── resume_002.docx
│   └── ...
├── evaluations/                  # Human-labeled match results
│   ├── matches.csv
│   └── labels.json
└── README.md                     # Dataset documentation
```

### 1.3 Data Fields

**Vacancy Data Structure:**
```json
{
  "id": "vacancy_001",
  "title": "Java Developer",
  "description": "Job description text...",
  "required_skills": ["Java", "Spring", "PostgreSQL"],
  "min_experience_years": 3,
  "location": "Remote",
  "salary_range": "5000-8000"
}
```

**Resume Data Structure:**
- Text content in .docx format
- Contains: Skills, Experience, Education, Contact Info
- Anonymized (no personal identifiers)

**Evaluation Data Structure:**
```json
{
  "vacancy_id": "vacancy_001",
  "resume_id": "resume_015",
  "match_score": 0.85,
  "human_label": "good_fit",
  "missing_skills": ["Kafka"],
  "matched_skills": ["Java", "Spring", "PostgreSQL"]
}
```

---

## 2. Project Compatibility Analysis

### 2.1 Architecture Alignment

| Project Feature | Dataset Support | Integration Complexity |
|----------------|-----------------|----------------------|
| **Resume Parsing (.docx)** | ✅ Direct Support | ⭐ Low (already supported) |
| **Skill Extraction** | ✅ Compatible | ⭐ Low (uses existing analyzers) |
| **Job Matching** | ✅ Core Feature | ⭐ Low (existing endpoint) |
| **Synonym Handling** | ✅ Compatible | ⭐ Low (existing skill_synonyms.json) |
| **Experience Calculation** | ✅ Compatible | ⭐ Low (existing calculator) |
| **Feedback System** | ✅ Perfect for ML | ⭐ Medium (for model improvement) |

### 2.2 Technical Compatibility

**Supported Formats:**
- ✅ `.docx` files - Already supported via `python-docx`
- ✅ Structured JSON data - Compatible with FastAPI models
- ✅ Text analysis - Compatible with KeyBERT and SpaCy

**Language Support:**
- ✅ Multi-language resumes (English/Russian) - Detected automatically
- ✅ Skill synonyms across languages - Already implemented

**ML Pipeline Integration:**
- ✅ Can be used for accuracy validation
- ✅ Can enhance skill synonym mappings
- ✅ Can train better matching models
- ✅ Feedback loop for continuous improvement

---

## 3. Integration Guide

### 3.1 Prerequisites

Ensure the following are installed:

```bash
# Python dependencies (already in requirements.txt)
pip install python-docx PyPDF2 keybert spacy langdetect

# SpaCy models
python -m spacy download en_core_web_sm
python -m spacy download ru_core_web_sm
```

### 3.2 Dataset Setup

**Step 1: Download the Dataset**

```bash
# Clone the repository or download from GitHub
git clone https://github.com/NataliaVanetik/vacancy-resume-matching-dataset.git
cd vacancy-resume-matching-dataset

# OR download as ZIP and extract
# unzip vacancy-resume-matching-dataset-main.zip
```

**Step 2: Organize Files**

```bash
# Create dataset directory in project
mkdir -p data/external-datasets/vacancy-resume-matching

# Copy dataset files
cp -r vacancy-resume-matching-dataset-main/* \
    data/external-datasets/vacancy-resume-matching/
```

**Step 3: Verify Structure**

```bash
# Expected structure:
data/external-datasets/vacancy-resume-matching/
├── vacancies/
├── resumes/
└── evaluations/
```

### 3.3 Database Integration

**Option A: Direct File Processing** (Quick Start)

```python
# backend/scripts/process_external_dataset.py
import json
from pathlib import Path
from services.data_extractor.extract import extract_text_from_docx

DATASET_DIR = Path("data/external-datasets/vacancy-resume-matching")

def process_dataset():
    """Process all resumes in the external dataset."""
    resumes_dir = DATASET_DIR / "resumes"
    vacancies_dir = DATASET_DIR / "vacancies"

    # Process resumes
    for resume_file in resumes_dir.glob("*.docx"):
        result = extract_text_from_docx(resume_file)
        # Store or analyze the resume text
        print(f"Processed {resume_file.name}: {len(result['text'])} chars")

    # Load vacancies
    vacancies = []
    for vacancy_file in vacancies_dir.glob("*.json"):
        with open(vacancy_file) as f:
            vacancies.append(json.load(f))

    return vacancies
```

**Option B: Database Storage** (Production-Ready)

```sql
-- Create tables for external dataset
CREATE TABLE external_vacancies (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    required_skills JSONB,
    min_experience_months INTEGER,
    source VARCHAR(50) DEFAULT 'external_dataset'
);

CREATE TABLE external_resumes (
    id VARCHAR(100) PRIMARY KEY,
    filename VARCHAR(255),
    extracted_text TEXT,
    source VARCHAR(50) DEFAULT 'external_dataset',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE external_evaluations (
    id SERIAL PRIMARY KEY,
    vacancy_id VARCHAR(100),
    resume_id VARCHAR(100),
    match_score DECIMAL(3,2),
    human_label VARCHAR(20),
    matched_skills JSONB,
    missing_skills JSONB,
    FOREIGN KEY (vacancy_id) REFERENCES external_vacancies(id),
    FOREIGN KEY (resume_id) REFERENCES external_resumes(id)
);
```

```python
# backend/scripts/load_dataset_to_db.py
from sqlalchemy.orm import Session
from models.database import get_db
from models.external_dataset import ExternalVacancy, ExternalResume, ExternalEvaluation

def load_dataset_to_database():
    """Load external dataset into PostgreSQL."""
    db: Session = next(get_db())

    # Load vacancies
    for vacancy_data in load_vacancies():
        vacancy = ExternalVacancy(**vacancy_data)
        db.add(vacancy)

    # Load resumes
    for resume_file in Path("data/external-datasets/vacancy-resume-matching/resumes").glob("*.docx"):
        result = extract_text_from_docx(resume_file)
        resume = ExternalResume(
            id=resume_file.stem,
            filename=resume_file.name,
            extracted_text=result['text']
        )
        db.add(resume)

    # Load evaluations
    for eval_data in load_evaluations():
        evaluation = ExternalEvaluation(**eval_data)
        db.add(evaluation)

    db.commit()
    print(f"Loaded dataset: {vacancy_count} vacancies, {resume_count} resumes")
```

### 3.4 API Integration

**Extend Matching API for Dataset Testing**

```python
# backend/api/dataset_testing.py
from fastapi import APIRouter, HTTPException
from analyzers import extract_resume_keywords, extract_resume_entities
from api.matching import compare_resume_to_vacancy

router = APIRouter()

@router.post("/test-dataset-matching")
async def test_dataset_matching(
    resume_id: str,
    vacancy_id: str
):
    """
    Test matching using external dataset entries.

    Useful for validating the accuracy of the matching algorithm
    against human-labeled ground truth.
    """
    # Load resume and vacancy from external dataset
    resume = get_external_resume(resume_id)
    vacancy = get_external_vacancy(vacancy_id)

    # Use existing matching logic
    from api.matching import MatchRequest
    request = MatchRequest(
        resume_id=resume_id,
        vacancy_data=vacancy
    )

    result = await compare_resume_to_vacancy(request)

    # Compare with human evaluation
    human_eval = get_human_evaluation(resume_id, vacancy_id)

    return {
        "ai_result": result,
        "human_evaluation": human_eval,
        "accuracy_metrics": calculate_accuracy(result, human_eval)
    }
```

---

## 4. Testing & Validation

### 4.1 Accuracy Validation

**Step 1: Run Baseline Tests**

```bash
cd backend

# Use existing validation framework
pytest tests/accuracy_validation/validate_skill_matching.py -v
```

**Step 2: Test with External Dataset**

```python
# backend/tests/accuracy_validation/test_external_dataset.py
import pytest
from pathlib import Path
from api.matching import compare_resume_to_vacancy, MatchRequest

def test_external_dataset_accuracy():
    """Validate matching accuracy against external dataset."""

    # Load all evaluations
    evaluations = load_external_evaluations()
    results = []

    for eval_item in evaluations:
        # Get AI prediction
        request = MatchRequest(
            resume_id=eval_item['resume_id'],
            vacancy_data=get_vacancy(eval_item['vacancy_id'])
        )
        ai_result = await compare_resume_to_vacancy(request)

        # Compare with human label
        accuracy = compare_with_human_label(ai_result, eval_item)
        results.append(accuracy)

    # Calculate overall accuracy
    overall_accuracy = sum(results) / len(results)
    assert overall_accuracy >= 0.85, f"Accuracy {overall_accuracy:.2%} below 85% target"
```

**Step 3: Generate Report**

```python
# backend/scripts/generate_accuracy_report.py
def generate_dataset_report():
    """Generate accuracy report comparing AI vs human evaluations."""

    metrics = {
        "total_evaluations": 0,
        "correct_predictions": 0,
        "skill_match_accuracy": 0.0,
        "missing_skill_detection": 0.0,
        "false_positive_rate": 0.0
    }

    # ... calculations ...

    with open("dataset-accuracy-report.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Overall Accuracy: {metrics['correct_predictions']/metrics['total_evaluations']:.2%}")
```

### 4.2 Quality Checks

**Data Quality Validation:**

```python
def validate_dataset_quality():
    """Ensure dataset meets quality standards."""

    checks = {
        "resume_count": len(list_resumes()) >= 50,
        "vacancy_count": len(list_vacancies()) >= 3,
        "evaluation_coverage": len(list_evaluations()) >= 200,
        "format_validity": all(validate_file_format(f) for f in all_files()),
        "language_detection": all(detect_language(resume) for resume in all_resumes())
    }

    if all(checks.values()):
        print("✅ Dataset quality checks passed")
    else:
        print("⚠️ Dataset quality issues found:")
        for check, passed in checks.items():
            if not passed:
                print(f"  ❌ {check}")
```

---

## 5. Enhancement Opportunities

### 5.1 Expand Skill Synonyms

**Extract New Synonyms from Dataset:**

```python
# backend/scripts/extract_new_synonyms.py
def discover_new_synonyms():
    """Find new skill synonyms from dataset evaluations."""

    from collections import defaultdict
    synonym_candidates = defaultdict(set)

    for eval_item in load_external_evaluations():
        vacancy_skills = eval_item['vacancy']['required_skills']
        resume_skills = eval_item['resume']['extracted_skills']

        for v_skill in vacancy_skills:
            for r_skill in resume_skills:
                # If marked as match but not in current synonym list
                if is_match(v_skill, r_skill) and not in_synonym_list(v_skill, r_skill):
                    synonym_candidates[v_skill].add(r_skill)

    # Review and add to skill_synonyms.json
    return dict(synonym_candidates)
```

### 5.2 Improve Matching Algorithm

**Train Enhanced Model:**

```python
# backend/analyzers/ml_skill_matcher.py
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class MLSkillMatcher:
    """ML-based skill matcher trained on external dataset."""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.is_trained = False

    def train(self, evaluations):
        """Train model on human-labeled evaluations."""
        X = []
        y = []

        for eval_item in evaluations:
            features = extract_features(eval_item['resume'], eval_item['vacancy'])
            label = 1 if eval_item['human_label'] in ['good_fit', 'excellent_fit'] else 0
            X.append(features)
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        self.model.fit(X, y)
        self.is_trained = True

    def predict_match(self, resume_skills, vacancy_skills):
        """Predict match score using trained model."""
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        features = extract_features_from_skills(resume_skills, vacancy_skills)
        match_probability = self.model.predict_proba([features])[0]
        return match_probability[1]
```

### 5.3 Feedback Loop Integration

**Use Dataset for Continuous Learning:**

```python
# backend/api/feedback_learning.py
async def incorporate_dataset_feedback():
    """Use external dataset as ground truth for feedback."""

    evaluations = load_external_evaluations()

    for eval_item in evaluations:
        # Submit as "perfect" feedback
        await submit_match_feedback(MatchFeedbackRequest(
            match_id=f"dataset-{eval_item['id']}",
            skill=eval_item['skill'],
            was_correct=True,  # Human-labeled as correct
            recruiter_correction=None,
            confidence_score=1.0,
            metadata={"source": "external_dataset_ground_truth"}
        ))

    print(f"Incorporated {len(evaluations)} ground truth labels")
```

---

## 6. Alternative Datasets

If the primary dataset doesn't fully meet your needs, consider these alternatives:

### 6.1 Kaggle Resume Dataset

**Source**: [Resume Data for Ranking](https://www.kaggle.com/datasets/thejohnwick001/resume-data-for-ranking)

- **Format**: CSV, JSON
- **Size**: Larger dataset with diverse resumes
- **Use Case**: Ranking algorithms, broader skill coverage
- **Integration**: Similar to primary dataset

**Pros:**
- ✅ Larger volume
- ✅ Structured CSV format
- ✅ Multiple job categories

**Cons:**
- ⚠️ May require more preprocessing
- ⚠️ Less human-verified labels

### 6.2 Custom Dataset Collection

**Build Your Own Dataset:**

```python
# backend/scripts/collect_training_data.py
def collect_production_data():
    """Collect anonymized production data for training."""

    from models.database import SessionLocal, Resume, Vacancy, MatchResult

    db = SessionLocal()

    # Get recent successful matches (anonymized)
    successful_matches = db.query(MatchResult).filter(
        MatchResult.match_percentage >= 80,
        MatchResult.created_at >= datetime.now() - timedelta(days=90)
    ).all()

    dataset = []
    for match in successful_matches:
        # Anonymize
        dataset.append({
            "resume_skills": match.resume.extracted_skills,
            "vacancy_skills": match.vacancy.required_skills,
            "match_score": match.match_percentage,
            "recruiter_feedback": match.recruiter_feedback
        })

    return dataset
```

### 6.3 Academic Datasets

**Research Sources:**
- [ResuméAtlas Dataset](https://arxiv.org/html/2406.18125v1) - Structured resume attributes
- [MDPI Zero-Shot Matching Dataset](https://www.mdpi.com/2079-9292/14/24/4960) - LLM-based matching

---

## 7. Implementation Roadmap

### Phase 1: Quick Start (1-2 hours)
- [ ] Download and organize dataset
- [ ] Process sample resumes through existing API
- [ ] Test matching with sample vacancies
- [ ] Validate basic functionality

### Phase 2: Integration (4-6 hours)
- [ ] Create database schema for external data
- [ ] Implement dataset loading scripts
- [ ] Extend API for dataset testing
- [ ] Set up automated validation tests

### Phase 3: Enhancement (8-12 hours)
- [ ] Extract new skill synonyms
- [ ] Train ML-based matcher
- [ ] Implement feedback loop
- [ ] Generate accuracy reports

### Phase 4: Production (2-4 hours)
- [ ] Set up continuous integration
- [ ] Schedule regular accuracy checks
- [ ] Monitor model performance
- [ ] Document findings and improvements

---

## 8. Best Practices

### 8.1 Data Privacy

⚠️ **IMPORTANT**: Even anonymized datasets may contain sensitive information.

```python
def sanitize_resume(resume_text):
    """Remove any remaining personal identifiers."""
    import re

    # Remove email patterns
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)

    # Remove SSN patterns
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

    return text
```

### 8.2 Version Control

```bash
# Track dataset versions
git add data/external-datasets/
git commit -m "Add vacancy-resume-matching-dataset v1.0"

# Use Git LFS for large files
git lfs track "data/external-datasets/**/*.docx"
git add .gitattributes
```

### 8.3 Regular Updates

```bash
# Schedule monthly dataset updates
# Add to crontab or GitHub Actions
0 0 1 * * cd /app && python scripts/update_dataset.py
```

---

## 9. Troubleshooting

### Common Issues

**Issue 1: File Format Errors**

```python
# Problem: .docx files not reading correctly
# Solution: Check python-docx version

pip install --upgrade python-docx

# Test extraction
from extract import extract_text_from_docx
result = extract_text_from_docx("path/to/resume.docx")
print(result)
```

**Issue 2: Character Encoding**

```python
# Problem: Special characters in resumes
# Solution: Specify encoding explicitly

with open(resume_file, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
```

**Issue 3: Memory Issues**

```python
# Problem: Too many resumes loaded at once
# Solution: Process in batches

def process_in_batches(resumes, batch_size=10):
    for i in range(0, len(resumes), batch_size):
        batch = resumes[i:i+batch_size]
        process_batch(batch)
        # Clear memory
        gc.collect()
```

---

## 10. Success Metrics

Track these metrics to measure integration success:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Dataset Coverage** | 65+ resumes, 5+ vacancies | Count processed files |
| **Matching Accuracy** | 85%+ match human labels | Compare AI vs human evaluations |
| **Processing Speed** | <2s per match | API response time |
| **Synonym Expansion** | +50 new mappings | New synonyms discovered |
| **Model Improvement** | +5% accuracy gain | Before/after comparison |

---

## 11. Next Steps

1. **Immediate Actions (Today)**
   - Download the dataset from GitHub
   - Process 5-10 sample resumes
   - Test with existing matching endpoint
   - Document any issues found

2. **Short-term (This Week)**
   - Complete full dataset integration
   - Run accuracy validation
   - Generate baseline report
   - Identify improvement opportunities

3. **Long-term (Next Month)**
   - Train enhanced ML model
   - Implement continuous learning
   - Expand skill synonym database
   - Publish accuracy benchmarks

---

## 12. Resources & References

### Dataset Sources
- **Primary**: [NataliaVanetik/vacancy-resume-matching-dataset](https://github.com/NataliaVanetik/vacancy-resume-matching-dataset) - GitHub
- **Alternative**: [Resume Data for Ranking](https://www.kaggle.com/datasets/thejohnwick001/resume-data-for-ranking) - Kaggle

### Research Papers
- [Zero-Shot Resume–Job Matching with LLMs](https://www.mdpi.com/2079-9292/14/24/4960) (MDPI, 2025)
- [ResuméAtlas: Resume Classification](https://arxiv.org/html/2406.18125v1) (arXiv, 2024)

### Project Documentation
- **Matching API**: `/backend/api/matching.py`
- **Skill Synonyms**: `/backend/models/skill_synonyms.json`
- **Test Data**: `/backend/tests/accuracy_validation/test_resume_vacancy_pairs.json`

---

## Conclusion

The **vacancy-resume-matching-dataset** is an **excellent fit** for this project and will significantly enhance the job matching capabilities. Follow the integration guide step-by-step, starting with Phase 1 (Quick Start) to validate compatibility, then proceed to deeper integration for production use.

**Estimated Total Integration Time**: 15-24 hours across all phases

**Expected Benefits**:
- ✅ Improved matching accuracy through ground truth validation
- ✅ Enhanced skill synonym database
- ✅ ML model training opportunities
- ✅ Continuous improvement through feedback loop

---

**Last Updated**: 2025-01-25
**Version**: 1.0
**Maintained By**: AgentHR Development Team

---

## Sources

- [NataliaVanetik/vacancy-resume-matching-dataset](https://github.com/NataliaVanetik/vacancy-resume-matching-dataset)
- [Resume Data for Ranking](https://www.kaggle.com/datasets/thejohnwick001/resume-data-for-ranking)
- [What Resume Data Hiring Algorithms Analyze in 2026](https://www.linkedin.com/pulse/what-resume-data-hiring-algorithms-analyze-2026-irc-resume-s6bfc)
- [Zero-Shot Resume–Job Matching with LLMs via Structured Approaches](https://www.mdpi.com/2079-9292/14/24/4960)
- [ResuméAtlas: Revisiting Resume Classification with Large Language Models](https://arxiv.org/html/2406.18125v1)
- [Towards smarter hiring solutions: artificial intelligence-driven recruitment systems](https://link.springer.com/article/10.1007/s11042-026-21263-0)
