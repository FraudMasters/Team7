#!/usr/bin/env python3
"""
Validation script to detect merge conflict markers in the repository.

This script scans all source files for git merge conflict markers (<<<<<<<,
=======, >>>>>>>) and reports any conflicts found. It's designed to be run
after merge operations to ensure all conflicts have been resolved.

Usage:
    python scripts/validate_no_conflicts.py

Exit codes:
    0 - No conflict markers found (success)
    1 - Conflict markers detected (failure)
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple


# Conflict marker patterns
CONFLICT_MARKERS = [
    "<<<<<<< <<",
    "<<<<<<< ",
    "======= ",
    ">>>>>>> ",
]

# File extensions to scan
INCLUDE_EXTENSIONS = {
    # Python
    '.py',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx',
    # Markup/Data
    '.html', '.htm', '.xml', '.json',
    '.yaml', '.yml',
    # Config/Docs
    '.md', '.txt', '.rst',
    '.cfg', '.conf', '.ini',
    # Styles
    '.css', '.scss', '.sass', '.less',
    # Shell
    '.sh', '.bash',
    # Other
    '.dockerfile',
}

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    '.git',
    '.auto-claude',
    'node_modules',
    '__pycache__',
    '.pytest_cache',
    '.venv',
    'venv',
    'env',
    '.env',
    'dist',
    'build',
    '.next',
    '.nuxt',
    'coverage',
    '.tox',
    '.mypy_cache',
}


def find_conflict_markers(root_dir: Path) -> List[Tuple[Path, int, str]]:
    """
    Scan directory for files containing conflict markers.

    Args:
        root_dir: Root directory to start scanning from

    Returns:
        List of tuples (file_path, line_number, line_content) for each conflict marker found
    """
    conflicts = []

    for file_path in root_dir.rglob('*'):
        # Skip directories
        if not file_path.is_file():
            continue

        # Skip excluded directories
        if any(excluded_dir in file_path.parts for excluded_dir in EXCLUDE_DIRS):
            continue

        # Skip files without matching extensions
        if file_path.suffix.lower() not in INCLUDE_EXTENSIONS:
            continue

        # Skip this script itself
        if file_path.name == 'validate_no_conflicts.py':
            continue

        try:
            # Read file and check for conflict markers
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for marker in CONFLICT_MARKERS:
                        if marker in line:
                            conflicts.append((file_path, line_num, line.strip()))
                            break  # Only record once per line
        except (IOError, OSError, PermissionError) as e:
            # Skip files that can't be read
            continue

    return conflicts


def group_conflicts_by_file(conflicts: List[Tuple[Path, int, str]]) -> dict:
    """
    Group conflict markers by file for better reporting.

    Args:
        conflicts: List of conflict tuples

    Returns:
        Dictionary mapping file paths to list of (line_num, line) tuples
    """
    grouped = {}
    for file_path, line_num, line in conflicts:
        if file_path not in grouped:
            grouped[file_path] = []
        grouped[file_path].append((line_num, line))
    return grouped


def print_results(conflicts: List[Tuple[Path, int, str]]):
    """Print conflict detection results."""
    if not conflicts:
        print("✓ No conflict markers found")
        print(f"  Scanned {os.getcwd()} and subdirectories")
        return

    grouped = group_conflicts_by_file(conflicts)

    print(f"✗ Found {len(conflicts)} conflict marker(s) in {len(grouped)} file(s)")
    print()

    for file_path, markers in sorted(grouped.items()):
        # Show relative path from current directory
        try:
            rel_path = file_path.relative_to(os.getcwd())
        except ValueError:
            rel_path = file_path

        print(f"  {rel_path}")

        # Show first few lines with conflicts
        for line_num, line in markers[:3]:
            # Truncate long lines
            display_line = line[:80] + "..." if len(line) > 80 else line
            print(f"    Line {line_num}: {display_line}")

        if len(markers) > 3:
            print(f"    ... and {len(markers) - 3} more")

        print()


def main():
    """Main entry point for conflict detection script."""
    print("=" * 70)
    print("Merge Conflict Marker Detection")
    print("=" * 70)
    print()

    # Get current directory
    root_dir = Path.cwd()

    # Scan for conflicts
    print("Scanning for conflict markers...")
    print(f"  Root directory: {root_dir}")
    print(f"  Excluded directories: {', '.join(sorted(EXCLUDE_DIRS))}")
    print(f"  Included file types: {len(INCLUDE_EXTENSIONS)} extensions")
    print()

    conflicts = find_conflict_markers(root_dir)

    # Print results
    print("=" * 70)
    print("Results")
    print("=" * 70)
    print()

    print_results(conflicts)

    print("=" * 70)

    if conflicts:
        print()
        print("ERROR: Merge conflict markers detected!")
        print("Please resolve all conflicts before committing.")
        print()
        return 1
    else:
        print()
        print("SUCCESS: Repository is clean - no conflict markers detected")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
