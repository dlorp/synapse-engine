#!/bin/bash

# CSS Test Page Verification Script
# Run this to verify the test page is working correctly

echo "=================================================="
echo "  S.Y.N.A.P.S.E. ENGINE - CSS Test Page Verification"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Check if frontend container is running
if ! docker-compose ps synapse_frontend | grep -q "Up"; then
    echo "❌ Frontend container is not running"
    echo "   Run: docker-compose up -d synapse_frontend"
    exit 1
fi

echo "✅ Frontend container is running"

# Check if page is accessible
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/css-test)
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ CSS test page not accessible (HTTP $HTTP_CODE)"
    echo "   Check frontend logs: docker-compose logs synapse_frontend"
    exit 1
fi

echo "✅ CSS test page is accessible (HTTP 200)"

# Verify CSS files exist
CSS_FILES=(
    "frontend/src/assets/styles/main.css"
    "frontend/src/assets/styles/theme.css"
    "frontend/src/assets/styles/components.css"
)

for file in "${CSS_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing CSS file: $file"
        exit 1
    fi
done

echo "✅ All CSS files present"

# Count CSS classes in components.css
CLASS_COUNT=$(grep -c '^\.' frontend/src/assets/styles/components.css)
echo "✅ Components CSS: $CLASS_COUNT class definitions"

# Verify route in router
if ! grep -q "css-test" frontend/src/router/routes.tsx; then
    echo "❌ Route not found in routes.tsx"
    exit 1
fi

echo "✅ Route registered in router"

# Verify CSSTestPage component
if [ ! -f "frontend/src/pages/CSSTestPage.tsx" ]; then
    echo "❌ CSSTestPage.tsx not found"
    exit 1
fi

LINE_COUNT=$(wc -l < frontend/src/pages/CSSTestPage.tsx | tr -d ' ')
echo "✅ CSSTestPage.tsx exists ($LINE_COUNT lines)"

echo ""
echo "=================================================="
echo "  ✅ ALL CHECKS PASSED"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Open your browser to: http://localhost:5173/css-test"
echo "2. Verify the following:"
echo "   - ASCII banner displays at top"
echo "   - All panels have phosphor orange borders with glow"
echo "   - Status indicators pulse (ACTIVE, PROCESSING)"
echo "   - Sparklines render as block characters"
echo "   - Grid adapts when resizing browser window"
echo "   - Animations run smoothly (60fps)"
echo ""
echo "3. Check browser console for errors (should be NONE)"
echo ""
echo "To view frontend logs:"
echo "   docker-compose logs -f synapse_frontend"
echo ""

# Try to open browser (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Opening browser..."
    open http://localhost:5173/css-test
fi
