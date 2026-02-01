# ML Pipeline Architecture

This document provides a comprehensive overview of the backend's machine learning pipeline, including all matchers, analyzers, extractors, and ML-powered services.

## Overview

The ML pipeline is organized into several functional layers:

1. **Skill Extraction** - Extract skills and entities from resumes
2. **Skill Matching** - Match candidate skills to job requirements
3. **Experience Analysis** - Calculate and extract work experience
4. **Quality Analysis** - Check resume quality and ATS compliance
5. **Candidate Analysis** - Skill gaps, learning recommendations, interview prep
6. **Candidate Ranking** - ML-based ranking with fairness monitoring
7. **Infrastructure** - Model versioning, benchmarking, performance tracking

---

## 1. Skill Extraction Layer

### Hugging Face Skill Extractor (`hf_skill_extractor.py`)
**NER-based skill extraction using transformer models**

Provides three extraction methods:

#### 1.1 NER-Based Extraction (`extract_skills_ner`)
Uses Named Entity Recognition to extract skills without predefined lists.

```python
from analyzers import extract_skills_ner

result = extract_skills_ner(
    resume_text,
    top_n=10,
    model_name="dslim/bert-base-NER",  # or "yashpwr/resume-ner-bert-v2"
    min_score=0.5
)

skills = result["skills"]
# Returns: ['Python', 'Django', 'PostgreSQL', 'Machine Learning', ...]
```

**Features:**
- No predefined skills needed
- Specialized resume models available
- Fast inference (~50ms per text)
- Confidence scoring for each skill

#### 1.2 Zero-Shot Classification (`extract_skills_zero_shot`)
Classifies resume against a predefined skill taxonomy.

```python
from analyzers import extract_skills_zero_shot

taxonomy = [
    "Python", "Java", "JavaScript", "TypeScript",
    "Django", "Flask", "FastAPI",
    "React", "Vue", "Angular"
]

result = extract_skills_zero_shot(
    resume_text,
    candidate_skills=taxonomy,
    top_n=10,
    min_score=0.3
)

skills = result["skills"]
scores = result["skills_with_scores"]
# Returns: [('Python', 0.95), ('Django', 0.87), ...]
```

**Features:**
- Predefined skill taxonomy support
- Best for matching against job requirements
- Highest accuracy with good taxonomy
- Consistent skill categorization

#### 1.3 Automatic Extraction (`extract_top_skills_auto`)
**Recommended method** - tries all methods automatically with fallback.

```python
from analyzers import extract_top_skills_auto

result = extract_top_skills_auto(resume_text, top_n=10)

if result["skills"]:
    print(f"Found {result['count']} skills using {result['method']}")
    print(f"Skills: {result['skills']}")
```

**Fallback chain:**
1. Hugging Face NER
2. KeyBERT (if available)
3. Zero-shot classification (if taxonomy provided)
4. SpaCy NER (final fallback)

### NER Extractor (`ner_extractor.py`)
**General-purpose Named Entity Recognition**

Extracts entities beyond just skills:

```python
from analyzers import extract_resume_entities

entities = extract_resume_entities(resume_text)
# Returns: {
#     'persons': ['John Doe', 'Jane Smith'],
#     'organizations': ['Google', 'Microsoft'],
#     'dates': ['2020-01', '2021-05'],
#     'locations': ['San Francisco', 'New York'],
#     'skills': ['Python', 'Django']
# }
```

**Features:**
- Multi-entity type extraction (persons, orgs, dates, locations, skills)
- Batch processing support
- Confidence scores
- SpaCy-based (en_core_web_sm)

### Keyword Extractor (`keyword_extractor.py`)
**Traditional keyword extraction using RAKE**

```python
from analyzers import extract_keywords, extract_resume_keywords

# Generic keyword extraction
keywords = extract_keywords(text, num_keywords=10)

# Resume-specific extraction (filters out common resume noise)
resume_keywords = extract_resume_keywords(resume_text, top_n=10)
```

**Features:**
- RAKE algorithm (Rapid Automatic Keyword Extraction)
- Resume-specific stopword filtering
- Fast, no ML models required
- Good for simple use cases

---

## 2. Skill Matching Layer

### Enhanced Skill Matcher (`enhanced_matcher.py`)
**Traditional keyword-based matching with intelligence**

```python
from analyzers import EnhancedSkillMatcher

matcher = EnhancedSkillMatcher()
result = matcher.match_multiple(
    resume_skills=['ReactJS', 'Python', 'PostgreSQL'],
    required_skills=['React', 'Python', 'SQL']
)
# Returns: {
#     'React': {'matched': True, 'confidence': 1.0, 'match_type': 'direct'},
#     'Python': {'matched': True, 'confidence': 1.0, 'match_type': 'direct'},
#     'SQL': {'matched': True, 'confidence': 0.8, 'match_type': 'context'}
# }
```

**Features:**
- Direct name matching
- Synonym-based matching (via `skill_synonyms.json`)
- Context-aware matching (web_framework, database, language categories)
- Fuzzy matching for typos (SequenceMatcher)
- Compound skill matching (C/C++ → C, C++)
- Language hierarchy matching (C++ implies C knowledge)

**Best for:** Quick keyword matching, synonym support, real-time matching

### TF-IDF Skill Matcher (`tfidf_matcher.py`)
**TF-IDF weighted keyword matching**

```python
from analyzers import get_tfidf_matcher

matcher = get_tfidf_matcher()
result = matcher.match(
    resume_text="Experienced with React and Python",
    job_title="Senior React Developer",
    job_description="Looking for React expert",
    required_skills=["React", "Python", "TypeScript"]
)
# Returns: TfidfMatchResult(
#     score=0.67,
#     missing_keywords=['TypeScript'],
#     matched_keywords=['React', 'Python'],
#     keyword_scores={'React': 0.8, 'Python': 0.6}
# )
```

**Features:**
- Uses TF-IDF to rank keyword importance
- Identifies missing keywords ranked by importance
- N-gram support (1-2 grams) for phrases
- Weighted scoring (important keywords count more)
- sklearn-based vectorization

**Best for:** Need to know which skills are most important

### Vector Similarity Matcher (`vector_matcher.py`)
**Semantic similarity using sentence-transformers**

```python
from analyzers import get_vector_matcher

matcher = get_vector_matcher()
result = matcher.match(
    resume_text="Experienced web developer with React expertise",
    job_title="Frontend Developer",
    job_description="Looking for React.js specialist",
    required_skills=["React"]
)
# Returns: VectorMatchResult(
#     score=0.85,
#     similarity=0.70,
#     matched_skills=['React']
# )
```

**Features:**
- Semantic understanding beyond keywords
- Finds similarity in meaning (e.g., "JS developer" ≈ "JavaScript programmer")
- Uses cosine similarity on embeddings
- Model: all-MiniLM-L6-v2 (fast, 384dim)
- ~80MB model, loads once and cached

**Best for:** Semantic meaning matters, different phrasings

### Unified Skill Matcher (`unified_matcher.py`)
**Combines all three methods for best results**

```python
from analyzers import get_unified_matcher

matcher = get_unified_matcher()
result = matcher.match(
    resume_text="Experienced with React and Python",
    resume_skills=["React", "Python"],
    job_title="Senior React Developer",
    job_description="Looking for React expert",
    required_skills=["React", "Python", "TypeScript"]
)
# Returns: UnifiedMatchResult(
#     overall_score=0.75,
#     keyword_score=0.67,
#     tfidf_score=0.80,
#     vector_score=0.72,
#     recommendation='good',  # excellent/good/maybe/poor
#     matched_skills=['React', 'Python'],
#     missing_skills=['TypeScript']
# )
```

**Features:**
- Combines Enhanced + TF-IDF + Vector matching
- Weighted overall score (default: 50% keyword, 30% TF-IDF, 20% vector)
- Generates hiring recommendation
- Most comprehensive matching approach
- Acceptable latency (~200-500ms)

**Best for:** Best overall accuracy, comprehensive analysis

---

## 3. Experience Analysis Layer

### Experience Calculator (`experience_calculator.py`)
**Calculate total work experience from resume data**

```python
from analyzers import calculate_total_experience, format_experience_summary

# Calculate total experience
experience_months = calculate_total_experience(work_history)
# Returns: 60 (months)

# Format for display
summary = format_experience_summary(experience_months)
# Returns: "5 years 0 months"

# Calculate experience for specific skills
skill_exp = calculate_skill_experience(
    work_history,
    target_skills=["Python", "Django"]
)
# Returns: {'Python': 48, 'Django': 36} (in months)

# Calculate multiple skills at once
multi_skill_exp = calculate_multiple_skills_experience(
    work_history,
    skills=["Python", "Django", "PostgreSQL"]
)
```

**Features:**
- Handles overlapping periods (deduplicates)
- Multiple date format support (YYYY-MM-DD, MM/YYYY, "Month YYYY")
- Filters by specific skills
- Converts between months and years
- Handles current positions (end_date = None)

**Date formats supported:**
- ISO format: `2023-02-01`
- Month/Year: `02/2023`
- Year-Month: `2023-02`
- Text format: `February 2023`, `Feb 2023`

### Experience Extractor (`experience_extractor.py`)
**Extract structured work experience from resume text**

```python
from analyzers import extract_work_experience, detect_overlaps

# Extract work history
work_history = extract_work_experience(resume_text)
# Returns: [
#     {
#         'title': 'Senior Developer',
#         'company': 'Google',
#         'start_date': '2020-01',
#         'end_date': '2022-05',
#         'description': '...'
#     },
#     ...
# ]

# Detect overlapping periods
overlaps = detect_overlaps(work_history)
# Returns: [
#     {'position1': {...}, 'position2': {...}, 'overlap_months': 3},
#     ...
# ]
```

**Features:**
- Parses work experience sections
- Extracts title, company, dates, description
- Detects overlapping employment periods
- Handles various resume formats

---

## 4. Quality Analysis Layer

### Grammar Checker (`grammar_checker.py`)
**Check resume grammar and writing quality**

```python
from analyzers import check_grammar_resume, get_error_suggestions_summary

result = check_grammar_resume(resume_text)
# Returns: {
#     'is_error_free': False,
#     'error_count': 3,
#     'grammar_errors': [...],
#     'spelling_errors': [...],
#     'style_issues': [...],
#     'readability_score': 7.2
# }

# Get human-readable summary
summary = get_error_suggestions_summary(result)
```

**Features:**
- Grammar error detection
- Spelling error detection
- Style issue identification
- Readability scoring (Flesch Reading Ease)
- Correction suggestions

### Error Detector (`error_detector.py`)
**Detect common resume errors and inconsistencies**

```python
from analyzers import detect_resume_errors, format_errors_for_display

errors = detect_resume_errors(resume_text)
# Returns: {
#     'missing_contact_info': False,
#     'missing_dates': [...],
#     'inconsistent_dates': [...],
#     'short_descriptions': [...],
#     'missing_bullets': [...],
#     'suspicious_patterns': [...]
}

# Format for user display
formatted = format_errors_for_display(errors)
```

**Features:**
- Missing contact information detection
- Inconsistent date format detection
- Short/missing bullet points
- Suspicious pattern detection
- Action verb usage checking

### ATS Simulator (`ats_simulation.py`)
**LLM-based ATS scoring simulation**

```python
from analyzers import evaluate_resume_ats, get_simple_ats_checker

# Simple ATS check
checker = get_simple_ats_checker()
result = checker.check_resume(
    resume_text=resume_text,
    job_description=job_description
)
# Returns: ATSScoreResult(
#     passed=True,
#     overall_score=0.85,
#     keyword_score=0.90,
#     experience_score=0.80,
#     education_score=0.85,
#     suggestions=[...]
# )

# Full ATS evaluation
result = await evaluate_resume_ats(
    resume_text=resume_text,
    job_description=job_description,
    provider="openai"  # or "anthropic", "google"
)
```

**Features:**
- LLM-based keyword matching score
- Experience relevance evaluation
- Education level matching
- Overall fit assessment
- Visual format checking
- Disqualification detection (red flags)
- Improvement suggestions

**Supported LLM providers:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)

**Best for:** Realistic ATS simulation before job applications

---

## 5. Candidate Analysis Layer

### Skill Gap Analyzer (`skill_gap_analyzer.py`)
**Identify and assess skill gaps**

```python
from analyzers import get_skill_gap_analyzer

analyzer = get_skill_gap_analyzer()
result = analyzer.analyze_gaps(
    candidate_skills=["Python", "Django", "PostgreSQL"],
    required_skills=["Python", "Django", "React", "AWS", "Docker"]
)
# Returns: SkillGapResult(
#     matched_skills=['Python', 'Django'],
#     missing_skills=['React', 'AWS', 'Docker'],
#     gap_severity='moderate',  # critical, moderate, minimal, none
#     gap_percentage=60.0,  # 60% of required skills missing
#     bridgeability_score=0.7,  # 0-1, higher = easier to bridge
#     estimated_time_to_bridge=120,  # hours
#     priority_ordering=['React', 'AWS', 'Docker']
# )
```

**Features:**
- Identifies missing required skills
- Matched skills tracking
- Partial match detection (skills present but insufficient proficiency)
- Gap severity assessment (critical/moderate/minimal/none)
- Bridgeability score (how easily gaps can be addressed)
- Estimated time to bridge gaps (in hours)
- Priority ordering for addressing gaps

**Best for:** Training needs assessment, candidate development planning

### Learning Recommendation Engine (`learning_recommendation_engine.py`)
**Match missing skills to learning resources**

```python
from analyzers import get_learning_recommendation_engine

engine = get_learning_recommendation_engine()

# Get recommendations for skill gaps
recommendations = engine.recommend_for_gaps(skill_gap_result)
# Returns: [
#     LearningRecommendation(
#         skill='React',
#         resource_type='course',
#         title='React - The Complete Guide',
#         provider='Udemy',
#         duration_hours=40,
#         cost_amount=15.00,
#         rating=4.8,
#         relevance_score=0.95
#     ),
#     ...
# ]

# Get recommendations for specific skills
recommendations = engine.get_recommendations_for_skills(
    skills=["React", "AWS"],
    max_per_skill=3
)
```

**Features:**
- Matches skills to relevant courses/certifications
- Ranks by quality, relevance, accessibility
- Multiple resource types (courses, certifications, tutorials, books)
- Considers cost, time investment, skill level
- Diverse platform options (Coursera, Udemy, freeCodeCamp, etc.)

**Resource types:**
- Online courses (Udemy, Coursera, edX)
- Certifications (AWS, Google, Microsoft)
- Tutorials (freeCodeCamp, Codecademy)
- Books (O'Reilly, Manning)
- Video series (Pluralsight, LinkedIn Learning)

### Interview Question Generator (`interview_question_generator.py`)
**Generate interview preparation questions**

```python
from analyzers import generate_interview_questions

result = generate_interview_questions(
    resume_text=resume_text,
    job_title="Senior Python Developer",
    job_description="Looking for Python expert with Django experience",
    required_skills=["Python", "Django", "PostgreSQL"],
    num_questions=15
)
# Returns: InterviewPrepResult(
#     total_questions=15,
#     questions=[
#         Question(
#             category=QuestionCategory.TECHNICAL,
#             question="Explain the difference between process and thread in Python.",
#             difficulty="hard",
#             related_skills=["Python", "Concurrency"]
#         ),
#         ...
#     ]
# )
```

**Features:**
- Technical and behavioral questions
- Difficulty levels (easy/medium/hard)
- Skill-specific questions
- General job-related questions
- Context-aware based on resume and job requirements

**Question categories:**
- Technical (coding, frameworks, tools)
- Behavioral (STAR method questions)
- System Design (architecture, scalability)
- Experience (resume-based)
- Culture Fit (soft skills)

**Best for:** Interview preparation, candidate screening

---

## 6. Candidate Ranking Layer

### Ranking Service (`ranking_service.py`)
**ML-based candidate ranking with feature extraction**

```python
# Ranking is typically done via API endpoints
# POST /api/ranking/rank-candidates
# {
#     "vacancy_id": "abc-123",
#     "candidate_ids": ["def-456", "ghi-789"]
# }

# Returns ranked candidates with scores:
# [
#     {
#         "candidate_id": "def-456",
#         "rank": 1,
#         "score": 0.87,
#         "match_confidence": "high",
#         "feature_contributions": {
#             "overall_match_score": 0.35,
#             "keyword_score": 0.15,
#             "tfidf_score": 0.12,
#             "vector_score": 0.10,
#             "experience_relevance": 0.08,
#             "education_quality": 0.07
#         }
#     },
#     ...
# ]
```

**Features:**
- ML models: GradientBoostingClassifier, RandomForestClassifier
- Feature extraction and normalization
- Feature importance tracking
- Model persistence and loading
- Performance metrics tracking

**Features used for ranking:**
- Overall match score (from unified matcher)
- Keyword/TF-IDF/Vector scores
- Experience relevance
- Education quality
- Skill gap percentage
- Historical hiring outcomes (if available)

**Best for:** Candidate shortlisting, hiring decisions

### Fairness Calculator (`fairness_calculator.py`)
**Demographic bias detection in ranking outcomes**

```python
# Typically used via API or scheduled tasks
# POST /api/fairness/analyze
# {
#     "vacancy_id": "abc-123"
# }

# Returns fairness metrics:
# {
#     "disparate_impact_ratio": 0.85,  # 0.8+ is compliant (80% rule)
#     "statistical_parity_difference": 0.05,  # < 0.1 is fair
#     "group_selection_rates": {
#         "male": 0.40,
#         "female": 0.38,
#         "non_binary": 0.35
#     },
#     "bias_alerts": [
#         {
#             "attribute": "age_group",
#             "threshold_exceeded": "statistical_parity",
#             "details": "55+ group has 15% lower selection rate"
#         }
#     ]
# }
```

**Features:**
- Disparate Impact Ratio (80% rule compliance)
- Statistical Parity Difference
- Group selection rate comparison
- Bias alerts when thresholds exceeded
- EEOC/FCRA compliance monitoring

**Demographic groups analyzed:**
- Gender (male, female, non_binary)
- Age groups (under_25, 25_34, 35_44, 45_54, 55_64, 65_plus)
- Ethnicity (asian, hispanic, black_african, white)

**Thresholds:**
- Disparate Impact: 0.8 (80% rule)
- Statistical Parity: 0.1 (10% difference)
- Minimum sample size: 5 per group

**Best for:** Compliance monitoring, ethical AI practices

---

## 7. Infrastructure Layer

### Taxonomy Loader (`taxonomy_loader.py`)
**Load and manage skill taxonomies**

```python
from analyzers import TaxonomyLoader

loader = TaxonomyLoader()

# Load taxonomy
taxonomy = loader.load_taxonomy("skills")
# Returns: {
#     "languages": ["Python", "Java", "JavaScript", ...],
#     "frameworks": ["Django", "Flask", "React", ...],
#     "databases": ["PostgreSQL", "MongoDB", ...],
#     ...
# }

# Get all skills
all_skills = loader.get_all_skills()

# Get skills by category
backend_skills = loader.get_skills_by_category("backend")
```

**Features:**
- JSON-based taxonomy storage
- Category-based organization
- Validation and normalization
- Caching for performance

### Model Version Manager (`model_versioning.py`)
**Manage ML model versions and deployments**

```python
from analyzers import ModelVersionManager

manager = ModelVersionManager()

# Register new model version
manager.register_model(
    model_name="ranking_model_v1",
    model_type="sklearn.ensemble.GradientBoostingClassifier",
    version="1.0.0",
    metrics={"accuracy": 0.85, "f1_score": 0.82}
)

# Load latest model
model = manager.load_model("ranking_model_v1")

# Compare model versions
comparison = manager.compare_versions("v1.0.0", "v2.0.0")
```

**Features:**
- Model version tracking
- Model metadata storage
- Performance metrics tracking
- A/B testing support
- Rollback capabilities

### Accuracy Benchmark (`accuracy_benchmark.py`)
**Benchmark and validate ML model accuracy**

```python
from analyzers import AccuracyBenchmark

benchmark = AccuracyBenchmark()

# Benchmark skill extractor
results = benchmark.benchmark_skill_extractor(
    test_resumes=test_data,
    ground_truth=ground_truth_labels
)

# Benchmark matcher
results = benchmark.benchmark_matcher(
    matcher=unified_matcher,
    test_pairs=resume_vacancy_pairs
)

# Generate report
report = benchmark.generate_report(results)
```

**Features:**
- Accuracy metrics calculation
- Precision/Recall/F1 scoring
- Confusion matrix generation
- Comparison across methods
- Statistical significance testing

### Performance Tracker (`performance_tracker.py`)
**Track ML pipeline performance metrics**

```python
from analyzers import PerformanceTracker

tracker = PerformanceTracker()

# Track metric
tracker.track_metric(
    metric_name="skill_extraction_time",
    value=0.15,  # seconds
    tags={"method": "ner", "model": "bert-base-NER"}
)

# Get statistics
stats = tracker.get_statistics("skill_extraction_time")
# Returns: {
#     "mean": 0.15,
#     "p50": 0.14,
#     "p95": 0.20,
#     "p99": 0.25,
#     "min": 0.10,
#     "max": 0.30
# }
```

**Features:**
- Metric tracking over time
- Percentile calculations
- Tag-based filtering
- Performance anomaly detection
- Export to monitoring systems

---

## 8. API Integration

### Matching Endpoints

#### Traditional Matching: `POST /api/matching/compare`
Uses EnhancedSkillMatcher with synonym and fuzzy matching.

**Request:**
```json
{
    "resume_id": "abc-123",
    "vacancy_data": {
        "title": "React Developer",
        "description": "Looking for React expert with TypeScript",
        "required_skills": ["React", "TypeScript", "JavaScript"]
    }
}
```

#### Unified Matching: `POST /api/matching/compare-unified`
Uses all three methods (Enhanced + TF-IDF + Vector).

**Response:**
```json
{
    "overall_score": 0.75,
    "keyword_score": 0.67,
    "tfidf_score": 0.80,
    "vector_score": 0.72,
    "recommendation": "good",
    "matched_skills": ["React", "Python"],
    "missing_skills": ["TypeScript"]
}
```

### Analysis Endpoints

#### ATS Scoring: `POST /api/analysis/ats-score`
```json
{
    "resume_text": "...",
    "job_description": "...",
    "provider": "openai"
}
```

#### Skill Gaps: `POST /api/analysis/skill-gaps`
```json
{
    "resume_id": "abc-123",
    "vacancy_id": "def-456"
}
```

#### Interview Prep: `POST /api/analysis/interview-questions`
```json
{
    "resume_text": "...",
    "job_title": "Senior Python Developer",
    "job_description": "...",
    "required_skills": ["Python", "Django"],
    "num_questions": 15
}
```

### Ranking Endpoints

#### Rank Candidates: `POST /api/ranking/rank-candidates`
```json
{
    "vacancy_id": "abc-123",
    "candidate_ids": ["def-456", "ghi-789"]
}
```

#### Fairness Analysis: `POST /api/fairness/analyze`
```json
{
    "vacancy_id": "abc-123"
}
```

---

## 9. Performance Comparison

### Skill Extraction Methods

| Method | Speed | Accuracy | Predefined Skills | Use Case |
|--------|-------|----------|-------------------|----------|
| **HF NER** | ⚡⚡⚡ | 🎯🎯🎯 | ❌ No | General extraction, no taxonomy |
| **HF Zero-Shot** | ⚡ | 🎯🎯🎯🎯 | ✅ Yes | Matching job requirements |
| **Automatic** | ⚡⚡ | 🎯🎯🎯 | Optional | Best all-around, fallback safe |
| **Keyword (RAKE)** | ⚡⚡⚡ | 🎯🎯 | ❌ No | Simple use cases, fast |

### Skill Matching Methods

| Matcher | Speed | Accuracy | Best For |
|---------|-------|----------|----------|
| **EnhancedSkillMatcher** | ⚡⚡⚡ | 🎯🎯 | Quick keyword matching, synonym support |
| **TfidfSkillMatcher** | ⚡⚡ | 🎯🎯🎯 | Identifying important missing skills |
| **VectorSimilarityMatcher** | ⚡ | 🎯🎯🎯 | Semantic meaning, different phrasings |
| **UnifiedSkillMatcher** | ⚡ | 🎯🎯🎯🎯 | Best overall accuracy, comprehensive analysis |

### Analysis Services

| Service | Latency | Resource Usage | Best For |
|---------|---------|----------------|----------|
| **Grammar Check** | ~100ms | Low | Writing quality |
| **Error Detection** | ~50ms | Low | Resume completeness |
| **Skill Gap Analysis** | ~200ms | Low | Training needs |
| **ATS Simulation** | ~2-5s | High (LLM) | Job applications |
| **Interview Generation** | ~3-5s | High (LLM) | Interview prep |
| **Candidate Ranking** | ~500ms | Medium | Hiring decisions |

---

## 10. Best Practices

### When to Use Each Component

**For Resume Parsing:**
1. Use `extract_top_skills_auto` for skill extraction (with fallback)
2. Use `extract_work_experience` for work history
3. Use `calculate_total_experience` for total tenure
4. Use `check_grammar_resume` for quality check

**For Candidate Matching:**
1. Use `get_unified_matcher` for best accuracy (all 3 methods)
2. Use `EnhancedSkillMatcher` for quick real-time matching
3. Use `get_skill_gap_analyzer` for training needs
4. Use `get_learning_recommendation_engine` for development plans

**For Hiring Decisions:**
1. Use `evaluate_resume_ats` for job applications
2. Use `generate_interview_questions` for interview prep
3. Use candidate ranking API for shortlisting
4. Use fairness analysis for compliance monitoring

### Performance Optimization

1. **Model Caching:** All ML models are cached after first load
2. **Batch Processing:** Load models once, process multiple resumes
3. **Text Truncation:** Models automatically truncate long text
4. **Feature Extraction:** Extract features once, reuse across models

### Error Handling

1. **Fallback Chain:** Automatic extraction tries multiple methods
2. **Graceful Degradation:** If model fails, falls back to simpler method
3. **Confidence Scores:** All extraction methods provide confidence
4. **Validation:** All analyzers validate inputs and provide clear errors

---

## 11. Dependencies

### ML Libraries
```txt
scikit-learn==1.5.0        # TF-IDF, classifiers
transformers==4.46.0       # Hugging Face models
torch==2.4.0               # PyTorch backend
sentence-transformers==2.2.0  # Semantic similarity
spacy==3.7.2               # NER, keyword extraction
```

### NLP Models
```python
# Hugging Face
"dslim/bert-base-NER"           # General NER
"yashpwr/resume-ner-bert-v2"   # Resume-specific NER
"sentence-transformers/all-MiniLM-L6-v2"  # Semantic similarity

# SpaCy
"en_core_web_sm"                # English NER (lightweight)
"en_core_web_md"                # English NER (medium accuracy)
```

### Optional: LLM Providers
```txt
openai==1.12.0         # OpenAI GPT models
anthropic==0.18.0      # Anthropic Claude models
google-generativeai    # Google Gemini models
```

---

## 12. Troubleshooting

### "Transformers not installed"
```bash
docker exec -u root resume_analysis_backend pip install transformers torch
```

### "CUDA out of memory"
Extractors automatically use CPU. To enable GPU:
```python
# In hf_skill_extractor.py, change device=-1 to device=0
_ner_pipeline = pipeline("ner", model=model_name, device=0)  # GPU
```

### Model Loading Takes Too Long
Models are cached after first load. For persistent cache:
```bash
export HF_HOME=/path/to/cache
```

### No Skills Extracted
1. Check text length (min 10 characters)
2. Lower the `min_score` threshold
3. Try a different extraction method
4. Use zero-shot with predefined skills

### Matcher Returns Zero Scores
1. Check if resume text is not empty
2. Verify required_skills is not empty
3. Check for encoding issues
4. Try individual matchers to isolate issue

---

## 13. Future Enhancements

### Planned Improvements
1. **More Resume-Specific Models:** Fine-tune models on resume datasets
2. **Multi-language Support:** Add NER models for other languages
3. **Explainability:** Add SHAP values for ranking decisions
4. **Continuous Learning:** Auto-retrain on feedback data
5. **Custom Taxonomies:** Support company-specific skill taxonomies

### Research Directions
1. **Few-shot Learning:** Reduce training data needs
2. **Cross-lingual Matching:** Match skills across languages
3. **Career Trajectory Prediction:** Predict career progression
4. **Salary Estimation:** Estimate market value from skills
5. **Soft Skills Detection:** Extract soft skills from descriptions

---

## 14. References

### Related Documentation
- [MATCHERS_GUIDE.md](../analyzers/MATCHERS_GUIDE.md) - Detailed matcher guide
- [HF_EXTRACTOR_README.md](../analyzers/HF_EXTRACTOR_README.md) - Hugging Face extractor guide
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Backend architecture overview
- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API documentation

### External Resources
- [Hugging Face Models](https://huggingface.co/models) - Pre-trained models
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities) - NER documentation
- [Sentence Transformers](https://www.sbert.net/) - Semantic similarity
- [scikit-learn](https://scikit-learn.org/) - ML algorithms

---

**Last Updated:** 2026-02-01
**Maintainer:** Backend Team
**Version:** 1.0.0
