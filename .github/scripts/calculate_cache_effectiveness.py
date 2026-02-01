#!/usr/bin/env python3
"""
Calculate cache effectiveness by comparing cached vs uncached performance.

Analyzes benchmark results to determine how effective caching is at
improving performance.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_results(filepath: Path) -> Dict[str, Any]:
    """Load benchmark results from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_benchmark_times(results: Dict[str, Any]) -> Dict[str, float]:
    """Extract mean execution times from benchmark results."""
    times = {}
    benchmarks = results.get('benchmarks', [])

    for bench in benchmarks:
        name = bench.get('name', bench.get('fullname', 'unknown'))
        mean_time = bench.get('stats', {}).get('mean', 0)
        times[name] = mean_time

    return times


def calculate_cache_effectiveness(
    cached_times: Dict[str, float],
    uncached_times: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate cache effectiveness metrics.

    Returns:
        Dict with speedup ratios and effectiveness statistics
    """
    speedups = []
    analyzed_endpoints = []

    for endpoint, cached_time in cached_times.items():
        # Find corresponding uncached benchmark
        uncached_key = endpoint.replace('_cached', '')

        if uncached_key in uncached_times:
            uncached_time = uncached_times[uncached_key]

            if uncached_time > 0:
                speedup = uncached_time / cached_time
                speedups.append(speedup)

                analyzed_endpoints.append({
                    'endpoint': endpoint,
                    'cached_time_ms': cached_time,
                    'uncached_time_ms': uncached_time,
                    'speedup': speedup,
                    'time_saved_ms': uncached_time - cached_time,
                    'time_saved_percent': ((uncached_time - cached_time) / uncached_time) * 100
                })

    # Calculate statistics
    if speedups:
        avg_speedup = sum(speedups) / len(speedups)
        min_speedup = min(speedups)
        max_speedup = max(speedup)
    else:
        avg_speedup = 0
        min_speedup = 0
        max_speedup = 0

    return {
        'avg_speedup': avg_speedup,
        'min_speedup': min_speedup,
        'max_speedup': max_speedup,
        'analyzed_endpoints_count': len(analyzed_endpoints),
        'endpoints': analyzed_endpoints,
        'cache_effective': avg_speedup >= 2.0  # Cache should provide at least 2x speedup
    }


def main():
    parser = argparse.ArgumentParser(
        description='Calculate cache effectiveness'
    )
    parser.add_argument(
        '--cached',
        type=Path,
        required=True,
        help='Path to cached benchmark results JSON'
    )
    parser.add_argument(
        '--uncached',
        type=Path,
        required=True,
        help='Path to uncached benchmark results JSON'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('cache-effectiveness.json'),
        help='Output path for effectiveness report'
    )

    args = parser.parse_args()

    # Load results
    cached_results = load_results(args.cached)
    uncached_results = load_results(args.uncached)

    # Extract times
    cached_times = extract_benchmark_times(cached_results)
    uncached_times = extract_benchmark_times(uncached_results)

    # Calculate effectiveness
    report = calculate_cache_effectiveness(cached_times, uncached_times)

    # Add summary
    report['summary'] = {
        'avg_speedup_ratio': f"{report['avg_speedup']:.2f}x",
        'time_saved_percent': f"{(1 - 1/report['avg_speedup']) * 100:.1f}%" if report['avg_speedup'] > 0 else "N/A",
        'recommendation': (
            'Cache is highly effective' if report['avg_speedup'] >= 10 else
            'Cache is effective' if report['avg_speedup'] >= 2 else
            'Cache effectiveness needs improvement'
        )
    }

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(json.dumps(report, indent=2))

    if report['cache_effective']:
        print(f"\n✅ Cache is effective (avg speedup: {report['avg_speedup']:.2f}x)")
        return 0
    else:
        print(f"\n⚠️ Cache effectiveness below target (avg speedup: {report['avg_speedup']:.2f}x)")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
