#!/usr/bin/env python3
"""Parse Locust test results and extract performance metrics."""

import argparse
import json
import sys
from pathlib import Path


def parse_locust_stats(stats_file):
    """Parse Locust stats JSON file and extract key metrics."""
    stats_file = Path(stats_file)
    if not stats_file.exists():
        print(f"Error: Stats file not found: {stats_file}", file=sys.stderr)
        sys.exit(1)

    with open(stats_file) as f:
        data = json.load(f)

    metrics = {
        "timestamp": data.get("state", {}).get("start_time", ""),
        "test_duration": data.get("state", {}).get("run_time", 0),
        "endpoints": {}
    }

    for entry in data.get("stats", []):
        name = entry.get("name", "")
        if not name:
            continue

        metrics["endpoints"][name] = {
            "request_count": entry.get("num_requests", 0),
            "failure_count": entry.get("num_failures", 0),
            "median_response_time_ms": entry.get("median_response_time", 0),
            "avg_response_time_ms": entry.get("avg_response_time", 0),
            "min_response_time_ms": entry.get("min_response_time", 0),
            "max_response_time_ms": entry.get("max_response_time", 0),
            "rps": entry.get("total_rps", 0),
            "failure_rate": entry.get("failure_ratio", 0)
        }

    total_requests = sum(e["request_count"] for e in metrics["endpoints"].values())
    total_failures = sum(e["failure_count"] for e in metrics["endpoints"].values())

    metrics["overall"] = {
        "total_requests": total_requests,
        "total_failures": total_failures,
        "overall_failure_rate": total_failures / total_requests if total_requests > 0 else 0,
        "avg_response_time_ms": sum(
            e["avg_response_time_ms"] for e in metrics["endpoints"].values()
        ) / len(metrics["endpoints"]) if metrics["endpoints"] else 0
    }

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Parse Locust results")
    parser.add_argument("--stats-file", required=True, help="Path to Locust stats JSON file")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    metrics = parse_locust_stats(args.stats_file)

    with open(args.output, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Parsed metrics written to {args.output}")
    print(f"Total requests: {metrics[\"overall\"][\"total_requests\"]}")
    print(f"Average response time: {metrics[\"overall\"][\"avg_response_time_ms\"]:.2f}ms")


if __name__ == "__main__":
    main()
