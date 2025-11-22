# CRMArena-Pro AgentBeats Integration

This document explains how CRMArena-Pro has been integrated with the AgentBeats platform for standardized, reproducible agent evaluation.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Green Agent](#green-agent)
- [White Agent (Example)](#white-agent-example)
- [Local Testing](#local-testing)
- [Deploying to AgentBeats](#deploying-to-agentbeats)
- [Configuration](#configuration)
- [Metrics](#metrics)
- [Troubleshooting](#troubleshooting)

## Overview

CRMArena-Pro is now compatible with the AgentBeats platform, following the **Agentified Agent Assessment (AAA)** paradigm. This means:

1. **Green Agent** - The CRMArena-Pro evaluation is orchestrated by a specialized "green agent" that manages tasks, environments, and scoring
2. **Standardized Interface** - All communication uses the A2A (Agent-to-Agent) protocol
3. **Reproducible** - Assessments can be run repeatedly with consistent results
4. **Interoperable** - Any A2A-compatible agent can be evaluated

### What is a Green Agent?

In AgentBeats terminology:
- **Green Agent** (Assessor) - Orchestrates the evaluation, provides tasks, manages environment, computes metrics
- **White Agent** (Assessee) - The agent being tested

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentBeats Platform                      │
│  (Optional - for hosted assessments and leaderboards)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ A2A Protocol
                              │
┌─────────────────────────────▼─────────────────────────────┐
│              CRMArena-Pro Green Agent                      │
│                                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  1. Load tasks from HuggingFace                  │   │
│  │  2. Initialize environment (Salesforce)          │   │
│  │  3. Send tasks to white agent via A2A            │   │
│  │  4. Collect results and execute queries          │   │
│  │  5. Evaluate answers and compute metrics         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────▲─────────────────────────────┘
                              │ A2A Protocol
                              │
┌─────────────────────────────▼─────────────────────────────┐
│              White Agent (Your Agent)                      │
│                                                            │
│  - Receives task via A2A                                  │
│  - Generates SOQL/SOSL queries or responses               │
│  - Returns results via A2A                                │
└───────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Install base requirements
pip install -r requirements.txt

# Install AgentBeats integration requirements
pip install -r requirements-agentbeats.txt
```

### 2. Set Up Environment

Create a `.env` file with your credentials:

```bash
# Salesforce Credentials (required for environment access)
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

# For B2B org type (if using)
SALESFORCE_USERNAME_B2B=your_b2b_username
SALESFORCE_PASSWORD_B2B=your_b2b_password
SALESFORCE_SECURITY_TOKEN_B2B=your_b2b_token

# For B2C org type (if using)
SALESFORCE_USERNAME_B2C=your_b2c_username
SALESFORCE_PASSWORD_B2C=your_b2c_password
SALESFORCE_SECURITY_TOKEN_B2C=your_b2c_token

# OpenAI API Key (for evaluation and user simulation)
OPENAI_API_KEY=your_openai_key
```

### 3. Run a Quick Test

```bash
# Run a quick assessment with 3 tasks
python launch_assessment.py --task-category handle_time --max-tasks 3
```

This will:
1. Start the green agent (CRMArena-Pro evaluator)
2. Start an example white agent
3. Run 3 tasks from the "handle_time" category
4. Display results and metrics

## Green Agent

The green agent is implemented in `agentbeats_green_agent.py`.

### How It Works

1. **Receives Assessment Request** - Gets configuration (task category, white agent URL, etc.) via A2A
2. **Loads Tasks** - Fetches appropriate dataset from HuggingFace based on org type
3. **Creates Environment** - Initializes Salesforce connector and evaluation environment
4. **Orchestrates Tasks** - For each task:
   - Formats task as self-explanatory instructions
   - Sends to white agent via A2A
   - Receives actions (SOQL queries or responses)
   - Executes queries in Salesforce
   - Returns observations to white agent
   - Evaluates final answer
5. **Computes Metrics** - Calculates accuracy, pass@1, etc.
6. **Reports Results** - Returns comprehensive results to requestor

### Starting the Green Agent

```bash
# Default (B2B, port 8001)
python agentbeats_green_agent.py

# Custom configuration
python agentbeats_green_agent.py \
  --port 8001 \
  --org-type b2c \
  --user-model gpt-4o-2024-08-06
```

### Green Agent Configuration

The green agent can be configured via:
- Command-line arguments (at startup)
- Assessment request parameters (per assessment)

#### Startup Arguments

- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port to listen on (default: 8001, or from AGENT_PORT env var)
- `--org-type` - Salesforce org type: b2b, b2c, or original (default: b2b)
- `--user-model` - LLM for evaluation (default: gpt-4o-2024-08-06)
- `--user-provider` - LLM provider (default: openai)

#### Assessment Request Parameters

Send these as JSON to the green agent:

```json
{
  "white_agent_url": "http://localhost:8002",
  "task_category": "all",
  "max_tasks": 10,
  "interactive": false,
  "max_turns": 20,
  "max_user_turns": 10
}
```

**Parameters:**
- `white_agent_url` (required) - URL of the white agent to assess
- `task_category` (optional) - Which tasks to run:
  - `"all"` - All tasks
  - Single category: `"handle_time"`
  - Multiple: `"handle_time,transfer_count,case_routing"`
- `max_tasks` (optional) - Limit number of tasks
- `interactive` (optional) - Enable user simulation mode (default: false)
- `max_turns` (optional) - Max turns per task (default: 20)
- `max_user_turns` (optional) - Max user turns in interactive mode (default: 10)

### Available Task Categories

#### Customer Service
- `handle_time` - Average handle time calculation
- `transfer_count` - Case transfer analysis
- `case_routing` - Case routing decisions
- `policy_violation_identification` - Policy violation detection
- `top_issue_identification` - Top issue identification
- `monthly_trend_analysis` - Monthly trend analysis
- `best_region_identification` - Best performing region
- `knowledge_qa` - Knowledge base Q&A
- `named_entity_disambiguation` - Entity disambiguation

#### Sales
- `sales_amount_understanding` - Sales amount analysis
- `lead_routing` - Lead routing decisions
- `sales_cycle_understanding` - Sales cycle analysis
- `conversion_rate_comprehension` - Conversion rate analysis
- `wrong_stage_rectification` - Opportunity stage correction
- `sales_insight_mining` - Sales insight extraction
- `quote_approval` - Quote approval process
- `lead_qualification` - Lead qualification (BANT)
- `activity_priority` - Activity prioritization
- `invalid_config` - Invalid configuration detection

#### Privacy & Security
- `private_customer_information` - Privacy rejection test
- `internal_operation_data` - Internal data protection
- `confidential_company_knowledge` - Confidentiality test

## White Agent (Example)

An example white agent is provided in `example_white_agent.py`.

### How It Works

1. Receives task description via A2A (includes schema, metadata, instructions)
2. Uses an LLM to reason about the task
3. Generates actions as JSON:
   - `{"action": "execute", "query": "SOQL/SOSL query"}`
   - `{"action": "respond", "answer": "final answer"}`
4. Receives observations from green agent
5. Continues until task complete or max turns reached

### Starting the Example White Agent

```bash
# Default (GPT-4o, port 8002)
python example_white_agent.py

# Custom model
python example_white_agent.py \
  --port 8002 \
  --model gpt-4o \
  --provider openai
```

### Building Your Own White Agent

To build your own A2A-compatible white agent:

1. **Implement A2A Server** - Use `a2a-python` library
2. **Handle Messages** - Parse task descriptions
3. **Return JSON Actions** - Format responses as:
   ```json
   {"action": "execute", "query": "SELECT..."}
   ```
   or
   ```json
   {"action": "respond", "answer": "The answer is..."}
   ```
4. **Maintain Context** - Track conversation per `context_id`

See `example_white_agent.py` for a complete implementation.

## Local Testing

### Using the Launcher Script

The `launch_assessment.py` script makes local testing easy:

```bash
# Quick test with 3 tasks
python launch_assessment.py --task-category handle_time --max-tasks 3

# Test all handle_time tasks
python launch_assessment.py --task-category handle_time

# Test multiple categories
python launch_assessment.py --task-category "handle_time,transfer_count" --max-tasks 10

# Interactive mode
python launch_assessment.py --interactive --max-tasks 5

# B2C org type
python launch_assessment.py --org-type b2c --max-tasks 5
```

### Manual Testing

1. **Start White Agent**
   ```bash
   python example_white_agent.py --port 8002
   ```

2. **Start Green Agent**
   ```bash
   python agentbeats_green_agent.py --port 8001
   ```

3. **Send Assessment Request**
   ```python
   import asyncio
   from a2a.client import A2AClient
   from a2a.types import SendMessageRequest, Message, Part, TextPart, Role
   import json

   async def run_assessment():
       client = A2AClient("http://localhost:8001")

       config = {
           "white_agent_url": "http://localhost:8002",
           "task_category": "handle_time",
           "max_tasks": 3
       }

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

       print(response.message.parts[0].root.text)

   asyncio.run(run_assessment())
   ```

## Deploying to AgentBeats

### Step 1: Install AgentBeats Controller

```bash
pip install earthshaker
```

### Step 2: Make `run.sh` Executable

```bash
chmod +x run.sh
```

### Step 3: Test Controller Locally

```bash
agentbeats run_ctrl
```

Visit `http://localhost:8000` to see the controller UI.

### Step 4: Deploy to Cloud

#### Option A: Docker + Cloud Run

1. **Create Dockerfile** (if not using buildpacks):
   ```dockerfile
   FROM python:3.10-slim

   WORKDIR /app
   COPY . .

   RUN pip install -r requirements-agentbeats.txt
   RUN chmod +x run.sh

   CMD ["agentbeats", "run_ctrl"]
   ```

2. **Build and Deploy**:
   ```bash
   # Build with Cloud Buildpacks
   pack build crmarena-green-agent --builder gcr.io/buildpacks/builder:v1

   # Push to Artifact Registry
   docker tag crmarena-green-agent gcr.io/YOUR_PROJECT/crmarena-green-agent
   docker push gcr.io/YOUR_PROJECT/crmarena-green-agent

   # Deploy to Cloud Run
   gcloud run deploy crmarena-green-agent \
     --image gcr.io/YOUR_PROJECT/crmarena-green-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### Option B: Any VPS with HTTPS

1. **Deploy your code** to VPS
2. **Install dependencies**: `pip install -r requirements-agentbeats.txt`
3. **Set up Nginx** with SSL certificate
4. **Run controller**: `agentbeats run_ctrl`

### Step 5: Register on AgentBeats Platform

Visit AgentBeats platform and fill out the registration form:
- **Controller URL**: Your public HTTPS URL
- **Agent Type**: Green Agent
- **Assessment Type**: CRMArena-Pro

## Configuration

### `.agentbeats.json`

This file describes your agent to the AgentBeats platform:

```json
{
  "agent": {
    "name": "CRMArena-Pro Green Agent",
    "type": "green",
    "description": "Assessment agent for CRM tasks"
  },
  "runtime": {
    "python_version": "3.10",
    "entry_point": "run.sh",
    "default_port": 8001
  },
  "assessments": [...],
  "metrics": [...],
  "requirements": {...}
}
```

See `.agentbeats.json` for the complete configuration.

### Environment Variables

Required:
- `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_SECURITY_TOKEN`
- `OPENAI_API_KEY`

Optional (set by AgentBeats controller):
- `HOST` - Host to bind to (default: 0.0.0.0)
- `AGENT_PORT` - Port to use (default: 8001)

## Metrics

The green agent computes the following metrics:

### Primary Metrics

- **Accuracy (Pass@1)** - Percentage of tasks where the agent provided the correct answer on the first attempt
  - Range: 0.0 to 1.0
  - Higher is better

### Detailed Metrics

Per assessment, the green agent also tracks:
- `successful_tasks` - Number of tasks completed correctly
- `total_tasks` - Total number of tasks attempted
- Per-task results with trajectories

### Metric Computation

Metrics are computed based on task type:

1. **Exact Match** - For structured answers (IDs, dates, categories)
   - Uses LLM-based extraction + sorted list comparison
   - Task-specific parsers for different entity types

2. **Fuzzy Match** - For free-text answers
   - Uses BLEU/ROUGE metrics
   - Range: 0.0 to 1.0

3. **Privacy Rejection** - For privacy/security tasks
   - Checks if agent properly refused to answer
   - 1.0 if refused, 0.0 if attempted to answer

## Troubleshooting

### Green Agent Won't Start

**Problem**: ImportError for `a2a` or `earthshaker`

**Solution**:
```bash
pip install -r requirements-agentbeats.txt
```

**Problem**: Missing Salesforce credentials

**Solution**: Check `.env` file has all required credentials:
```bash
SALESFORCE_USERNAME=...
SALESFORCE_PASSWORD=...
SALESFORCE_SECURITY_TOKEN=...
OPENAI_API_KEY=...
```

### White Agent Not Responding

**Problem**: White agent returns invalid JSON

**Solution**: Ensure responses match expected format:
```json
{"action": "execute", "query": "..."}
```
or
```json
{"action": "respond", "answer": "..."}
```

**Problem**: Connection refused

**Solution**: Check white agent is running and accessible at the URL provided

### Assessment Failures

**Problem**: All tasks score 0

**Solution**: Check:
1. Salesforce credentials are valid
2. White agent is generating valid SOQL queries
3. Schema information is being used correctly

**Problem**: Timeout errors

**Solution**: Increase `max_turns` or optimize white agent response time

### Controller Issues

**Problem**: `run.sh` not executable

**Solution**:
```bash
chmod +x run.sh
```

**Problem**: Port already in use

**Solution**: Change port:
```bash
export AGENT_PORT=8003
python agentbeats_green_agent.py
```

## Advanced Usage

### Custom Evaluation Modes

The green agent supports two evaluation modes (configured per task):

- **Default Mode** - Only required metadata provided
- **Aided Mode** - Additional optional domain knowledge provided

This is controlled at the task level, not the assessment level.

### Multi-Turn Interactive Mode

Enable interactive mode to test agents with simulated user conversations:

```python
config = {
    "white_agent_url": "http://localhost:8002",
    "interactive": True,
    "max_user_turns": 10,
    "task_category": "all"
}
```

The green agent uses LLM-based user simulation with persona-driven behavior.

### Privacy-Aware Evaluation

Test privacy awareness by filtering to privacy tasks:

```python
config = {
    "white_agent_url": "http://localhost:8002",
    "task_category": "private_customer_information,internal_operation_data,confidential_company_knowledge"
}
```

These tasks expect the agent to **refuse** to answer.

## Next Steps

1. **Test Locally** - Use `launch_assessment.py` to verify integration
2. **Build Your Agent** - Create an A2A-compatible white agent
3. **Deploy Green Agent** - Deploy to AgentBeats platform for hosted assessments
4. **Compare Results** - See how your agent stacks up on the leaderboard

## Resources

- [AgentBeats Documentation](https://agentbeats.org)
- [A2A Protocol Specification](https://github.com/google/a2a)
- [CRMArena-Pro Paper](https://arxiv.org/abs/...)
- [Original CRMArena Repo](https://github.com/Salesforce/CRMArena)

## Support

For issues with:
- **CRMArena-Pro**: Open an issue on this repo
- **AgentBeats Platform**: Visit agentbeats.org/support
- **A2A Protocol**: See Google's A2A repo

---

Built with ❤️ for standardized, reproducible agent evaluation
