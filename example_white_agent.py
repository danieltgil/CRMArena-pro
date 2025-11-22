"""
Example White Agent for CRMArena-Pro Assessment

This is a simple A2A-compatible agent that can be tested by the green agent.
It uses an LLM to interpret tasks and generate actions.
"""

import os
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from a2a.server import A2AServer
from a2a.types import Message, Part, TextPart, Role
import litellm


class CRMArenaWhiteAgent:
    """
    A general-purpose white agent for CRMArena tasks.

    This agent:
    1. Receives task descriptions via A2A
    2. Uses an LLM to reason about the task
    3. Generates SOQL/SOSL queries or responses
    4. Maintains conversation context per task
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8002,
        model: str = "gpt-4o",
        provider: str = "openai",
    ):
        self.host = host
        self.port = port
        self.model = model
        self.provider = provider
        self.contexts = {}  # Store conversation history per context_id

        # Initialize A2A server
        self.server = A2AServer(
            agent_card={
                "name": "CRMArena White Agent",
                "description": "A general-purpose agent for solving CRM tasks using Salesforce",
                "capabilities": {
                    "streaming": False,
                    "task_types": ["crm", "salesforce", "data-query"],
                },
            }
        )

        # Register message handler
        self.server.register_message_handler(self.handle_message)

    async def handle_message(self, message: Message, context_id: Optional[str]) -> Message:
        """Handle incoming messages from the green agent"""

        # Initialize context if needed
        if context_id not in self.contexts:
            self.contexts[context_id] = {
                "messages": [],
                "turns": 0,
            }

        context = self.contexts[context_id]
        message_text = message.parts[0].root.text

        # Add user message to context
        context["messages"].append({
            "role": "user",
            "content": message_text,
        })

        # Generate response using LLM
        try:
            response_text = await self.generate_response(context["messages"])
            context["messages"].append({
                "role": "assistant",
                "content": response_text,
            })
            context["turns"] += 1

            return Message(
                role=Role.agent,
                parts=[Part(root=TextPart(kind="text", text=response_text))],
            )

        except Exception as e:
            import traceback
            error_message = f"Error generating response: {str(e)}\n{traceback.format_exc()}"

            return Message(
                role=Role.agent,
                parts=[Part(root=TextPart(kind="text", text=error_message))],
            )

    async def generate_response(self, messages: list) -> str:
        """
        Generate a response using the LLM.

        The LLM should output JSON with either:
        - {"action": "execute", "query": "SOQL/SOSL query"}
        - {"action": "respond", "answer": "final answer"}
        """

        # Add system prompt for first message
        if len(messages) == 1:
            system_prompt = """
You are an AI agent that helps with Salesforce CRM tasks.

When you receive a task:
1. Analyze what information you need
2. If you need to query data, use SOQL or SOSL queries
3. When you have enough information, provide your final answer

Always respond with valid JSON in one of these formats:

For executing a query:
```json
{"action": "execute", "query": "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"}
```

For providing a final answer:
```json
{"action": "respond", "answer": "The answer is: ..."}
```

Guidelines:
- SOQL uses SELECT statements (like SQL)
- SOSL uses FIND statements for text search
- Be precise with field names and object names
- Provide clear, complete answers
"""
            llm_messages = [
                {"role": "system", "content": system_prompt},
            ] + messages
        else:
            llm_messages = messages

        # Call LLM
        response = litellm.completion(
            model=self.model,
            messages=llm_messages,
            temperature=0.0,
            max_tokens=2000,
        )

        return response.choices[0].message.content

    def reset_context(self, context_id: str):
        """Reset a specific context (called by controller between assessments)"""
        if context_id in self.contexts:
            del self.contexts[context_id]

    def reset_all(self):
        """Reset all contexts (called by controller between assessments)"""
        self.contexts = {}

    def run(self):
        """Start the white agent server"""
        import uvicorn

        print(f"Starting CRMArena White Agent on {self.host}:{self.port}")
        print(f"Model: {self.model}")

        uvicorn.run(
            self.server.app,
            host=self.host,
            port=self.port,
        )


def main():
    load_dotenv()

    import argparse
    parser = argparse.ArgumentParser(description="CRMArena White Agent")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("AGENT_PORT", 8002)))
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--provider", type=str, default="openai")

    args = parser.parse_args()

    white_agent = CRMArenaWhiteAgent(
        host=args.host,
        port=args.port,
        model=args.model,
        provider=args.provider,
    )

    white_agent.run()


if __name__ == "__main__":
    main()
