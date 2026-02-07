#!/usr/bin/env python3
"""Generate combined performance summary from backend and frontend results."""

import argparse
import json
import sys
from pathlib import Path


def load_json_files(directory, pattern="*.json"):
    """Load all JSON files matching pattern from directory."""
    results = []
    directory = Path(directory)
    if not directory.exists():
        return results

    for file_path in directory.glob(pattern):
        try:
            with open(file_path) as f:
                results.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    return results


def generate_combined_summary(backend_dir, frontend_dir):
    """Generate combined Markdown summary."""
    lines = []
    lines.append("# ⚡ Performance Test Results\n")

    backend_metrics = load_json_files(backend_dir, "locust-metrics.json")
    if backend_metrics:
        metrics = backend_metrics[0]
        overall = metrics.get("overall", {})

        lines.append("## Backend Load Tests (Locust)\n")
        lines.append("### Overall Metrics\n")
        lines.append(f"- **Total Requests**: {overall.get('total_requests', 0)}")
        lines.append(f"- **Total Failures**: {overall.get('total_failures', 0)}")
        lines.append(f"- **Failure Rate**: {overall.get('overall_failure_rate', 0)*100:.2f}%")
        lines.append(f"- **Avg Response Time**: {overall.get('avg_response_time_ms', 0):.2f}ms")
        lines.append("")

        endpoints = metrics.get("endpoints", {})
        if endpoints:
            lines.append("### Top Endpoints (by request count)\n")
            sorted_endpoints = sorted(
                endpoints.items(),
                key=lambda x: x[1].get("request_count", 0),
                reverse=True
            )[:10]

            lines.append("| Endpoint | Requests | Avg Response | Median |")
            lines.append("|----------|----------|--------------|--------|")
            for name, stats in sorted_endpoints:
                lines.append(
                    f"| {name} | "
                    f"{stats.get('request_count', 0)} | "
                    f"{stats.get('avg_response_time_ms', 0):.2f}ms | "
                    f"{stats.get('median_response_time_ms', 0):.2f}ms |"
                )
            lines.append("")

    frontend_results = load_json_files(frontend_dir, "*.json")
    if frontend_results:
        lines.append("## Frontend Performance (Lighthouse)\n")

        for result in frontend_results[:1]:
            categories = result.get("categories", {})
            lines.append("### Scores\n")
            lines.append("| Category | Score |")
            lines.append("|----------|-------|")

            for cat_name, cat_data in categories.items():
                score = cat_data.get("score", 0) * 100
                title = cat_data.get("title", cat_name)
                status = "✅" if score >= 90 else "⚠️" if score >= 50 else "❌"
                lines.append(f"| {title} | {score:.0f} {status} |")
            lines.append("")

    lines.append("---\n")
    lines.append("*Detailed reports are available in the workflow artifacts*\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate combined performance summary")
    parser.add_argument("--backend-results", required=True, help="Backend results directory")
    parser.add_argument("--frontend-results", required=True, help="Frontend results directory")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    args = parser.parse_args()

    summary = generate_combined_summary(
        args.backend_results,
        args.frontend_results
    )

    with open(args.output, "w") as f:
        f.write(summary)

    print(f"Combined summary written to {args.output}")


if __name__ == "__main__":
    main()
