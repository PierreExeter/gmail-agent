# Gmail Agent

AI-powered email and calendar management using Streamlit, LangChain, and HuggingFace.

## Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: LangChain + HuggingFace Inference API
- **Database**: SQLAlchemy (SQLite)
- **APIs**: Gmail API, Google Calendar API
- **Package Manager**: uv (NEVER pip)

## Project Structure

```
agent/       - AI agents (classifier, drafter, scheduler, approval)
services/    - API wrappers (gmail, calendar, llm)
db/          - Database models and operations
ui/          - Streamlit UI components
auth/        - Google OAuth authentication
config.py    - Centralized configuration
```

## Essential Commands

```bash
# Run application
uv run streamlit run app.py

# Testing
uv run --frozen pytest

# Type checking
uv run --frozen pyright

# Linting
uv run --frozen ruff check .
uv run --frozen ruff format .

# Package management
uv add <package>
uv lock --upgrade-package <package>
```

## Development Rules

### Code Quality
- Type hints required for all code
- Public APIs must have docstrings
- Imports at file top (FORBIDDEN inside functions)
- Follow existing patterns exactly

### Testing
- Use anyio for async tests (not asyncio)
- Use test functions, not `Test` prefixed classes
- New features require tests; bug fixes require regression tests

### Exception Handling
- Use `logger.exception()` for caught exceptions (not `logger.error()`)
- Catch specific exceptions where possible
- FORBIDDEN: bare `except Exception:` except in top-level handlers

## Commits & PRs

```bash
# For bug fixes from user reports
git commit --trailer "Reported-by:<name>"

# For GitHub issues
git commit --trailer "Github-Issue:#<number>"
```

- NEVER mention co-authored-by or tools used
- Focus PR descriptions on the problem and solution, not code details

## Breaking Changes

Document in `docs/migration.md`:
- What changed
- Why it changed
- How to migrate

## Additional Documentation

- `.claude/docs/architectural_patterns.md` - Design patterns and conventions
- `docs/` - MkDocs user documentation
