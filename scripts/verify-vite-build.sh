#!/bin/bash
# =============================================================================
# Vite Build Verification Script
# =============================================================================
# Verifies that Vite environment variables are correctly embedded in the build
#
# Usage:
#   ./scripts/verify-vite-build.sh
#   VITE_API_BASE_URL=http://custom:8000 ./scripts/verify-vite-build.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=============================================="
echo "Vite Build Verification"
echo "=============================================="
echo ""

# Check environment variables
echo "Environment Variables:"
echo "  VITE_API_BASE_URL = ${VITE_API_BASE_URL:-<not set>}"
echo "  VITE_WS_URL       = ${VITE_WS_URL:-<not set>}"
echo ""

# Build frontend container
echo "Building frontend container..."
cd "${PROJECT_ROOT}"
docker-compose build --no-cache frontend

echo ""
echo "Creating temporary container to extract build artifacts..."
docker create --name temp_frontend_verify synapse_frontend 2>/dev/null || \
docker create --name temp_frontend_verify synapse-frontend 2>/dev/null || {
    echo "ERROR: Could not create container. Check image name."
    exit 1
}

# Extract built files
TEMP_DIR="${PROJECT_ROOT}/.verify-build"
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

echo "Extracting build artifacts to ${TEMP_DIR}..."
docker cp temp_frontend_verify:/usr/share/nginx/html "${TEMP_DIR}/"

# Clean up container
docker rm temp_frontend_verify >/dev/null

echo ""
echo "=============================================="
echo "Verification Results"
echo "=============================================="
echo ""

# Check for expected API URL
EXPECTED_API_URL="${VITE_API_BASE_URL:-http://localhost:8000}"
EXPECTED_WS_URL="${VITE_WS_URL:-ws://localhost:8000/ws}"

echo "Searching for embedded URLs in JavaScript bundles..."
echo ""

# Find JavaScript files
JS_FILES=$(find "${TEMP_DIR}/html/assets" -name "*.js" 2>/dev/null)

if [ -z "$JS_FILES" ]; then
    echo "ERROR: No JavaScript files found in build output"
    echo "Build may have failed. Check docker-compose build output."
    rm -rf "${TEMP_DIR}"
    exit 1
fi

# Search for API URL
echo "Looking for API URL: ${EXPECTED_API_URL}"
if grep -r "${EXPECTED_API_URL}" "${TEMP_DIR}/html/assets" >/dev/null 2>&1; then
    echo "✅ SUCCESS: Found '${EXPECTED_API_URL}' in bundle"
    
    # Show context
    echo ""
    echo "Context:"
    grep -r "${EXPECTED_API_URL}" "${TEMP_DIR}/html/assets" | head -1 | cut -c1-100
else
    echo "❌ FAILED: Could not find '${EXPECTED_API_URL}' in bundle"
    echo ""
    echo "Searching for any baseURL assignments..."
    grep -r "baseURL" "${TEMP_DIR}/html/assets" | head -3
fi

echo ""
echo "Looking for WebSocket URL: ${EXPECTED_WS_URL}"
if grep -r "${EXPECTED_WS_URL}" "${TEMP_DIR}/html/assets" >/dev/null 2>&1; then
    echo "✅ SUCCESS: Found '${EXPECTED_WS_URL}' in bundle"
else
    echo "⚠️  WARNING: Could not find '${EXPECTED_WS_URL}' in bundle"
    echo "This may be okay if WebSocket URL is constructed dynamically"
fi

echo ""
echo "=============================================="
echo "Build Artifact Details"
echo "=============================================="
echo ""

# List files
echo "Build output files:"
ls -lh "${TEMP_DIR}/html/" | tail -n +2

echo ""
echo "JavaScript bundles:"
ls -lh "${TEMP_DIR}/html/assets/"*.js | tail -n +2

# Calculate total size
TOTAL_SIZE=$(du -sh "${TEMP_DIR}/html" | cut -f1)
echo ""
echo "Total build size: ${TOTAL_SIZE}"

# Clean up
echo ""
echo "Cleaning up temporary files..."
rm -rf "${TEMP_DIR}"

echo ""
echo "=============================================="
echo "Verification Complete"
echo "=============================================="
