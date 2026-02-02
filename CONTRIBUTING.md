# Contributing to synapse-engine

Thanks for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/synapse-engine.git`
3. Install dependencies (see below)
4. Create a branch: `git checkout -b feature/your-feature`

## Development Setup

### Backend (Python)

```bash
cd backend
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Format
black .

# Type check
mypy app/
```

### Frontend (TypeScript/React)

```bash
cd frontend
npm install

# Run tests
npm test

# Lint
npm run lint

# Type check
npm run type-check
```

## Pull Requests

- Keep PRs focused - one feature or fix per PR
- Add tests for new functionality
- Update docs if needed
- Follow existing code style

## Code Style

### Backend
- Python 3.11+ type hints
- Use `black` for formatting
- Use `mypy` for type checking

### Frontend
- TypeScript strict mode
- Use `eslint` for linting
- Follow React best practices

## Reporting Issues

- Check existing issues first
- Include steps to reproduce
- Include Python/Node version and OS

## Questions?

Open a discussion or issue - we're happy to help!
