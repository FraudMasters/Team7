#!/usr/bin/env python3
"""
Configuration migration validation script.

This script validates that the centralized configuration migration is complete
by checking for required files, proper config usage, and absence of hardcoded values.

Usage:
    python scripts/validate_config_migration.py [--verbose] [--exit-on-error]

Options:
    --verbose       Show detailed validation output
    --exit-on-error Exit with error code if validation fails

Exit codes:
    0: All validations passed
    1: One or more validations failed
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigMigrationValidator:
    """Validates that configuration migration is complete."""

    def __init__(self, root_dir: Path, verbose: bool = False):
        """
        Initialize the validator.

        Args:
            root_dir: Root directory of the project
            verbose: Whether to show detailed output
        """
        self.root_dir = root_dir
        self.verbose = verbose
        self.results: List[Dict[str, any]] = []

    def _add_result(
        self,
        check_name: str,
        passed: bool,
        message: str,
        details: str = ""
    ) -> None:
        """
        Add a validation result.

        Args:
            check_name: Name of the validation check
            passed: Whether the check passed
            message: Summary message
            details: Additional details (shown in verbose mode)
        """
        self.results.append({
            'check': check_name,
            'passed': passed,
            'message': message,
            'details': details,
        })

    def check_backend_config_files(self) -> None:
        """Check that all required backend config files exist."""
        required_files = [
            'backend/config/__init__.py',
            'backend/config/base.py',
            'backend/config/environments.py',
            'backend/config/validators.py',
            'backend/config/validation.py',
            'backend/config/audit.py',
            'backend/config/hotreload.py',
            'backend/config/encryption.py',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Backend config files',
                False,
                f'Missing {len(missing_files)} required config file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Backend config files',
                True,
                'All required backend config files exist',
                f'Found {len(required_files)} config module files'
            )

    def check_backend_env_config_files(self) -> None:
        """Check that environment-specific backend config files exist."""
        required_files = [
            'backend/config/config.dev.yml',
            'backend/config/config.staging.yml',
            'backend/config/config.production.yml',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Backend env config files',
                False,
                f'Missing {len(missing_files)} environment config file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Backend env config files',
                True,
                'All environment-specific config files exist',
                f'Found dev, staging, and production config files'
            )

    def check_frontend_config_files(self) -> None:
        """Check that required frontend config files exist."""
        required_files = [
            'frontend/src/config/types.ts',
            'frontend/src/config/validation.ts',
            'frontend/src/config/index.ts',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Frontend config files',
                False,
                f'Missing {len(missing_files)} required config file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Frontend config files',
                True,
                'All required frontend config files exist',
                f'Found {len(required_files)} frontend config files'
            )

    def check_env_files(self) -> None:
        """Check that environment .env files exist."""
        required_files = [
            '.env.dev',
            '.env.staging',
            '.env.production',
            '.env.dev.example',
            '.env.staging.example',
            '.env.production.example',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Environment files',
                False,
                f'Missing {len(missing_files)} .env file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Environment files',
                True,
                'All environment .env files exist',
                f'Found {len(required_files)} environment file templates'
            )

    def check_docker_compose_files(self) -> None:
        """Check that environment-specific docker-compose files exist."""
        required_files = [
            'docker-compose.dev.yml',
            'docker-compose.staging.yml',
            'docker-compose.production.yml',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Docker Compose override files',
                False,
                f'Missing {len(missing_files)} docker-compose file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Docker Compose override files',
                True,
                'All environment-specific docker-compose files exist',
                f'Found dev, staging, and production override files'
            )

    def check_backend_imports_config(self) -> None:
        """Check that backend services import from centralized config."""
        # Check key backend files
        files_to_check = [
            ('backend/main.py', 'from config import'),
            ('backend/celery_config.py', 'from config import'),
            ('backend/celery_app.py', 'from config import'),
        ]

        issues = []
        for filepath, expected_import in files_to_check:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if expected_import not in content:
                        issues.append(f'{filepath} does not import from config')
            except Exception as e:
                issues.append(f'{filepath}: {e}')

        if issues:
            self._add_result(
                'Backend config imports',
                False,
                f'{len(issues)} file(s) not using centralized config',
                '\n'.join(f'  - {issue}' for issue in issues)
            )
        else:
            self._add_result(
                'Backend config imports',
                True,
                'All checked backend files use centralized config',
                'Verified imports in main.py, celery_config.py, celery_app.py'
            )

    def check_frontend_uses_config(self) -> None:
        """Check that frontend uses centralized config service."""
        # Check key frontend files
        filepath = self.root_dir / 'frontend/src/api/client.ts'

        if not filepath.exists():
            self._add_result(
                'Frontend config usage',
                False,
                'frontend/src/api/client.ts not found',
                ''
            )
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should import config
            if "from '@/config'" in content or "from '@/config/index'" in content:
                self._add_result(
                    'Frontend config usage',
                    True,
                    'Frontend uses centralized config service',
                    'client.ts imports from @/config'
                )
            else:
                self._add_result(
                    'Frontend config usage',
                    False,
                    'Frontend not using centralized config service',
                    'client.ts should import from @/config'
                )
        except Exception as e:
            self._add_result(
                'Frontend config usage',
                False,
                f'Error checking frontend config: {e}',
                ''
            )

    def check_documentation(self) -> None:
        """Check that configuration documentation exists."""
        required_files = [
            'docs/configuration.md',
            'docs/configuration/reference.md',
            'backend/config/README.md',
        ]

        missing_files = []
        for filepath in required_files:
            full_path = self.root_dir / filepath
            if not full_path.exists():
                missing_files.append(filepath)

        if missing_files:
            self._add_result(
                'Configuration documentation',
                False,
                f'Missing {len(missing_files)} documentation file(s)',
                f'Missing files:\n' + '\n'.join(f'  - {f}' for f in missing_files)
            )
        else:
            self._add_result(
                'Configuration documentation',
                True,
                'All configuration documentation exists',
                f'Found {len(required_files)} documentation files'
            )

    def check_no_hardcoded_localhost(self) -> None:
        """Check that there are no hardcoded localhost references in backend code."""
        import subprocess

        try:
            # Run the hardcoded value detection script
            result = subprocess.run(
                [sys.executable, 'scripts/detect_hardcoded_values.py'],
                capture_output=True,
                text=True,
                cwd=self.root_dir,
            )

            if result.returncode == 0:
                self._add_result(
                    'Hardcoded values check',
                    True,
                    'No hardcoded configuration values found',
                    result.stdout.strip()
                )
            else:
                self._add_result(
                    'Hardcoded values check',
                    False,
                    'Hardcoded configuration values detected',
                    result.stdout.strip()
                )
        except Exception as e:
            self._add_result(
                'Hardcoded values check',
                False,
                f'Error running hardcoded value detection: {e}',
                ''
            )

    def run_all_checks(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all checks passed, False otherwise
        """
        print("🔍 Running configuration migration validation...")
        print()

        # Run all checks
        self.check_backend_config_files()
        self.check_backend_env_config_files()
        self.check_frontend_config_files()
        self.check_env_files()
        self.check_docker_compose_files()
        self.check_backend_imports_config()
        self.check_frontend_uses_config()
        self.check_documentation()
        self.check_no_hardcoded_localhost()

        # Print results
        self._print_results()

        # Return overall status
        return all(r['passed'] for r in self.results)

    def _print_results(self) -> None:
        """Print validation results."""
        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)

        print(f"\n{'='*60}")
        print(f"Validation Results: {passed_count}/{total_count} checks passed")
        print(f"{'='*60}")
        print()

        for result in self.results:
            status_icon = "✅" if result['passed'] else "❌"
            print(f"{status_icon} {result['check']}: {result['message']}")

            if self.verbose and result['details']:
                print(f"\n  Details:")
                for line in result['details'].split('\n'):
                    print(f"    {line}")
            print()

        if passed_count == total_count:
            print(f"{'='*60}")
            print("✅ All validation checks passed!")
            print(f"{'='*60}")
        else:
            failed_count = total_count - passed_count
            print(f"{'='*60}")
            print(f"❌ {failed_count} validation check(s) failed")
            print(f"{'='*60}")


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Validate configuration migration is complete'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed validation output'
    )
    parser.add_argument(
        '--exit-on-error',
        action='store_true',
        help='Exit with error code if validation fails'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='.',
        help='Root directory of the project (default: current directory)'
    )

    args = parser.parse_args()

    # Get the root directory
    root_dir = Path(args.directory).resolve()

    # Check if directory exists
    if not root_dir.exists():
        print(f"❌ Error: Directory '{root_dir}' does not exist", file=sys.stderr)
        return 1

    # Run validation
    validator = ConfigMigrationValidator(root_dir, verbose=args.verbose)
    all_passed = validator.run_all_checks()

    # Return appropriate exit code
    if not all_passed and args.exit_on_error:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
