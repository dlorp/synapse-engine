# Contributing to Synapse Engine

Thanks for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/synapse-engine.git`
3. Create a branch: `git checkout -b feature/your-feature`

## Development Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- llama-server (for local model testing)

### Quick Start

```bash
# Clone and enter repo
git clone https://github.com/dlorp/synapse-engine.git
cd synapse-engine

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d
```

### Backend Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Format code
black app/

# Type check
mypy app/

# Lint
ruff check app/
```

### Frontend Development

```bash
cd frontend
npm install

# Development server
npm run dev

# Run tests
npm test

# Lint
npm run lint

# Type check
npm run type-check
```

## Code Style

### Python (Backend)

- Python 3.11+ with type hints
- Format with `black`
- Type check with `mypy`
- Lint with `ruff`
- Follow existing patterns in codebase

### TypeScript (Frontend)

- TypeScript strict mode
- Format with Prettier (via ESLint)
- Lint with ESLint
- Follow React best practices

### Commit Messages

Use conventional commit format:

```
feat: add new query mode
fix: resolve model timeout issue
docs: update API reference
test: add orchestrator unit tests
refactor: simplify model selector
```

## Pull Requests

### Before Submitting

- [ ] Run tests (`pytest` for backend, `npm test` for frontend)
- [ ] Run type checks (`mypy` for backend, `npm run type-check` for frontend)
- [ ] Run linters (`ruff` for backend, `npm run lint` for frontend)
- [ ] Update documentation if adding features
- [ ] Add tests for new functionality

### PR Guidelines

- Keep PRs focused - one feature or fix per PR
- Write descriptive PR titles and descriptions
- Reference related issues with `Fixes #123` or `Closes #123`
- Respond to review feedback promptly

## Project Structure

```
synapse-engine/
├── backend/           # FastAPI backend
│   ├── app/           # Application code
│   └── tests/         # Backend tests
├── frontend/          # React frontend
│   └── src/           # Source code
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── tools/             # Development tools
├── host-api/          # Host API for Metal mode
└── sandbox/           # Sandbox utilities
```

## Documentation

- Update relevant docs when changing features
- Add docstrings to Python functions
- Add JSDoc comments to TypeScript functions
- Keep README files current

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v                          # All tests
pytest tests/test_orchestrator.py -v      # Specific file
pytest tests/ -k "test_query" -v          # Pattern match
pytest tests/ --cov=app                   # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test                    # Run tests
npm test -- --watch         # Watch mode
npm test -- --coverage      # With coverage
```

## Reporting Issues

Before opening an issue:

1. Search existing issues to avoid duplicates
2. Check the [troubleshooting docs](docs/troubleshooting/)

When opening an issue, include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python/Node version
- Operating system
- Relevant logs or error messages

## Getting Help

- Open a GitHub issue for bugs
- Start a GitHub Discussion for questions
- Check existing issues and discussions first

## License

By contributing, you agree that your contributions will be licensed under the [PolyForm NonCommercial 1.0.0](LICENSE) license.
