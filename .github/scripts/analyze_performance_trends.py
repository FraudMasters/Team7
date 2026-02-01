#!/usr/bin/env python3
"""
Analyze performance trends over time.

Loads historical benchmark results and analyzes trends to identify
gradual performance degradation or improvement.
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


def load_history(history_dir: Path) -> List[Dict[str, Any]]:
    """Load all benchmark result files from history directory."""
    history = []

    if not history_dir.exists():
        return history

    for filepath in history_dir.glob('*.json'):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Add file metadata
                data['_timestamp'] = datetime.fromtimestamp(filepath.stat().st_mtime)
                data['_source_file'] = str(filepath)
                history.append(data)
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")

    # Sort by timestamp
    history.sort(key=lambda x: x['_timestamp'])

    return history


def filter_recent_history(
    history: List[Dict[str, Any]],
    days: int = 30
) -> List[Dict[str, Any]]:
    """Filter history to only include recent results."""
    cutoff = datetime.now() - timedelta(days=days)
    return [h for h in history if h['_timestamp'] >= cutoff]


def extract_metric_history(
    history: List[Dict[str, Any]],
    metric_name: str
) -> List[tuple]:
    """Extract time series for a specific metric."""
    series = []

    for result in history:
        benchmarks = result.get('benchmarks', [])

        for bench in benchmarks:
            name = bench.get('name', bench.get('fullname', 'unknown'))

            if name == metric_name:
                timestamp = result['_timestamp']
                mean_time = bench.get('stats', {}).get('mean', 0)
                series.append((timestamp, mean_time))

    return sorted(series, key=lambda x: x[0])


def calculate_trend(series: List[tuple]) -> Dict[str, Any]:
    """
    Calculate trend statistics for a metric time series.

    Returns trend analysis with slope, correlation, and classification.
    """
    if len(series) < 2:
        return {
            'trend': 'insufficient_data',
            'slope': 0,
            'change_percent': 0
        }

    # Convert to numeric
    timestamps = [(t - datetime(1970, 1, 1)).total_seconds() for t, _ in series]
    values = [v for _, v in series]

    # Simple linear regression
    n = len(series)
    sum_x = sum(timestamps)
    sum_y = sum(values)
    sum_xy = sum(t * v for t, v in zip(timestamps, values))
    sum_x2 = sum(t ** 2 for t in timestamps)

    # Calculate slope
    denominator = (n * sum_x2) - (sum_x ** 2)
    if denominator == 0:
        slope = 0
    else:
        slope = ((n * sum_xy) - (sum_x * sum_y)) / denominator

    # Calculate percent change from first to last
    first_value = values[0]
    last_value = values[-1]

    if first_value > 0:
        change_percent = ((last_value - first_value) / first_value) * 100
    else:
        change_percent = 0

    # Classify trend
    if change_percent > 10:
        trend = 'degrading'
    elif change_percent > 5:
        trend = 'potentially_degrading'
    elif change_percent < -10:
        trend = 'improving'
    elif change_percent < -5:
        trend = 'potentially_improving'
    else:
        trend = 'stable'

    return {
        'trend': trend,
        'slope': slope,
        'change_percent': change_percent,
        'first_value': first_value,
        'last_value': last_value,
        'data_points': n
    }


def generate_trend_report(
    history: List[Dict[str, Any]],
    current_results: Dict[str, Any],
    days: int = 30
) -> Dict[str, Any]:
    """Generate comprehensive trend analysis report."""
    recent_history = filter_recent_history(history, days)

    # Get all unique metric names
    metric_names = set()
    for result in recent_history:
        for bench in result.get('benchmarks', []):
            name = bench.get('name', bench.get('fullname'))
            if name:
                metric_names.add(name)

    # Analyze trends for each metric
    trends = {}
    for metric_name in metric_names:
        series = extract_metric_history(recent_history, metric_name)
        if series:
            trends[metric_name] = calculate_trend(series)

    # Count trends by category
    trend_counts = {
        'degrading': 0,
        'potentially_degrading': 0,
        'stable': 0,
        'potentially_improving': 0,
        'improving': 0,
        'insufficient_data': 0
    }

    for trend_data in trends.values():
        trend_counts[trend_data['trend']] += 1

    return {
        'analysis_period_days': days,
        'data_points_analyzed': len(recent_history),
        'total_metrics': len(metric_names),
        'trends': trends,
        'trend_counts': trend_counts,
        'has_degrading_trends': trend_counts['degrading'] > 0,
        'degrading_metrics': [
            name for name, data in trends.items()
            if data['trend'] == 'degrading'
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description='Analyze performance trends over time'
    )
    parser.add_argument(
        '--history-dir',
        type=Path,
        required=True,
        help='Directory containing historical benchmark results'
    )
    parser.add_argument(
        '--current',
        type=Path,
        required=True,
        help='Path to current benchmark results'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('trend-report.json'),
        help='Output path for trend report'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )

    args = parser.parse_args()

    # Load history
    history = load_history(args.history_dir)
    print(f'Loaded {len(history)} historical results')

    # Load current results
    with open(args.current, 'r') as f:
        current_results = json.load(f)

    # Generate trend report
    report = generate_trend_report(
        history,
        current_results,
        args.days
    )

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print(json.dumps(report, indent=2))

    if report['has_degrading_trends']:
        print(f'\n⚠️ Warning: {len(report["degrading_metrics"])} metrics show degrading trends')
        return 1
    else:
        print(f'\n✅ No significant performance degradation trends detected')
        return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
