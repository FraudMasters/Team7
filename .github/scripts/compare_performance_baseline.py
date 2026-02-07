#!/usr/bin/env python3
"""
Compare current performance metrics with baseline.

This script compares current performance metrics with a baseline and detects regressions.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def compare_metrics(
    current: Dict[str, Any],
    baseline: Dict[str, Any],
    threshold: float = 0.20
) -> Dict[str, Any]:
    """
    Compare current metrics with baseline.

    Args:
        current: Current performance metrics
        baseline: Baseline performance metrics
        threshold: Regression threshold (e.g., 0.20 = 20% degradation)

    Returns:
        Regression report dictionary
    """
    regressions = []
    has_regression = False

    current_endpoints = current.get('endpoints', {})
    baseline_endpoints = baseline.get('endpoints', {})

    # Compare each endpoint
    for endpoint_name, current_data in current_endpoints.items():
        if endpoint_name not in baseline_endpoints:
            continue

        baseline_data = baseline_endpoints[endpoint_name]

        # Compare average response time
        current_avg = current_data.get('avg_response_time', 0.0)
        baseline_avg = baseline_data.get('avg_response_time', 0.0)

        if baseline_avg > 0:
            degradation = (current_avg - baseline_avg) / baseline_avg

            if degradation > threshold:
                has_regression = True
                regressions.append({
                    'endpoint': endpoint_name,
                    'metric': 'avg_response_time',
                    'current': current_avg,
                    'baseline': baseline_avg,
                    'degradation': degradation,
                    'threshold': threshold,
                })

        # Compare failure ratio
        current_failure = current_data.get('failure_ratio', 0.0)
        baseline_failure = baseline_data.get('failure_ratio', 0.0)

        if current_failure > baseline_failure + 0.05:  # 5% absolute increase
            has_regression = True
            regressions.append({
                'endpoint': endpoint_name,
                'metric': 'failure_ratio',
                'current': current_failure,
                'baseline': baseline_failure,
                'degradation': current_failure - baseline_failure,
                'threshold': 0.05,
            })

    # Compare overall summary
    current_summary = current.get('summary', {})
    baseline_summary = baseline.get('summary', {})

    current_avg = current_summary.get('avg_response_time', 0.0)
    baseline_avg = baseline_summary.get('avg_response_time', 0.0)

    if baseline_avg > 0:
        degradation = (current_avg - baseline_avg) / baseline_avg
        if degradation > threshold:
            has_regression = True
            regressions.append({
                'endpoint': 'overall',
                'metric': 'avg_response_time',
                'current': current_avg,
                'baseline': baseline_avg,
                'degradation': degradation,
                'threshold': threshold,
            })

    return {
        'has_regression': has_regression,
        'regressions': regressions,
        'threshold': threshold,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Compare current performance metrics with baseline'
    )
    parser.add_argument(
        '--current',
        type=Path,
        required=True,
        help='Current performance metrics JSON file'
    )
    parser.add_argument(
        '--baseline',
        type=Path,
        required=True,
        help='Baseline performance metrics JSON file'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.20,
        help='Regression threshold (default: 0.20 = 20%% degradation)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('regression-report.json'),
        help='Output report JSON file path'
    )

    args = parser.parse_args()

    if not args.current.exists():
        print(f"Warning: Current metrics file not found: {args.current}", file=sys.stderr)
        # Create empty report if no baseline exists yet
        report = {
            'has_regression': False,
            'regressions': [],
            'threshold': args.threshold,
            'note': 'No baseline to compare against',
        }
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Baseline report created (no comparison possible)")
        sys.exit(0)

    if not args.baseline.exists():
        print(f"Warning: Baseline file not found: {args.baseline}", file=sys.stderr)
        # Create empty report if no baseline exists yet
        report = {
            'has_regression': False,
            'regressions': [],
            'threshold': args.threshold,
            'note': 'No baseline to compare against',
        }
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Baseline report created (no comparison possible)")
        sys.exit(0)

    try:
        with open(args.current, 'r') as f:
            current_metrics = json.load(f)

        with open(args.baseline, 'r') as f:
            baseline_metrics = json.load(f)

        report = compare_metrics(
            current_metrics,
            baseline_metrics,
            args.threshold
        )

        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)

        if report['has_regression']:
            print(f"⚠️  Performance regression detected!")
            print(f"Regressions: {len(report['regressions'])}")
            for r in report['regressions']:
                print(f"  - {r['endpoint']}: {r['metric']}: {(r['degradation'] * 100):.1f}% slower")
            sys.exit(1)
        else:
            print(f"✅ No performance regressions detected")
            print(f"Report written to {args.output}")

    except Exception as e:
        print(f"Error comparing metrics: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
