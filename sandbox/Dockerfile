# =============================================================================
# S.Y.N.A.P.S.E. ENGINE - Python Sandbox Container
# =============================================================================
# Isolated execution environment for Code Chat run_python tool
# Security features:
#   - Non-root user
#   - Read-only filesystem (with /tmp for temp files)
#   - No dangerous imports (os, subprocess, socket, etc.)
#   - Memory limit: 512MB
#   - CPU limit: 1 core
#   - Execution timeout: 30s max
# =============================================================================

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash sandbox

# Set working directory
WORKDIR /app

# Install Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Copy server code
COPY server.py /app/
RUN chown -R sandbox:sandbox /app

# Security: Switch to non-root user
USER sandbox

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# Run server
CMD ["python", "server.py"]
