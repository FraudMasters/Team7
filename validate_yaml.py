#!/usr/bin/env python3
"""Validate YAML syntax for GitHub/Gitea workflow files."""

import yaml
import sys
from pathlib import Path

def validate_yaml_file(file_path):
    """Validate a single YAML file."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print(f"✓ {file_path}: Valid YAML")
        return True
    except yaml.YAMLError as e:
        print(f"✗ {file_path}: YAML Error - {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path}: Error - {e}")
        return False

def main():
    """Validate all workflow YAML files."""
    workflows_dir = Path('.github/workflows')
    yaml_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))

    if not yaml_files:
        print("No YAML files found in .github/workflows/")
        return 1

    print(f"Validating {len(yaml_files)} workflow file(s)...\n")

    all_valid = True
    for yaml_file in yaml_files:
        if not validate_yaml_file(yaml_file):
            all_valid = False

    print()
    if all_valid:
        print("✓ All workflow files have valid YAML syntax")
        return 0
    else:
        print("✗ Some workflow files have YAML syntax errors")
        return 1

if __name__ == '__main__':
    sys.exit(main())
