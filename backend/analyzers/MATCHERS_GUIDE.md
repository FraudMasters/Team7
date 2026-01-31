# Skill Matching Methods

This directory contains multiple skill matching strategies that can be used individually or combined.

## Available Matchers

### 1. EnhancedSkillMatcher (`enhanced_matcher.py`)
**Traditional keyword-based matching with intelligence**

Features:
- Direct name matching
- Synonym-based matching (via skill_synonyms.json)
- Context-aware matching (web_framework, database, language)
- Fuzzy matching for typos (SequenceMatcher)
- Compound skill matching (C/C++ → C, C++)
- Language hierarchy matching (C++ implies C knowledge)

```python
from analyzers import EnhancedSkillMatcher

matcher = EnhancedSkillMatcher()
result = matcher.match_multiple(
    resume_skills=['ReactJS', 'Python', 'PostgreSQL'],
    required_skills=['React', 'Python', 'SQL']
)
# Returns: {'React': {'matched': True, 'confidence': 1.0, 'match_type': 'direct'}, ...}
```

### 2. TfidfSkillMatcher (`tfidf_matcher.py`)
**TF-IDF weighted keyword matching**

Features:
- Uses TF-IDF to rank keyword importance
- Identifies missing keywords ranked by importance
- N-gram support (1-2 grams) for phrases
- Weighted scoring (important keywords count more)

```python
from analyzers import get_tfidf_matcher

matcher = get_tfidf_matcher()
result = matcher.match(
    resume_text="Experienced with React and Python",
    job_title="Senior React Developer",
    job_description="Looking for React expert",
    required_skills=["React", "Python", "TypeScript"]
)
# Returns: TfidfMatchResult(score=0.67, missing_keywords=['TypeScript'], ...)
```

### 3. VectorSimilarityMatcher (`vector_matcher.py`)
**Semantic similarity using sentence-transformers**

Features:
- Semantic understanding beyond keywords
- Finds similarity in meaning (e.g., "JS developer" ≈ "JavaScript programmer")
- Uses cosine similarity on embeddings
- Model: all-MiniLM-L6-v2 (fast, 384dim)

```python
from analyzers import get_vector_matcher

matcher = get_vector_matcher()
result = matcher.match(
    resume_text="Experienced web developer with React expertise",
    job_title="Frontend Developer",
    job_description="Looking for React.js specialist",
    required_skills=["React"]
)
# Returns: VectorMatchResult(score=0.85, similarity=0.70, ...)
```

### 4. UnifiedSkillMatcher (`unified_matcher.py`)
**Combines all three methods for best results**

Features:
- Combines Enhanced + TF-IDF + Vector matching
- Weighted overall score (default: 50% keyword, 30% TF-IDF, 20% vector)
- Generates hiring recommendation (excellent/good/maybe/poor)
- Most comprehensive matching approach

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
#     recommendation='good',
#     matched_skills=['React', 'Python'],
#     missing_skills=['TypeScript']
# )
```

## API Endpoints

### Traditional Matching: `POST /api/matching/compare`
Uses EnhancedSkillMatcher with synonym and fuzzy matching.

### Unified Matching: `POST /api/matching/compare-unified`
Uses all three methods (Enhanced + TF-IDF + Vector) for comprehensive scoring.

Request format:
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

Response includes:
- `overall_score`: Combined score (0-1)
- `keyword_score`: Enhanced matching score
- `tfidf_score`: TF-IDF weighted score
- `vector_score`: Semantic similarity score
- `recommendation`: excellent/good/maybe/poor
- `matched_skills`: List of matched skills
- `missing_skills`: List of missing skills (ranked by importance)

## Which Matcher to Use?

| Matcher | Use Case | Speed | Accuracy |
|---------|----------|-------|----------|
| EnhancedSkillMatcher | Quick keyword matching, synonym support | ⚡⚡⚡ | 🎯🎯 |
| TfidfSkillMatcher | Need to know which skills are most important | ⚡⚡ | 🎯🎯🎯 |
| VectorSimilarityMatcher | Semantic meaning matters, different phrasings | ⚡ | 🎯🎯🎯 |
| UnifiedSkillMatcher | Best overall accuracy, comprehensive analysis | ⚡ | 🎯🎯🎯🎯 |

## Performance Notes

- **EnhancedSkillMatcher**: Fastest, suitable for real-time matching
- **TfidfSkillMatcher**: Fast, sklearn-based vectorization
- **VectorSimilarityMatcher**: Slower due to model loading (cached after first use)
- **UnifiedSkillMatcher**: Uses all three, but still acceptable latency (~200-500ms)

The sentence-transformers model (all-MiniLM-L6-v2) is:
- ~80MB in size
- Loads once and cached
- Fast inference (~50ms per text)
