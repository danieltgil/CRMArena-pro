#!/usr/bin/env python3
"""
Quick Battle Test - Run Green vs Barebones White Agent

This script will:
1. Install dependencies if needed
2. Start both agents
3. Run a quick 3-task battle
4. Show results
"""

import subprocess
import sys
import time
import os

def install_dependencies():
    """Install required packages"""
    print("📦 Checking dependencies...")
    try:
        import a2a
        import uvicorn
        import fastapi
        print("✅ Dependencies already installed")
    except ImportError:
        print("Installing a2a-python and dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "a2a-python", "uvicorn", "fastapi", "-q"
        ])
        print("✅ Dependencies installed")

def start_agent(script, port, name):
    """Start an agent in the background"""
    print(f"🚀 Starting {name} on port {port}...")
    env = os.environ.copy()
    env["AGENT_PORT"] = str(port)

    proc = subprocess.Popen(
        [sys.executable, script, "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return proc

def wait_for_agent(port, timeout=30):
    """Wait for agent to be ready"""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def run_battle():
    """Run the battle assessment"""
    print("\n⚔️  STARTING BATTLE!")
    print("=" * 60)

    import asyncio
    import json

    try:
        from a2a.client import A2AClient
        from a2a.types import SendMessageRequest, Message, Part, TextPart, Role
    except ImportError:
        print("❌ Failed to import a2a. Installing...")
        install_dependencies()
        from a2a.client import A2AClient
        from a2a.types import SendMessageRequest, Message, Part, TextPart, Role

    async def assess():
        client = A2AClient("http://localhost:8001")

        config = {
            "white_agent_url": "http://localhost:8002",
            "task_category": "handle_time",
            "max_tasks": 3,
            "interactive": False,
            "max_turns": 20
        }

        print(f"\n📋 Assessment Config:")
        print(f"   Task Category: {config['task_category']}")
        print(f"   Number of Tasks: {config['max_tasks']}")
        print(f"   Interactive: {config['interactive']}")
        print()

        try:
            response = await client.send_message(
                SendMessageRequest(
                    message=Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(
                            kind="text",
                            text=json.dumps(config)
                        ))]
                    )
                )
            )

            if response and response.message.parts:
                result = response.message.parts[0].root.text
                print("\n" + "=" * 60)
                print("🏆 BATTLE RESULTS")
                print("=" * 60)
                print(result)
                print("=" * 60)
            else:
                print("❌ No response from green agent")

        except Exception as e:
            print(f"❌ Error during assessment: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(assess())

def main():
    print("🥊 CRMArena-Pro Battle Test")
    print("=" * 60)
    print()

    # Install dependencies
    install_dependencies()

    # Start agents
    white_proc = start_agent("barebones_white_agent.py", 8002, "Barebones White Agent")
    green_proc = start_agent("agentbeats_green_agent.py", 8001, "Green Agent (Evaluator)")

    try:
        # Wait for agents to start
        print("\n⏳ Waiting for agents to start...")
        white_ready = wait_for_agent(8002, timeout=30)
        green_ready = wait_for_agent(8001, timeout=30)

        if not white_ready:
            print("❌ White agent failed to start")
            return
        if not green_ready:
            print("❌ Green agent failed to start")
            return

        print("✅ Both agents are ready!\n")
        time.sleep(2)

        # Run the battle
        run_battle()

    finally:
        # Cleanup
        print("\n\n🛑 Stopping agents...")
        white_proc.terminate()
        green_proc.terminate()

        try:
            white_proc.wait(timeout=5)
            green_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            white_proc.kill()
            green_proc.kill()

        print("✅ Agents stopped")

if __name__ == "__main__":
    main()
