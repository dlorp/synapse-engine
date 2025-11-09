#!/bin/bash

# CSS Layer System Verification Script
# S.Y.N.A.P.S.E. ENGINE - Tasks 0.2-0.4

echo "=========================================="
echo "CSS Layer System Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Check file existence
echo "1. Checking CSS file structure..."
if [ -f "frontend/src/assets/styles/main.css" ]; then
    echo -e "${GREEN}✓${NC} main.css exists"
else
    echo -e "${RED}✗${NC} main.css missing"
fi

if [ -f "frontend/src/assets/styles/theme.css" ]; then
    echo -e "${GREEN}✓${NC} theme.css exists"
else
    echo -e "${RED}✗${NC} theme.css missing"
fi

if [ -f "frontend/src/assets/styles/components.css" ]; then
    echo -e "${GREEN}✓${NC} components.css exists"
else
    echo -e "${RED}✗${NC} components.css missing"
fi

echo ""

# 2. Check @webtui/css installation
echo "2. Checking @webtui/css installation..."
if npm list @webtui/css --prefix frontend 2>/dev/null | grep -q "@webtui/css"; then
    VERSION=$(npm list @webtui/css --prefix frontend 2>/dev/null | grep "@webtui/css" | awk '{print $2}')
    echo -e "${GREEN}✓${NC} @webtui/css installed ($VERSION)"
else
    echo -e "${RED}✗${NC} @webtui/css not installed"
fi

echo ""

# 3. Check CSS layer declarations
echo "3. Checking CSS layer declarations..."
if grep -q "@layer base, utils, components" frontend/src/assets/styles/main.css; then
    echo -e "${GREEN}✓${NC} CSS layers declared correctly"
else
    echo -e "${RED}✗${NC} CSS layers not declared"
fi

echo ""

# 4. Check WebTUI import
echo "4. Checking WebTUI import..."
if grep -q "@import '@webtui/css'" frontend/src/assets/styles/main.css; then
    echo -e "${GREEN}✓${NC} WebTUI CSS imported"
else
    echo -e "${RED}✗${NC} WebTUI CSS not imported"
fi

echo ""

# 5. Check phosphor orange color
echo "5. Checking phosphor orange theme..."
if grep -q "#ff9500" frontend/src/assets/styles/theme.css; then
    echo -e "${GREEN}✓${NC} Phosphor orange (#ff9500) configured"
else
    echo -e "${RED}✗${NC} Phosphor orange not found"
fi

echo ""

# 6. Check glow effects
echo "6. Checking phosphor glow effects..."
if grep -q "phosphor-glow" frontend/src/assets/styles/theme.css; then
    echo -e "${GREEN}✓${NC} Phosphor glow effects defined"
else
    echo -e "${RED}✗${NC} Phosphor glow not defined"
fi

echo ""

# 7. Check component styles
echo "7. Checking component styles..."
COMPONENTS=(
    "synapse-panel"
    "synapse-status"
    "synapse-chart"
    "synapse-metric"
    "synapse-grid"
)

for component in "${COMPONENTS[@]}"; do
    if grep -q "\.$component" frontend/src/assets/styles/components.css; then
        echo -e "${GREEN}✓${NC} .$component defined"
    else
        echo -e "${RED}✗${NC} .$component missing"
    fi
done

echo ""

# 8. Check Docker container status
echo "8. Checking Docker container status..."
if docker-compose ps synapse_frontend | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Frontend container running"
else
    echo -e "${RED}✗${NC} Frontend container not running"
fi

echo ""

# 9. Check for CSS errors in logs
echo "9. Checking for CSS errors in logs..."
ERRORS=$(docker-compose logs synapse_frontend 2>&1 | grep -i -c "error")
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No errors in frontend logs"
else
    echo -e "${YELLOW}⚠${NC} Found $ERRORS error(s) in logs"
fi

echo ""
echo "=========================================="
echo "Manual Verification Required"
echo "=========================================="
echo ""
echo "Open http://localhost:5173 in your browser and verify:"
echo ""
echo "1. Chrome DevTools → Elements → html → Styles → @layer"
echo "   - Check for: base, utils, components layers"
echo ""
echo "2. Chrome DevTools → Elements → html → Computed"
echo "   - --webtui-primary should be #ff9500"
echo "   - --webtui-background should be #000000"
echo "   - --phosphor-glow should be defined"
echo ""
echo "3. Visual Check"
echo "   - Background should be pure black"
echo "   - Text should be phosphor orange"
echo "   - Headings should have glow effect"
echo ""
echo "=========================================="
