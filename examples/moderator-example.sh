#!/bin/bash

# Example: Council Debate Mode with Moderator Analysis
#
# This example demonstrates how to use the Council Moderator feature
# to get deep analytical insights into debate dialogues.

echo "=================================================="
echo "Council Debate Mode with Moderator Analysis"
echo "=================================================="
echo ""

# Example 1: Simple debate with moderator
echo "Example 1: Simple Technical Debate"
echo "--------------------------------------------------"

curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TypeScript vs JavaScript for backend development?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 3,
    "councilModerator": true
  }' | jq '{
    query: .query,
    synthesis: .metadata.councilSynthesis,
    moderatorAnalysis: .metadata.councilModeratorAnalysis,
    thinkingSteps: .metadata.councilModeratorThinkingSteps,
    winner: .metadata.councilModeratorBreakdown.overall_winner
  }'

echo ""
echo ""

# Example 2: Extended debate with custom personas
echo "Example 2: Extended Debate with Custom Personas"
echo "--------------------------------------------------"

curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Microservices vs Monolith for a startup?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 5,
    "councilModerator": true,
    "councilPersonas": {
      "pro": "Experienced DevOps engineer who has scaled multiple startups",
      "con": "Pragmatic CTO focused on time-to-market and simplicity"
    }
  }' | jq '{
    query: .query,
    turns: .metadata.councilTotalTurns,
    terminationReason: .metadata.councilTerminationReason,
    moderatorBreakdown: {
      argumentStrength: .metadata.councilModeratorBreakdown.argument_strength,
      fallacies: .metadata.councilModeratorBreakdown.logical_fallacies,
      winner: .metadata.councilModeratorBreakdown.overall_winner
    }
  }'

echo ""
echo ""

# Example 3: Full analysis with context
echo "Example 3: Full Analysis with CGRAG Context"
echo "--------------------------------------------------"

curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React vs Vue for enterprise applications?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 6,
    "councilModerator": true,
    "useContext": true,
    "temperature": 0.8
  }' | jq '{
    query: .query,
    contextUsed: (.metadata.cgragArtifacts > 0),
    synthesis: .metadata.councilSynthesis,
    moderatorAnalysis: .metadata.councilModeratorAnalysis
  }'

echo ""
echo ""
echo "=================================================="
echo "Examples Complete"
echo "=================================================="
echo ""
echo "To view full moderator analysis:"
echo "  curl ... | jq '.metadata.councilModeratorAnalysis'"
echo ""
echo "To view structured breakdown:"
echo "  curl ... | jq '.metadata.councilModeratorBreakdown'"
echo ""
echo "To view thinking steps:"
echo "  curl ... | jq '.metadata.councilModeratorThinkingSteps'"
echo ""
