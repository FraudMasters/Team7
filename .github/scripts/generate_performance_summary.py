#!/usr/bin/env python3
"""Generate performance summary in Markdown format."""

import argparse
import json
import sys
from pathlib import Path


def load_json_file(path):
    """Load JSON file, return empty dict if not found."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def generate_summary(metrics, regression):
    """Generate Markdown summary from metrics and regression report."""
    lines = []

    overall = metrics.get("overall", {})
    lines.append("### Overall Performance\n")
    lines.append(f"- **Total Requests**: {overall.get('total_requests', 0)}")
    lines.append(f"- **Total Failures**: {overall.get('total_failures', 0)}")
    lines.append(f"- **Failure Rate**: {overall.get('overall_failure_rate', 0)*100:.2f}%")
    lines.append(f"- **Avg Response Time**: {overall.get('avg_response_time_ms', 0):.2f}ms")
    lines.append("")

    endpoints = metrics.get("endpoints", {})
    if endpoints:
        lines.append("### Endpoint Performance\n")
        lines.append("| Endpoint | Requests | Failures | Avg Response | Median | Min | Max |")
        lines.append("|----------|----------|----------|--------------|--------|-----|-----|")

        for name, stats in sorted(endpoints.items()):
            lines.append(
                f"| {name} | "
                f"{stats.get('request_count', 0)} | "
                f"{stats.get('failure_count', 0)} | "
                f"{stats.get('avg_response_time_ms', 0):.2f}ms | "
                f"{stats.get('median_response_time_ms', 0):.2f}ms | "
                f"{stats.get('min_response_time_ms', 0):.2f}ms | "
                f"{stats.get('max_response_time_ms', 0):.2f}ms |"
            )
        lines.append("")

    if regression.get("baseline_exists"):
        if regression.get("has_regression"):
            lines.append("### ⚠️ Performance Regressions\n")
            for r in regression.get("regressions", []):
                lines.append(f"- **{r['endpoint']}**")
                lines.append(f"  - {r['degradation']*100:.1f}% slower")
                lines.append(f"  - Current: {r['current']:.2f}ms")
                lines.append(f"  - Baseline: {r['baseline']:.2f}ms")
            lines.append("")
        else:
            lines.append("### ✅ No Regressions\n")
            lines.append("All endpoints are within acceptable performance thresholds.\n")
            lines.append("")
    else:
        lines.append("### 📊 Baseline\n")
        lines.append("No baseline exists - current metrics will be used as baseline.\n")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate performance summary")
    parser.add_argument("--metrics", required=True, help="Current metrics JSON file")
    parser.add_argument("--regression", required=True, help="Regression report JSON file")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    args = parser.parse_args()

    metrics = load_json_file(args.metrics)
    regression = load_json_file(args.regression)

    if not metrics:
        print("Error: Metrics file is empty or invalid", file=sys.stderr)
        sys.exit(1)

    summary = generate_summary(metrics, regression)

    with open(args.output, "w") as f:
        f.write(summary)

    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
