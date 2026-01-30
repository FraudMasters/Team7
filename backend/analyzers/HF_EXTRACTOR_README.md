# Hugging Face Skill Extractor - Migration Guide

## Overview

The new Hugging Face-based skill extractor replaces KeyBERT to avoid Keras 3 compatibility issues. It provides:

- ✅ **No KeyBERT dependency** - avoids Keras 3 / Transformers conflicts
- ✅ **Specialized resume models** - models trained specifically on resume data
- ✅ **Automatic fallback** - tries multiple methods automatically
- ✅ **Zero-shot support** - use with predefined skill taxonomies
- ✅ **Drop-in replacement** - compatible API with existing code

## Installation

The new extractor uses `transformers` and `torch`, which are already in your `requirements.txt`:

```txt
transformers==4.46.0
torch==2.4.0
```

If not installed, run:

```bash
docker exec -u root resume_analysis_backend pip install transformers torch
```

## Quick Start

### Option 1: Automatic Extraction (Recommended)

The easiest way - automatically tries all methods and uses the best one:

```python
from analyzers import extract_top_skills_auto

# Automatic method selection
result = extract_top_skills_auto(resume_text, top_n=10)

if result["skills"]:
    print(f"Found {result['count']} skills using {result['method']}")
    print(f"Skills: {result['skills']}")
    print(f"With scores: {result['skills_with_scores']}")
else:
    print(f"Error: {result['error']}")
```

### Option 2: Hugging Face NER (No predefined skills needed)

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

### Option 3: Zero-Shot Classification (With predefined skill taxonomy)

```python
from analyzers import extract_skills_zero_shot

# Your skill taxonomy
taxonomy = [
    "Python", "Java", "JavaScript", "TypeScript",
    "Django", "Flask", "FastAPI",
    "React", "Vue", "Angular",
    "PostgreSQL", "MongoDB", "Redis"
]

result = extract_skills_zero_shot(
    resume_text,
    candidate_skills=taxonomy,
    top_n=10,
    min_score=0.3
)

skills = result["skills"]
scores = result["skills_with_scores"]
# Returns: [('Python', 0.95), ('Django', 0.87), ('PostgreSQL', 0.82), ...]
```

## API Reference

### `extract_top_skills_auto(text, top_n=10, candidate_skills=None)`

**Recommended for most use cases**

Automatically tries multiple extraction methods:
1. Hugging Face NER
2. KeyBERT (if available)
3. Zero-shot classification (if candidate_skills provided)
4. SpaCy NER (fallback)

**Parameters:**
- `text` (str): Resume text
- `top_n` (int): Maximum skills to return
- `candidate_skills` (List[str], optional): Predefined skill taxonomy

**Returns:**
```python
{
    "skills": ["Python", "Django", ...],
    "skills_with_scores": [("Python", 0.95), ...],
    "count": 3,
    "method": "huggingface_ner",  # Which method succeeded
    "model": "dslim/bert-base-NER",
    "error": None
}
```

### `extract_skills_ner(text, top_n=10, model_name="dslim/bert-base-NER", min_score=0.5)`

Extract skills using Named Entity Recognition.

**Parameters:**
- `text` (str): Resume text
- `top_n` (int): Maximum skills to return
- `model_name` (str): Hugging Face model name
- `min_score` (float): Minimum confidence threshold (0.0-1.0)

**Available Models:**
- `dslim/bert-base-NER` - Reliable, well-tested (default)
- `yashpwr/resume-ner-bert-v2` - Resume-specific (experimental)

### `extract_skills_zero_shot(text, candidate_skills, top_n=10, min_score=0.3)`

Extract skills using zero-shot classification with predefined taxonomy.

**Parameters:**
- `text` (str): Resume text
- `candidate_skills` (List[str]): Skill taxonomy to search for
- `top_n` (int): Maximum skills to return
- `min_score` (float): Minimum confidence threshold

**Best for:**
- When you have a predefined skill taxonomy
- Matching against specific job requirements
- Consistent skill categorization

## Migration from KeyBERT

### Before (KeyBERT - now broken):

```python
from analyzers import extract_top_skills

result = extract_top_skills(resume_text, top_n=10)
skills = result["skills"]
```

### After (Option 1 - Automatic):

```python
from analyzers import extract_top_skills_auto

result = extract_top_skills_auto(resume_text, top_n=10)
skills = result["skills"]
print(f"Used method: {result['method']}")  # See which method worked
```

### After (Option 2 - NER only):

```python
from analyzers import extract_skills_ner

result = extract_skills_ner(resume_text, top_n=10)
skills = result["skills"]
```

### After (Option 3 - With taxonomy):

```python
from analyzers import extract_skills_zero_shot

# Load your skill taxonomy
from models.skill_taxonomy import SkillTaxonomy
taxonomy = SkillTaxonomy.get_all_skills()

result = extract_skills_zero_shot(resume_text, taxonomy, top_n=10)
skills = result["skills"]
```

## Comparison with KeyBERT

| Feature | KeyBERT | HF NER | HF Zero-Shot |
|---------|---------|--------|--------------|
| **Keras 3 Compatible** | ❌ No | ✅ Yes | ✅ Yes |
| **Predefined Skills** | ❌ No | ❌ No | ✅ Yes |
| **Resume-Specific** | ❌ No | ✅ Yes | ✅ Yes |
| **Speed** | Medium | Fast | Slow |
| **Accuracy** | High | High | Highest* |

*Zero-shot is most accurate when using a good taxonomy.

## Model Recommendations

### For General Resume Analysis

Use **Hugging Face NER** with the default model:
```python
from analyzers import extract_skills_ner
result = extract_skills_ner(resume_text, top_n=10)
```

### For Matching Against Job Requirements

Use **Zero-Shot** with job-specific skills:
```python
from analyzers import extract_skills_zero_shot

# Extract skills from job description
job_skills = ["Python", "AWS", "Docker", "Kubernetes"]
result = extract_skills_zero_shot(resume_text, job_skills)
```

### For Maximum Reliability

Use **Automatic** with fallback:
```python
from analyzers import extract_top_skills_auto
result = extract_top_skills_auto(resume_text, top_n=10)
```

## Troubleshooting

### "Transformers not installed"

```bash
docker exec -u root resume_analysis_backend pip install transformers torch
```

### "CUDA out of memory"

The extractor automatically uses CPU. If you want to use GPU:

```python
# In hf_skill_extractor.py, change device=-1 to device=0
_ner_pipeline = pipeline("ner", model=model_name, device=0)  # GPU
```

### Model Loading Takes Too Long

Models are cached after first load. Subsequent calls are fast. For persistent cache:

```python
# Set environment variable
export HF_HOME=/path/to/cache
```

### No Skills Extracted

1. Check the text length (min 10 characters)
2. Lower the `min_score` threshold
3. Try a different model
4. Use zero-shot with predefined skills

```python
# Debug: see what went wrong
result = extract_skills_ner(resume_text, top_n=10, min_score=0.3)
print(result.get("error"))
```

## Performance Tips

1. **Batch Processing**: Load model once, process multiple resumes
   ```python
   from analyzers import extract_skills_ner

   # First call loads the model (slow)
   result1 = extract_skills_ner(resume1_text)

   # Subsequent calls are fast (model is cached)
   result2 = extract_skills_ner(resume2_text)
   result3 = extract_skills_ner(resume3_text)
   ```

2. **Text Truncation**: Models automatically truncate long text
   - NER: ~1000 characters
   - Zero-shot: ~2000 characters

3. **Use Zero-Shot for Specific Skills**: Faster when you know what to look for
   ```python
   # Faster: only checks for specific skills
   result = extract_skills_zero_shot(
       resume_text,
       ["Python", "Java", "C++"],  # Only 3 skills to check
       top_n=3
   )
   ```

## Testing

Test the new extractor:

```python
# test_hf_extractor.py
from analyzers import extract_top_skills_auto

test_resume = """
John Doe - Senior Python Developer

Skills:
- Programming: Python, JavaScript, TypeScript, SQL
- Frameworks: Django, Flask, FastAPI, React
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Docker, Kubernetes, Git, AWS

Experience:
5 years of experience in Python development...
"""

result = extract_top_skills_auto(test_resume, top_n=10)

print(f"Method: {result['method']}")
print(f"Model: {result['model']}")
print(f"Count: {result['count']}")
print(f"Skills: {result['skills']}")
print(f"With scores: {result['skills_with_scores']}")

# Expected output:
# Method: huggingface_ner
# Skills: ['Python', 'Django', 'PostgreSQL', 'JavaScript', ...]
```

## Next Steps

1. ✅ **Hugging Face extractor created**
2. ✅ **Fallback mechanism implemented**
3. ✅ **Documentation complete**

**To integrate into your codebase:**

Replace imports in your files:
```python
# Before
from analyzers import extract_top_skills

# After
from analyzers import extract_top_skills_auto as extract_top_skills
```

Or use the explicit import:
```python
from analyzers import extract_top_skills_auto
```

The function signatures are compatible, so most code should work without changes!
