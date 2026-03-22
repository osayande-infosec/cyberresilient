# Contributing to CyberResilient

Thanks for your interest in contributing! This guide covers the setup and process.

---

## Development Setup

```bash
# Clone and install in editable mode with dev dependencies
git clone https://github.com/osayande-infosec/cyberresilient.git
cd CyberResilient
pip install -e ".[dev]"

# Initialize the database with sample data
CyberResilient init --seed

# Run the app
streamlit run app.py
```

---

## Code Quality

We use these tools (run before committing):

```bash
ruff check .           # Linting
ruff format .          # Formatting
pytest tests/ -v       # Tests
bandit -r cyberresilient/ -ll --skip B101   # Security scan
```

Pre-commit hooks are configured — install them with:

```bash
pre-commit install
```

---

## Project Conventions

- **Package code** goes in `cyberresilient/` (models, services, config)
- **Page code** goes in `pages/` (Streamlit UI only — no business logic)
- **Tests** go in `tests/` with `test_` prefix
- **Data models**: Pydantic for validation, SQLAlchemy for persistence
- **Services**: One service per domain (risk, DR, compliance, auth, reports)
- **Imports**: Use `from cyberresilient.services.xxx import ...` — no `sys.path` hacks

---

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Make your changes with tests
3. Ensure all checks pass: `ruff check . && pytest tests/ -v`
4. Open a PR with a clear description of what and why
5. One approval required before merge

---

## Adding a New Page

1. Create `pages/N_PageName.py`
2. Add any business logic to a service in `cyberresilient/services/`
3. Add learning callouts using `learning_callout()` from auth_service
4. Add tests in `tests/test_pagename.py`

---

## Reporting Issues

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
