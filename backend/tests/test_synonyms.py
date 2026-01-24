"""
Tests for skill synonym matching functionality.

Tests cover loading synonyms, normalizing skill names,
checking skill matches, and finding matching synonyms.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from api.matching import (
    load_skill_synonyms,
    normalize_skill_name,
    check_skill_match,
    find_matching_synonym,
)


class TestNormalizeSkillName:
    """Tests for normalize_skill_name function."""

    def test_basic_normalization(self):
        """Test basic skill name normalization."""
        result = normalize_skill_name("React JS")
        assert result == "react js"

    def test_leading_trailing_whitespace(self):
        """Test removing leading and trailing whitespace."""
        result = normalize_skill_name("  Python  ")
        assert result == "python"

    def test_multiple_spaces(self):
        """Test removing multiple internal spaces."""
        result = normalize_skill_name("Machine   Learning")
        assert result == "machine learning"

    def test_case_insensitive(self):
        """Test case is converted to lowercase."""
        result = normalize_skill_name("POSTGRESQL")
        assert result == "postgresql"

    def test_mixed_case(self):
        """Test mixed case is normalized."""
        result = normalize_skill_name("JaVa ScRiPt")
        assert result == "java script"

    def test_tabs_and_newlines(self):
        """Test tabs and newlines are handled."""
        result = normalize_skill_name("\tDjango\t\nFramework\n")
        assert result == "django framework"

    def test_empty_string(self):
        """Test empty string normalization."""
        result = normalize_skill_name("")
        assert result == ""

    def test_only_whitespace(self):
        """Test string with only whitespace."""
        result = normalize_skill_name("   \t\n  ")
        assert result == ""

    def test_single_word(self):
        """Test single word skill."""
        result = normalize_skill_name("Python")
        assert result == "python"

    def test_multi_word_skill(self):
        """Test multi-word skill."""
        result = normalize_skill_name("Natural Language Processing")
        assert result == "natural language processing"

    def test_special_characters(self):
        """Test special characters are preserved."""
        result = normalize_skill_name("C++")
        assert result == "c++"

    def test_dots_and_slashes(self):
        """Test dots and slashes in skill names."""
        result = normalize_skill_name("Node.js / Express.js")
        assert result == "node.js / express.js"


class TestLoadSkillSynonyms:
    """Tests for load_skill_synonyms function."""

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["SQL", "PostgreSQL", "MySQL"],
            "PostgreSQL": ["PostgreSQL", "Postgres"]
        },
        "web_frameworks": {
            "React": ["React", "ReactJS", "React.js"]
        }
    }''')
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_successful_loading(self, mock_file):
        """Test successful loading of synonyms file."""
        result = load_skill_synonyms()

        assert "SQL" in result
        assert "PostgreSQL" in result
        assert "React" in result
        assert result["SQL"] == ["SQL", "PostgreSQL", "MySQL"]
        assert result["PostgreSQL"] == ["PostgreSQL", "Postgres"]
        assert result["React"] == ["React", "ReactJS", "React.js"]

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_file_not_found(self, mock_file):
        """Test handling when synonyms file is not found."""
        result = load_skill_synonyms()
        assert result == {}

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_invalid_json(self, mock_file):
        """Test handling of invalid JSON."""
        result = load_skill_synonyms()
        assert result == {}

    @patch("api.matching._skill_synonyms_cache")
    def test_cache_used(self, mock_cache):
        """Test that cached value is used on subsequent calls."""
        mock_cache.return_value = {"Test": ["Test", "Testing"]}

        result = load_skill_synonyms()

        assert result == mock_cache.return_value
        # Should not try to open file

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["SQL", "PostgreSQL"]
        }
    }''')
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_canonical_name_added_to_synonyms(self, mock_file):
        """Test that canonical name is added to its own synonym list."""
        result = load_skill_synonyms()

        # Canonical name "SQL" should be in its own list
        assert "SQL" in result["SQL"]

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["PostgreSQL", "MySQL"]
        }
    }''')
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_synonyms_deduplicated(self, mock_file):
        """Test that synonyms are deduplicated."""
        result = load_skill_synonyms()

        # Should have unique values
        assert len(result["SQL"]) == len(set(result["SQL"]))

    @patch("api.matching._skill_synonyms_cache", None)
    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "category1": {"Skill1": ["Skill1", "Skill1a"]},
        "category2": {"Skill2": ["Skill2", "Skill2a"]}
    }''')
    @patch("api.matching.SYNONYMS_FILE", Path("/test/synonyms.json"))
    def test_multiple_categories_merged(self, mock_file):
        """Test that multiple categories are merged into single dict."""
        result = load_skill_synonyms()

        assert len(result) == 2
        assert "Skill1" in result
        assert "Skill2" in result


class TestCheckSkillMatch:
    """Tests for check_skill_match function."""

    def test_direct_match_case_insensitive(self):
        """Test direct match is case-insensitive."""
        resume_skills = ["Python", "Java", "Django"]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "python", synonyms_map)

        assert result is True

    def test_direct_match_with_whitespace(self):
        """Test direct match with whitespace normalization."""
        resume_skills = ["Machine Learning", "Deep Learning"]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "  machine   learning  ", synonyms_map)

        assert result is True

    def test_no_match(self):
        """Test when skill is not found."""
        resume_skills = ["Python", "Java"]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "Ruby", synonyms_map)

        assert result is False

    def test_synonym_match_postgresql_sql(self):
        """Test synonym match: PostgreSQL matches SQL."""
        resume_skills = ["Python", "PostgreSQL", "Django"]
        synonyms_map = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}

        result = check_skill_match(resume_skills, "SQL", synonyms_map)

        assert result is True

    def test_synonym_match_react_reactjs(self):
        """Test synonym match: ReactJS matches React."""
        resume_skills = ["ReactJS", "TypeScript", "Node.js"]
        synonyms_map = {"React": ["React", "ReactJS", "React.js"]}

        result = check_skill_match(resume_skills, "React", synonyms_map)

        assert result is True

    def test_synonym_match_js_javascript(self):
        """Test synonym match: JS matches JavaScript."""
        resume_skills = ["HTML", "CSS", "JS"]
        synonyms_map = {"JavaScript": ["JavaScript", "JS", "ES6"]}

        result = check_skill_match(resume_skills, "JavaScript", synonyms_map)

        assert result is True

    def test_synonym_match_via_synonym_list(self):
        """Test matching when required skill is in synonym list."""
        resume_skills = ["Python", "Java"]
        synonyms_map = {"Python": ["Python", "Python 3", "Python3"]}

        # Required skill is a synonym
        result = check_skill_match(resume_skills, "Python 3", synonyms_map)

        assert result is True

    def test_multiple_synonyms_one_match(self):
        """Test with multiple skills, only one matches."""
        resume_skills = ["Python", "Django", "Flask"]
        synonyms_map = {"Java": ["Java", "Java EE"]}

        result = check_skill_match(resume_skills, "Java", synonyms_map)

        assert result is False

    def test_complex_synonym_chain(self):
        """Test complex synonym chain."""
        resume_skills = ["Postgres"]
        synonyms_map = {
            "SQL": ["SQL", "PostgreSQL", "MySQL"],
            "PostgreSQL": ["PostgreSQL", "Postgres", "Postgres SQL"]
        }

        result = check_skill_match(resume_skills, "SQL", synonyms_map)

        assert result is True

    def test_case_insensitive_synonym_match(self):
        """Test synonym matching is case-insensitive."""
        resume_skills = ["REACTJS", "TYPESCRIPT"]
        synonyms_map = {"React": ["React", "ReactJS", "React.js"]}

        result = check_skill_match(resume_skills, "react", synonyms_map)

        assert result is True

    def test_empty_resume_skills(self):
        """Test with empty resume skills list."""
        resume_skills = []
        synonyms_map = {}

        result = check_skill_match(resume_skills, "Python", synonyms_map)

        assert result is False

    def test_empty_synonyms_map(self):
        """Test with empty synonyms map."""
        resume_skills = ["Python", "Java"]

        result = check_skill_match(resume_skills, "Python", {})

        assert result is True

    def test_partial_word_no_match(self):
        """Test partial words don't match."""
        resume_skills = ["Django", "Flask"]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "Djang", synonyms_map)

        assert result is False


class TestFindMatchingSynonym:
    """Tests for find_matching_synonym function."""

    def test_find_direct_match(self):
        """Test finding direct match returns the skill."""
        resume_skills = ["Python", "Java", "Django"]
        synonyms_map = {}

        result = find_matching_synonym(resume_skills, "python", synonyms_map)

        assert result == "Python"

    def test_find_synonym_match(self):
        """Test finding synonym match returns the resume skill."""
        resume_skills = ["Python", "PostgreSQL", "Django"]
        synonyms_map = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}

        result = find_matching_synonym(resume_skills, "SQL", synonyms_map)

        assert result == "PostgreSQL"

    def test_no_match_returns_none(self):
        """Test when no match found returns None."""
        resume_skills = ["Python", "Java"]
        synonyms_map = {}

        result = find_matching_synonym(resume_skills, "Ruby", synonyms_map)

        assert result is None

    def test_find_reactjs_for_react(self):
        """Test finding ReactJS when React is required."""
        resume_skills = ["ReactJS", "TypeScript"]
        synonyms_map = {"React": ["React", "ReactJS", "React.js"]}

        result = find_matching_synonym(resume_skills, "React", synonyms_map)

        assert result == "ReactJS"

    def test_find_js_for_javascript(self):
        """Test finding JS when JavaScript is required."""
        resume_skills = ["HTML", "CSS", "JS"]
        synonyms_map = {"JavaScript": ["JavaScript", "JS", "ES6"]}

        result = find_matching_synonym(resume_skills, "JavaScript", synonyms_map)

        assert result == "JS"

    def test_returns_exact_resume_skill(self):
        """Test that exact resume skill name is returned."""
        resume_skills = ["  ReactJS  ", "TypeScript"]  # Note: spaces
        synonyms_map = {"React": ["React", "ReactJS"]}

        result = find_matching_synonym(resume_skills, "React", synonyms_map)

        # Should return the original skill from resume, with spaces
        assert result == "  ReactJS  "

    def test_case_preserved(self):
        """Test that case from resume is preserved."""
        resume_skills = ["REACTJS", "Typescript"]
        synonyms_map = {"React": ["React", "ReactJS"]}

        result = find_matching_synonym(resume_skills, "react", synonyms_map)

        assert result == "REACTJS"

    def test_first_match_returned(self):
        """Test that first match is returned when multiple exist."""
        resume_skills = ["Postgres", "PostgreSQL"]
        synonyms_map = {"SQL": ["SQL", "PostgreSQL"]}

        result = find_matching_synonym(resume_skills, "SQL", synonyms_map)

        assert result == "Postgres"  # First match

    def test_synonym_in_resume_for_canonical(self):
        """Test when resume has synonym for canonical name."""
        resume_skills = ["Postgres"]
        synonyms_map = {"PostgreSQL": ["PostgreSQL", "Postgres"]}

        result = find_matching_synonym(resume_skills, "PostgreSQL", synonyms_map)

        assert result == "Postgres"

    def test_empty_resume_skills(self):
        """Test with empty resume skills."""
        resume_skills = []
        synonyms_map = {}

        result = find_matching_synonym(resume_skills, "Python", synonyms_map)

        assert result is None

    def test_empty_synonyms_map(self):
        """Test with empty synonyms map."""
        resume_skills = ["Python", "Java"]

        result = find_matching_synonym(resume_skills, "Python", {})

        assert result == "Python"


class TestSkillMatchingScenarios:
    """Tests for real-world skill matching scenarios."""

    def test_database_synonym_matching(self):
        """Test database skill synonym scenarios."""
        resume_skills = ["PostgreSQL", "MongoDB", "Redis"]
        synonyms_map = {
            "SQL": ["SQL", "PostgreSQL", "MySQL", "SQLite"],
            "MongoDB": ["MongoDB", "Mongo", "Mongoose"],
            "Redis": ["Redis", "Redis Cache"]
        }

        # SQL should match PostgreSQL
        assert check_skill_match(resume_skills, "SQL", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "SQL", synonyms_map) == "PostgreSQL"

        # MongoDB direct match
        assert check_skill_match(resume_skills, "Mongo", synonyms_map) is True

        # Oracle not in resume
        assert check_skill_match(resume_skills, "Oracle", synonyms_map) is False

    def test_web_framework_synonym_matching(self):
        """Test web framework synonym scenarios."""
        resume_skills = ["ReactJS", "ExpressJS", "TypeScript"]
        synonyms_map = {
            "React": ["React", "ReactJS", "React.js", "React JS"],
            "Express": ["Express", "Express.js", "ExpressJS"],
            "Angular": ["Angular", "AngularJS", "Angular 2+"]
        }

        # React matches ReactJS
        assert check_skill_match(resume_skills, "React", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "React", synonyms_map) == "ReactJS"

        # Express matches ExpressJS
        assert check_skill_match(resume_skills, "Express", synonyms_map) is True

        # Angular not in resume
        assert check_skill_match(resume_skills, "Angular", synonyms_map) is False

    def test_programming_language_synonym_matching(self):
        """Test programming language synonym scenarios."""
        resume_skills = ["JS", "Python 3", "TypeScript"]
        synonyms_map = {
            "JavaScript": ["JavaScript", "JS", "ES6", "ES6+"],
            "Python": ["Python", "Python 3", "Python3"],
            "TypeScript": ["TypeScript", "TS"]
        }

        # JavaScript matches JS
        assert check_skill_match(resume_skills, "JavaScript", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "JavaScript", synonyms_map) == "JS"

        # Python matches Python 3
        assert check_skill_match(resume_skills, "Python", synonyms_map) is True

        # TypeScript direct match
        assert check_skill_match(resume_skills, "TS", synonyms_map) is True

    def test_devops_synonym_matching(self):
        """Test DevOps tool synonym scenarios."""
        resume_skills = ["K8s", "Docker Compose", "Jenkins"]
        synonyms_map = {
            "Kubernetes": ["Kubernetes", "K8s", "K8s cluster"],
            "Docker": ["Docker", "Docker Container", "Docker Compose"],
            "CI/CD": ["CI/CD", "Jenkins", "GitLab CI", "GitHub Actions"]
        }

        # Kubernetes matches K8s
        assert check_skill_match(resume_skills, "Kubernetes", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "Kubernetes", synonyms_map) == "K8s"

        # Docker matches Docker Compose
        assert check_skill_match(resume_skills, "Docker", synonyms_map) is True

        # CI/CD matches Jenkins
        assert check_skill_match(resume_skills, "CI/CD", synonyms_map) is True

    def test_orm_synonym_matching(self):
        """Test ORM synonym scenarios."""
        resume_skills = ["JPA", "TypeORM", "SQLAlchemy"]
        synonyms_map = {
            "Hibernate": ["Hibernate", "Hibernate ORM", "JPA", "Java Persistence API"],
            "SQLAlchemy": ["SQLAlchemy", "SQL Alchemy"],
            "TypeORM": ["TypeORM", "Type ORM"]
        }

        # Hibernate matches JPA
        assert check_skill_match(resume_skills, "Hibernate", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "Hibernate", synonyms_map) == "JPA"

        # SQLAlchemy direct match
        assert check_skill_match(resume_skills, "SQLAlchemy", synonyms_map) is True

        # Entity Framework not in resume
        assert check_skill_match(resume_skills, "Entity Framework", synonyms_map) is False

    def test_concept_synonym_matching(self):
        """Test concept synonym scenarios."""
        resume_skills = ["Microservice architecture", "Scrum", "OOP"]
        synonyms_map = {
            "Microservices": ["Microservices", "Microservice architecture", "Microservice"],
            "Agile": ["Agile", "Agile methodology", "Scrum", "Kanban"],
            "OOP": ["OOP", "Object Oriented Programming", "Object-Oriented Programming"]
        }

        # Microservices matches Microservice architecture
        assert check_skill_match(resume_skills, "Microservices", synonyms_map) is True
        assert find_matching_synonym(resume_skills, "Microservices", synonyms_map) == "Microservice architecture"

        # Agile matches Scrum
        assert check_skill_match(resume_skills, "Agile", synonyms_map) is True

        # OOP direct match
        assert check_skill_match(resume_skills, "OOP", synonyms_map) is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_strings(self):
        """Test with empty strings."""
        resume_skills = ["Python", ""]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "", synonyms_map)
        # Empty string should match empty string in list
        assert result is True

    def test_very_long_skill_name(self):
        """Test with very long skill name."""
        long_skill = "A" * 100
        resume_skills = [long_skill]
        synonyms_map = {}

        result = check_skill_match(resume_skills, long_skill, synonyms_map)
        assert result is True

    def test_special_characters_in_skills(self):
        """Test skills with special characters."""
        resume_skills = ["C++", "C#", ".NET"]
        synonyms_map = {
            "C++": ["C++", "CPlusPlus"],
            "C#": ["C#", "C Sharp", "CSharp"]
        }

        assert check_skill_match(resume_skills, "C++", synonyms_map) is True
        assert check_skill_match(resume_skills, "C#", synonyms_map) is True

    def test_unicode_characters(self):
        """Test skills with unicode characters."""
        resume_skills = ["Русский язык", "Français"]
        synonyms_map = {}

        result = normalize_skill_name("Русский язык")
        assert result == "русский язык"

    def test_synonyms_with_hyphens(self):
        """Test skill names with hyphens."""
        resume_skills = ["React-Router", "Node-js"]
        synonyms_map = {}

        result = check_skill_match(resume_skills, "react-router", synonyms_map)
        assert result is True

    def test_synonyms_with_periods(self):
        """Test skill names with periods."""
        resume_skills = ["Node.js", "React.js"]
        synonyms_map = {"Node.js": ["Node.js", "NodeJS"]}

        result = check_skill_match(resume_skills, "NodeJS", synonyms_map)
        assert result is True

    def test_synonyms_with_slashes(self):
        """Test skill names with slashes."""
        resume_skills = ["CI/CD", "Frontend/Backend"]
        synonyms_map = {"CI/CD": ["CI/CD", "CI CD", "Continuous Integration"]}

        result = check_skill_match(resume_skills, "CI CD", synonyms_map)
        assert result is True
