"""
Accuracy Benchmark Module for Skill Matching System

This module provides comprehensive accuracy metrics calculation and benchmarking
capabilities for the skill matching system. It supports:

- Metrics calculation (accuracy, precision, recall, F1 score)
- Benchmark comparisons against baseline models
- Performance tracking over time
- Detailed mismatch analysis
- Integration with ML feedback loop

Usage:
    from analyzers.accuracy_benchmark import AccuracyBenchmark

    bench = AccuracyBenchmark()
    metrics = bench.calculate_metrics(detected_matches, expected_matches)
    report = bench.generate_comparison_report(current_metrics, baseline_metrics)

Classes:
    AccuracyBenchmark: Main benchmarking class
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AccuracyBenchmark:
    """
    Accuracy benchmarking system for skill matching.

    Provides methods to calculate classification metrics, compare model versions,
    track performance over time, and generate detailed benchmark reports.

    Attributes:
        target_accuracy (float): Target accuracy threshold (default: 0.90)
        min_sample_size (int): Minimum samples for reliable metrics (default: 10)
    """

    def __init__(
        self,
        target_accuracy: float = 0.90,
        min_sample_size: int = 10
    ):
        """
        Initialize the accuracy benchmark.

        Args:
            target_accuracy: Target accuracy threshold (0.0-1.0)
            min_sample_size: Minimum samples required for reliable metrics

        Example:
            bench = AccuracyBenchmark(target_accuracy=0.90, min_sample_size=20)
        """
        self.target_accuracy = target_accuracy
        self.min_sample_size = min_sample_size
        logger.info(
            f"Initialized AccuracyBenchmark with target={target_accuracy}, "
            f"min_samples={min_sample_size}"
        )

    def calculate_metrics(
        self,
        detected_matches: List[Dict[str, Any]],
        expected_matches: List[str],
        detected_missing: Optional[List[Dict[str, Any]]] = None,
        expected_missing: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate classification metrics from detection results.

        Args:
            detected_matches: List of detected match results with 'skill' and 'status'
            expected_matches: List of skills that should be matched
            detected_missing: Optional list of detected missing results
            expected_missing: Optional list of skills that should be missing

        Returns:
            Dictionary with accuracy, precision, recall, f1_score, and confusion matrix

        Example:
            detected = [
                {"skill": "React", "status": "matched"},
                {"skill": "Python", "status": "matched"},
                {"skill": "Java", "status": "missing"}
            ]
            expected = ["React", "Python", "JavaScript"]
            metrics = bench.calculate_metrics(detected, expected)
            print(f"Accuracy: {metrics['accuracy']:.2%}")
        """
        try:
            # Extract detected matched skills
            detected_matched_set = set()
            for match in detected_matches:
                if match.get("status") == "matched":
                    detected_matched_set.add(match["skill"])

            # Convert expected to sets
            expected_matched_set = set(expected_matches) if expected_matches else set()
            expected_missing_set = set(expected_missing) if expected_missing else set()

            # Calculate confusion matrix
            true_positives = len(detected_matched_set & expected_matched_set)
            false_positives = len(detected_matched_set & expected_missing_set)
            false_negatives = len(expected_matched_set - detected_matched_set)
            true_negatives = 0  # Not applicable in this context

            # Calculate metrics
            total_expected = len(expected_matched_set)
            accuracy = (
                true_positives / total_expected
                if total_expected > 0 else 0.0
            )

            total_detected = true_positives + false_positives
            precision = (
                true_positives / total_detected
                if total_detected > 0 else 0.0
            )

            total_actual = true_positives + false_negatives
            recall = (
                true_positives / total_actual
                if total_actual > 0 else 0.0
            )

            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0 else 0.0
            )

            metrics = {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4),
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "total_expected": total_expected,
                "total_detected": total_detected,
                "passed": accuracy >= self.target_accuracy,
                "sample_size_sufficient": total_expected >= self.min_sample_size
            }

            logger.info(
                f"Calculated metrics: accuracy={accuracy:.2%}, "
                f"precision={precision:.2%}, recall={recall:.2%}, "
                f"f1={f1_score:.2%}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise

    def calculate_aggregate_metrics(
        self,
        results_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across multiple test cases.

        Args:
            results_list: List of individual test result dictionaries

        Returns:
            Dictionary with aggregate metrics (averages, totals, pass rate)

        Example:
            results = [
                {"true_positives": 8, "false_positives": 1, "false_negatives": 2},
                {"true_positives": 10, "false_positives": 0, "false_negatives": 1}
            ]
            agg = bench.calculate_aggregate_metrics(results)
            print(f"Average accuracy: {agg['avg_accuracy']:.2%}")
        """
        try:
            if not results_list:
                logger.warning("No results provided for aggregate metrics")
                return self._empty_aggregate_metrics()

            total_tp = sum(r.get("true_positives", 0) for r in results_list)
            total_fp = sum(r.get("false_positives", 0) for r in results_list)
            total_fn = sum(r.get("false_negatives", 0) for r in results_list)
            total_expected = sum(r.get("total_expected", 0) for r in results_list)

            # Calculate aggregate metrics
            accuracy = (
                total_tp / total_expected
                if total_expected > 0 else 0.0
            )

            total_detected = total_tp + total_fp
            precision = (
                total_tp / total_detected
                if total_detected > 0 else 0.0
            )

            total_actual = total_tp + total_fn
            recall = (
                total_tp / total_actual
                if total_actual > 0 else 0.0
            )

            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0 else 0.0
            )

            # Calculate individual metrics for each result
            individual_metrics = []
            for result in results_list:
                tp = result.get("true_positives", 0)
                fp = result.get("false_positives", 0)
                fn = result.get("false_negatives", 0)
                exp = result.get("total_expected", 0)

                acc = tp / exp if exp > 0 else 0.0
                individual_metrics.append(acc)

            pass_count = sum(1 for m in individual_metrics if m >= self.target_accuracy)
            pass_rate = pass_count / len(results_list) if results_list else 0.0

            aggregate = {
                "total_cases": len(results_list),
                "total_true_positives": total_tp,
                "total_false_positives": total_fp,
                "total_false_negatives": total_fn,
                "total_expected": total_expected,
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4),
                "pass_count": pass_count,
                "pass_rate": round(pass_rate, 4),
                "min_accuracy": round(min(individual_metrics), 4) if individual_metrics else 0.0,
                "max_accuracy": round(max(individual_metrics), 4) if individual_metrics else 0.0,
                "avg_accuracy": round(sum(individual_metrics) / len(individual_metrics), 4) if individual_metrics else 0.0,
                "passed": accuracy >= self.target_accuracy
            }

            logger.info(
                f"Aggregate metrics: {len(results_list)} cases, "
                f"accuracy={accuracy:.2%}, pass_rate={pass_rate:.2%}"
            )

            return aggregate

        except Exception as e:
            logger.error(f"Error calculating aggregate metrics: {e}")
            raise

    def compare_model_versions(
        self,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        model_name: str = "skill_matching"
    ) -> Dict[str, Any]:
        """
        Compare current model performance against baseline.

        Args:
            current_metrics: Current model metrics
            baseline_metrics: Baseline model metrics
            model_name: Name of the model being compared

        Returns:
            Dictionary with comparison results and improvement deltas

        Example:
            current = {"accuracy": 0.92, "precision": 0.89, "recall": 0.94}
            baseline = {"accuracy": 0.88, "precision": 0.85, "recall": 0.90}
            comparison = bench.compare_model_versions(current, baseline)
            print(f"Improvement: {comparison['accuracy_improvement']:.2%}")
        """
        try:
            current_acc = current_metrics.get("accuracy", 0.0)
            baseline_acc = baseline_metrics.get("accuracy", 0.0)

            current_prec = current_metrics.get("precision", 0.0)
            baseline_prec = baseline_metrics.get("precision", 0.0)

            current_rec = current_metrics.get("recall", 0.0)
            baseline_rec = baseline_metrics.get("recall", 0.0)

            current_f1 = current_metrics.get("f1_score", 0.0)
            baseline_f1 = baseline_metrics.get("f1_score", 0.0)

            # Calculate improvements
            accuracy_improvement = current_acc - baseline_acc
            precision_improvement = current_prec - baseline_prec
            recall_improvement = current_rec - baseline_rec
            f1_improvement = current_f1 - baseline_f1

            # Determine if improvement is significant (≥2%)
            min_significant_delta = 0.02
            significant_improvement = accuracy_improvement >= min_significant_delta
            significant_regression = accuracy_improvement <= -min_significant_delta

            # Overall comparison result
            if significant_improvement:
                comparison_result = "improvement"
            elif significant_regression:
                comparison_result = "regression"
            else:
                comparison_result = "stable"

            comparison = {
                "model_name": model_name,
                "current_accuracy": round(current_acc, 4),
                "baseline_accuracy": round(baseline_acc, 4),
                "accuracy_improvement": round(accuracy_improvement, 4),
                "precision_improvement": round(precision_improvement, 4),
                "recall_improvement": round(recall_improvement, 4),
                "f1_improvement": round(f1_improvement, 4),
                "relative_improvement_pct": round(
                    (accuracy_improvement / baseline_acc * 100) if baseline_acc > 0 else 0.0,
                    2
                ),
                "comparison_result": comparison_result,
                "significant_improvement": significant_improvement,
                "significant_regression": significant_regression,
                "meets_target": current_acc >= self.target_accuracy,
                "recommendation": self._generate_recommendation(
                    comparison_result, current_acc, significant_improvement
                )
            }

            logger.info(
                f"Model comparison: {model_name}, "
                f"result={comparison_result}, "
                f"delta={accuracy_improvement:+.2%}"
            )

            return comparison

        except Exception as e:
            logger.error(f"Error comparing model versions: {e}")
            raise

    def analyze_mismatches(
        self,
        detected_matches: List[Dict[str, Any]],
        expected_matches: List[str],
        expected_missing: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze mismatches between detected and expected matches.

        Args:
            detected_matches: List of detected match results
            expected_matches: List of skills that should be matched
            expected_missing: List of skills that should be missing

        Returns:
            Dictionary with false positive and false negative analysis

        Example:
            detected = [{"skill": "React", "status": "matched"}]
            expected = ["React", "Python"]
            analysis = bench.analyze_mismatches(detected, expected)
            print(f"False negatives: {analysis['false_negatives']}")
        """
        try:
            detected_matched_set = set()
            for match in detected_matches:
                if match.get("status") == "matched":
                    detected_matched_set.add(match["skill"])

            expected_matched_set = set(expected_matches) if expected_matches else set()
            expected_missing_set = set(expected_missing) if expected_missing else set()

            # False positives: detected as matched but should be missing
            false_positives = list(detected_matched_set & expected_missing_set)

            # False negatives: should be matched but detected as missing
            false_negatives = list(expected_matched_set - detected_matched_set)

            # Categorize mismatches
            mismatch_details = []
            for skill in false_positives:
                mismatch_details.append({
                    "skill": skill,
                    "type": "false_positive",
                    "description": f"Detected as matched but should be missing"
                })

            for skill in false_negatives:
                mismatch_details.append({
                    "skill": skill,
                    "type": "false_negative",
                    "description": f"Should be matched but detected as missing"
                })

            analysis = {
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "total_mismatches": len(false_positives) + len(false_negatives),
                "mismatch_details": mismatch_details,
                "false_positive_rate": (
                    len(false_positives) / len(detected_matched_set)
                    if detected_matched_set else 0.0
                ),
                "false_negative_rate": (
                    len(false_negatives) / len(expected_matched_set)
                    if expected_matched_set else 0.0
                )
            }

            logger.info(
                f"Mismatch analysis: {len(false_positives)} FPs, "
                f"{len(false_negatives)} FNs"
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing mismatches: {e}")
            raise

    def generate_benchmark_report(
        self,
        metrics: Dict[str, Any],
        baseline_metrics: Optional[Dict[str, Any]] = None,
        model_name: str = "skill_matching",
        include_mismatches: bool = False,
        mismatch_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive benchmark report.

        Args:
            metrics: Current model metrics
            baseline_metrics: Optional baseline metrics for comparison
            model_name: Name of the model
            include_mismatches: Whether to include mismatch analysis
            mismatch_data: Optional mismatch analysis data

        Returns:
            Dictionary with complete benchmark report

        Example:
            metrics = bench.calculate_metrics(detected, expected)
            report = bench.generate_benchmark_report(
                metrics, baseline_metrics, model_name="skill_matching_v2"
            )
        """
        try:
            report = {
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "target_accuracy": self.target_accuracy,
                "min_sample_size": self.min_sample_size
            }

            # Add comparison if baseline provided
            if baseline_metrics:
                comparison = self.compare_model_versions(
                    metrics, baseline_metrics, model_name
                )
                report["comparison"] = comparison
            else:
                report["comparison"] = None

            # Add mismatch analysis if requested
            if include_mismatches and mismatch_data:
                report["mismatch_analysis"] = mismatch_data
            else:
                report["mismatch_analysis"] = None

            # Generate summary
            report["summary"] = self._generate_report_summary(
                metrics, baseline_metrics, mismatch_data
            )

            logger.info(f"Generated benchmark report for {model_name}")

            return report

        except Exception as e:
            logger.error(f"Error generating benchmark report: {e}")
            raise

    def save_benchmark_report(
        self,
        report: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Save benchmark report to JSON file.

        Args:
            report: Benchmark report dictionary
            output_path: Path to output JSON file

        Returns:
            True if saved successfully, False otherwise

        Example:
            report = bench.generate_benchmark_report(metrics, baseline)
            success = bench.save_benchmark_report(report, "benchmark_report.json")
        """
        try:
            import json

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved benchmark report to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save benchmark report: {e}")
            return False

    def _empty_aggregate_metrics(self) -> Dict[str, Any]:
        """Return empty aggregate metrics structure."""
        return {
            "total_cases": 0,
            "total_true_positives": 0,
            "total_false_positives": 0,
            "total_false_negatives": 0,
            "total_expected": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "pass_count": 0,
            "pass_rate": 0.0,
            "min_accuracy": 0.0,
            "max_accuracy": 0.0,
            "avg_accuracy": 0.0,
            "passed": False
        }

    def _generate_recommendation(
        self,
        comparison_result: str,
        current_accuracy: float,
        significant_improvement: bool
    ) -> str:
        """Generate recommendation based on comparison results."""
        if significant_improvement and current_accuracy >= self.target_accuracy:
            return "Promote to production"
        elif comparison_result == "improvement":
            return "Continue testing, monitor performance"
        elif comparison_result == "regression":
            return "Investigate regression, do not deploy"
        elif current_accuracy >= self.target_accuracy:
            return "Meets target, consider deployment"
        else:
            return "Below target, continue training"

    def _generate_report_summary(
        self,
        metrics: Dict[str, Any],
        baseline_metrics: Optional[Dict[str, Any]],
        mismatch_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate text summary for report."""
        accuracy = metrics.get("accuracy", 0.0)
        passed = metrics.get("passed", False)

        summary_lines = [
            f"Accuracy: {accuracy:.2%}",
            f"Target: {self.target_accuracy:.2%}",
            f"Status: {'✅ PASSED' if passed else '❌ FAILED'}"
        ]

        if baseline_metrics:
            baseline_acc = baseline_metrics.get("accuracy", 0.0)
            delta = accuracy - baseline_acc
            summary_lines.append(
                f"vs Baseline: {delta:+.2%} ({baseline_acc:.2%} → {accuracy:.2%})"
            )

        if mismatch_data:
            total_mismatches = mismatch_data.get("total_mismatches", 0)
            if total_mismatches > 0:
                fp = len(mismatch_data.get("false_positives", []))
                fn = len(mismatch_data.get("false_negatives", []))
                summary_lines.append(f"Mismatches: {total_mismatches} (FP: {fp}, FN: {fn})")

        return " | ".join(summary_lines)
