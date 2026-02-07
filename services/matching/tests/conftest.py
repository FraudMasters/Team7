"""
Pytest configuration and fixtures for Matching Service tests.

This module provides common fixtures and configuration for running tests.
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_synonyms_data():
    """Sample synonyms data for testing."""
    return {
        "databases": {
            "SQL": ["SQL", "PostgreSQL", "MySQL", "SQLite"],
            "NoSQL": ["MongoDB", "Cassandra", "Redis", "DynamoDB"]
        },
        "programming_languages": {
            "JavaScript": ["JavaScript", "JS", "ECMAScript"],
            "Python": ["Python", "Python 3", "Python3"]
        },
        "web_frameworks": {
            "React": ["React", "ReactJS", "React.js", "ReactJS"],
            "Vue": ["Vue", "Vue.js", "VueJS"],
            "Angular": ["Angular", "AngularJS", "Angular.js"]
        }
    }


@pytest.fixture
def sample_resume_skills():
    """Sample resume skills for testing."""
    return [
        "Python",
        "Django",
        "PostgreSQL",
        "JavaScript",
        "React",
        "Docker",
        "Git",
        "REST APIs"
    ]


@pytest.fixture
def sample_vacancy_data():
    """Sample vacancy data for testing."""
    return {
        "title": "Senior Full Stack Developer",
        "description": "Looking for an experienced developer with Python, Django, and React skills.",
        "required_skills": ["Python", "Django", "React", "Docker"],
        "additional_skills": ["AWS", "Kubernetes", "Redis"],
        "min_experience_months": 36
    }


@pytest.fixture
def sample_match_result():
    """Sample match result for testing."""
    return {
        "matched": True,
        "confidence": 0.95,
        "matched_as": "ReactJS",
        "match_type": "synonym"
    }


@pytest.fixture
def temp_synonyms_file(tmp_path, sample_synonyms_data):
    """Create a temporary synonyms file for testing."""
    synonyms_file = tmp_path / "test_synonyms.json"
    with open(synonyms_file, "w") as f:
        json.dump(sample_synonyms_data, f)
    return synonyms_file


@pytest.fixture
def mock_uuid():
    """Mock UUID for testing."""
    return uuid4()


@pytest.fixture
def caplog(caplog):
    """Extend caplog fixture with custom configuration."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog
