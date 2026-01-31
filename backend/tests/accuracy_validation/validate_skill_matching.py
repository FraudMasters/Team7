#!/usr/bin/env python3
"""
Skill Matching Accuracy Validation Script

This script validates the accuracy of the skill matching system by running
it on a test dataset of 20 resume-vacancy pairs with known matches (ground truth).

Target: 90%+ accuracy

Usage:
    python tests/accuracy_validation/validate_skill_matching.py

Output:
    - Console output with detailed metrics
    - JSON report file with results
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load the test dataset from JSON file."""
    logger.info(f"Loading test dataset from {dataset_path}")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        summary = dataset.get('summary', {})
        logger.info(f"Loaded {summary.get('total_pairs', 0)} test resume-vacancy pairs")
        logger.info(f"Total expected matches: {summary.get('total_expected_matches', 0)}")
        logger.info(f"Synonym matches tested: {summary.get('synonym_matches_tested', 0)}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def import_skill_matching_functions() -> Dict[str, Any]:
    """Import skill matching functions from the matching module."""
    try:
        # Add backend to path if needed
        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        # Import data extractor functions
        services_path = backend_path.parent.parent / "services" / "data_extractor"
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from analyzers.keyword_extractor import extract_resume_keywords
        from analyzers.ner_extractor import extract_resume_entities
        from api.matching import (
            check_skill_match,
            normalize_skill_name,
            load_skill_synonyms
        )

        logger.info("Successfully imported skill matching functions")
        return {
            'extract_resume_keywords': extract_resume_keywords,
            'extract_resume_entities': extract_resume_entities,
            'check_skill_match': check_skill_match,
            'normalize_skill_name': normalize_skill_name,
            'load_skill_synonyms': load_skill_synonyms
        }
    except ImportError as e:
        logger.error(f"Failed to import skill matching functions: {e}")
        raise


def extract_skills_from_resume(
    resume_text: str,
    extract_keywords: Any,
    extract_entities: Any
) -> List[str]:
    """
    Extract skills from resume text.

    Combines keywords and technical skills from NER.
    """
    try:
        # Detect language (default to English for this test dataset)
        language = "en"

        # Extract keywords
        keywords_result = extract_keywords(
            resume_text, language=language, top_n=50
        )

        # Extract entities
        entities_result = extract_entities(resume_text, language=language)

        # Combine keywords and technical skills
        resume_skills = list(set(
            keywords_result.get("keywords", []) +
            keywords_result.get("keyphrases", []) +
            entities_result.get("technical_skills", [])
        ))

        return resume_skills
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []


def match_skills(
    resume_skills: List[str],
    required_skills: List[str],
    additional_skills: List[str],
    synonyms_map: Dict[str, List[str]],
    check_match: Any
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    """
    Match resume skills to vacancy requirements.

    Returns:
        Tuple of (required_matches, additional_matches, match_percentage)
    """
    required_matches = []
    for skill in required_skills:
        matched = check_match(resume_skills, skill, synonyms_map)
        required_matches.append({
            "skill": skill,
            "status": "matched" if matched else "missing"
        })

    additional_matches = []
    for skill in additional_skills:
        matched = check_match(resume_skills, skill, synonyms_map)
        additional_matches.append({
            "skill": skill,
            "status": "matched" if matched else "missing"
        })

    # Calculate match percentage (required skills only)
    total_required = len(required_skills)
    matched_required = sum(1 for m in required_matches if m["status"] == "matched")
    match_percentage = (
        round((matched_required / total_required * 100), 2) if total_required > 0 else 0.0
    )

    return required_matches, additional_matches, match_percentage


def compare_skill_matches(
    detected_required: List[Dict[str, Any]],
    detected_additional: List[Dict[str, Any]],
    expected_matches: Dict[str, Any]
) -> Tuple[int, int, int, List[str]]:
    """
    Compare detected skill matches with expected matches.

    Returns:
        Tuple of (true_positives, false_positives, false_negatives, mismatches)
    """
    detected_matched = set()
    for match in detected_required + detected_additional:
        if match["status"] == "matched":
            detected_matched.add(match["skill"])

    expected_matched = set(expected_matches.get("matched_skills", []))
    expected_missing = set(expected_matches.get("missing_skills", []))

    # True positives: correctly identified as matched
    true_positives = len(detected_matched & expected_matched)

    # False positives: detected as matched but should be missing
    false_positives = len(detected_matched & expected_missing)

    # False negatives: should be matched but detected as missing
    false_negatives = len(expected_matched - detected_matched)

    # Track mismatches
    mismatches = []
    for skill in detected_matched - expected_matched:
        mismatches.append(f"FP: '{skill}' detected as matched but should be missing")
    for skill in expected_matched - detected_matched:
        mismatches.append(f"FN: '{skill}' should be matched but detected as missing")

    return true_positives, false_positives, false_negatives, mismatches


def run_validation(
    dataset: Dict[str, Any],
    functions: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run validation on all test pairs.

    Returns:
        Tuple of (metrics, detailed_results)
    """
    logger.info("Starting skill matching validation...")

    # Load skill synonyms
    synonyms_map = functions['load_skill_synonyms']()
    logger.info(f"Loaded {len(synonyms_map)} skill synonym mappings")

    pairs = dataset.get('pairs', [])
    detailed_results = []

    total_true_positives = 0
    total_false_positives = 0
    total_false_negatives = 0
    total_expected_matches = 0

    for pair in pairs:
        pair_id = pair.get('id')
        pair_name = pair.get('name')
        resume_text = pair.get('resume_text')
        vacancy = pair.get('vacancy')
        expected = pair.get('expected_matches', {})

        logger.info(f"Processing {pair_id}: {pair_name}")

        # Extract skills from resume
        resume_skills = extract_skills_from_resume(
            resume_text,
            functions['extract_resume_keywords'],
            functions['extract_resume_entities']
        )

        logger.info(f"  Extracted {len(resume_skills)} skills from resume")

        # Get vacancy skills
        required_skills = vacancy.get('required_skills', [])
        additional_skills = vacancy.get('additional_skills', [])

        # Match skills
        detected_required, detected_additional, match_percentage = match_skills(
            resume_skills,
            required_skills,
            additional_skills,
            synonyms_map,
            functions['check_skill_match']
        )

        logger.info(f"  Matched {match_percentage}% of required skills")

        # Compare with expected
        tp, fp, fn, mismatches = compare_skill_matches(
            detected_required,
            detected_additional,
            expected
        )

        total_true_positives += tp
        total_false_positives += fp
        total_false_negatives += fn
        total_expected_matches += len(expected.get('matched_skills', []))

        # Store detailed results
        detailed_results.append({
            "pair_id": pair_id,
            "pair_name": pair_name,
            "expected_match_percentage": expected.get('expected_match_percentage', 0.0),
            "detected_match_percentage": match_percentage,
            "expected_matched_count": len(expected.get('matched_skills', [])),
            "detected_matched_count": tp,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "mismatches": mismatches,
            "resume_skills_count": len(resume_skills),
            "required_skills": required_skills,
            "additional_skills": additional_skills,
            "detected_required": detected_required,
            "detected_additional": detected_additional
        })

    # Calculate overall metrics
    accuracy = (
        total_true_positives / total_expected_matches * 100
        if total_expected_matches > 0 else 0.0
    )

    precision = (
        total_true_positives / (total_true_positives + total_false_positives)
        if (total_true_positives + total_false_positives) > 0 else 0.0
    )

    recall = (
        total_true_positives / (total_true_positives + total_false_negatives)
        if (total_true_positives + total_false_negatives) > 0 else 0.0
    )

    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0 else 0.0
    )

    metrics = {
        "total_pairs": len(pairs),
        "total_expected_matches": total_expected_matches,
        "true_positives": total_true_positives,
        "false_positives": total_false_positives,
        "false_negatives": total_false_negatives,
        "accuracy": round(accuracy, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1_score * 100, 2),
        "target_accuracy": 90.0,
        "passed": accuracy >= 90.0
    }

    return metrics, detailed_results


def print_report(metrics: Dict[str, Any], detailed_results: List[Dict[str, Any]]):
    """Print validation report to console."""
    print("\n" + "="*80)
    print("SKILL MATCHING ACCURACY VALIDATION REPORT")
    print("="*80 + "\n")

    # Summary metrics
    print("SUMMARY METRICS")
    print("-" * 80)
    print(f"Total Test Pairs:                {metrics['total_pairs']}")
    print(f"Total Expected Skill Matches:    {metrics['total_expected_matches']}")
    print(f"True Positives (Correct):        {metrics['true_positives']}")
    print(f"False Positives (Over-matched):  {metrics['false_positives']}")
    print(f"False Negatives (Missed):        {metrics['false_negatives']}")
    print()

    # Accuracy metrics
    print("ACCURACY METRICS")
    print("-" * 80)
    print(f"Accuracy:       {metrics['accuracy']:>6.2f}% (Target: {metrics['target_accuracy']}%)")
    print(f"Precision:      {metrics['precision']:>6.2f}%")
    print(f"Recall:         {metrics['recall']:>6.2f}%")
    print(f"F1 Score:       {metrics['f1_score']:>6.2f}%")
    print()

    # Pass/Fail status
    status = "✅ PASSED" if metrics['passed'] else "❌ FAILED"
    print(f"Status: {status}")
    print()

    # Failed cases
    failed_cases = [r for r in detailed_results if r['false_positives'] > 0 or r['false_negatives'] > 0]
    if failed_cases:
        print("FAILED CASES")
        print("-" * 80)
        for result in failed_cases[:10]:  # Show first 10 failures
            print(f"\n{result['pair_id']}: {result['pair_name']}")
            print(f"  Expected: {result['expected_match_percentage']}%, Detected: {result['detected_match_percentage']}%")
            print(f"  TP: {result['true_positives']}, FP: {result['false_positives']}, FN: {result['false_negatives']}")
            if result['mismatches']:
                for mismatch in result['mismatches'][:5]:  # Show first 5 mismatches
                    print(f"    - {mismatch}")
        if len(failed_cases) > 10:
            print(f"\n... and {len(failed_cases) - 10} more failed cases")
        print()

    # Recommendations
    if not metrics['passed']:
        print("RECOMMENDATIONS")
        print("-" * 80)
        print("1. Review skill extraction accuracy - may need tuning KeyBERT parameters")
        print("2. Expand skill synonym mappings in skill_synonyms.json")
        print("3. Improve NER patterns for technical skills in ner_extractor.py")
        print("4. Consider adding domain-specific skill lists for different job types")
        print()


def save_json_report(
    metrics: Dict[str, Any],
    detailed_results: List[Dict[str, Any]],
    output_path: str
):
    """Save validation report to JSON file."""
    logger.info(f"Saving JSON report to {output_path}")

    report = {
        "validation_type": "skill_matching_accuracy",
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "detailed_results": detailed_results
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("JSON report saved successfully")
    except Exception as e:
        logger.error(f"Failed to save JSON report: {e}")


def main():
    """Main validation function."""
    try:
        # Paths
        script_dir = Path(__file__).parent
        dataset_path = script_dir / "test_resume_vacancy_pairs.json"
        report_path = script_dir / "skill_matching_validation_report.json"

        # Load test dataset
        dataset = load_test_dataset(str(dataset_path))

        # Import skill matching functions
        functions = import_skill_matching_functions()

        # Run validation
        metrics, detailed_results = run_validation(dataset, functions)

        # Print report
        print_report(metrics, detailed_results)

        # Save JSON report
        save_json_report(metrics, detailed_results, str(report_path))

        # Exit with appropriate code
        if metrics['passed']:
            logger.info("✅ Validation PASSED - Accuracy meets 90%+ target")
            sys.exit(0)
        else:
            logger.error(f"❌ Validation FAILED - Accuracy {metrics['accuracy']}% below 90% target")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
