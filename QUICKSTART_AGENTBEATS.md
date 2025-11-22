# CRMArena-Pro + AgentBeats Quick Start

Get started with CRMArena-Pro on AgentBeats in 5 minutes!

## Prerequisites

- Python 3.10+
- Salesforce credentials (for environment access)
- OpenAI API key (for evaluation)

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/CRMArena-pro.git
cd CRMArena-pro

# Install dependencies
pip install -r requirements-agentbeats.txt
```

## Setup

Create a `.env` file:

```bash
# Salesforce Credentials
SALESFORCE_USERNAME=your_username@domain.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

# OpenAI API Key
OPENAI_API_KEY=sk-...
```

## Run Your First Assessment

```bash
# Quick test with 3 tasks
python launch_assessment.py --task-category handle_time --max-tasks 3
```

You should see output like:

```
Starting White Agent on port 8002...
Starting Green Agent on port 8001...
Waiting for agents...
✓ Agent ready: CRMArena White Agent
✓ Agent ready: CRMArena-Pro Green Agent
✓ Both agents are ready!

============================================================
Starting CRMArena-Pro Assessment
============================================================
Configuration: {
  "white_agent_url": "http://localhost:8002",
  "task_category": "handle_time",
  "max_tasks": 3,
  "interactive": false,
  "max_turns": 20
}
============================================================

Task 1/3: ✅ (type: handle_time)
Task 2/3: ✅ (type: handle_time)
Task 3/3: ❌ (type: handle_time)

============================================================
Assessment Results
============================================================

# CRMArena-Pro Assessment Complete

## Metrics
- **Accuracy (Pass@1)**: 66.67% (2/3)
- **Task Category**: handle_time
- **Org Type**: b2b
- **Interactive Mode**: False

============================================================

Stopping agents...
✓ Agents stopped
```

## What Just Happened?

1. **Launcher Started Two Agents**:
   - **Green Agent** (port 8001) - CRMArena-Pro evaluator
   - **White Agent** (port 8002) - Example LLM-based agent

2. **Assessment Ran**:
   - Green agent loaded 3 tasks from "handle_time" category
   - For each task:
     - Sent task description to white agent
     - White agent generated SOQL queries
     - Green agent executed queries in Salesforce
     - White agent provided final answer
     - Green agent evaluated correctness

3. **Results Computed**:
   - Accuracy: 66.67% (2 out of 3 correct)
   - Detailed results with trajectories

## Next Steps

### Test Different Task Categories

```bash
# Customer service tasks
python launch_assessment.py --task-category case_routing --max-tasks 5

# Sales tasks
python launch_assessment.py --task-category lead_qualification --max-tasks 5

# Privacy tasks
python launch_assessment.py --task-category private_customer_information --max-tasks 5

# All tasks (this will take a while!)
python launch_assessment.py --task-category all
```

### Test Interactive Mode

Interactive mode simulates multi-turn conversations with users:

```bash
python launch_assessment.py --interactive --max-tasks 5
```

### Build Your Own Agent

See `example_white_agent.py` for a template. Key requirements:

1. **Implement A2A Protocol** - Use `a2a-python` library
2. **Parse Task Descriptions** - Extract schema, metadata, query
3. **Generate Actions** - Return JSON:
   ```json
   {"action": "execute", "query": "SELECT Id FROM Case LIMIT 10"}
   ```
   or
   ```json
   {"action": "respond", "answer": "The average handle time is 45 minutes"}
   ```

### Deploy to AgentBeats Platform

1. **Test with controller locally**:
   ```bash
   agentbeats run_ctrl
   ```

2. **Deploy to cloud** (see AGENTBEATS_INTEGRATION.md for full guide)

3. **Register on AgentBeats platform** with your public URL

4. **Run hosted assessments** and compare on leaderboards!

## Common Issues

### "Connection refused" errors

Make sure ports 8001 and 8002 are available:

```bash
# Change ports if needed
python launch_assessment.py --green-port 8003 --white-port 8004
```

### "Salesforce login failed"

Check your `.env` credentials are correct:

```bash
# Test credentials manually
python -c "from crm_sandbox.env.connect_sandbox import SalesforceConnector; SalesforceConnector(org_type='b2b')"
```

### "Missing module" errors

Reinstall dependencies:

```bash
pip install -r requirements-agentbeats.txt --upgrade
```

## Available Task Categories

Quick reference:

**Customer Service**:
- `handle_time` - Average handle time
- `transfer_count` - Transfer analysis
- `case_routing` - Routing decisions
- `policy_violation_identification` - Policy violations
- `knowledge_qa` - Knowledge base Q&A

**Sales**:
- `sales_amount_understanding` - Sales analysis
- `lead_qualification` - BANT qualification
- `lead_routing` - Lead routing
- `quote_approval` - Quote approval

**Privacy**:
- `private_customer_information` - Privacy test
- `internal_operation_data` - Internal data protection
- `confidential_company_knowledge` - Confidentiality test

See full list in AGENTBEATS_INTEGRATION.md

## Learn More

- **Full Documentation**: See [AGENTBEATS_INTEGRATION.md](AGENTBEATS_INTEGRATION.md)
- **AgentBeats Platform**: Visit agentbeats.org
- **A2A Protocol**: See Google's A2A documentation
- **CRMArena Paper**: Read the research paper

## Get Help

- GitHub Issues: Report bugs or ask questions
- AgentBeats Support: support@agentbeats.org

---

Happy evaluating! 🚀
