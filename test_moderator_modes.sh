#!/bin/bash

# Test script for Council Moderator Modes
# Demonstrates 4 different configurations

echo "=========================================="
echo "Council Moderator Mode Test"
echo "=========================================="
echo ""

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

echo "=========================================="
echo "Test 1: NO MODERATOR (Baseline)"
echo "=========================================="
echo ""
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 4,
    "councilModerator": false,
    "councilModeratorActive": false
  }' | jq '{
    turns: .councilTotalTurns,
    moderatorInterjections: .metadata.councilModeratorInterjections,
    hasAnalysis: (.metadata.councilModeratorAnalysis != null),
    synthesis: .councilSynthesis[:100]
  }'

echo ""
echo ""
echo "=========================================="
echo "Test 2: POST-DEBATE ANALYSIS ONLY"
echo "councilModerator=true, councilModeratorActive=false"
echo "=========================================="
echo ""
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should we use Python or Go for microservices?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 4,
    "councilModerator": true,
    "councilModeratorActive": false
  }' | jq '{
    turns: .councilTotalTurns,
    moderatorInterjections: .metadata.councilModeratorInterjections,
    hasAnalysis: (.metadata.councilModeratorAnalysis != null),
    analysisPreview: (.metadata.councilModeratorAnalysis[:200] + "...")
  }'

echo ""
echo ""
echo "=========================================="
echo "Test 3: ACTIVE INTERJECTIONS ONLY"
echo "councilModerator=false, councilModeratorActive=true"
echo "=========================================="
echo ""
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 6,
    "councilModerator": false,
    "councilModeratorActive": true,
    "councilModeratorCheckFrequency": 2
  }' | jq '{
    turns: .councilTotalTurns,
    moderatorInterjections: .metadata.councilModeratorInterjections,
    hasAnalysis: (.metadata.councilModeratorAnalysis != null),
    turnSpeakers: [.councilTurns[]?.speakerId]
  }'

echo ""
echo ""
echo "=========================================="
echo "Test 4: BOTH (Active Interjections + Post-Debate Analysis)"
echo "councilModerator=true, councilModeratorActive=true"
echo "=========================================="
echo ""
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TypeScript vs JavaScript for backend development?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 6,
    "councilModerator": true,
    "councilModeratorActive": true,
    "councilModeratorCheckFrequency": 2
  }' | jq '{
    turns: .councilTotalTurns,
    moderatorInterjections: .metadata.councilModeratorInterjections,
    hasPostAnalysis: (.metadata.councilModeratorAnalysis != null),
    turnSpeakers: [.councilTurns[]?.speakerId],
    analysisPreview: (.metadata.councilModeratorAnalysis[:200] + "...")
  }'

echo ""
echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Test 1: No moderation at all"
echo "- Test 2: Post-debate analysis only (no interjections during debate)"
echo "- Test 3: Active interjections during debate (no post-analysis)"
echo "- Test 4: Both active interjections AND post-debate analysis"
echo ""
