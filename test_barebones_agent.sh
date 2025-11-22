#!/bin/bash
# Quick test of barebones agent (no OpenAI key needed!)

echo "🤖 Testing Barebones White Agent (No LLM Required!)"
echo "======================================================"
echo ""

# Check if a2a-python is installed
if ! python -c "import a2a" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements-agentbeats.txt
fi

echo "Starting barebones white agent on port 8002..."
python barebones_white_agent.py --port 8002 &
WHITE_PID=$!

# Wait for white agent to start
sleep 3

echo "Starting green agent on port 8001..."
python agentbeats_green_agent.py --port 8001 &
GREEN_PID=$!

# Wait for green agent to start
sleep 5

echo ""
echo "✅ Both agents started!"
echo ""
echo "Running quick assessment (3 tasks)..."
echo ""

# Run assessment
python -c "
import asyncio
import json
from a2a.client import A2AClient
from a2a.types import SendMessageRequest, Message, Part, TextPart, Role

async def test():
    client = A2AClient('http://localhost:8001')

    config = {
        'white_agent_url': 'http://localhost:8002',
        'task_category': 'handle_time',
        'max_tasks': 3
    }

    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role=Role.agent,
                parts=[Part(root=TextPart(kind='text', text=json.dumps(config)))]
            )
        )
    )

    print(response.message.parts[0].root.text)

asyncio.run(test())
"

# Cleanup
echo ""
echo "Stopping agents..."
kill $WHITE_PID $GREEN_PID 2>/dev/null

echo "✅ Done!"
