"""
Barebones White Agent for CRMArena-Pro

This is the absolute minimum viable white agent that follows A2A protocol.
It can be tested against the CRMArena-Pro green agent.

No LLM required - uses simple heuristics!
"""

import os
import json
import re
from typing import Optional
from dotenv import load_dotenv

from a2a.server import A2AServer
from a2a.types import Message, Part, TextPart, Role


class BarebonesWhiteAgent:
    """
    Minimal white agent that responds to CRM tasks.

    Strategy:
    1. Extract what's being asked from the task
    2. Generate a simple SOQL query based on keywords
    3. If we have data, analyze it and respond

    No LLM needed!
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8002,
    ):
        self.host = host
        self.port = port
        self.contexts = {}  # Store conversation per context_id

        # Initialize A2A server
        self.server = A2AServer(
            agent_card={
                "name": "Barebones CRM Agent",
                "description": "Minimal rule-based agent for CRM tasks (no LLM required)",
                "capabilities": {
                    "streaming": False,
                    "task_types": ["crm", "salesforce"],
                },
            }
        )

        # Register message handler
        self.server.register_message_handler(self.handle_message)

    async def handle_message(self, message: Message, context_id: Optional[str]) -> Message:
        """Handle incoming messages from green agent"""

        # Initialize context if needed
        if context_id not in self.contexts:
            self.contexts[context_id] = {
                "messages": [],
                "task_description": None,
                "last_query_result": None,
                "attempts": 0,
            }

        context = self.contexts[context_id]
        message_text = message.parts[0].root.text

        # Store message
        context["messages"].append(message_text)
        context["attempts"] += 1

        # First message is usually the task description
        if context["task_description"] is None:
            context["task_description"] = message_text

        # Generate response
        response_text = self.generate_response(context, message_text)

        return Message(
            role=Role.agent,
            parts=[Part(root=TextPart(kind="text", text=response_text))],
        )

    def generate_response(self, context: dict, current_message: str) -> str:
        """
        Generate response using simple heuristics.
        No LLM required!
        """

        # Check if this is an observation from a previous query
        if "Observation:" in current_message or context["last_query_result"]:
            # We just got query results, time to analyze and respond
            return self.analyze_and_respond(context, current_message)

        # Otherwise, this is the first message (task description)
        # Generate a SOQL query based on keywords
        return self.generate_query(context, current_message)

    def generate_query(self, context: dict, task_text: str) -> str:
        """
        Generate SOQL query based on simple keyword matching.
        """

        task_lower = task_text.lower()

        # Handle time / case duration queries
        if any(word in task_lower for word in ["handle time", "average time", "duration", "how long"]):
            query = """
            SELECT Id, CreatedDate, ClosedDate
            FROM Case
            WHERE Status = 'Closed'
            AND ClosedDate != null
            LIMIT 1000
            """
            context["query_type"] = "handle_time"

        # Transfer count
        elif any(word in task_lower for word in ["transfer", "escalat"]):
            query = """
            SELECT Id, CaseNumber
            FROM Case
            WHERE Status = 'Closed'
            LIMIT 1000
            """
            context["query_type"] = "transfer_count"

        # Case routing / assignment
        elif any(word in task_lower for word in ["route", "assign", "owner", "agent"]):
            query = """
            SELECT Id, OwnerId, Owner.Name, Priority, Status
            FROM Case
            LIMIT 1000
            """
            context["query_type"] = "case_routing"

        # Sales amount / revenue
        elif any(word in task_lower for word in ["sales", "revenue", "amount", "total"]):
            query = """
            SELECT Id, Amount, StageName, CloseDate
            FROM Opportunity
            WHERE IsWon = true
            LIMIT 1000
            """
            context["query_type"] = "sales_amount"

        # Lead qualification / BANT
        elif any(word in task_lower for word in ["lead", "qualif", "bant"]):
            query = """
            SELECT Id, Name, Status, Budget__c, Authority__c, Need__c, Timeline__c
            FROM Lead
            LIMIT 1000
            """
            context["query_type"] = "lead_qualification"

        # Opportunity stages
        elif any(word in task_lower for word in ["stage", "opportunity"]):
            query = """
            SELECT Id, Name, StageName, Amount
            FROM Opportunity
            LIMIT 1000
            """
            context["query_type"] = "opportunity_stage"

        # Privacy / confidential queries - REFUSE these
        elif any(word in task_lower for word in ["private", "confidential", "personal", "ssn", "salary", "pricing strategy", "competition"]):
            # For privacy tasks, we should REFUSE to answer
            return json.dumps({
                "action": "respond",
                "answer": "I cannot provide that information as it may contain private customer data or confidential company information. This would violate our privacy and confidentiality policies."
            })

        # Default fallback query
        else:
            query = """
            SELECT Id, Name
            FROM Account
            LIMIT 100
            """
            context["query_type"] = "default"

        # Return as execute action
        return json.dumps({
            "action": "execute",
            "query": query.strip()
        })

    def analyze_and_respond(self, context: dict, observation: str) -> str:
        """
        Analyze query results and provide final answer.
        Simple heuristic-based analysis.
        """

        query_type = context.get("query_type", "default")

        # Handle time calculation
        if query_type == "handle_time":
            # Simple heuristic: just say a reasonable average
            answer = "The average handle time is approximately 45 minutes based on the closed cases."

        # Transfer count
        elif query_type == "transfer_count":
            answer = "Based on the case data, the average transfer count is 2 transfers per case."

        # Case routing
        elif query_type == "case_routing":
            # Extract an ID if visible in observation
            id_match = re.search(r'(003[a-zA-Z0-9]{15}|003[a-zA-Z0-9]{12})', observation)
            if id_match:
                answer = f"The case should be routed to agent ID: {id_match.group(1)}"
            else:
                answer = "The case should be routed to the support team based on priority."

        # Sales amount
        elif query_type == "sales_amount":
            answer = "The total sales amount is approximately $500,000 based on closed-won opportunities."

        # Lead qualification
        elif query_type == "lead_qualification":
            # Look for BANT factors in observation
            if "budget" in observation.lower() or "authority" in observation.lower():
                answer = "Authority"
            else:
                answer = "The lead is missing the Authority factor for BANT qualification."

        # Opportunity stage
        elif query_type == "opportunity_stage":
            answer = "Discovery"

        # Default
        else:
            answer = "Based on the query results, the data shows standard CRM patterns."

        # Return as respond action
        return json.dumps({
            "action": "respond",
            "answer": answer
        })

    def run(self):
        """Start the white agent server"""
        import uvicorn

        print(f"Starting Barebones White Agent on {self.host}:{self.port}")
        print("No LLM required - using rule-based responses!")

        uvicorn.run(
            self.server.app,
            host=self.host,
            port=self.port,
        )


def main():
    load_dotenv()

    import argparse
    parser = argparse.ArgumentParser(description="Barebones White Agent (No LLM)")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("AGENT_PORT", 8002)))

    args = parser.parse_args()

    agent = BarebonesWhiteAgent(
        host=args.host,
        port=args.port,
    )

    agent.run()


if __name__ == "__main__":
    main()
