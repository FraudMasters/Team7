#!/usr/bin/env python3
"""
Generate comprehensive test summary dashboard.
Aggregates test results, coverage, security scans, and performance data.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file if it exists."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_status_emoji(status: str) -> str:
    """Get emoji for job status."""
    status_lower = status.lower()
    if status_lower == 'success':
        return '✅'
    elif status_lower == 'failure':
        return '❌'
    elif status_lower in ('cancelled', 'skipped'):
        return '⏭️'
    else:
        return '⚠️'


def get_coverage_color(percentage: float) -> str:
    """Get color for coverage percentage."""
    if percentage >= 90:
        return '🟢'
    elif percentage >= 80:
        return '🟡'
    else:
        return '🔴'


def get_performance_color(degradation: float, threshold: float = 0.20) -> str:
    """Get color for performance degradation."""
    if degradation < threshold:
        return '🟢'
    elif degradation < threshold * 1.5:
        return '🟡'
    else:
        return '🔴'


def generate_test_results_section(test_jobs: Dict[str, str]) -> str:
    """Generate test results section."""
    lines = [
        "## 🧪 Test Results",
        "",
        "| Job | Status |",
        "|-----|--------|"
    ]

    for job, status in test_jobs.items():
        emoji = get_status_emoji(status)
        lines.append(f"| {job} | {emoji} {status} |")

    lines.append("")
    return "\n".join(lines)


def generate_coverage_section(frontend_cov: Optional[Dict], backend_cov: Optional[Dict]) -> str:
    """Generate coverage section."""
    lines = [
        "## 📊 Test Coverage",
        ""
    ]

    # Frontend coverage
    if frontend_cov:
        total = frontend_cov.get('total', {})
        lines.append("### Frontend")
        lines.append("")
        lines.append("| Metric | Coverage | Status |")
        lines.append("|--------|----------|--------|")

        for metric in ['lines', 'functions', 'branches', 'statements']:
            metric_data = total.get(metric, {})
            pct = metric_data.get('pct', 0)
            covered = metric_data.get('covered', 0)
            total_count = metric_data.get('total', 0)
            color = get_coverage_color(pct)
            lines.append(f"| {metric.capitalize()} | {covered}/{total_count} ({pct}%) | {color} |")

        lines.append("")

    # Backend coverage
    if backend_cov:
        totals = backend_cov.get('totals', {})
        lines.append("### Backend")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Overall Coverage | {totals.get('percent_covered', 'N/A')}% |")
        lines.append(f"| Lines Covered | {totals.get('covered_lines', 'N/A')} |")
        lines.append(f"| Total Statements | {totals.get('num_statements', 'N/A')} |")
        lines.append("")

    # Coverage thresholds
    lines.append("### Coverage Thresholds")
    lines.append("")
    lines.append("| Component | Threshold | Current | Status |")
    lines.append("|-----------|-----------|---------|--------|")

    frontend_pct = frontend_cov.get('total', {}).get('statements', {}).get('pct', 0) if frontend_cov else 0
    backend_pct = float(backend_cov.get('totals', {}).get('percent_covered', 0)) if backend_cov else 0

    frontend_status = '✅' if frontend_pct >= 85 else '❌'
    backend_status = '✅' if backend_pct >= 80 else '❌'

    lines.append(f"| Frontend | ≥85% | {frontend_pct}% | {frontend_status} |")
    lines.append(f"| Backend | ≥80% | {backend_pct}% | {backend_status} |")
    lines.append("")

    return "\n".join(lines)


def generate_security_section(security_data: Dict[str, Any]) -> str:
    """Generate security scan section."""
    lines = [
        "## 🛡️ Security Scan Results",
        "",
        "| Scan Type | Status | Findings |",
        "|-----------|--------|----------|"
    ]

    # Frontend dependencies
    frontend_deps = security_data.get('frontend_dependencies', {})
    vulns = frontend_deps.get('vulnerabilities', {})
    total_vulns = sum(vulns.values()) if vulns else 0
    status = '✅' if total_vulns == 0 else '⚠️'
    lines.append(f"| Frontend Dependencies | {status} | {total_vulns} vulnerabilities |")

    # Backend dependencies
    backend_deps = security_data.get('backend_dependencies', {})
    vulns = backend_deps.get('vulnerabilities', {})
    total_vulns = sum(vulns.values()) if vulns else 0
    status = '✅' if total_vulns == 0 else '⚠️'
    lines.append(f"| Backend Dependencies | {status} | {total_vulns} vulnerabilities |")

    # Python security (Bandit)
    bandit = security_data.get('bandit', {})
    errors = bandit.get('errors', 0)
    status = '✅' if errors == 0 else '⚠️'
    lines.append(f"| Bandit Scan | {status} | {errors} issues |")

    # Semgrep
    semgrep = security_data.get('semgrep', {})
    results = semgrep.get('results', 0)
    status = '✅' if results == 0 else '⚠️'
    lines.append(f"| Semgrep Scan | {status} | {results} findings |")

    # Secrets
    secrets = security_data.get('secrets', {})
    found = secrets.get('found', False)
    status = '✅' if not found else '❌'
    lines.append(f"| Secrets Scan | {status} | {'Secrets found!' if found else 'No secrets'} |")

    # CodeQL
    codeql = security_data.get('codeql', {})
    alerts = codeql.get('alerts', 0)
    status = '✅' if alerts == 0 else '⚠️'
    lines.append(f"| CodeQL Analysis | {status} | {alerts} alerts |")

    # Docker
    docker = security_data.get('docker', {})
    vulnerabilities = docker.get('vulnerabilities', {})
    critical = vulnerabilities.get('critical', 0)
    high = vulnerabilities.get('high', 0)
    status = '✅' if critical == 0 and high == 0 else '⚠️'
    lines.append(f"| Docker Image Scan | {status} | {critical} critical, {high} high |")

    lines.append("")
    return "\n".join(lines)


def generate_performance_section(performance_data: Dict[str, Any]) -> str:
    """Generate performance test section."""
    lines = [
        "## ⚡ Performance Test Results",
        ""
    ]

    # Backend load tests
    backend = performance_data.get('backend', {})
    if backend:
        lines.append("### Backend Load Tests (Locust)")
        lines.append("")
        lines.append("| Endpoint | Requests | Failures | Median (ms) | 95th %ile (ms) | RPS |")
        lines.append("|----------|----------|----------|------------|----------------|-----|")

        endpoints = backend.get('endpoints', [])
        for ep in endpoints:
            name = ep.get('name', 'N/A')
            requests = ep.get('requests', 0)
            failures = ep.get('failures', 0)
            median = ep.get('median', 0)
            p95 = ep.get('p95', 0)
            rps = ep.get('rps', 0)

            lines.append(f"| {name} | {requests} | {failures} | {median:.2f} | {p95:.2f} | {rps:.2f} |")

        # Regression detection
        regression = backend.get('regression', {})
        has_regression = regression.get('has_regression', False)
        if has_regression:
            lines.append("")
            lines.append("#### ⚠️ Performance Regressions Detected")
            lines.append("")
            lines.append("| Endpoint | Current | Baseline | Degradation | Threshold |")
            lines.append("|----------|---------|----------|-------------|-----------|")

            for reg in regression.get('regressions', []):
                endpoint = reg.get('endpoint', 'N/A')
                current = reg.get('current', 0)
                baseline = reg.get('baseline', 0)
                degradation = reg.get('degradation', 0) * 100
                threshold = reg.get('threshold', 0) * 100
                color = get_performance_color(reg.get('degradation', 0))

                lines.append(f"| {endpoint} | {current:.2f}ms | {baseline:.2f}ms | {color} {degradation:.1f}% | {threshold:.0f}% |")
        else:
            lines.append("")
            lines.append("✅ **No performance regressions detected**")

        lines.append("")

    # Frontend Lighthouse tests
    frontend = performance_data.get('frontend', {})
    if frontend:
        lines.append("### Frontend Lighthouse Scores")
        lines.append("")
        lines.append("| Category | Score | Status |")
        lines.append("|----------|-------|--------|")

        categories = frontend.get('categories', {})
        for cat_name, cat_data in categories.items():
            score = cat_data.get('score', 0) * 100
            status = '✅' if score >= 90 else ('⚠️' if score >= 50 else '❌')
            lines.append(f"| {cat_name.capitalize()} | {score:.0f} | {status} |")

        lines.append("")

    return "\n".join(lines)


def generate_summary_statistics(all_data: Dict[str, Any]) -> str:
    """Generate summary statistics section."""
    lines = [
        "## 📈 Summary Statistics",
        ""
    ]

    # Calculate pass rate
    test_results = all_data.get('test_jobs', {})
    passed = sum(1 for s in test_results.values() if s.lower() == 'success')
    total = len(test_results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    # Coverage averages
    frontend_cov = all_data.get('frontend_coverage', {})
    backend_cov = all_data.get('backend_coverage', {})

    frontend_pct = frontend_cov.get('total', {}).get('statements', {}).get('pct', 0) if frontend_cov else 0
    backend_pct = float(backend_cov.get('totals', {}).get('percent_covered', 0)) if backend_cov else 0
    overall_coverage = (frontend_pct + backend_pct) / 2 if frontend_pct and backend_pct else 0

    # Security issues
    security = all_data.get('security', {})
    total_issues = 0
    for scan_type, data in security.items():
        if isinstance(data, dict) and 'vulnerabilities' in data:
            total_issues += sum(data['vulnerabilities'].values())

    # Performance
    performance = all_data.get('performance', {})
    backend_perf = performance.get('backend', {})
    has_regression = backend_perf.get('regression', {}).get('has_regression', False)

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Test Pass Rate | {pass_rate:.1f}% ({passed}/{total}) |")
    lines.append(f"| Overall Coverage | {overall_coverage:.1f}% |")
    lines.append(f"| Security Issues | {total_issues} |")
    lines.append(f"| Performance Regression | {'❌ Yes' if has_regression else '✅ No'} |")
    lines.append("")

    # Overall status
    all_passed = (
        pass_rate == 100 and
        overall_coverage >= 80 and
        total_issues == 0 and
        not has_regression
    )

    if all_passed:
        lines.append("### 🎉 All Checks Passed!")
        lines.append("")
        lines.append("Your changes are ready to merge. All tests pass, coverage is adequate,")
        lines.append("no security issues were found, and no performance regressions detected.")
    else:
        lines.append("### ⚠️ Action Required")
        lines.append("")
        if pass_rate < 100:
            lines.append(f"- ❌ Some tests failed ({passed}/{total} passed)")
        if overall_coverage < 80:
            lines.append(f"- ❌ Coverage below threshold ({overall_coverage:.1f}% < 80%)")
        if total_issues > 0:
            lines.append(f"- ⚠️ Security issues found: {total_issues}")
        if has_regression:
            lines.append(f"- ❌ Performance regression detected")

    lines.append("")

    return "\n".join(lines)


def generate_artifacts_section(artifacts: List[str]) -> str:
    """Generate artifacts section."""
    if not artifacts:
        return ""

    lines = [
        "## 📎 Detailed Reports",
        "",
        "Download detailed reports from the workflow artifacts:",
        ""
    ]

    for artifact in artifacts:
        lines.append(f"- 📁 `{artifact}`")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive test summary')
    parser.add_argument('--test-results', help='Test results JSON file')
    parser.add_argument('--frontend-coverage', help='Frontend coverage JSON file')
    parser.add_argument('--backend-coverage', help='Backend coverage JSON file')
    parser.add_argument('--security-data', help='Security scan results JSON file')
    parser.add_argument('--performance-data', help='Performance test results JSON file')
    parser.add_argument('--test-jobs', help='Test job statuses JSON file')
    parser.add_argument('--output', default='comprehensive-summary.md', help='Output markdown file')
    parser.add_argument('--artifacts', help='Artifacts list JSON file')

    args = parser.parse_args()

    # Load all data
    test_jobs = load_json(args.test_jobs) if args.test_jobs else {}
    frontend_cov = load_json(args.frontend_coverage) if args.frontend_coverage else None
    backend_cov = load_json(args.backend_coverage) if args.backend_coverage else None
    security_data = load_json(args.security_data) if args.security_data else {}
    performance_data = load_json(args.performance_data) if args.performance_data else {}
    artifacts_data = load_json(args.artifacts) if args.artifacts else {}
    artifacts = artifacts_data.get('artifacts', []) if artifacts_data else []

    # Build comprehensive data structure
    all_data = {
        'test_jobs': test_jobs,
        'frontend_coverage': frontend_cov,
        'backend_coverage': backend_cov,
        'security': security_data,
        'performance': performance_data,
    }

    # Generate summary
    summary_lines = [
        "# 🔬 Comprehensive Test Summary Dashboard",
        "",
        f"**Generated:** {os.environ.get('GENERATED_TIME', 'N/A')}",
        f"**Commit:** {os.environ.get('COMMIT_SHA', 'N/A')[:8]}",
        f"**Branch:** {os.environ.get('BRANCH_NAME', 'N/A')}",
        "",
        "---",
        ""
    ]

    # Add each section
    summary_lines.append(generate_test_results_section(test_jobs))
    summary_lines.append(generate_coverage_section(frontend_cov, backend_cov))
    summary_lines.append(generate_security_section(security_data))
    summary_lines.append(generate_performance_section(performance_data))
    summary_lines.append(generate_summary_statistics(all_data))
    summary_lines.append(generate_artifacts_section(artifacts))

    # Footer
    summary_lines.extend([
        "---",
        "",
        "<details>",
        "<summary>📖 About this report</summary>",
        "",
        "This comprehensive test summary aggregates results from:",
        "",
        "- **CI Pipeline**: Unit tests, integration tests, linting",
        "- **Coverage Reports**: Frontend and backend code coverage",
        "- **Security Scans**: Dependency scans, SAST, secrets detection",
        "- **Performance Tests**: Load tests and Lighthouse scores",
        "",
        "For detailed analysis, download the individual artifacts.",
        "</details>",
        ""
    ])

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(summary_lines))

    print(f"✅ Comprehensive summary generated: {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
