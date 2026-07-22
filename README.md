# Tyrwar

Tyrwar is a Python project scaffold prepared for clean, reproducible development.

## Repository status

The earlier repository contained unresolved Git subproject pointers rather than tracked source. Those pointers have been removed. No unavailable component source has been recreated or inferred.

## Development

Requirements:

- Python 3.11 or newer

Install the project with development tools:

```bash
python -m pip install -e ".[dev]"
```

Run validation:

```bash
ruff check .
ruff format --check .
pytest
```

## Structure

```text
src/tyrwar/        Python package
tests/             Automated tests
.github/workflows/ Continuous integration
```

## Restoring Professor Git

When the actual Professor Git source is available, add it as normal tracked source under `src/tyrwar/professor_git/` or import its history using `git subtree`. Do not copy a nested `.git` directory into this repository.
