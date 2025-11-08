# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Core - Multi-Stage Docker Build
# =============================================================================
# Stage 1: Builder - Install dependencies in isolated environment
# Stage 2: Runtime - Lean production image with only necessary files
#
# Build arguments:
#   PYTHON_VERSION: Python version to use (default: 3.11)
#
# Usage:
#   docker build -t synapse-core .
#   docker run -p 8000:8000 -p 8080-8099:8080-8099 --env-file .env synapse-core
# =============================================================================

# =============================================================================
# Stage 1: Builder
# =============================================================================
# Build stage for installing Python dependencies
# This stage is discarded in the final image to keep it lean
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies required for Python packages
# These are only needed during pip install and won't be in final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
# Using venv ensures clean dependency isolation
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements.txt first (Docker layer caching optimization)
# This layer will be cached unless requirements.txt changes
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies into virtual environment
# The venv will be copied to the runtime stage
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt

# =============================================================================
# Stage 2: llama.cpp Builder (Simplified for ARM64)
# =============================================================================
# Build llama.cpp with minimal features for ARM64 compatibility
FROM debian:bookworm-slim AS llama-builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Clone llama.cpp (using shallow clone for speed)
RUN git clone --depth 1 https://github.com/ggerganov/llama.cpp.git

# Build with minimal configuration for ARM64
WORKDIR /build/llama.cpp
RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_NATIVE=OFF \
    -DGGML_CUDA=OFF \
    -DGGML_METAL=OFF \
    -DGGML_BLAS=OFF \
    -DLLAMA_CURL=OFF \
    -DGGML_OPENMP=ON && \
    cmake --build build --config Release --target llama-server -j $(nproc)

# =============================================================================
# Stage 3: Runtime
# =============================================================================
# Final lean image with only runtime dependencies
# Using python:3.11-slim reduces image size from ~1.75GB to ~500-700MB
FROM python:${PYTHON_VERSION}-slim AS runtime

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime dependencies
# - curl: Required for health checks and HTTP requests
# - ca-certificates: Required for HTTPS requests
# - procps: Required for process management (ps, kill)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# Running as root in containers is a security risk
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
# This contains all installed Python packages
COPY --from=builder /opt/venv /opt/venv

# Copy llama-server binary from llama-builder stage
# This is the Linux-compatible binary built from source
COPY --from=llama-builder /build/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
RUN chmod +x /usr/local/bin/llama-server

# Copy application code
# Structure:
#   /app
#   ├── app/           (FastAPI application)
#   └── requirements.txt
COPY --chown=appuser:appuser ./app /app/app
COPY --chown=appuser:appuser ./requirements.txt /app/requirements.txt

# Create directories for data storage with proper permissions
# These will be mounted as volumes in docker-compose.yml
# - data/model_registry.json: Model discovery results
# - data/faiss_indexes/: CGRAG indexes
# - logs/: Application logs
RUN mkdir -p /app/data/faiss_indexes && \
    mkdir -p /app/data && \
    mkdir -p /app/logs && \
    mkdir -p /app/config && \
    chown -R appuser:appuser /app/data /app/logs /app/config

# Switch to non-root user
USER appuser

# Expose ports
# 8000: FastAPI backend
# 8080-8099: llama.cpp model servers (managed by backend)
EXPOSE 8000 8080-8099

# Health check endpoint
# Checks if FastAPI is responding on /health
# - interval: How often to check (15s)
# - timeout: How long to wait for response (5s)
# - retries: How many failures before unhealthy (3)
# - start_period: Grace period on startup (40s for model loading)
HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - Uvicorn with production settings
# For development with hot reload, override this in docker-compose.dev.yml
#
# Command explanation:
#   uvicorn app.main:app          - Run the FastAPI app
#   --host 0.0.0.0                - Listen on all interfaces (required for Docker)
#   --port 8000                   - Listen on port 8000
#   --log-level info              - Logging level
#   --access-log                  - Enable access logging
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--log-level", "info", \
     "--access-log"]

# =============================================================================
# Build Notes:
# =============================================================================
# 1. Multi-stage build with python:3.11-slim base reduces image size significantly
#    - Standard python:3.11 base: ~1.75GB
#    - Optimized python:3.11-slim base: ~500-700MB
#    - Size reduction: ~60-70% smaller
# 2. Virtual environment ensures clean dependency isolation
# 3. Non-root user (appuser) follows security best practices
# 4. Health check ensures container is actually healthy, not just running
# 5. Procps package added for process management (needed for model servers)
# 6. PYTHONPATH includes /app for proper module imports
# 7. All files owned by appuser to prevent permission issues
#
# Model Management:
# - llama-server binary built from source and included in image
# - Model files mounted from host HUB directory
# - Model servers launched on ports 8080-8099
# - Registry stored in data/model_registry.json (mounted volume)
# - llama.cpp built in Stage 2 for Linux compatibility (solves macOS/Linux binary issues)
#
# Development vs Production:
# - This Dockerfile supports both development and production modes
# - Development: docker-compose.yml overrides CMD with --reload
# - Development mounts source code for hot reload
# - Production: Use default CMD (no --reload flag)
#
# Resource Considerations:
# - Image size: ~500-700MB (optimized with python:3.11-slim + multi-stage build)
# - Runtime memory: Depends on models loaded (set limits in docker-compose.yml)
# - CPU: Model servers are CPU-intensive (adjust cpus in docker-compose.yml)
# =============================================================================
