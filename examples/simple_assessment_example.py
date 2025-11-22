"""
Simple Example: Running a CRMArena-Pro Assessment

This example shows how to programmatically run an assessment
without using the launcher script.
"""

import asyncio
import json
from a2a.client import A2AClient
from a2a.types import SendMessageRequest, Message, Part, TextPart, Role


async def run_simple_assessment():
    """
    Run a simple assessment with custom configuration.

    Prerequisites:
    1. Green agent running on localhost:8001
    2. White agent running on localhost:8002
    """

    print("Connecting to CRMArena-Pro Green Agent...")

    # Create A2A client for the green agent
    green_agent_url = "http://localhost:8001"
    client = A2AClient(green_agent_url)

    # Define assessment configuration
    assessment_config = {
        "white_agent_url": "http://localhost:8002",
        "task_category": "handle_time",  # Test handle time calculation tasks
        "max_tasks": 3,                   # Run only 3 tasks for quick demo
        "interactive": False,             # Single-turn mode
        "max_turns": 20,                  # Max 20 turns per task
    }

    print(f"\nAssessment Configuration:")
    print(json.dumps(assessment_config, indent=2))
    print("\nSending assessment request...")

    # Send assessment request to green agent
    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role=Role.agent,
                parts=[Part(root=TextPart(
                    kind="text",
                    text=json.dumps(assessment_config)
                ))]
            )
        )
    )

    # Extract and display results
    if response and response.message.parts:
        results_text = response.message.parts[0].root.text

        print("\n" + "="*60)
        print("ASSESSMENT RESULTS")
        print("="*60)
        print(results_text)
        print("="*60)

        return results_text
    else:
        print("Error: No response received from green agent")
        return None


async def run_interactive_assessment():
    """
    Example: Run assessment in interactive mode with user simulation.
    """

    print("Running Interactive Assessment...")

    green_agent_url = "http://localhost:8001"
    client = A2AClient(green_agent_url)

    assessment_config = {
        "white_agent_url": "http://localhost:8002",
        "task_category": "all",           # All tasks
        "max_tasks": 5,                    # 5 tasks
        "interactive": True,               # Enable user simulation
        "max_turns": 20,                   # Max agent turns per task
        "max_user_turns": 10,              # Max user conversation turns
    }

    print(f"\nInteractive Assessment Configuration:")
    print(json.dumps(assessment_config, indent=2))
    print("\nThis will test multi-turn conversations with simulated users...")

    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role=Role.agent,
                parts=[Part(root=TextPart(
                    kind="text",
                    text=json.dumps(assessment_config)
                ))]
            )
        )
    )

    if response and response.message.parts:
        print("\n" + "="*60)
        print("INTERACTIVE ASSESSMENT RESULTS")
        print("="*60)
        print(response.message.parts[0].root.text)
        print("="*60)


async def run_privacy_assessment():
    """
    Example: Test privacy awareness by evaluating privacy-sensitive tasks.

    These tasks expect the agent to REFUSE to answer.
    """

    print("Running Privacy Assessment...")

    green_agent_url = "http://localhost:8001"
    client = A2AClient(green_agent_url)

    # Privacy tasks - agent should refuse to answer
    privacy_categories = ",".join([
        "private_customer_information",
        "internal_operation_data",
        "confidential_company_knowledge"
    ])

    assessment_config = {
        "white_agent_url": "http://localhost:8002",
        "task_category": privacy_categories,
        "interactive": False,
        "max_turns": 20,
    }

    print(f"\nPrivacy Assessment Configuration:")
    print(json.dumps(assessment_config, indent=2))
    print("\nNote: For privacy tasks, the agent should REFUSE to answer.")
    print("A correct response is a refusal, not an answer.\n")

    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role=Role.agent,
                parts=[Part(root=TextPart(
                    kind="text",
                    text=json.dumps(assessment_config)
                ))]
            )
        )
    )

    if response and response.message.parts:
        print("\n" + "="*60)
        print("PRIVACY ASSESSMENT RESULTS")
        print("="*60)
        print(response.message.parts[0].root.text)
        print("="*60)


async def run_multi_category_assessment():
    """
    Example: Test multiple task categories in one assessment.
    """

    print("Running Multi-Category Assessment...")

    green_agent_url = "http://localhost:8001"
    client = A2AClient(green_agent_url)

    # Test both customer service and sales tasks
    multi_categories = ",".join([
        "handle_time",
        "transfer_count",
        "lead_qualification",
        "sales_amount_understanding"
    ])

    assessment_config = {
        "white_agent_url": "http://localhost:8002",
        "task_category": multi_categories,
        "max_tasks": 10,  # Up to 10 tasks total across categories
        "interactive": False,
        "max_turns": 20,
    }

    print(f"\nMulti-Category Assessment Configuration:")
    print(json.dumps(assessment_config, indent=2))
    print("\nTesting agent on diverse task types...\n")

    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role=Role.agent,
                parts=[Part(root=TextPart(
                    kind="text",
                    text=json.dumps(assessment_config)
                ))]
            )
        )
    )

    if response and response.message.parts:
        print("\n" + "="*60)
        print("MULTI-CATEGORY ASSESSMENT RESULTS")
        print("="*60)
        print(response.message.parts[0].root.text)
        print("="*60)


def main():
    """
    Main function - choose which example to run.
    """
    import sys

    print("CRMArena-Pro Assessment Examples")
    print("="*60)
    print("\nMake sure you have:")
    print("1. Green agent running: python agentbeats_green_agent.py")
    print("2. White agent running: python example_white_agent.py")
    print("="*60)

    if len(sys.argv) > 1:
        example = sys.argv[1]
    else:
        print("\nAvailable examples:")
        print("  1. simple       - Simple 3-task assessment")
        print("  2. interactive  - Interactive mode with user simulation")
        print("  3. privacy      - Privacy awareness test")
        print("  4. multi        - Multi-category assessment")

        example = input("\nChoose example (1-4): ").strip()

    # Run selected example
    if example in ["1", "simple"]:
        asyncio.run(run_simple_assessment())
    elif example in ["2", "interactive"]:
        asyncio.run(run_interactive_assessment())
    elif example in ["3", "privacy"]:
        asyncio.run(run_privacy_assessment())
    elif example in ["4", "multi"]:
        asyncio.run(run_multi_category_assessment())
    else:
        print(f"Unknown example: {example}")
        print("Run with: python simple_assessment_example.py [1|2|3|4]")


if __name__ == "__main__":
    main()
