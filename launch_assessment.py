"""
Local launcher for CRMArena-Pro AgentBeats Assessment

This script starts both green and white agents locally and runs an assessment.
"""

import asyncio
import json
import time
import subprocess
import sys
import requests
from typing import Optional
import argparse
from dotenv import load_dotenv

from a2a.client import A2AClient
from a2a.types import SendMessageRequest, Message, Part, TextPart, Role


class AssessmentLauncher:
    """Manages local assessment between green and white agents"""

    def __init__(
        self,
        green_agent_port: int = 8001,
        white_agent_port: int = 8002,
        green_agent_host: str = "localhost",
        white_agent_host: str = "localhost",
    ):
        self.green_agent_port = green_agent_port
        self.white_agent_port = white_agent_port
        self.green_agent_host = green_agent_host
        self.white_agent_host = white_agent_host

        self.green_agent_url = f"http://{green_agent_host}:{green_agent_port}"
        self.white_agent_url = f"http://{white_agent_host}:{white_agent_port}"

        self.green_process: Optional[subprocess.Popen] = None
        self.white_process: Optional[subprocess.Popen] = None

    def start_agent(self, script: str, port: int, name: str) -> subprocess.Popen:
        """Start an agent subprocess"""
        print(f"Starting {name} on port {port}...")

        env = {
            **subprocess.os.environ,
            "AGENT_PORT": str(port),
            "HOST": "0.0.0.0",
        }

        process = subprocess.Popen(
            [sys.executable, script, "--port", str(port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        return process

    def wait_for_agent(self, url: str, timeout: int = 30) -> bool:
        """Wait for agent to be ready"""
        print(f"Waiting for agent at {url}...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/.well-known/agent-card.json", timeout=2)
                if response.status_code == 200:
                    agent_card = response.json()
                    print(f"✓ Agent ready: {agent_card.get('name', 'Unknown')}")
                    return True
            except requests.exceptions.RequestException:
                pass

            time.sleep(1)

        return False

    async def run_assessment(
        self,
        task_category: str = "all",
        max_tasks: Optional[int] = None,
        interactive: bool = False,
        org_type: str = "b2b",
    ):
        """Run the assessment by sending a request to the green agent"""

        # Build assessment config
        config = {
            "white_agent_url": self.white_agent_url,
            "task_category": task_category,
            "interactive": interactive,
            "max_turns": 20,
        }

        if max_tasks is not None:
            config["max_tasks"] = max_tasks

        if interactive:
            config["max_user_turns"] = 10

        print(f"\n{'='*60}")
        print("Starting CRMArena-Pro Assessment")
        print(f"{'='*60}")
        print(f"Configuration: {json.dumps(config, indent=2)}")
        print(f"{'='*60}\n")

        # Create A2A client for green agent
        client = A2AClient(self.green_agent_url)

        try:
            # Send assessment request
            response = await client.send_message(
                SendMessageRequest(
                    message=Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(
                            kind="text",
                            text=json.dumps(config)
                        ))],
                    )
                )
            )

            # Print results
            if response and response.message.parts:
                result_text = response.message.parts[0].root.text
                print(f"\n{'='*60}")
                print("Assessment Results")
                print(f"{'='*60}")
                print(result_text)
                print(f"{'='*60}\n")

                return result_text
            else:
                print("Error: No response from green agent")
                return None

        except Exception as e:
            print(f"Error during assessment: {e}")
            import traceback
            traceback.print_exc()
            return None

    def start_agents(self):
        """Start both green and white agents"""
        # Start white agent first
        self.white_process = self.start_agent(
            "example_white_agent.py",
            self.white_agent_port,
            "White Agent"
        )

        # Start green agent
        self.green_process = self.start_agent(
            "agentbeats_green_agent.py",
            self.green_agent_port,
            "Green Agent"
        )

        # Wait for both agents to be ready
        white_ready = self.wait_for_agent(self.white_agent_url)
        green_ready = self.wait_for_agent(self.green_agent_url)

        if not white_ready or not green_ready:
            print("Error: Failed to start agents")
            self.cleanup()
            return False

        print("\n✓ Both agents are ready!\n")
        return True

    def cleanup(self):
        """Stop all agent processes"""
        print("\nStopping agents...")

        if self.green_process:
            self.green_process.terminate()
            try:
                self.green_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.green_process.kill()

        if self.white_process:
            self.white_process.terminate()
            try:
                self.white_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.white_process.kill()

        print("✓ Agents stopped")

    async def run(
        self,
        task_category: str = "all",
        max_tasks: Optional[int] = 3,
        interactive: bool = False,
        org_type: str = "b2b",
    ):
        """Main execution flow"""
        try:
            # Start agents
            if not self.start_agents():
                return

            # Run assessment
            await self.run_assessment(
                task_category=task_category,
                max_tasks=max_tasks,
                interactive=interactive,
                org_type=org_type,
            )

        finally:
            # Always cleanup
            self.cleanup()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Launch CRMArena-Pro Assessment")
    parser.add_argument(
        "--task-category",
        type=str,
        default="handle_time",
        help="Task category to test (default: handle_time for quick demo)",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=3,
        help="Maximum number of tasks to run (default: 3 for quick demo)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode with user simulation",
    )
    parser.add_argument(
        "--org-type",
        type=str,
        default="b2b",
        choices=["b2b", "b2c", "original"],
        help="Organization type (default: b2b)",
    )
    parser.add_argument(
        "--green-port",
        type=int,
        default=8001,
        help="Port for green agent (default: 8001)",
    )
    parser.add_argument(
        "--white-port",
        type=int,
        default=8002,
        help="Port for white agent (default: 8002)",
    )

    args = parser.parse_args()

    launcher = AssessmentLauncher(
        green_agent_port=args.green_port,
        white_agent_port=args.white_port,
    )

    # Run assessment
    asyncio.run(
        launcher.run(
            task_category=args.task_category,
            max_tasks=args.max_tasks,
            interactive=args.interactive,
            org_type=args.org_type,
        )
    )


if __name__ == "__main__":
    main()
