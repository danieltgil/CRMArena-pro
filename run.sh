#!/bin/bash
# AgentBeats controller startup script for CRMArena-Pro Green Agent

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Use environment variables provided by AgentBeats controller
# HOST and AGENT_PORT are set by the controller
HOST=${HOST:-0.0.0.0}
AGENT_PORT=${AGENT_PORT:-8001}

echo "Starting CRMArena-Pro Green Agent..."
echo "Host: $HOST"
echo "Port: $AGENT_PORT"

# Run the green agent
python agentbeats_green_agent.py --host $HOST --port $AGENT_PORT
