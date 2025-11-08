# MAGI Backend - Quick Start Guide

## 🚀 First Time Setup

```bash
cd ${PROJECT_DIR}/backend
./start.sh
```

That's it! The script will:
1. Create virtual environment if needed
2. Install dependencies
3. Copy .env.example to .env if needed
4. Start the server

## 📡 API Endpoints

Once running, test with:

```bash
# Health check
curl http://localhost:8000/health

# Model status (mock data)
curl http://localhost:8000/api/models/status

# Interactive docs
open http://localhost:8000/api/docs
```

## 🔧 Manual Setup

If you prefer manual control:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

```bash
# Health check
curl -s http://localhost:8000/health | python3 -m json.tool

# Models status
curl -s http://localhost:8000/api/models/status | python3 -m json.tool

# CORS test (from frontend origin)
curl -v http://localhost:8000/health -H "Origin: http://localhost:5173" 2>&1 | grep access-control
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/routers/health.py` | Health check endpoints |
| `app/routers/models.py` | Model status endpoints |
| `config/default.yaml` | Configuration file |
| `.env` | Environment variables |
| `requirements.txt` | Python dependencies |

## 🔍 Logging

Logs are structured JSON format. To view:

```bash
# Follow logs in real-time
tail -f /tmp/magi-backend.log

# Pretty print JSON logs
tail -f /tmp/magi-backend.log | grep '^{' | jq
```

## 🛠️ Configuration

Edit `.env` to change settings:

```bash
# Application
APP_NAME="MAGI Backend"
ENVIRONMENT=development
PORT=8000

# Model servers (update these for your setup)
MODEL_Q2_FAST_1_URL=http://localhost:8080
MODEL_Q2_FAST_2_URL=http://localhost:8081
MODEL_Q3_SYNTH_URL=http://localhost:8082
MODEL_Q4_DEEP_URL=http://localhost:8083

# Logging
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json       # json or text
```

## 🐛 Troubleshooting

**Port 8000 already in use:**
```bash
# Find and kill process
lsof -ti :8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Module not found:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Verify Python can find modules
python -c "import app; print(app.__version__)"
```

**Configuration errors:**
```bash
# Test configuration loading
python -c "from app.core.config import load_config; config = load_config(); print(config.app_name)"
```

## 📊 Mock Data

Current implementation returns mock data for:
- 4 models: Q2_FAST_1, Q2_FAST_2, Q3_SYNTH, Q4_DEEP
- States: active, idle, processing
- Metrics: memory, request counts, response times
- System metrics: VRAM, cache hit rate

Real model integration coming in Session 2!

## 🔗 Integration with Frontend

Frontend should connect to: `http://localhost:8000`

All endpoints support CORS from:
- `http://localhost:5173` (Vite)
- `http://localhost:3000` (Create React App)

## ✅ Verify Everything Works

Run this test script:

```bash
python3 << 'EOF'
import requests
import json

# Test health
r = requests.get("http://localhost:8000/health")
assert r.status_code == 200
print("✓ Health check passed")

# Test models
r = requests.get("http://localhost:8000/api/models/status")
assert r.status_code == 200
data = r.json()
assert len(data["models"]) == 4
print("✓ Models status passed")

print("\n✅ Backend is working correctly!")
EOF
```

## 📚 Documentation

- Full documentation: `README.md`
- Implementation details: `SESSION1_COMPLETE.md`
- API docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🎯 Next Steps

For Session 2, we'll add:
- Real llama.cpp model integration
- WebSocket real-time updates
- Query routing implementation
- Redis caching
- CGRAG context retrieval

---

**Status:** Session 1 Complete ✅
**Version:** 0.1.0
**Updated:** 2025-11-02
