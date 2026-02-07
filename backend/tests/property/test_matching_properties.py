"""
Property-based tests for skill matching algorithms.

This module uses Hypothesis to generate hundreds of random test cases
and verify that certain properties (invariants) always hold true for
the skill matching algorithms.

Properties tested:
- Normalization idempotence and consistency
- Similarity metric mathematical properties
- Match result structure and range constraints
- Empty input handling
"""
import pytest
from hypothesis import given, strategies as st, settings, example
from typing import Dict, Any, List
from analyzers.enhanced_matcher import EnhancedSkillMatcher


class TestNormalizationProperties:
    """Property-based tests for skill name normalization."""

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_normalization_idempotent(self, text: str):
        """Normalizing twice should give the same result as normalizing once."""
        result1 = EnhancedSkillMatcher.normalize_skill_name(text)
        result2 = EnhancedSkillMatcher.normalize_skill_name(result1)
        assert result1 == result2

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_normalization_produces_lowercase(self, text: str):
        """Normalized text should always be lowercase."""
        result = EnhancedSkillMatcher.normalize_skill_name(text)
        # Check that result is lowercase (no uppercase letters)
        assert result == result.lower()

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_normalization_no_extra_whitespace(self, text: str):
        """Normalized text should not have multiple consecutive spaces."""
        result = EnhancedSkillMatcher.normalize_skill_name(text)
        # No double spaces
        assert "  " not in result
        # No leading/trailing whitespace
        assert result == result.strip()

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_normalization_preserves_valid_chars(self, text: str):
        """Normalization should preserve alphanumeric chars, dots, plus, hash."""
        result = EnhancedSkillMatcher.normalize_skill_name(text)
        # All chars should be alphanumeric, space, dot, plus, or hash
        for char in result:
            assert char.isalnum() or char in " .+#"

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    @example("  React   JS  ")
    @example("C++")
    @example("Node.js")
    @example("C#")
    def test_normalization_removes_invalid_chars(self, text: str):
        """Normalization should remove commas, exclamation marks, etc."""
        result = EnhancedSkillMatcher.normalize_skill_name(text)
        # Should not have common punctuation that was removed
        # The function removes chars that are not: alphanumeric, space, dot, plus, hash
        invalid_removed = [",", "!", "@", "$", "%", "^", "&", "*", "(", ")", "[", "]", "{", "}", "|", "\\", ":", ";", "\"", "'", "<", ">", "?", "/", "~", "`"]
        for char in invalid_removed:
            assert char not in result

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_empty_string_normalizes_to_empty(self, text: str):
        """Whitespace-only strings should normalize to empty string."""
        # First normalize the text
        result = EnhancedSkillMatcher.normalize_skill_name(text)
        # Check if original only had whitespace/control chars
        # If so, result should be empty
        if all(c.isspace() or not c.isprintable() for c in text):
            assert result == ""


class TestSimilarityProperties:
    """Property-based tests for fuzzy similarity calculation."""

    @given(st.text(min_size=0, max_size=50), st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_similarity_symmetry(self, text1: str, text2: str):
        """Similarity should be symmetric: sim(A, B) == sim(B, A)."""
        matcher = EnhancedSkillMatcher()
        result1 = matcher.calculate_fuzzy_similarity(text1, text2)
        result2 = matcher.calculate_fuzzy_similarity(text2, text1)
        assert result1 == result2

    @given(st.text(min_size=0, max_size=50), st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_similarity_range(self, text1: str, text2: str):
        """Similarity should always be between 0 and 1."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity(text1, text2)
        assert 0.0 <= result <= 1.0

    @given(st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    @example("React")
    @example("Python")
    @example("C++")
    def test_similarity_reflexivity(self, text: str):
        """Similarity of a string with itself should be 1.0."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity(text, text)
        # After normalization, identical strings should have max similarity
        normalized = EnhancedSkillMatcher.normalize_skill_name(text)
        if normalized:  # Non-empty after normalization
            assert result == 1.0
        else:
            assert result == 1.0  # Empty strings are equal

    @given(st.text(min_size=0, max_size=50), st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_similarity_based_on_normalized(self, text1: str, text2: str):
        """Similarity should be based on normalized strings."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity(text1, text2)

        # Normalize both and calculate
        norm1 = EnhancedSkillMatcher.normalize_skill_name(text1)
        norm2 = EnhancedSkillMatcher.normalize_skill_name(text2)

        # If normalized strings are equal, similarity should be 1
        if norm1 == norm2:
            assert result == 1.0


class TestMatchResultProperties:
    """Property-based tests for match result structure."""

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_match_result_structure(self, resume_skills: List[str], required_skill: str):
        """Match result should always have the required keys."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, required_skill)

        # Check structure
        assert "matched" in result
        assert "confidence" in result
        assert "matched_as" in result
        assert "match_type" in result

        # Check types
        assert isinstance(result["matched"], bool)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["match_type"], str)
        assert result["matched_as"] is None or isinstance(result["matched_as"], str)

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_confidence_range(self, resume_skills: List[str], required_skill: str):
        """Confidence should always be between 0 and 1."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, required_skill)
        assert 0.0 <= result["confidence"] <= 1.0

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_match_type_consistency(self, resume_skills: List[str], required_skill: str):
        """Match type should be one of the valid types."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, required_skill)

        valid_types = {"direct", "context", "synonym", "fuzzy", "compound", "language_hierarchy", "none"}
        assert result["match_type"] in valid_types

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_matched_flag_consistency(self, resume_skills: List[str], required_skill: str):
        """If matched is True, matched_as should not be None."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, required_skill)

        if result["matched"]:
            assert result["matched_as"] is not None
            assert isinstance(result["matched_as"], str)
        else:
            assert result["matched_as"] is None


class TestEmptyInputProperties:
    """Property-based tests for handling edge cases and empty inputs."""

    @given(st.lists(st.text(min_size=0, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_empty_required_skill_no_match(self, resume_skills: List[str]):
        """Empty required skill should return no match."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, "")
        assert result["matched"] is False
        assert result["confidence"] == 0.0
        assert result["match_type"] == "none"

    @given(st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_empty_resume_skills_no_match(self, required_skill: str):
        """Empty resume skills list should return no match."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context([], required_skill)
        assert result["matched"] is False
        assert result["match_type"] == "none"

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.one_of(st.none(), st.text(min_size=1, max_size=30)))
    @settings(max_examples=100)
    def test_context_parameter_does_not_crash(self, resume_skills: List[str],
                                              required_skill: str, context):
        """Context parameter should never cause a crash."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(resume_skills, required_skill, context=context)
        # Should always return a valid result structure
        assert "matched" in result
        assert "confidence" in result


class TestMatchMultipleProperties:
    """Property-based tests for matching multiple skills."""

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_match_multiple_returns_all_keys(self, resume_skills: List[str],
                                             required_skills: List[str]):
        """Should return results for all required skills."""
        matcher = EnhancedSkillMatcher()
        results = matcher.match_multiple(resume_skills, required_skills)

        # Should have entry for each required skill
        assert len(results) == len(required_skills)
        for skill in required_skills:
            assert skill in results

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_match_multiple_result_structure(self, resume_skills: List[str],
                                             required_skills: List[str]):
        """All match_multiple results should have correct structure."""
        matcher = EnhancedSkillMatcher()
        results = matcher.match_multiple(resume_skills, required_skills)

        for skill, result in results.items():
            assert "matched" in result
            assert "confidence" in result
            assert "matched_as" in result
            assert "match_type" in result
            assert 0.0 <= result["confidence"] <= 1.0


class TestMatchPercentageProperties:
    """Property-based tests for match percentage calculation."""

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
        st.fixed_dictionaries({"matched": st.booleans()}),
        min_size=0, max_size=20
    ))
    @settings(max_examples=100)
    def test_match_percentage_range(self, match_results: Dict[str, Dict[str, Any]]):
        """Match percentage should always be between 0 and 100."""
        matcher = EnhancedSkillMatcher()
        percentage = matcher.calculate_match_percentage(match_results)
        assert 0.0 <= percentage <= 100.0

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
        st.fixed_dictionaries({"matched": st.booleans()}),
        min_size=0, max_size=20
    ))
    @settings(max_examples=100)
    def test_match_percentage_calculation(self, match_results: Dict[str, Dict[str, Any]]):
        """Match percentage should equal (matched / total) * 100."""
        matcher = EnhancedSkillMatcher()
        percentage = matcher.calculate_match_percentage(match_results)

        if match_results:
            matched = sum(1 for r in match_results.values() if r.get("matched", False))
            expected = round((matched / len(match_results)) * 100, 2)
            assert percentage == expected
        else:
            assert percentage == 0.0


class TestLowConfidenceFilterProperties:
    """Property-based tests for low confidence match filtering."""

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
        st.fixed_dictionaries({
            "matched": st.booleans(),
            "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        }),
        min_size=0, max_size=20
    ))
    @settings(max_examples=100)
    def test_low_confidence_returns_list(self, match_results: Dict[str, Dict[str, Any]]):
        """get_low_confidence_matches should always return a list."""
        matcher = EnhancedSkillMatcher()
        result = matcher.get_low_confidence_matches(match_results)
        assert isinstance(result, list)

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
        st.fixed_dictionaries({
            "matched": st.booleans(),
            "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        }),
        min_size=0, max_size=20
    ), st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_low_confidence_threshold(self, match_results: Dict[str, Dict[str, Any]], threshold: float):
        """Filtered skills should all have confidence below threshold."""
        matcher = EnhancedSkillMatcher()
        result = matcher.get_low_confidence_matches(match_results, threshold=threshold)

        for skill in result:
            confidence = match_results[skill].get("confidence", 0)
            assert match_results[skill].get("matched", False) is True
            assert confidence < threshold

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
        st.fixed_dictionaries({
            "matched": st.booleans(),
            "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        }),
        min_size=0, max_size=20
    ))
    @settings(max_examples=100)
    def test_unmatched_not_in_low_confidence(self, match_results: Dict[str, Dict[str, Any]]):
        """Unmatched skills should not be in low confidence list."""
        matcher = EnhancedSkillMatcher()
        result = matcher.get_low_confidence_matches(match_results)

        for skill in result:
            assert match_results[skill].get("matched", False) is True


class TestCompoundSkillProperties:
    """Property-based tests for compound skill splitting."""

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    @example("C/C++")
    @example("Python, Django")
    @example("SQL & NoSQL")
    def test_compound_split_returns_list(self, skill: str):
        """Splitting compound skill should always return a list."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill(skill)
        assert isinstance(result, list)

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_compound_split_non_empty(self, skill: str):
        """Split compound skill should return non-empty list."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill(skill)
        assert len(result) > 0

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_compound_split_parts_are_strings(self, skill: str):
        """All parts from compound split should be strings."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill(skill)
        for part in result:
            assert isinstance(part, str)


class TestSynonymMatchProperties:
    """Property-based tests for synonym matching."""

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.dictionaries(
               st.text(min_size=1, max_size=20),
               st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10),
               min_size=0, max_size=10
           ))
    @settings(max_examples=100)
    def test_synonym_match_returns_tuple_or_none(self, resume_skills: List[str],
                                                  required_skill: str,
                                                  synonyms_map: Dict[str, List[str]]):
        """Synonym match should return tuple or None."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_synonym_match(resume_skills, required_skill, synonyms_map)

        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.dictionaries(
               st.text(min_size=1, max_size=20),
               st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10),
               min_size=0, max_size=10
           ))
    @settings(max_examples=100)
    def test_synonym_confidence_range(self, resume_skills: List[str],
                                      required_skill: str,
                                      synonyms_map: Dict[str, List[str]]):
        """Synonym match confidence should be between 0 and 1."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_synonym_match(resume_skills, required_skill, synonyms_map)

        if result:
            matched_skill, confidence = result
            assert 0.0 <= confidence <= 1.0


class TestFuzzyMatchProperties:
    """Property-based tests for fuzzy matching."""

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_fuzzy_match_returns_tuple_or_none(self, resume_skills: List[str],
                                               required_skill: str):
        """Fuzzy match should return tuple or None."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_fuzzy_match(resume_skills, required_skill)
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_fuzzy_match_threshold_effect(self, resume_skills: List[str],
                                          required_skill: str,
                                          threshold: float):
        """Lower threshold should not reduce number of matches."""
        matcher = EnhancedSkillMatcher()
        result1 = matcher.find_fuzzy_match(resume_skills, required_skill, threshold=threshold)

        # With lower threshold, should still find match if found with higher threshold
        # (or might find additional matches)
        if threshold > 0.1:
            result2 = matcher.find_fuzzy_match(resume_skills, required_skill, threshold=threshold - 0.1)
            if result1 is not None:
                # Should still find something with lower threshold
                assert result2 is not None

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_fuzzy_confidence_range(self, resume_skills: List[str],
                                    required_skill: str):
        """Fuzzy match confidence should be between 0 and 1."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_fuzzy_match(resume_skills, required_skill)

        if result:
            matched_skill, confidence = result
            assert 0.0 <= confidence <= 1.0


class TestContextMatchProperties:
    """Property-based tests for context-aware matching."""

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_context_match_none_context(self, resume_skills: List[str], required_skill: str):
        """None context should return None."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_context_match(resume_skills, required_skill, None)
        assert result is None

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_context_match_returns_tuple_or_none(self, resume_skills: List[str],
                                                 required_skill: str,
                                                 context: str):
        """Context match should return tuple or None."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_context_match(resume_skills, required_skill, context)
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    @given(st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=30),
           st.text(min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_context_confidence_range(self, resume_skills: List[str],
                                      required_skill: str,
                                      context: str):
        """Context match confidence should be between 0 and 1."""
        matcher = EnhancedSkillMatcher()
        result = matcher.find_context_match(resume_skills, required_skill, context)

        if result:
            matched_skill, confidence = result
            assert 0.0 <= confidence <= 1.0
