#!/usr/bin/env python3
"""Compare current performance metrics against baseline."""

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


def compare_metrics(current, baseline, threshold=0.20):
    """Compare current metrics against baseline and detect regressions."""
    regressions = []

    if not baseline or not baseline.get("endpoints"):
        return {
            "has_regression": False,
            "regressions": [],
            "improvements": [],
            "baseline_exists": False
        }

    current_endpoints = current.get("endpoints", {})
    baseline_endpoints = baseline.get("endpoints", {})

    for endpoint, current_metrics in current_endpoints.items():
        if endpoint not in baseline_endpoints:
            continue

        baseline_metrics = baseline_endpoints[endpoint]
        current_rt = current_metrics.get("avg_response_time_ms", 0)
        baseline_rt = baseline_metrics.get("avg_response_time_ms", 0)

        if baseline_rt > 0:
            degradation = (current_rt - baseline_rt) / baseline_rt
            if degradation > threshold:
                regressions.append({
                    "endpoint": endpoint,
                    "metric": "avg_response_time_ms",
                    "current": current_rt,
                    "baseline": baseline_rt,
                    "degradation": degradation,
                    "threshold": threshold
                })

    return {
        "has_regression": len(regressions) > 0,
        "regressions": regressions,
        "improvements": [],
        "baseline_exists": True
    }


def main():
    parser = argparse.ArgumentParser(description="Compare performance against baseline")
    parser.add_argument("--current", required=True, help="Current metrics JSON file")
    parser.add_argument("--baseline", required=True, help="Baseline metrics JSON file")
    parser.add_argument("--threshold", type=float, default=0.20, help="Degradation threshold (default: 0.20 = 20%)")
    parser.add_argument("--output", required=True, help="Output regression report JSON")
    args = parser.parse_args()

    current_metrics = load_json_file(args.current)
    baseline_metrics = load_json_file(args.baseline)

    if not current_metrics:
        print("Error: Current metrics file is empty or invalid", file=sys.stderr)
        sys.exit(1)

    regression_report = compare_metrics(current_metrics, baseline_metrics, args.threshold)

    with open(args.output, "w") as f:
        json.dump(regression_report, f, indent=2)

    if not regression_report["baseline_exists"]:
        print("No baseline found - skipping comparison")
    elif regression_report["has_regression"]:
        print(f"Performance regression detected: {len(regression_report['regressions'])} endpoints degraded")
        for r in regression_report["regressions"]:
            print(f"  - {r['endpoint']}: {r['degradation']*100:.1f}% slower")
    else:
        print("No performance regressions detected")

    sys.exit(1 if regression_report["has_regression"] else 0)


if __name__ == "__main__":
    main()
