"""
Simple AgentBeats Green Agent for CRMArena-Pro (FastAPI-based)

This is a simplified version that doesn't require the a2a-python package.
It implements a basic HTTP API compatible with AgentBeats.
"""

import json
import os
import traceback
import uuid
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import httpx
import asyncio

# Lazy imports - we'll import these only when needed to avoid slow startup
# from crm_sandbox.data.assets import (
#     TASKS_B2B,
#     TASKS_B2B_INTERACTIVE,
#     TASKS_B2C,
#     TASKS_B2C_INTERACTIVE,
#     B2B_SCHEMA,
#     B2C_SCHEMA,
#     EXTERNAL_FACING_TASKS,
# )
# from crm_sandbox.env.env import ChatEnv, InteractiveChatEnv

# Cache for lazily loaded assets
_assets_cache = None

def get_assets():
    """Lazily load CRM assets only when needed"""
    global _assets_cache
    if _assets_cache is None:
        from crm_sandbox.data.assets import (
            TASKS_B2B,
            TASKS_B2B_INTERACTIVE,
            TASKS_B2C,
            TASKS_B2C_INTERACTIVE,
            B2B_SCHEMA,
            B2C_SCHEMA,
            EXTERNAL_FACING_TASKS,
        )
        from crm_sandbox.env.env import ChatEnv, InteractiveChatEnv

        _assets_cache = {
            'TASKS_B2B': TASKS_B2B,
            'TASKS_B2B_INTERACTIVE': TASKS_B2B_INTERACTIVE,
            'TASKS_B2C': TASKS_B2C,
            'TASKS_B2C_INTERACTIVE': TASKS_B2C_INTERACTIVE,
            'B2B_SCHEMA': B2B_SCHEMA,
            'B2C_SCHEMA': B2C_SCHEMA,
            'EXTERNAL_FACING_TASKS': EXTERNAL_FACING_TASKS,
            'ChatEnv': ChatEnv,
            'InteractiveChatEnv': InteractiveChatEnv,
        }
    return _assets_cache


# Pydantic models for A2A protocol
class TaskInput(BaseModel):
    """A2A protocol task input"""
    white_agent_url: str = Field(..., description="URL of the white agent to assess")
    task_category: str = Field(default="all", description="Task category to evaluate")
    max_tasks: Optional[int] = Field(default=None, description="Maximum number of tasks")
    interactive: bool = Field(default=False, description="Whether to use interactive mode")
    max_turns: int = Field(default=20, description="Maximum turns per task")
    max_user_turns: int = Field(default=10, description="Maximum user turns in interactive mode")

class TaskStatus(BaseModel):
    """A2A protocol task status"""
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TaskResponse(BaseModel):
    """A2A protocol task creation response"""
    task_id: str
    status: str

# In-memory task storage (in production, use a database)
tasks_storage: Dict[str, TaskStatus] = {}
tasks_results: Dict[str, Any] = {}

# Pydantic models for legacy /assess endpoint
class AssessmentConfig(BaseModel):
    white_agent_url: str
    task_category: str = "all"
    max_tasks: Optional[int] = None
    interactive: bool = False
    max_turns: int = 20
    max_user_turns: int = 10


# FastAPI app
app = FastAPI(title="CRMArena-Pro Green Agent")


@app.get("/.well-known/agent-card.json")
async def agent_card():
    """Return agent card for AgentBeats discovery"""
    return {
        "name": "CRMArena-Pro Green Agent",
        "description": "Assessment agent for evaluating CRM task performance using CRMArena-Pro benchmark",
        "version": "1.0.0",
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
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Whether to use interactive mode",
                    "default": False,
                },
            },
            "required": ["white_agent_url"],
        },
    }


@app.post("/task", response_model=TaskResponse)
async def create_task(task_input: TaskInput):
    """A2A protocol: Create a new assessment task"""
    task_id = str(uuid.uuid4())

    # Initialize task as pending
    tasks_storage[task_id] = TaskStatus(status="pending")

    # Start assessment in background
    asyncio.create_task(run_assessment_background(task_id, task_input))

    return TaskResponse(task_id=task_id, status="pending")


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """A2A protocol: Get task status"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    return tasks_storage[task_id]


@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """A2A protocol: Cancel a task"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    tasks_storage[task_id].status = "cancelled"
    return {"status": "cancelled"}


async def run_assessment_background(task_id: str, task_input: TaskInput):
    """Background task to run assessment (used by A2A protocol)"""
    try:
        # Update status to running
        tasks_storage[task_id].status = "running"

        # Run the assessment
        result = await execute_assessment(
            white_agent_url=task_input.white_agent_url,
            task_category=task_input.task_category,
            max_tasks=task_input.max_tasks,
            interactive=task_input.interactive,
            max_turns=task_input.max_turns,
            max_user_turns=task_input.max_user_turns
        )

        # Update status to completed
        tasks_storage[task_id].status = "completed"
        tasks_storage[task_id].result = result

    except Exception as e:
        tasks_storage[task_id].status = "failed"
        tasks_storage[task_id].error = str(e)


async def execute_assessment(
    white_agent_url: str,
    task_category: str = "all",
    max_tasks: Optional[int] = None,
    interactive: bool = False,
    max_turns: int = 20,
    max_user_turns: int = 10
) -> Dict[str, Any]:
    """Core assessment logic (shared by both A2A and legacy endpoints)"""
    # Lazily load assets (this may take time on first request, but won't block startup)
    assets = get_assets()

    # Load tasks
    org_type = "b2b"  # Default for now

    if interactive:
        selected_tasks = assets['TASKS_B2B_INTERACTIVE']
        schema = assets['B2B_SCHEMA']
    else:
        selected_tasks = assets['TASKS_B2B']
        schema = assets['B2B_SCHEMA']

    # Filter by category
    if task_category != "all":
        categories = task_category.split(",")
        selected_tasks = [t for t in selected_tasks if t["task"] in categories]

    # Limit tasks
    if max_tasks:
        selected_tasks = selected_tasks[:max_tasks]

    # Create environment
    tasks_dict = {t["idx"]: t for t in selected_tasks}

    if interactive:
        env = assets['InteractiveChatEnv'](
            tasks=tasks_dict,
            max_user_turns=max_user_turns,
            org_type=org_type,
        )
    else:
        env = assets['ChatEnv'](
            tasks=tasks_dict,
            org_type=org_type,
        )

    # Run assessment
    results = []
    successful_tasks = 0

    async with httpx.AsyncClient(timeout=300.0) as client:
        for task in selected_tasks:
            task_idx = task["idx"]
            agent_type = "external" if task["task"] in assets['EXTERNAL_FACING_TASKS'] else "internal"

            # Create task message
            task_message = create_task_message(task, schema, agent_type, max_turns)

            # Interact with white agent
            result = await interact_with_white_agent(
                client=client,
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

    # Compute metrics
    accuracy = successful_tasks / len(selected_tasks) if len(selected_tasks) > 0 else 0

    return {
        "status": "completed",
        "metrics": {
            "accuracy": accuracy,
            "successful_tasks": successful_tasks,
            "total_tasks": len(selected_tasks),
            "pass@1": accuracy,
        },
        "results": results,
    }


@app.post("/assess")
async def run_assessment(config: AssessmentConfig):
    """Legacy endpoint: Run an assessment on a white agent (returns result directly)"""
    try:
        result = await execute_assessment(
            white_agent_url=config.white_agent_url,
            task_category=config.task_category,
            max_tasks=config.max_tasks,
            interactive=config.interactive,
            max_turns=config.max_turns,
            max_user_turns=config.max_user_turns
        )
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )


def create_task_message(task: Dict, schema: List[Dict], agent_type: str, max_turns: int) -> str:
    """Create task message for white agent"""

    # Build schema description
    schema_desc = "# Salesforce Schema\n\n"
    for obj in schema:
        schema_desc += f"## {obj['object']}\n"
        for field, desc in obj["fields"].items():
            schema_desc += f"  - {field}: {desc}\n"
        schema_desc += "\n"

    # Role description
    if agent_type == "internal":
        role_desc = "You are an internal Salesforce agent helping employees query and analyze CRM data."
    else:
        role_desc = "You are a customer-facing Salesforce agent. You must protect customer privacy and not reveal confidential information."

    # Metadata
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

Please begin by analyzing the task and deciding on your first action.
"""
    return instructions.strip()


async def interact_with_white_agent(
    client: httpx.AsyncClient,
    white_agent_url: str,
    task_message: str,
    env: Any,
    task_idx: int,
    max_turns: int,
) -> Dict:
    """Interact with white agent to complete a task"""

    current_turn = 0
    done = False
    reward = 0
    trajectory = []

    # Reset environment
    env.reset(task_index=task_idx)

    try:
        # Send initial task
        response = await client.post(
            f"{white_agent_url}/message",
            json={"message": task_message},
            timeout=60.0
        )

        # Interaction loop
        while current_turn < max_turns and not done:
            current_turn += 1

            if response.status_code != 200:
                break

            response_data = response.json()
            agent_response = response_data.get("message", "")

            trajectory.append({
                "turn": current_turn,
                "agent_response": agent_response,
            })

            # Parse action
            action_data = parse_action(agent_response)
            if not action_data:
                # Ask for retry
                response = await client.post(
                    f"{white_agent_url}/message",
                    json={"message": "Invalid format. Please respond with valid JSON."},
                    timeout=60.0
                )
                continue

            # Execute action
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

            # Send observation back
            response = await client.post(
                f"{white_agent_url}/message",
                json={"message": f"Observation: {observation}\n\nWhat is your next action?"},
                timeout=60.0
            )

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


def parse_action(response_text: str) -> Optional[Dict]:
    """Parse action from agent response"""
    import re

    # Try to extract JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
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


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "crmarena-pro-green-agent"}

@app.on_event("startup")
async def startup_event():
    """Log when the server is starting"""
    print("=" * 60)
    print("CRMArena-Pro Green Agent starting...")
    print("Assets will be loaded lazily on first assessment request")
    print("=" * 60)


def main():
    load_dotenv()

    port = int(os.getenv("PORT", os.getenv("AGENT_PORT", 8001)))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"Starting CRMArena-Pro Green Agent (Simple) on {host}:{port}")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
