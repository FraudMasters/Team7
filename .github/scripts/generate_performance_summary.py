#!/usr/bin/env python3
"""
Generate human-readable performance summary.

This script generates a Markdown summary of performance test results.
"""

import argparse
import json
import sys
from pathlib import Path


def generate_summary(metrics: Dict, regression: Dict) -> str:
    """Generate a Markdown summary of performance results."""
    lines = []

    # Overall status
    if regression.get('has_regression', False):
        lines.append("### ⚠️ Status: Performance Regression Detected\n")
    else:
        lines.append("### ✅ Status: All Performance Tests Passed\n")

    # Summary metrics
    summary = metrics.get('summary', {})
    lines.append("#### Overall Metrics\n")
    lines.append(f"- **Total Requests:** {summary.get('total_requests', 0)}")
    lines.append(f"- **Avg Response Time:** {summary.get('avg_response_time', 0):.2f}ms")
    lines.append(f"- **Min Response Time:** {summary.get('min_response_time', 0):.2f}ms")
    lines.append(f"- **Max Response Time:** {summary.get('max_response_time', 0):.2f}ms")
    lines.append(f"- **Failure Ratio:** {(summary.get('failure_ratio', 0) * 100):.2f}%")
    lines.append("")

    # Endpoint breakdown
    lines.append("#### Endpoint Performance\n")
    lines.append("| Endpoint | Requests | Failures | Avg (ms) | Min (ms) | Max (ms) | RPS |")
    lines.append("|----------|----------|----------|----------|----------|----------|-----|")

    for endpoint, data in metrics.get('endpoints', {}).items():
        name = endpoint.split('/')[-1] if '/' in endpoint else endpoint
        lines.append(
            f"| {name} | "
            f"{data.get('request_count', 0)} | "
            f"{data.get('failure_count', 0)} | "
            f"{data.get('avg_response_time', 0):.1f} | "
            f"{data.get('min_response_time', 0):.1f} | "
            f"{data.get('max_response_time', 0):.1f} | "
            f"{data.get('requests_per_second', 0):.1f} |"
        )

    lines.append("")

    # Regressions
    if regression.get('has_regression', False):
        lines.append("#### Regressions Detected\n")
        for r in regression.get('regressions', []):
            lines.append(f"- **{r['endpoint']}** - {r['metric']}: "
                        f"{(r['degradation'] * 100):.1f}% slower "
                        f"({r['current']:.2f}ms vs {r['baseline']:.2f}ms)")

        lines.append("")
        lines.append(f"Threshold: {(regression.get('threshold', 0) * 100):.0f}% degradation")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate performance summary'
    )
    parser.add_argument(
        '--metrics',
        type=Path,
        required=True,
        help='Performance metrics JSON file'
    )
    parser.add_argument(
        '--regression',
        type=Path,
        required=True,
        help='Regression report JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('performance-summary.md'),
        help='Output summary file path'
    )

    args = parser.parse_args()

    try:
        with open(args.metrics, 'r') as f:
            metrics = json.load(f)

        with open(args.regression, 'r') as f:
            regression = json.load(f)

        summary = generate_summary(metrics, regression)

        with open(args.output, 'w') as f:
            f.write(summary)

        print(f"Summary written to {args.output}")

    except Exception as e:
        print(f"Error generating summary: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
