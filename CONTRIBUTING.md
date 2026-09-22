# Contributing to CortexMesh

Thank you for your interest in contributing! This document outlines how to get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/cortexmesh.git`
3. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -e ".[dev]"`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linters: `ruff check cortexmesh tests && black --check cortexmesh tests`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

## Code Style

- **Formatting**: black (line length 88)
- **Linting**: ruff
- **Type hints**: All functions must have type annotations
- **Docstrings**: Google style for public APIs

## Testing

- All new features require tests
- Maintain or improve code coverage
- Tests must pass before PR is merged

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cortexmesh --cov-report=html

# Run specific test file
pytest tests/test_scheduler.py
```

## Pull Request Guidelines

1. Keep PRs focused on a single feature/fix
2. Update documentation if needed
3. Add tests for new functionality
4. Ensure CI passes
5. Request review from maintainers

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

- Open a GitHub Discussion
- Join our community Discord
- Check existing issues and PRs first
