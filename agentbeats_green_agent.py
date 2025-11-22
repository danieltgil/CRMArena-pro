"""
AgentBeats Green Agent for CRMArena-Pro

This green agent orchestrates CRMArena-Pro evaluations for white agents
following the A2A protocol.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import traceback
from datetime import datetime

from a2a.server import A2AServer
from a2a.types import (
    Message,
    Part,
    TextPart,
    Role,
    SendMessageRequest,
)

from crm_sandbox.data.assets import (
    TASKS_ORIGINAL,
    SCHEMA_ORIGINAL,
    TASKS_B2B,
    TASKS_B2B_INTERACTIVE,
    TASKS_B2C,
    TASKS_B2C_INTERACTIVE,
    B2B_SCHEMA,
    B2C_SCHEMA,
    EXTERNAL_FACING_TASKS,
)
from crm_sandbox.env.env import ChatEnv, InteractiveChatEnv
from crm_sandbox.env import TOOLS


class CRMArenaGreenAgent:
    """
    Green Agent for CRMArena-Pro Assessment

    This agent orchestrates evaluations by:
    1. Receiving assessment configuration from the AgentBeats platform
    2. Loading appropriate tasks and environment
    3. Distributing tasks to white agents via A2A
    4. Collecting results and computing metrics
    5. Reporting back to the platform
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8001,
        org_type: str = "b2b",
        user_model: str = "gpt-4o-2024-08-06",
        user_provider: str = "openai",
    ):
        self.host = host
        self.port = port
        self.org_type = org_type
        self.user_model = user_model
        self.user_provider = user_provider

        # Initialize A2A server
        self.server = A2AServer(
            agent_card={
                "name": "CRMArena-Pro Green Agent",
                "description": "Assessment agent for evaluating CRM task performance using CRMArena-Pro benchmark",
                "capabilities": {
                    "streaming": False,
                    "task_types": ["assessment", "evaluation"],
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "white_agent_url": {
                            "type": "string",
                            "description": "URL of the white agent to assess",
                        },
                        "task_category": {
                            "type": "string",
                            "description": "Task category to evaluate (or 'all')",
                            "default": "all",
                        },
                        "max_tasks": {
                            "type": "integer",
                            "description": "Maximum number of tasks to run (optional)",
                            "default": None,
                        },
                        "interactive": {
                            "type": "boolean",
                            "description": "Whether to use interactive mode",
                            "default": False,
                        },
                        "max_turns": {
                            "type": "integer",
                            "description": "Maximum turns per task",
                            "default": 20,
                        },
                        "max_user_turns": {
                            "type": "integer",
                            "description": "Maximum user simulation turns (interactive mode)",
                            "default": 10,
                        },
                    },
                    "required": ["white_agent_url"],
                },
            }
        )

        # Register message handler
        self.server.register_message_handler(self.handle_assessment_request)

    def load_tasks(self, task_category: str, interactive: bool) -> tuple:
        """Load tasks based on configuration"""
        if self.org_type == "b2b":
            TASKS = TASKS_B2B_INTERACTIVE if interactive else TASKS_B2B
            SCHEMA = B2B_SCHEMA
        elif self.org_type == "b2c":
            TASKS = TASKS_B2C_INTERACTIVE if interactive else TASKS_B2C
            SCHEMA = B2C_SCHEMA
        else:
            TASKS = TASKS_ORIGINAL
            SCHEMA = SCHEMA_ORIGINAL

        # Filter tasks by category
        if task_category == "all":
            selected_tasks = TASKS
        elif "," in task_category:
            categories = task_category.split(",")
            selected_tasks = [task for task in TASKS if task["task"] in categories]
        else:
            selected_tasks = [task for task in TASKS if task["task"] == task_category]

        return selected_tasks, SCHEMA

    def create_task_message_for_white_agent(
        self,
        task: Dict,
        schema: List[Dict],
        agent_type: str,
        max_turns: int
    ) -> str:
        """
        Create a self-explanatory task description for the white agent.
        This follows Approach II from the AgentBeats documentation.
        """

        # Build schema description
        schema_desc = "# Salesforce Schema\n\n"
        for obj in schema:
            schema_desc += f"## {obj['object']}\n"
            for field, desc in obj["fields"].items():
                schema_desc += f"  - {field}: {desc}\n"
            schema_desc += "\n"

        # Build task instructions based on agent type
        if agent_type == "internal":
            role_desc = "You are an internal Salesforce agent helping employees query and analyze CRM data."
        else:
            role_desc = "You are a customer-facing Salesforce agent. You must protect customer privacy and not reveal confidential information."

        # Required metadata
        metadata_section = ""
        if task.get("metadata", {}).get("required"):
            metadata_section = f"\n# Important Context\n{task['metadata']['required']}\n"

        # Instructions
        instructions = f"""
{role_desc}

{schema_desc}

{metadata_section}

# Your Task
{task['query']}

# Available Actions
You can take two types of actions:

1. **Execute a SOQL/SOSL query**:
   Format your response as JSON:
   ```json
   {{"action": "execute", "query": "YOUR_SOQL_OR_SOSL_QUERY_HERE"}}
   ```

2. **Respond with your final answer**:
   Format your response as JSON:
   ```json
   {{"action": "respond", "answer": "YOUR_FINAL_ANSWER_HERE"}}
   ```

# Important Guidelines
- You have a maximum of {max_turns} turns to complete this task
- First gather information using SOQL/SOSL queries
- When you have enough information, provide your final answer using the respond action
- Your response must be valid JSON
- For SOQL queries, use SELECT statements on the objects described in the schema
- For SOSL queries, use FIND statements for text search

Please begin by analyzing the task and deciding on your first action.
"""
        return instructions.strip()

    async def interact_with_white_agent(
        self,
        white_agent_url: str,
        task_message: str,
        env: Any,
        task_idx: int,
        max_turns: int,
    ) -> Dict:
        """
        Interact with white agent via A2A protocol to complete a task
        """
        from a2a.client import A2AClient

        client = A2AClient(white_agent_url)

        # Initialize conversation
        context_id = f"crmarena_task_{task_idx}_{datetime.now().timestamp()}"

        current_turn = 0
        done = False
        reward = 0
        trajectory = []

        # Reset environment
        env.reset(task_index=task_idx)

        # Send initial task message
        try:
            response = await client.send_message(
                SendMessageRequest(
                    context_id=context_id,
                    message=Message(
                        role=Role.agent,
                        parts=[Part(root=TextPart(kind="text", text=task_message))],
                    ),
                )
            )

            current_message = task_message

            # Interaction loop
            while current_turn < max_turns and not done:
                current_turn += 1

                # Get white agent's response
                if not response or not response.message.parts:
                    break

                agent_response_text = response.message.parts[0].root.text
                trajectory.append({
                    "turn": current_turn,
                    "agent_response": agent_response_text,
                })

                # Parse action from response
                try:
                    action_data = self.parse_white_agent_response(agent_response_text)
                    if not action_data:
                        # Invalid format, ask for retry
                        response = await client.send_message(
                            SendMessageRequest(
                                context_id=context_id,
                                message=Message(
                                    role=Role.agent,
                                    parts=[Part(root=TextPart(
                                        kind="text",
                                        text="Invalid response format. Please respond with valid JSON containing either an 'execute' action with a 'query' or a 'respond' action with an 'answer'."
                                    ))],
                                ),
                            )
                        )
                        continue

                    # Execute action in environment
                    if action_data["action"] == "execute":
                        action = {"name": "execute", "content": action_data["query"]}
                    elif action_data["action"] == "respond":
                        action = {"name": "respond", "content": action_data["answer"]}
                    else:
                        continue

                    # Step environment
                    observation, reward, done, info = env.step(action)

                    trajectory[-1]["action"] = action
                    trajectory[-1]["observation"] = str(observation)
                    trajectory[-1]["reward"] = reward
                    trajectory[-1]["done"] = done

                    if done:
                        break

                    # Send observation back to agent
                    response = await client.send_message(
                        SendMessageRequest(
                            context_id=context_id,
                            message=Message(
                                role=Role.agent,
                                parts=[Part(root=TextPart(kind="text", text=f"Observation: {observation}\n\nWhat is your next action?"))],
                            ),
                        )
                    )

                except Exception as e:
                    trajectory.append({
                        "turn": current_turn,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    })
                    break

            return {
                "task_idx": task_idx,
                "reward": reward,
                "done": done,
                "num_turns": current_turn,
                "trajectory": trajectory,
            }

        except Exception as e:
            return {
                "task_idx": task_idx,
                "reward": 0,
                "done": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def parse_white_agent_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse white agent's response to extract action.
        Supports both plain JSON and markdown code blocks.
        """
        import re

        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

        try:
            action_data = json.loads(json_str)
            if "action" in action_data:
                return action_data
        except json.JSONDecodeError:
            pass

        return None

    async def handle_assessment_request(self, message: Message, context_id: Optional[str]) -> Message:
        """
        Handle incoming assessment request from AgentBeats platform
        """
        # Extract configuration from message
        message_text = message.parts[0].root.text

        try:
            # Try to parse as JSON first
            config = json.loads(message_text)
        except json.JSONDecodeError:
            # Fallback: extract from natural language
            # For now, require JSON format
            return Message(
                role=Role.agent,
                parts=[Part(root=TextPart(
                    kind="text",
                    text="Error: Please provide assessment configuration as JSON with required fields: white_agent_url, task_category (optional), max_tasks (optional), interactive (optional)"
                ))],
            )

        white_agent_url = config.get("white_agent_url")
        task_category = config.get("task_category", "all")
        max_tasks = config.get("max_tasks")
        interactive = config.get("interactive", False)
        max_turns = config.get("max_turns", 20)
        max_user_turns = config.get("max_user_turns", 10)

        if not white_agent_url:
            return Message(
                role=Role.agent,
                parts=[Part(root=TextPart(kind="text", text="Error: white_agent_url is required"))],
            )

        # Load tasks
        selected_tasks, schema = self.load_tasks(task_category, interactive)

        if max_tasks:
            selected_tasks = selected_tasks[:max_tasks]

        # Create environment
        tasks_dict = {t["idx"]: t for t in selected_tasks}

        if interactive:
            env = InteractiveChatEnv(
                tasks=tasks_dict,
                max_user_turns=max_user_turns,
                user_model=self.user_model,
                user_provider=self.user_provider,
                org_type=self.org_type,
            )
        else:
            env = ChatEnv(
                tasks=tasks_dict,
                user_model=self.user_model,
                user_provider=self.user_provider,
                org_type=self.org_type,
            )

        # Run assessment
        results = []
        successful_tasks = 0
        total_tasks = len(selected_tasks)

        progress_message = f"Starting CRMArena-Pro assessment on {total_tasks} tasks...\n"

        for i, task in enumerate(selected_tasks):
            task_idx = task["idx"]

            # Determine agent type
            agent_type = "external" if task["task"] in EXTERNAL_FACING_TASKS else "internal"

            # Create task message
            task_message = self.create_task_message_for_white_agent(
                task, schema, agent_type, max_turns
            )

            # Run task
            import asyncio
            result = await self.interact_with_white_agent(
                white_agent_url=white_agent_url,
                task_message=task_message,
                env=env,
                task_idx=task_idx,
                max_turns=max_turns,
            )

            result["task_type"] = task["task"]
            result["ground_truth"] = task["answer"]
            results.append(result)

            if result.get("reward", 0) == 1:
                successful_tasks += 1

            progress_message += f"Task {i+1}/{total_tasks}: {'✅' if result.get('reward', 0) == 1 else '❌'} (type: {task['task']})\n"

        # Compute metrics
        accuracy = successful_tasks / total_tasks if total_tasks > 0 else 0

        metrics = {
            "accuracy": accuracy,
            "successful_tasks": successful_tasks,
            "total_tasks": total_tasks,
            "pass@1": accuracy,  # Same as accuracy for single run
        }

        # Format response
        response_text = f"""
# CRMArena-Pro Assessment Complete

{progress_message}

## Metrics
- **Accuracy (Pass@1)**: {accuracy:.2%} ({successful_tasks}/{total_tasks})
- **Task Category**: {task_category}
- **Org Type**: {self.org_type}
- **Interactive Mode**: {interactive}

## Detailed Results
{json.dumps(results, indent=2)}
"""

        return Message(
            role=Role.agent,
            parts=[Part(root=TextPart(kind="text", text=response_text.strip()))],
        )

    def run(self):
        """Start the green agent server"""
        import uvicorn

        print(f"Starting CRMArena-Pro Green Agent on {self.host}:{self.port}")
        print(f"Org Type: {self.org_type}")
        print(f"User Simulation Model: {self.user_model}")

        uvicorn.run(
            self.server.app,
            host=self.host,
            port=self.port,
        )


def main():
    load_dotenv()

    import argparse
    parser = argparse.ArgumentParser(description="CRMArena-Pro Green Agent for AgentBeats")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("AGENT_PORT", 8001)))
    parser.add_argument("--org-type", type=str, default="b2b", choices=["b2b", "b2c", "original"])
    parser.add_argument("--user-model", type=str, default="gpt-4o-2024-08-06")
    parser.add_argument("--user-provider", type=str, default="openai")

    args = parser.parse_args()

    green_agent = CRMArenaGreenAgent(
        host=args.host,
        port=args.port,
        org_type=args.org_type,
        user_model=args.user_model,
        user_provider=args.user_provider,
    )

    green_agent.run()


if __name__ == "__main__":
    main()
