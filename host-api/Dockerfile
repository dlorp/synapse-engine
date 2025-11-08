FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck and openssh-client for SSH connections
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl openssh-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Copy SSH keys and config for connecting to Mac host
COPY .ssh /root/.ssh
RUN chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/config

# Expose API port
EXPOSE 9090

CMD ["python", "main.py"]
