# Synapse Engine Backend

FastAPI backend for the Multi-Model Orchestration WebUI.

## Quick Start

### 1. Create Virtual Environment

```bash
cd ${PROJECT_DIR}/backend
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

The `.env` file has been created with default values. Update if needed:

```bash
# Model server URLs are already configured for localhost:8080-8083
MODEL_Q2_FAST_1_URL=http://localhost:8080
MODEL_Q2_FAST_2_URL=http://localhost:8081
MODEL_Q3_SYNTH_URL=http://localhost:8082
MODEL_Q4_DEEP_URL=http://localhost:8083
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Checks

- `GET /health` - Basic health check
- `GET /health/models` - Model health status

### Model Management

- `GET /api/models/status` - Get all model statuses with system metrics

### Documentation

- `GET /api/docs` - Interactive API documentation (Swagger UI)
- `GET /api/redoc` - ReDoc API documentation

## Testing Endpoints

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Models status
curl http://localhost:8000/api/models/status

# Pretty print with jq
curl -s http://localhost:8000/api/models/status | jq
```

### Using httpie

```bash
# Health check
http :8000/health

# Models status
http :8000/api/models/status
```

## Project Structure

```
backend/
├── app/
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration loading
│   │   ├── dependencies.py # FastAPI dependencies
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── logging.py     # Structured logging
│   ├── models/            # Pydantic data models
│   │   ├── config.py      # Configuration models
│   │   └── model.py       # Model status models
│   ├── routers/           # API endpoints
│   │   ├── health.py      # Health check endpoints
│   │   └── models.py      # Model management endpoints
│   ├── services/          # Business logic (to be implemented)
│   ├── utils/             # Utilities
│   │   └── timing.py      # Performance timing
│   └── main.py            # FastAPI application
├── config/
│   └── default.yaml       # Default configuration
├── tests/                 # Test suite (to be implemented)
├── .env                   # Environment variables
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Python project metadata
```

## Configuration

Configuration is loaded from two sources:

1. `config/default.yaml` - Default configuration
2. `.env` - Environment variables (overrides YAML)

Environment variables use `${VAR_NAME}` syntax in YAML files.

## Current Implementation Status

**Session 1 (Complete):**
- ✅ FastAPI application structure
- ✅ Configuration management with YAML + environment variables
- ✅ Structured JSON logging
- ✅ Exception handling hierarchy
- ✅ Health check endpoints
- ✅ Model status endpoints (mock data)
- ✅ CORS configuration
- ✅ Request ID tracking
- ✅ Performance monitoring middleware

**Session 2 (Next):**
- ⏳ Real model integration with llama.cpp servers
- ⏳ Model health checking service
- ⏳ Query routing implementation
- ⏳ WebSocket real-time updates
- ⏳ Redis caching
- ⏳ CGRAG integration

## Development

### Code Quality Tools

```bash
# Format code
black app/

# Type checking
mypy app/

# Run tests (when implemented)
pytest
```

### Logging

The application uses structured JSON logging by default. Log format can be changed to text in `.env`:

```bash
LOG_FORMAT=text  # or json
LOG_LEVEL=INFO   # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### CORS

CORS is configured for the frontend running on `localhost:5173`. Update `cors_origins` in `config/default.yaml` to allow additional origins.

## Mock Data

For Session 1, all endpoints return realistic mock data:

- **Model Status**: 4 models (Q2_FAST_1, Q2_FAST_2, Q3_SYNTH, Q4_DEEP)
- **States**: Various states (active, idle, processing)
- **Metrics**: Request counts, response times, memory usage
- **System Metrics**: VRAM usage, cache hit rate, active queries

Mock data will be replaced with real model integration in Session 2.

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Module Import Errors

Ensure you're running from the backend directory and the virtual environment is activated:

```bash
cd ${PROJECT_DIR}/backend
source venv/bin/activate
python -c "import app; print(app.__version__)"
```

### Configuration Errors

Check that environment variables are properly set:

```bash
# View current environment
cat .env

# Test configuration loading
python -c "from app.core.config import load_config; config = load_config(); print(config.app_name)"
```
