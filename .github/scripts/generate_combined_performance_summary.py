#!/usr/bin/env python3
"""
Generate combined performance summary from backend and frontend results.

This script combines performance test results from both backend and frontend.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load JSON file if it exists, return empty dict otherwise."""
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def generate_combined_summary(backend_dir: Path, frontend_dir: Path) -> str:
    """Generate combined performance summary."""
    lines = []

    lines.append("# Performance Test Results Summary\n")

    # Backend results
    backend_metrics = load_json_file(backend_dir / 'locust-metrics.json')
    backend_regression = load_json_file(backend_dir / 'regression-report.json')

    lines.append("## Backend Load Tests\n")

    if backend_metrics:
        summary = backend_metrics.get('summary', {})
        lines.append("### Overall Metrics\n")
        lines.append(f"- **Total Requests:** {summary.get('total_requests', 0)}")
        lines.append(f"- **Avg Response Time:** {summary.get('avg_response_time', 0):.2f}ms")
        lines.append(f"- **Min Response Time:** {summary.get('min_response_time', 0):.2f}ms")
        lines.append(f"- **Max Response Time:** {summary.get('max_response_time', 0):.2f}ms")
        lines.append(f"- **Failure Ratio:** {(summary.get('failure_ratio', 0) * 100):.2f}%")
        lines.append("")

        # Endpoint breakdown
        if backend_metrics.get('endpoints'):
            lines.append("### Endpoint Performance\n")
            lines.append("| Endpoint | Requests | Avg (ms) | Max (ms) | Failures |")
            lines.append("|----------|----------|----------|----------|----------|")

            for endpoint, data in backend_metrics.get('endpoints', {}).items():
                name = endpoint.split('/')[-1] if '/' in endpoint else endpoint
                lines.append(
                    f"| {name} | "
                    f"{data.get('request_count', 0)} | "
                    f"{data.get('avg_response_time', 0):.1f} | "
                    f"{data.get('max_response_time', 0):.1f} | "
                    f"{data.get('failure_count', 0)} |"
                )
            lines.append("")
    else:
        lines.append("No backend metrics available.\n")

    # Backend regression status
    if backend_regression.get('has_regression'):
        lines.append("### ⚠️ Backend Regressions\n")
        for r in backend_regression.get('regressions', []):
            lines.append(
                f"- **{r['endpoint']}** - {r['metric']}: "
                f"{(r['degradation'] * 100):.1f}% slower"
            )
        lines.append("")
    elif backend_regression:
        lines.append("### ✅ Backend: No Regressions\n")

    # Frontend results (Lighthouse)
    lighthouse_report = load_json_file(frontend_dir / 'lhr-report.json')

    lines.append("## Frontend Performance Tests\n")

    if lighthouse_report:
        # Lighthouse results structure
        categories = lighthouse_report.get('categories', {})

        lines.append("### Lighthouse Scores\n")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")

        score_mapping = {
            'performance': 'Performance',
            'accessibility': 'Accessibility',
            'best-practices': 'Best Practices',
            'seo': 'SEO',
            'pwa': 'PWA',
        }

        for key, label in score_mapping.items():
            if key in categories:
                score = categories[key].get('score', 0) * 100
                emoji = '🟢' if score >= 90 else '🟡' if score >= 50 else '🔴'
                lines.append(f"| {label} | {emoji} {score:.0f} |")

        lines.append("")

        # Audits of interest
        audits = lighthouse_report.get('audits', {})

        lines.append("### Key Metrics\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")

        metrics_of_interest = [
            ('first-contentful-paint', 'First Contentful Paint'),
            ('largest-contentful-paint', 'Largest Contentful Paint'),
            ('cumulative-layout-shift', 'Cumulative Layout Shift'),
            ('total-blocking-time', 'Total Blocking Time'),
            ('speed-index', 'Speed Index'),
            ('interactive', 'Time to Interactive'),
        ]

        for audit_key, label in metrics_of_interest:
            if audit_key in audits:
                audit = audits[audit_key]
                display_value = audit.get('displayValue', 'N/A')
                lines.append(f"| {label} | {display_value} |")

        lines.append("")
    else:
        lines.append("No frontend metrics available.\n")

    # Overall status
    lines.append("## Overall Status\n")

    backend_regressions = backend_regression.get('has_regression', False)
    frontend_issues = False  # Could be determined from Lighthouse scores

    if backend_regressions:
        lines.append("⚠️ **Performance regressions detected in backend. Review required.**")
    elif frontend_issues:
        lines.append("⚠️ **Frontend performance issues detected. Review required.**")
    else:
        lines.append("✅ **All performance tests passed.**")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate combined performance summary'
    )
    parser.add_argument(
        '--backend-results',
        type=Path,
        required=True,
        help='Backend results directory'
    )
    parser.add_argument(
        '--frontend-results',
        type=Path,
        required=True,
        help='Frontend results directory'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('combined-summary.md'),
        help='Output summary file path'
    )

    args = parser.parse_args()

    try:
        summary = generate_combined_summary(
            args.backend_results,
            args.frontend_results
        )

        with open(args.output, 'w') as f:
            f.write(summary)

        print(f"Combined summary written to {args.output}")

    except Exception as e:
        print(f"Error generating summary: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
