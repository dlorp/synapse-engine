# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Frontend - Production Dockerfile
# =============================================================================
# Multi-stage build for optimized production deployment
# Stage 1: Builder - Build React app with Vite
# Stage 2: Runtime - Serve with nginx
#
# Build arguments:
#   NODE_VERSION: Node.js version for builder (default: 20)
#
# Usage:
#   docker build -t synapse-frontend .
#   docker run -p 80:80 synapse-frontend
# =============================================================================

# =============================================================================
# Stage 1: Builder
# =============================================================================
# Build the React application with Vite
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

# Set build-time environment variables
# NOTE: Keep NODE_ENV undefined during build to install devDependencies
ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

# Set working directory
WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install ALL dependencies (including devDependencies for build tools)
# We need TypeScript, Vite, etc. to build the application
RUN npm ci --prefer-offline --include=dev

# Copy application source
COPY . .

# Build arguments for Vite environment variables
# These must be declared as ARGs and converted to ENV for Vite to access them
# during the build process. Vite embeds these values into the JavaScript bundle.
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_URL=ws://localhost:8000/ws

# Convert build args to environment variables for Vite build process
# Vite accesses these via import.meta.env.VITE_* during bundling
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

# Build the application
# Vite will:
# - Bundle and minify JavaScript/TypeScript
# - Optimize CSS
# - Process assets
# - Generate static files in /app/dist
# - Embed VITE_* environment variables into the JavaScript bundle
RUN npm run build

# List build output for verification (helpful for debugging)
RUN ls -lah /app/dist

# =============================================================================
# Stage 2: Production
# =============================================================================
# Serve the built application with nginx
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx configuration and static files
RUN rm -rf /usr/share/nginx/html/* && \
    rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx cache directories
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    chown -R nginx:nginx /var/cache/nginx

# Expose HTTP port
EXPOSE 80

# Health check - verify nginx is serving the application
HEALTHCHECK --interval=30s --timeout=3s --retries=3 --start-period=10s \
    CMD curl -f http://localhost/health || exit 1

# Start nginx in foreground
# -g "daemon off;" keeps nginx in foreground for Docker
CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# Production Build Notes:
# =============================================================================
# 1. Multi-stage build reduces final image from ~1GB to ~25MB
# 2. nginx serves static files efficiently
# 3. Builder stage is discarded, only /app/dist is kept
# 4. nginx configuration includes:
#    - Gzip compression for faster transfers
#    - SPA routing (all routes → index.html)
#    - API proxy to backend
#    - WebSocket proxy for real-time updates
#    - Security headers
# 5. Health check uses /health endpoint (should return static file or nginx default)
#
# Build Size Comparison:
#   - node:20 image: ~1GB
#   - nginx:alpine + built assets: ~25MB
#   - Savings: ~97.5%
#
# To use in docker-compose.yml:
#   frontend:
#     build:
#       context: ./frontend
#       dockerfile: Dockerfile  # Production build
#     ports:
#       - "80:80"
#     environment:
#       - VITE_API_URL=http://backend:8000
# =============================================================================
