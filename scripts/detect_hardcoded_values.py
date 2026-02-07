#!/usr/bin/env python3
"""
Automated hardcoded value detection script.

This script scans Python source files for hardcoded configuration values
that should be loaded from the centralized configuration system.

Usage:
    python scripts/detect_hardcoded_values.py [--all] [--exit-on-error] [--verbose]

Options:
    --all           Scan all files including tests and scripts
    --exit-on-error Exit with error code if hardcoded values are found
    --verbose       Show detailed output with file locations

Exit codes:
    0: No hardcoded values found
    1: Hardcoded values found
"""
import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class HardcodedValueDetector(ast.NodeVisitor):
    """AST visitor to detect hardcoded configuration values in Python code."""

    def __init__(self, filename: str, exclude_patterns: Set[str]):
        """
        Initialize the detector.

        Args:
            filename: Name of the file being scanned (for reporting)
            exclude_patterns: Set of regex patterns to exclude from detection
        """
        self.filename = filename
        self.exclude_patterns = exclude_patterns
        self.issues: List[Dict[str, str]] = []

        # Patterns to detect hardcoded values
        self.url_patterns = [
            r'https?://localhost:\d+',
            r'https?://127\.0\.0\.1:\d+',
        ]

        self.string_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
        ]

        # Settings that should come from config
        self.config_settings = {
            'database_url', 'redis_url', 'backend_host', 'backend_port',
            'frontend_url', 'max_upload_size_mb', 'allowed_file_types',
            'analysis_timeout_seconds', 'log_level', 'celery_broker_url',
            'celery_result_backend', 'backup_retention_days',
            'audit_log_retention_days', 'upload_dir', 'backup_dir',
            'models_cache_path', 'languagetool_server', 'environment',
        }

    def _should_exclude(self, value: str) -> bool:
        """Check if a value matches any exclusion pattern."""
        for pattern in self.exclude_patterns:
            if re.search(pattern, value):
                return True
        return False

    def _check_hardcoded_string(self, node: ast.Str, value: str) -> None:
        """
        Check if a string literal contains hardcoded configuration.

        Args:
            node: AST string node
            value: String value to check
        """
        # Skip if matches exclusion patterns
        if self._should_exclude(value):
            return

        line_no = node.lineno if hasattr(node, 'lineno') else 0

        # Check for hardcoded localhost/127.0.0.1 in URLs
        for pattern in self.url_patterns:
            if re.search(pattern, value):
                self.issues.append({
                    'type': 'hardcoded_url',
                    'value': value,
                    'line': line_no,
                    'message': f'Hardcoded URL detected: {value}',
                })
                return

        # Check for localhost/127.0.0.1 strings in certain contexts
        for pattern in self.string_patterns:
            if re.search(pattern, value):
                # Check if it's likely a config value (not just a comment, etc.)
                self.issues.append({
                    'type': 'hardcoded_host',
                    'value': value,
                    'line': line_no,
                    'message': f'Hardcoded host reference detected: {value}',
                })
                return

    def _check_hardcoded_path(self, node: ast.Constant) -> None:
        """Check for hardcoded file paths."""
        if not isinstance(node.value, str):
            return

        value = node.value
        line_no = node.lineno if hasattr(node, 'lineno') else 0

        # Check for Path() calls with hardcoded directories
        path_indicators = ['data/', 'uploads/', 'backups/', './data', 'models_cache']
        for indicator in path_indicators:
            if indicator in value.lower() and not self._should_exclude(value):
                self.issues.append({
                    'type': 'hardcoded_path',
                    'value': value,
                    'line': line_no,
                    'message': f'Hardcoded path detected: {value}',
                })
                return

    def _check_hardcoded_number(self, node: ast.Constant) -> None:
        """Check for hardcoded numeric configuration values."""
        if not isinstance(node.value, (int, float)):
            return

        value = node.value
        line_no = node.lineno if hasattr(node, 'lineno') else 0

        # Common hardcoded config values to flag
        # Skip small numbers that are likely loop counters or array indices
        if isinstance(value, int):
            # Port numbers
            if 1024 <= value <= 65535:
                self.issues.append({
                    'type': 'hardcoded_port',
                    'value': str(value),
                    'line': line_no,
                    'message': f'Possible hardcoded port number: {value}',
                })
            # File size limits (in MB or bytes)
            elif value in [5242880, 10485760, 20971520]:  # 5MB, 10MB, 20MB in bytes
                self.issues.append({
                    'type': 'hardcoded_file_size',
                    'value': str(value),
                    'line': line_no,
                    'message': f'Hardcoded file size limit (bytes): {value}',
                })
            elif value in [5, 10, 20, 50, 100]:  # Common MB values
                # Only flag if it's a standalone number, not a loop counter
                # This is a rough heuristic
                self.issues.append({
                    'type': 'hardcoded_file_size_mb',
                    'value': str(value),
                    'line': line_no,
                    'message': f'Possible hardcoded file size limit (MB): {value}',
                })
            # Timeout values
            elif 10 <= value <= 3600 and value % 10 == 0:
                self.issues.append({
                    'type': 'hardcoded_timeout',
                    'value': str(value),
                    'line': line_no,
                    'message': f'Possible hardcoded timeout (seconds): {value}',
                })

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant nodes (Python 3.8+)."""
        if isinstance(node.value, str):
            self._check_hardcoded_string(node, node.value)
            self._check_hardcoded_path(node)
        elif isinstance(node.value, (int, float)):
            self._check_hardcoded_number(node)
        self.generic_visit(node)

    def visit_Str(self, node: ast.Str) -> None:
        """Visit string nodes (Python 3.7 compatibility)."""
        self._check_hardcoded_string(node, node.s)
        self.generic_visit(node)

    def visit_Num(self, node: ast.Num) -> None:
        """Visit number nodes (Python 3.7 compatibility)."""
        self._check_hardcoded_number(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes to detect Path() and other config calls."""
        # Check for Path("hardcoded") patterns
        if isinstance(node.func, ast.Name) and node.func.id == 'Path':
            if node.args and isinstance(node.args[0], (ast.Constant, ast.Str)):
                arg = node.args[0]
                value = arg.value if isinstance(arg, ast.Constant) else arg.s
                line_no = node.lineno if hasattr(node, 'lineno') else 0

                path_indicators = ['data/', 'uploads/', 'backups/', './data']
                for indicator in path_indicators:
                    if indicator in value.lower() and not self._should_exclude(value):
                        self.issues.append({
                            'type': 'hardcoded_path_call',
                            'value': f'Path("{value}")',
                            'line': line_no,
                            'message': f'Hardcoded Path() detected: Path("{value}")',
                        })
                        break

        # Check for os.getenv with default values that contain localhost
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'getenv':
            if len(node.args) >= 2:
                default_arg = node.args[1]
                if isinstance(default_arg, (ast.Constant, ast.Str)):
                    default_value = default_arg.value if isinstance(default_arg, ast.Constant) else default_arg.s
                    if 'localhost' in default_value or '127.0.0.1' in default_value:
                        line_no = node.lineno if hasattr(node, 'lineno') else 0
                        self.issues.append({
                            'type': 'localhost_default',
                            'value': default_value,
                            'line': line_no,
                            'message': f'os.getenv() with localhost default: {default_value}',
                        })

        self.generic_visit(node)


def scan_file(filepath: Path, exclude_patterns: Set[str]) -> List[Dict[str, str]]:
    """
    Scan a single Python file for hardcoded values.

    Args:
        filepath: Path to the file to scan
        exclude_patterns: Set of regex patterns to exclude from detection

    Returns:
        List of issues found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse the AST
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'value': str(e),
                'line': e.lineno or 0,
                'message': f'Syntax error in file: {e}',
            }]

        # Run the detector
        detector = HardcodedValueDetector(str(filepath), exclude_patterns)
        detector.visit(tree)
        return detector.issues

    except Exception as e:
        return [{
            'type': 'scan_error',
            'value': str(e),
            'line': 0,
            'message': f'Error scanning file: {e}',
        }]


def scan_directory(
    root_dir: Path,
    include_tests: bool = False,
    exclude_patterns: Set[str] = None,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Scan a directory for hardcoded configuration values.

    Args:
        root_dir: Root directory to scan
        include_tests: Whether to include test files
        exclude_patterns: Set of regex patterns to exclude from detection

    Returns:
        Dictionary mapping file paths to lists of issues
    """
    if exclude_patterns is None:
        exclude_patterns = set()

    # Default exclusion patterns
    default_exclusions = {
        r'# *example',  # Commented examples
        r'https?://example\.com',  # Example URLs
        r'://.*\.example\.com',  # Example domain URLs
        r'db\.example\.com',  # Example database host
        r'postgres://user:password@',  # Example connection strings
        r'SK-EXAMPLE',  # Example API keys
        r'xxx',  # Placeholder values
    }
    exclude_patterns.update(default_exclusions)

    results = {}

    # Find all Python files
    python_files = []
    for ext in ['*.py']:
        python_files.extend(root_dir.rglob(ext))

    # Filter out test files if not including them
    for filepath in python_files:
        # Skip test files if not including them
        if not include_tests and (
            'test_' in filepath.name or
            '_test.py' in filepath.name or
            'tests/' in str(filepath) or
            '__pycache__' in str(filepath)
        ):
            continue

        # Skip migrations and __init__.py files
        if filepath.name == '__init__.py':
            continue

        # Skip the migration script itself
        if 'detect_hardcoded_values.py' in str(filepath):
            continue

        issues = scan_file(filepath, exclude_patterns)
        if issues:
            results[str(filepath.relative_to(root_dir))] = issues

    return results


def print_results(results: Dict[str, List[Dict[str, str]]], verbose: bool = False) -> None:
    """
    Print scan results in a formatted way.

    Args:
        results: Dictionary of scan results
        verbose: Whether to show detailed output
    """
    if not results:
        print("✅ No hardcoded configuration values found")
        return

    total_issues = sum(len(issues) for issues in results.values())
    print(f"❌ Found {total_issues} hardcoded value(s) in {len(results)} file(s)")
    print()

    # Group issues by type
    by_type: Dict[str, List[Dict[str, str]]] = {}
    for filepath, issues in results.items():
        for issue in issues:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append({
                'file': filepath,
                **issue
            })

    # Print issues grouped by type
    for issue_type, issues in sorted(by_type.items()):
        print(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)}):")
        print("-" * 60)

        for issue in issues:
            if verbose:
                print(f"  {issue['file']}:{issue['line']}")
                print(f"    {issue['message']}")
            else:
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Detect hardcoded configuration values in Python code'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Scan all files including tests and scripts'
    )
    parser.add_argument(
        '--exit-on-error',
        action='store_true',
        help='Exit with error code if hardcoded values are found'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output with file locations'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='.',
        help='Directory to scan (default: current directory)'
    )

    args = parser.parse_args()

    # Get the root directory
    root_dir = Path(args.directory).resolve()

    # Check if directory exists
    if not root_dir.exists():
        print(f"❌ Error: Directory '{root_dir}' does not exist", file=sys.stderr)
        return 1

    # Scan for hardcoded values
    print(f"🔍 Scanning '{root_dir}' for hardcoded configuration values...")
    print()

    results = scan_directory(
        root_dir,
        include_tests=args.all,
    )

    # Print results
    print_results(results, verbose=args.verbose)
    print()

    # Return appropriate exit code
    if results and args.exit_on_error:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
