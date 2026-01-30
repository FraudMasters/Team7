#!/usr/bin/env python3
"""
Performance Benchmark Script for AI Candidate Ranking

Measures ranking performance for N candidates and verifies response time < 2 seconds.

Usage:
    python scripts/benchmark_ranking.py --vacancy_id <id> --candidates 100 --max_time 2000
"""

import argparse
import time
import statistics
import sys
from typing import List, Dict, Any
import requests
import json


class RankingBenchmark:
    """Benchmark ranking API performance."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    def generate_mock_candidates(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock candidate data for testing."""
        candidates = []
        skills = ["Python", "Java", "JavaScript", "Go", "Rust", "C++", "TypeScript", "Django", "FastAPI"]

        for i in range(count):
            candidates.append({
                "resume_id": f"benchmark-resume-{i}",
                "candidate_name": f"Candidate {i}",
                "match_score": min(100, 50 + (i % 50)),
                "experience_relevance": 0.5 + (i % 5) * 0.1,
                "education_level": 0.5 + (i % 3) * 0.15,
                "skills_freshness_days": 30 + (i % 10) * 10,
                "feedback_score": 0.6 + (i % 4) * 0.1,
            })

        return candidates

    def benchmark_ranking(
        self,
        vacancy_id: str,
        num_candidates: int,
        max_time_ms: int = 2000
    ) -> Dict[str, Any]:
        """Run ranking benchmark and return metrics."""
        print(f"Ranking {num_candidates} candidates for vacancy {vacancy_id}...")
        print(f"Maximum allowed time: {max_time_ms}ms")
        print("-" * 60)

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/ranking/rank",
                json={
                    "vacancy_id": vacancy_id,
                    "limit": num_candidates,
                },
                timeout=10,
            )

            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000

            success = response.status_code == 200
            within_limit = elapsed_ms <= max_time_ms

            result = {
                "success": success,
                "elapsed_ms": elapsed_ms,
                "within_limit": within_limit,
                "candidates_processed": num_candidates,
                "status_code": response.status_code,
                "max_time_ms": max_time_ms,
            }

            if success:
                data = response.json()
                result["candidates_returned"] = len(data.get("ranked_candidates", []))
                result["model_version"] = data.get("model_version", "unknown")

                # Calculate throughput
                result["candidates_per_second"] = num_candidates / (elapsed_ms / 1000)

                # Print results
                print(f"Status: {'✓ PASS' if within_limit else '✗ FAIL'}")
                print(f"Response time: {elapsed_ms:.2f}ms")
                print(f"Target: {max_time_ms}ms")
                print(f"Candidates processed: {num_candidates}")
                print(f"Throughput: {result['candidates_per_second']:.2f} candidates/sec")
                print(f"Model version: {result['model_version']}")
            else:
                print(f"Status: ✗ FAIL")
                print(f"HTTP {response.status_code}: {response.text}")

            print("-" * 60)

            return result

        except requests.Timeout:
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000

            print(f"Status: ✗ FAIL (Timeout)")
            print(f"Request exceeded 10 second timeout")
            print("-" * 60)

            return {
                "success": False,
                "elapsed_ms": elapsed_ms,
                "within_limit": False,
                "error": "timeout",
            }
        except Exception as e:
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000

            print(f"Status: ✗ FAIL (Error)")
            print(f"Error: {e}")
            print("-" * 60)

            return {
                "success": False,
                "elapsed_ms": elapsed_ms,
                "within_limit": False,
                "error": str(e),
            }

    def run_multiple_benchmarks(
        self,
        vacancy_id: str,
        num_candidates: int,
        iterations: int = 5,
        max_time_ms: int = 2000
    ) -> Dict[str, Any]:
        """Run multiple benchmark iterations and aggregate results."""
        print(f"\nRunning {iterations} benchmark iterations...")
        print("=" * 60)

        results = []
        for i in range(iterations):
            print(f"\nIteration {i + 1}/{iterations}")
            result = self.benchmark_ranking(vacancy_id, num_candidates, max_time_ms)
            results.append(result)

        # Aggregate statistics
        successful = [r for r in results if r["success"]]

        if not successful:
            return {
                "overall_status": "FAIL",
                "all_failed": True,
                "results": results,
            }

        elapsed_times = [r["elapsed_ms"] for r in successful]
        within_limits = [r for r in successful if r["within_limit"]]

        aggregate = {
            "overall_status": "PASS" if len(within_limits) == iterations else "PARTIAL",
            "iterations": iterations,
            "successful": len(successful),
            "within_limit_count": len(within_limits),
            "avg_time_ms": statistics.mean(elapsed_times),
            "min_time_ms": min(elapsed_times),
            "max_time_ms": max(elapsed_times),
            "median_time_ms": statistics.median(elapsed_times),
            "stdev_time_ms": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
            "p95_time_ms": statistics.quantiles(elapsed_times, n=20)[18] if len(elapsed_times) > 1 else elapsed_times[0],
            "target_ms": max_time_ms,
            "candidates_per_run": num_candidates,
            "results": results,
        }

        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {aggregate['overall_status']}")
        print(f"Iterations: {aggregate['successful']}/{aggregate['iterations']} successful")
        print(f"Within Target: {aggregate['within_limit_count']}/{aggregate['iterations']}")
        print(f"\nResponse Times (ms):")
        print(f"  Average: {aggregate['avg_time_ms']:.2f}ms")
        print(f"  Median:  {aggregate['median_time_ms']:.2f}ms")
        print(f"  Min:     {aggregate['min_time_ms']:.2f}ms")
        print(f"  Max:     {aggregate['max_time_ms']:.2f}ms")
        print(f"  StdDev:  {aggregate['stdev_time_ms']:.2f}ms")
        print(f"  P95:     {aggregate['p95_time_ms']:.2f}ms")
        print(f"\nTarget: {max_time_ms}ms")
        print("=" * 60)

        return aggregate


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="Benchmark AI Candidate Ranking API performance"
    )
    parser.add_argument(
        "--vacancy_id",
        type=str,
        required=True,
        help="Vacancy ID to rank candidates for"
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=100,
        help="Number of candidates to rank (default: 100)"
    )
    parser.add_argument(
        "--max_time",
        type=int,
        default=2000,
        help="Maximum acceptable response time in ms (default: 2000)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations (default: 5)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for results"
    )

    args = parser.parse_args()

    benchmark = RankingBenchmark(args.url)

    # Run benchmarks
    results = benchmark.run_multiple_benchmarks(
        vacancy_id=args.vacancy_id,
        num_candidates=args.candidates,
        iterations=args.iterations,
        max_time_ms=args.max_time,
    )

    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        print("\n✓ All benchmarks PASSED")
        sys.exit(0)
    elif results['overall_status'] == 'PARTIAL':
        print("\n⚠ Some benchmarks FAILED")
        sys.exit(1)
    else:
        print("\n✗ All benchmarks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
