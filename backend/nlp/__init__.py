"""
NLP processing modules for resume parsing.

This package contains natural language processing components for extracting
structured information from resume text, including:
- Entity extraction (positions, education, age, languages)
- Skills extraction and matching
- Text normalization and preprocessing
"""

from nlp.resume_entities import (
    extract_resume_entities,
    extract_position,
    extract_education,
    extract_age,
    extract_languages,
)

__all__ = [
    "extract_resume_entities",
    "extract_position",
    "extract_education",
    "extract_age",
    "extract_languages",
]
