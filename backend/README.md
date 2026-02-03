# Synapse Engine Backend

FastAPI backend for Multi-Model Orchestration.

## Quick Start

### With Docker (Recommended)

```bash
# From project root
docker-compose up -d
```

Backend runs at http://localhost:8000

### Local Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Interactive docs available when running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [API Reference](../docs/API.md) for complete endpoint documentation.

## Project Structure

```
backend/
├── app/
│   ├── cli/               # CLI tools
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration loading
│   │   ├── dependencies.py # FastAPI dependencies
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── logging.py     # Structured logging
│   ├── models/            # Pydantic data models
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   │   ├── orchestrator/  # Query orchestration
│   │   ├── cgrag/         # CGRAG retrieval
│   │   ├── model_manager/ # Model lifecycle
│   │   └── ...
│   ├── utils/             # Utilities
│   └── main.py            # FastAPI application
├── data/                  # Runtime data (indexes, registry)
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Project metadata
```

## Configuration

Environment variables (`.env`):

```bash
# Model paths
PRAXIS_MODEL_PATH=/path/to/huggingface/cache

# Server config
NEURAL_LLAMA_SERVER_PATH=/usr/local/bin/llama-server
NEURAL_PORT_START=8080
NEURAL_PORT_END=8099

# CGRAG
RECALL_TOKEN_BUDGET=8000
RECALL_CHUNK_SIZE=512

# Query defaults
PRAXIS_DEFAULT_MODE=two-stage

# Metal acceleration (Apple Silicon)
USE_EXTERNAL_SERVERS=true
```

See [.env.example](./.env.example) for all options.

## Development

### Code Quality

```bash
# Format
black app/

# Type check
mypy app/

# Lint
ruff check app/
```

### Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_orchestrator.py -v
```

### Logging

Structured JSON logging by default:

```bash
# Environment variables
LOG_FORMAT=json  # or text
LOG_LEVEL=INFO   # DEBUG, INFO, WARNING, ERROR
```

## Key Components

### Query Orchestrator
Routes queries through processing modes (simple, two-stage, council).

### Model Selector
Chooses models based on tier (FAST/BALANCED/POWERFUL) and availability.

### CGRAG Engine
Sub-100ms contextual retrieval using FAISS vector similarity.

### Event Emitter
WebSocket events for real-time UI updates.

## Additional Documentation

Backend-specific guides in this directory:

| Document | Description |
|----------|-------------|
| [API_ARCHITECTURE.md](./API_ARCHITECTURE.md) | API design and patterns |
| [API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md) | Common API operations |
| [WEBSOCKET_EVENTS_INTEGRATION_GUIDE.md](./WEBSOCKET_EVENTS_INTEGRATION_GUIDE.md) | WebSocket integration |
| [METRICS_API_INTEGRATION_GUIDE.md](./METRICS_API_INTEGRATION_GUIDE.md) | Metrics API usage |

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Import Errors

Ensure virtual environment is activated:

```bash
source .venv/bin/activate
python -c "import app; print('OK')"
```

### Configuration Issues

```bash
# Check environment
cat .env

# Test config loading
python -c "from app.core.config import load_config; print(load_config())"
```
