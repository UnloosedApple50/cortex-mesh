# HermesMesh Development Guide

## Getting Started

```bash
# Clone the repository
git clone https://github.com/hermesmesh/hermesmesh.git
cd hermesmesh

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"
```

## Project Structure

```
hermesmesh/
├── hermesmesh/
│   ├── __init__.py
│   ├── cli/           # CLI tool (hermesctl)
│   │   └── __init__.py
│   ├── core/          # Core logic
│   │   ├── __init__.py
│   │   └── scheduler.py
│   ├── server/        # API server
│   │   ├── __init__.py
│   │   └── api.py
│   ├── agent/         # Node agent
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── models/        # Pydantic models
│   │   └── __init__.py
│   ├── adapters/      # Hardware adapters
│   │   ├── __init__.py
│   │   └── platform/
│   │       ├── __init__.py
│   │       └── detect.py
│   └── database.py    # SQLAlchemy layer
├── tests/             # Test suite
├── docs/              # Documentation
├── pyproject.toml     # Project config
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hermesmesh --cov-report=html

# Run specific test file
pytest tests/test_scheduler.py

# Run specific test
pytest tests/test_scheduler.py::TestScheduler::test_select_best_node
```

## Code Style

We use:
- **black** — Code formatting
- **ruff** — Linting
- **mypy** — Type checking

```bash
# Format code
black hermesmesh tests

# Lint
ruff check hermesmesh tests

# Type check
mypy hermesmesh
```

## Adding a New CLI Command

1. Add the command function in `hermesmesh/cli/__init__.py`
2. Add tests in `tests/test_cli.py`
3. Update documentation in `docs/api.md`

## Adding a New API Endpoint

1. Add the endpoint in `hermesmesh/server/api.py`
2. Add Pydantic models in `hermesmesh/models/__init__.py`
3. Add database models in `hermesmesh/database.py` if needed
4. Add tests in `tests/test_api.py`

## Database Migrations

We use Alembic for database migrations:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.1.0`
4. Push: `git push --tags`
5. Build: `python -m build`
6. Upload: `twine upload dist/*`

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## Architecture Decisions

- **Async-first** — All I/O is async for scalability
- **Pydantic models** — Type-safe data validation
- **SQLAlchemy 2.0** — Modern ORM with async support
- **Typer CLI** — Type-safe CLI with auto-completion
- **Capability-driven** — Score based on actual hardware, not assumptions
