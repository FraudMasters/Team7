#!/usr/bin/env python3
"""
Parse Locust JSON output into performance metrics.

This script reads the Locust stats JSON file and extracts key performance metrics.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def parse_locust_stats(stats_file: Path) -> Dict[str, Any]:
    """
    Parse Locust stats file and extract metrics.

    Args:
        stats_file: Path to Locust stats JSON file

    Returns:
        Dictionary with parsed metrics
    """
    with open(stats_file, 'r') as f:
        data = json.load(f)

    metrics = {
        'endpoints': {},
        'summary': {
            'total_requests': 0,
            'total_failures': 0,
            'failure_ratio': 0.0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'requests_per_second': 0.0,
        }
    }

    # Process individual endpoint stats
    for entry in data.get('stats', []):
        name = entry.get('name', 'unknown')
        stats = entry.get('stats', {})

        metrics['endpoints'][name] = {
            'request_count': stats.get('num_requests', 0),
            'failure_count': stats.get('num_failures', 0),
            'failure_ratio': stats.get('failure_ratio', 0.0),
            'avg_response_time': stats.get('avg_response_time', 0.0),
            'min_response_time': stats.get('min_response_time', 0.0),
            'max_response_time': stats.get('max_response_time', 0.0),
            'median_response_time': stats.get('median_response_time', 0.0),
            'requests_per_second': entry.get('requests_per_second', 0.0),
        }

        # Update summary
        metrics['summary']['total_requests'] += stats.get('num_requests', 0)
        metrics['summary']['total_failures'] += stats.get('num_failures', 0)

        if stats.get('min_response_time', float('inf')) < metrics['summary']['min_response_time']:
            metrics['summary']['min_response_time'] = stats.get('min_response_time', 0.0)

        if stats.get('max_response_time', 0.0) > metrics['summary']['max_response_time']:
            metrics['summary']['max_response_time'] = stats.get('max_response_time', 0.0)

    # Calculate summary stats
    if metrics['summary']['total_requests'] > 0:
        metrics['summary']['failure_ratio'] = (
            metrics['summary']['total_failures'] / metrics['summary']['total_requests']
        )

    # Calculate weighted average response time
    total_time = 0
    total_requests = 0
    for endpoint, data in metrics['endpoints'].items():
        count = data['request_count']
        avg = data['avg_response_time']
        total_time += count * avg
        total_requests += count

    if total_requests > 0:
        metrics['summary']['avg_response_time'] = total_time / total_requests

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description='Parse Locust stats JSON file and extract metrics'
    )
    parser.add_argument(
        '--stats-file',
        type=Path,
        required=True,
        help='Path to Locust stats JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('locust-metrics.json'),
        help='Output JSON file path'
    )

    args = parser.parse_args()

    if not args.stats_file.exists():
        print(f"Error: Stats file not found: {args.stats_file}", file=sys.stderr)
        sys.exit(1)

    try:
        metrics = parse_locust_stats(args.stats_file)

        with open(args.output, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"Metrics written to {args.output}")
        print(f"Total requests: {metrics['summary']['total_requests']}")
        print(f"Avg response time: {metrics['summary']['avg_response_time']:.2f}ms")

    except Exception as e:
        print(f"Error parsing stats: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
