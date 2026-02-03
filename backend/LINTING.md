# Backend Linting Guide

This guide covers Python code linting and formatting for the backend service.

## Overview

The backend uses three linting tools to maintain code quality and consistency:

| Tool | Purpose | Config File |
|------|---------|-------------|
| **Black** | Code formatter (opinionated, auto-fixes) | `pyproject.toml` |
| **Flake8** | Style guide enforcement (PEP 8) | `pyproject.toml` |
| **MyPy** | Static type checker (gradual typing) | `pyproject.toml` |

All tools are configured in `backend/pyproject.toml` with project-specific settings.

## Quick Start

### Check code formatting (Black)

```bash
cd backend
black --check --diff .
```

This will show what Black **would** change without making any modifications.

### Auto-format code (Black)

```bash
cd backend
black .
```

This will automatically format all Python files according to Black's style guide.

### Check style issues (Flake8)

```bash
cd backend
flake8 .
```

Reports style violations, syntax errors, and complexity issues.

### Check type annotations (MyPy)

```bash
cd backend
mypy .
```

Reports type checking errors and missing type annotations.

## Run All Linters

To run all linting checks at once:

```bash
cd backend
black --check --diff . && flake8 . && mypy .
```

Or use the individual commands:

```bash
# Format code
cd backend && black .

# Check style
cd backend && flake8 .

# Check types
cd backend && mypy .
```

## Configuration

All linting tools are configured in `backend/pyproject.toml`:

### Black Settings

- **Line length**: 100 characters
- **Target Python**: 3.9, 3.10, 3.11
- **Excluded**: `.git`, `__pycache__`, `venv`, `.venv`, build artifacts

### Flake8 Settings

- **Max line length**: 100 characters (matches Black)
- **Ignored errors**:
  - `E203`: Whitespace before ':' (conflicts with Black)
  - `E266`: Too many '#' for block comment
  - `E501`: Line too long (handled by Black)
  - `W503`: Line break before binary operator (conflicts with Black)
- **Max complexity**: 10 (McCabe complexity checker)

### MyPy Settings

- **Python version**: 3.9
- **Gradual typing**: Enabled (doesn't require all functions to be typed)
- **Checks enabled**:
  - Warns about missing return type annotations
  - Warns about unused configuration
  - Checks untyped function definitions
  - Shows error codes and column numbers

## Pre-Commit Hooks (Optional)

To automatically run linting before each commit, install pre-commit hooks:

```bash
# Install pre-commit framework
pip install pre-commit

# Set up the git hook
cd backend
pre-commit install
```

Create `.pre-commit-config.yaml` in the backend directory:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-requests
```

Now every `git commit` will automatically run the linters.

## CI/CD Integration

Linting is automatically run in GitHub Actions for every pull request:

```yaml
# From .github/workflows/deploy.yml
- name: Run linting
  run: |
    black --check --config pyproject.toml .
    flake8 --config pyproject.toml .
    mypy --config-file pyproject.toml .
```

If any linter fails, the PR cannot be merged until issues are fixed.

## Common Workflows

### Before Committing Code

```bash
# 1. Format with Black (auto-fixes)
cd backend && black .

# 2. Check style with Flake8
cd backend && flake8 .

# 3. Check types with MyPy
cd backend && mypy .
```

### Fix Black Formatting Issues

```bash
# See what would change
cd backend && black --check --diff .

# Auto-fix all issues
cd backend && black .
```

### Fix Flake8 Issues

```bash
# See all issues
cd backend && flake8 .

# Fix specific file
cd backend && flake8 path/to/file.py

# Ignore specific error (not recommended)
# Add # noqa: E501 at the end of the line
```

### Fix MyPy Issues

```bash
# Check all files
cd backend && mypy .

# Check specific file
cd backend && mypy path/to/file.py

# Ignore specific error (use sparingly)
# Add # type: ignore comment at the end of the line
```

## Troubleshooting

### Black reports formatting issues

**Solution**: Run `black .` to auto-format all files. Black is opinionated and generally has no configuration options beyond line length and target version.

### Flake8 reports line too long (E501)

**Solution**: Black should handle this automatically. If you still see E501 errors:
1. Run `black .` first
2. If error persists, refactor the long line (extract variables, break up expressions)

### Flake8 reports complexity too high

**Solution**: Refactor complex functions into smaller functions:
```python
# Before: Complexity 12
def process_data(data):
    # ... lots of logic ...
    return result

# After: Lower complexity
def process_data(data):
    cleaned = clean_data(data)
    validated = validate_data(cleaned)
    return transform_data(validated)
```

### MyPy reports missing type annotations

**Solution**: Add type hints to your functions:
```python
# Before
def calculate_score(resume, vacancy):
    return match(resume, vacancy)

# After
def calculate_score(resume: Resume, vacancy: Vacancy) -> float:
    return match(resume, vacancy)
```

### MyPy reports "cannot import" errors

**Solution**: Add type stub packages or use `# type: ignore`:
```bash
# Install type stubs for common libraries
pip install types-requests types-pyyaml
```

### Pre-commit hooks not running

**Solution**: Verify pre-commit is installed:
```bash
# Check if installed
cd backend && pre-commit --version

# Re-install if needed
cd backend && pre-commit install
```

### CI linting fails but local passes

**Solution**: Ensure you're using the same configuration:
```bash
# Run with explicit config file (like CI does)
cd backend
black --check --config pyproject.toml .
flake8 --config pyproject.toml .
mypy --config-file pyproject.toml .
```

## Best Practices

1. **Run Black first** - Auto-format before checking style or types
2. **Fix Flake8 issues** - Address style warnings before committing
3. **Add type hints gradually** - MyPy uses gradual typing, start with new code
4. **Don't ignore errors** - Use `# noqa` or `# type: ignore` sparingly
5. **Commit often** - Small commits make linting issues easier to fix

## IDE Integration

### VS Code

Install these extensions:
- **Black Formatter** (`ms-python.black-formatter`)
- **Flake8** (`ms-python.flake8`)
- **MyPy** (`matangover.mypy`)

Configure in `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "flake8.args": ["--config=pyproject.toml"],
  "mypy.targets": ["."],
  "mypy.configFile": "pyproject.toml"
}
```

### PyCharm

1. **Settings → Tools → Black**: Enable "On save"
2. **Settings → Tools → External Tools**: Add Flake8 and MyPy
3. **Settings → Inspections**: Enable "Type checking" (MyPy)

## Learn More

- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
