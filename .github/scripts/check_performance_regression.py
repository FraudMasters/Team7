#!/usr/bin/env python3
"""
Check for performance regressions in benchmark results.

Compares current benchmark results against a baseline and detects
significant performance degradations.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_results(filepath: Path) -> Dict[str, Any]:
    """Load benchmark results from JSON file."""
    if not filepath.exists():
        print(f"Warning: Baseline file {filepath} not found")
        return {}

    with open(filepath, 'r') as f:
        return json.load(f)


def extract_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """Extract mean execution times from benchmark results."""
    metrics = {}
    benchmarks = results.get('benchmarks', {})

    for bench in benchmarks:
        name = bench.get('name', bench.get('fullname', 'unknown'))
        # Use mean as the primary metric
        mean_time = bench.get('stats', {}).get('mean', 0)
        metrics[name] = mean_time

    return metrics


def check_regression(
    current_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    threshold: float = 0.20
) -> Dict[str, Any]:
    """
    Check for performance regressions.

    Args:
        current_metrics: Current benchmark results
        baseline_metrics: Baseline benchmark results
        threshold: Maximum acceptable degradation (default 20%)

    Returns:
        Dict with regression detection results
    """
    regressions = []
    improvements = []

    for key, current_value in current_metrics.items():
        if key in baseline_metrics:
            baseline_value = baseline_metrics[key]

            if baseline_value > 0:
                # Calculate degradation (positive = slower, negative = faster)
                degradation = (current_value - baseline_value) / baseline_value

                if degradation > threshold:
                    regressions.append({
                        'metric': key,
                        'current': current_value,
                        'baseline': baseline_value,
                        'degradation': degradation,
                        'percent_degradation': degradation * 100
                    })
                elif degradation < -threshold:
                    improvements.append({
                        'metric': key,
                        'current': current_value,
                        'baseline': baseline_value,
                        'improvement': abs(degradation),
                        'percent_improvement': abs(degradation) * 100
                    })

    return {
        'has_regression': len(regressions) > 0,
        'regressions': regressions,
        'improvements': improvements,
        'total_metrics': len(current_metrics),
        'threshold_percent': threshold * 100
    }


def main():
    parser = argparse.ArgumentParser(
        description='Check for performance regressions'
    )
    parser.add_argument(
        '--current',
        type=Path,
        required=True,
        help='Path to current benchmark results JSON'
    )
    parser.add_argument(
        '--baseline',
        type=Path,
        required=True,
        help='Path to baseline benchmark results JSON'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.20,
        help='Regression threshold (default: 0.20 = 20%%)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('regression-report.json'),
        help='Output path for regression report'
    )

    args = parser.parse_args()

    # Load results
    current_results = load_results(args.current)
    baseline_results = load_results(args.baseline)

    if not baseline_results:
        # No baseline to compare against, exit gracefully
        report = {
            'has_regression': False,
            'reason': 'No baseline available for comparison',
            'regressions': [],
            'improvements': []
        }
    else:
        # Extract metrics
        current_metrics = extract_metrics(current_results)
        baseline_metrics = extract_metrics(baseline_results)

        # Check for regressions
        report = check_regression(
            current_metrics,
            baseline_metrics,
            args.threshold
        )

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(json.dumps(report, indent=2))

    # Exit with error if regressions detected
    if report.get('has_regression'):
        print(f'\n❌ Performance regressions detected!', file=sys.stderr)
        print(f'Threshold: {args.threshold * 100}%', file=sys.stderr)
        sys.exit(1)
    else:
        print(f'\n✅ No performance regressions detected')
        sys.exit(0)


if __name__ == '__main__':
    main()
