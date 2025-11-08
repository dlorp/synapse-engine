#!/bin/bash
# S.Y.N.A.P.S.E. ENGINE Backend Verification Script

echo "🔍 S.Y.N.A.P.S.E. ENGINE Backend Verification"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

ERRORS=0

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo -e "   ${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "   ${RED}✗${NC} Python $PYTHON_VERSION (need 3.11+)"
    ERRORS=$((ERRORS+1))
fi

# Check virtual environment
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "   ${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "   ${YELLOW}⚠${NC} Virtual environment not found (will be created)"
fi

# Check configuration files
echo "3. Checking configuration files..."
if [ -f "config/default.yaml" ]; then
    echo -e "   ${GREEN}✓${NC} config/default.yaml"
else
    echo -e "   ${RED}✗${NC} config/default.yaml missing"
    ERRORS=$((ERRORS+1))
fi

if [ -f ".env.example" ]; then
    echo -e "   ${GREEN}✓${NC} .env.example"
else
    echo -e "   ${RED}✗${NC} .env.example missing"
    ERRORS=$((ERRORS+1))
fi

if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} .env"
else
    echo -e "   ${YELLOW}⚠${NC} .env not found (will be copied from .env.example)"
fi

# Check requirements file
echo "4. Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    PACKAGE_COUNT=$(wc -l < requirements.txt | tr -d ' ')
    echo -e "   ${GREEN}✓${NC} requirements.txt ($PACKAGE_COUNT dependencies)"
else
    echo -e "   ${RED}✗${NC} requirements.txt missing"
    ERRORS=$((ERRORS+1))
fi

# Check application structure
echo "5. Checking application structure..."
REQUIRED_FILES=(
    "app/__init__.py"
    "app/main.py"
    "app/core/__init__.py"
    "app/core/config.py"
    "app/core/exceptions.py"
    "app/core/logging.py"
    "app/core/dependencies.py"
    "app/models/__init__.py"
    "app/models/config.py"
    "app/models/model.py"
    "app/routers/__init__.py"
    "app/routers/health.py"
    "app/routers/models.py"
    "app/utils/__init__.py"
    "app/utils/timing.py"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "   ${RED}✗${NC} Missing: $file"
        MISSING=$((MISSING+1))
        ERRORS=$((ERRORS+1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} All ${#REQUIRED_FILES[@]} required files present"
fi

# Check if server is running
echo "6. Checking if server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Server is running on port 8000"
    
    # Test endpoints
    echo "7. Testing API endpoints..."
    
    # Health check
    HEALTH=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "   ${GREEN}✓${NC} GET /health"
    else
        echo -e "   ${RED}✗${NC} GET /health"
        ERRORS=$((ERRORS+1))
    fi
    
    # Models status
    MODELS=$(curl -s http://localhost:8000/api/models/status)
    if echo "$MODELS" | grep -q "Q2_FAST_1"; then
        MODEL_COUNT=$(echo "$MODELS" | grep -o '"id"' | wc -l)
        echo -e "   ${GREEN}✓${NC} GET /api/models/status ($MODEL_COUNT models)"
    else
        echo -e "   ${RED}✗${NC} GET /api/models/status"
        ERRORS=$((ERRORS+1))
    fi
    
    # CORS headers
    CORS=$(curl -s -I http://localhost:8000/health -H "Origin: http://localhost:5173" 2>&1 | grep -i "access-control-allow-origin")
    if [ ! -z "$CORS" ]; then
        echo -e "   ${GREEN}✓${NC} CORS headers present"
    else
        echo -e "   ${RED}✗${NC} CORS headers missing"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Server not running"
    echo "      Run: ./start.sh"
    echo "7. Skipping API tests (server not running)"
fi

# Summary
echo ""
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Backend is ready to use."
    echo "Run './start.sh' to start the server."
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found${NC}"
    echo ""
    echo "Please fix the errors above before starting the server."
    exit 1
fi
