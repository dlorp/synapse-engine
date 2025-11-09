#!/bin/bash
# Test script for Dot Matrix Animation Restart Bug Fix
# Tests the useMemo implementation that prevents animation restarts

set -e

echo "=========================================="
echo "Dot Matrix Animation Restart Bug - Test"
echo "=========================================="
echo ""

# Check if Docker containers are running
echo "[1/5] Checking Docker containers..."
if ! docker-compose ps | grep -q "synapse_frontend.*Up"; then
  echo "❌ Frontend container not running!"
  echo "Run: docker-compose up -d"
  exit 1
fi
echo "✅ Frontend container is running"
echo ""

# Check if frontend is responding
echo "[2/5] Checking frontend server..."
if ! curl -s http://localhost:5173 > /dev/null; then
  echo "❌ Frontend not responding at http://localhost:5173"
  exit 1
fi
echo "✅ Frontend server is responding"
echo ""

# Check for useMemo import in HomePage.tsx
echo "[3/5] Verifying useMemo import..."
if grep -q "import React, { useState, useMemo }" frontend/src/pages/HomePage/HomePage.tsx; then
  echo "✅ useMemo imported correctly"
else
  echo "❌ useMemo not imported!"
  exit 1
fi
echo ""

# Check for memoized reactive object
echo "[4/5] Verifying memoized reactive object..."
if grep -q "const dotMatrixReactive = useMemo" frontend/src/pages/HomePage/HomePage.tsx; then
  echo "✅ Reactive object is memoized"
else
  echo "❌ Reactive object not memoized!"
  exit 1
fi
echo ""

# Check that inline reactive object is NOT present
echo "[5/5] Verifying inline object removed..."
if grep -q "reactive={{" frontend/src/pages/HomePage/HomePage.tsx; then
  echo "❌ Inline reactive object still present!"
  echo "This will cause animation restarts!"
  exit 1
fi
echo "✅ No inline reactive object found"
echo ""

echo "=========================================="
echo "✅ All automated checks passed!"
echo "=========================================="
echo ""
echo "Manual Testing Checklist:"
echo "-------------------------"
echo "1. Open http://localhost:5173 in browser"
echo "2. Observe 'SYNAPSE ENGINE' animation reveal"
echo "3. Let animation play completely (14 letters × 100ms)"
echo "4. Submit a query MID-ANIMATION (around letter 'P')"
echo "5. Verify animation DOES NOT restart"
echo "6. Observe blink effect added smoothly"
echo "7. Wait for query to complete"
echo "8. Verify animation continues without restart"
echo ""
echo "Expected Results:"
echo "-----------------"
echo "✅ Animation plays once on page load"
echo "✅ NO restart when submitting query"
echo "✅ Wave pattern maintained throughout"
echo "✅ Blink effect adds/removes smoothly"
echo "✅ Only ERROR state causes restart (intentional)"
echo ""
echo "Debugging Tips:"
echo "---------------"
echo "1. Open React DevTools → Components → HomePage"
echo "2. Enable 'Highlight updates when components render'"
echo "3. Verify re-renders don't restart animation"
echo "4. Check console for any errors"
echo "5. Add console.log in DotMatrixDisplay useEffect if needed:"
echo "   console.log('[DotMatrix] Reactive changed:', reactive);"
echo ""
echo "Documentation:"
echo "--------------"
echo "- Full report: DOT_MATRIX_RESTART_BUG_FIX.md"
echo "- Session notes: SESSION_NOTES.md (2025-11-08 22:30)"
echo "- Component: frontend/src/components/terminal/DotMatrixDisplay/"
echo ""
