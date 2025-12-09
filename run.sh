#!/bin/bash
# Simple startup script for CRMArena-Pro Green Agent

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Use PORT from Cloud Run or AGENT_PORT
export AGENT_PORT=${PORT:-${AGENT_PORT:-8001}}
export HOST=${HOST:-0.0.0.0}

echo "Starting CRMArena-Pro Green Agent (Simple)..."
echo "Host: $HOST"
echo "Port: $AGENT_PORT"

# Run the simplified green agent
python3 agentbeats_green_agent_simple.py
