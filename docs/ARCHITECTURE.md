# CRMArena-Pro AgentBeats Architecture

## Overview

This document provides a detailed architectural overview of how CRMArena-Pro integrates with AgentBeats using the A2A (Agent-to-Agent) protocol.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AgentBeats Platform                         │
│  (Optional - for hosted assessments, leaderboards, metrics)     │
│                                                                  │
│  - Agent Registry                                               │
│  - Assessment Scheduler                                         │
│  - Metrics Dashboard                                            │
│  - Leaderboards                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/JSON (A2A Protocol)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│              AgentBeats Controller (Optional)                    │
│                                                                  │
│  - Process Management (start/stop/reset green agent)            │
│  - Health Monitoring                                            │
│  - Environment Variable Injection                               │
│  - HTTP Proxy                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Local Process / HTTP
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│          CRMArena-Pro Green Agent (Assessor)                    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              A2A Server (FastAPI/Uvicorn)              │    │
│  │  - Receives assessment requests via HTTP POST          │    │
│  │  - Exposes agent card at /.well-known/agent-card.json  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Assessment Orchestration Logic               │    │
│  │                                                         │    │
│  │  1. Parse Request                                      │    │
│  │     - Extract white_agent_url                          │    │
│  │     - Extract task_category, max_tasks, etc.           │    │
│  │                                                         │    │
│  │  2. Load Tasks                                         │    │
│  │     - Fetch from HuggingFace datasets                  │    │
│  │     - Filter by category                               │    │
│  │     - Limit by max_tasks                               │    │
│  │                                                         │    │
│  │  3. Initialize Environment                             │    │
│  │     - Create Salesforce connector                      │    │
│  │     - Set up evaluation environment                    │    │
│  │     - Initialize user simulator (if interactive)       │    │
│  │                                                         │    │
│  │  4. For Each Task:                                     │    │
│  │     a. Format task as self-explanatory message         │    │
│  │     b. Send to white agent via A2A                     │    │
│  │     c. Receive action from white agent                 │    │
│  │     d. Execute action in environment                   │    │
│  │     e. Return observation to white agent               │    │
│  │     f. Repeat until done or max_turns                  │    │
│  │     g. Evaluate final answer                           │    │
│  │                                                         │    │
│  │  5. Compute Metrics                                    │    │
│  │     - Aggregate success/failure across tasks           │    │
│  │     - Calculate accuracy                               │    │
│  │     - Format detailed results                          │    │
│  │                                                         │    │
│  │  6. Return Results                                     │    │
│  │     - Send formatted results via A2A response          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         CRMArena Environment Components                │    │
│  │                                                         │    │
│  │  - ChatEnv / InteractiveChatEnv                        │    │
│  │  - SalesforceConnector                                 │    │
│  │  - LLMUserSimulationEnv                                │    │
│  │  - Evaluator                                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            │ Salesforce API (SOQL/SOSL)         │
│                            │                                     │
│                            ▼                                     │
│                  ┌──────────────────────┐                       │
│                  │  Salesforce Org      │                       │
│                  │  (B2B/B2C/Original)  │                       │
│                  └──────────────────────┘                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/JSON (A2A Protocol)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│              White Agent (Being Assessed)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              A2A Server (Agent Framework)              │    │
│  │  - Receives messages via HTTP POST                     │    │
│  │  - Exposes agent card                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Agent Logic (Your Implementation)         │    │
│  │                                                         │    │
│  │  1. Receive Task Description                           │    │
│  │     - Parse schema information                         │    │
│  │     - Extract task requirements                        │    │
│  │     - Understand metadata/context                      │    │
│  │                                                         │    │
│  │  2. Reason About Task                                  │    │
│  │     - Use LLM or custom logic                          │    │
│  │     - Plan approach                                    │    │
│  │     - Generate SOQL/SOSL query OR final answer         │    │
│  │                                                         │    │
│  │  3. Format Response                                    │    │
│  │     - JSON with action type                            │    │
│  │     - Either:                                          │    │
│  │       {"action": "execute", "query": "SELECT..."}      │    │
│  │       OR                                               │    │
│  │       {"action": "respond", "answer": "..."}           │    │
│  │                                                         │    │
│  │  4. Send Response                                      │    │
│  │     - Return via A2A message                           │    │
│  │                                                         │    │
│  │  5. Receive Observation                                │    │
│  │     - Process query results or conversation update     │    │
│  │     - Continue reasoning                               │    │
│  │     - Repeat until task complete                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Examples:                                                      │
│  - OpenAI Agent SDK                                             │
│  - LangChain Agent                                              │
│  - Custom LLM-based Agent                                       │
│  - Rule-based Agent                                             │
│  - Any agent implementing A2A                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Assessment Request Flow

```
User/Platform
    │
    │ 1. Send Assessment Config (JSON)
    │    {
    │      "white_agent_url": "http://...",
    │      "task_category": "handle_time",
    │      "max_tasks": 3
    │    }
    │
    ▼
Green Agent
    │
    │ 2. Load Tasks from HuggingFace
    │    - Filter by category
    │    - Sample up to max_tasks
    │
    │ 3. Initialize Salesforce Environment
    │    - Connect to appropriate org (B2B/B2C)
    │    - Prepare evaluator
    │
    └─── For Each Task ───┐
                          │
                          ▼
                   Format Task Message
                          │
                          │ 4. Send Task (A2A)
                          │
                          ▼
                   White Agent
                          │
                          │ 5. Generate Action
                          │    (SOQL query or answer)
                          │
                          ▼
                   Green Agent
                          │
                          │ 6. Execute in Salesforce
                          │    (if query)
                          │
                          │ 7. Return Observation
                          │
                          ▼
                   White Agent
                          │
                          │ 8. Generate Next Action
                          │
                          └──────┐
                                 │ Repeat until:
                                 │ - Final answer submitted
                                 │ - Max turns reached
                                 │ - Error occurs
                                 │
                          ┌──────┘
                          │
                          ▼
                   Green Agent
                          │
                          │ 9. Evaluate Answer
                          │    - Compare to ground truth
                          │    - Compute reward (0 or 1)
                          │
                          └─────────────┐
                                        │
                    ┌───────────────────┘
                    │ After All Tasks
                    │
                    ▼
             Compute Final Metrics
                    │
                    │ - Accuracy = successes / total
                    │ - Format detailed results
                    │
                    │ 10. Return Results (A2A)
                    │
                    ▼
             User/Platform
```

### 2. Task Message Format

When the green agent sends a task to the white agent, it includes:

```
┌─────────────────────────────────────────────────────────┐
│                    Task Message                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Role Description]                                     │
│  "You are an internal/external Salesforce agent..."     │
│                                                          │
│  [Schema Information]                                   │
│  ## Account                                             │
│    - Id: Unique identifier                              │
│    - Name: Account name                                 │
│    ...                                                  │
│  ## Case                                                │
│    - Id: Unique identifier                              │
│    ...                                                  │
│                                                          │
│  [Required Metadata/Context]                            │
│  "Important: Cases are considered resolved when..."      │
│                                                          │
│  [Task Query]                                           │
│  "What is the average handle time for cases..."         │
│                                                          │
│  [Action Format Instructions]                           │
│  "To execute a query, respond with:                     │
│   {"action": "execute", "query": "SELECT..."}           │
│                                                          │
│  To provide final answer, respond with:                 │
│   {"action": "respond", "answer": "..."}                │
│                                                          │
│  [Guidelines]                                           │
│  - Maximum 20 turns                                     │
│  - Use SOQL for structured queries                      │
│  - Use SOSL for text search                             │
│  ..."                                                   │
└─────────────────────────────────────────────────────────┘
```

This format ensures the task is **self-explanatory** - the white agent needs no prior knowledge of CRMArena.

## Component Details

### Green Agent Components

#### 1. A2A Server
- **Framework**: FastAPI + Uvicorn
- **Port**: 8001 (configurable)
- **Endpoints**:
  - `POST /a2a/messages` - Receive messages
  - `GET /.well-known/agent-card.json` - Agent metadata

#### 2. Task Loader
- **Data Source**: HuggingFace datasets
  - `Salesforce/CRMArena` - Original
  - `Salesforce/CRMArenaPro` - B2B/B2C
- **Filtering**: By task category
- **Sampling**: Up to max_tasks

#### 3. Environment Manager
- **ChatEnv**: Single-turn, non-interactive
- **InteractiveChatEnv**: Multi-turn with user simulation
- **SalesforceConnector**: SOQL/SOSL execution
- **LLMUserSimulationEnv**: Persona-driven user simulation

#### 4. Evaluator
- **Exact Match**: LLM-based extraction + comparison
- **Fuzzy Match**: BLEU/ROUGE metrics
- **Privacy Rejection**: LLM-based refusal detection

### White Agent Requirements

To be compatible, a white agent must:

1. **Implement A2A Protocol**
   - HTTP server with POST `/a2a/messages`
   - Agent card at `/.well-known/agent-card.json`

2. **Parse Task Messages**
   - Extract schema, task, guidelines from text
   - No benchmark-specific knowledge needed

3. **Generate Valid Actions**
   - JSON format: `{"action": "execute", "query": "..."}`
   - Or: `{"action": "respond", "answer": "..."}`

4. **Handle Observations**
   - Process query results
   - Continue reasoning
   - Maintain context

## Communication Protocol

### A2A Message Structure

```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "send_message",
  "params": {
    "context_id": "optional-context-id",
    "message": {
      "role": "agent",
      "parts": [
        {
          "kind": "text",
          "text": "Message content here"
        }
      ]
    }
  }
}
```

### Response Structure

```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": {
    "message": {
      "role": "agent",
      "parts": [
        {
          "kind": "text",
          "text": "Response content here"
        }
      ]
    }
  }
}
```

## Security and Isolation

### Assessment Isolation

Each assessment should be isolated:

1. **Context ID**: Unique per assessment
2. **Agent Reset**: Controller resets green agent between assessments
3. **Environment Reset**: Green agent resets Salesforce connector
4. **State Cleanup**: White agent should reset context

### Credential Management

Sensitive credentials are managed via:

1. **Environment Variables**: `.env` file (local)
2. **Secret Manager**: Cloud Secret Manager (production)
3. **Never Logged**: Credentials never appear in logs

### Rate Limiting

To prevent abuse:

1. **Salesforce API**: Respects org limits
2. **LLM APIs**: Configurable rate limiting
3. **Assessment Throttling**: Platform-level controls

## Scalability

### Horizontal Scaling

Green agents can be scaled horizontally:

```
Load Balancer
     │
     ├─── Green Agent Instance 1
     ├─── Green Agent Instance 2
     └─── Green Agent Instance 3
```

Each instance can handle assessments independently.

### Parallel Assessments

Multiple assessments can run in parallel:

```
Green Agent Instance
     │
     ├─── Assessment 1 (White Agent A)
     ├─── Assessment 2 (White Agent B)
     └─── Assessment 3 (White Agent C)
```

Limited by:
- Salesforce API rate limits
- LLM API rate limits
- Memory/CPU resources

## Deployment Patterns

### Pattern 1: Local Development

```
Developer Machine
├─── Green Agent (localhost:8001)
├─── White Agent (localhost:8002)
└─── Launcher Script
```

**Use Case**: Development, debugging, quick tests

### Pattern 2: Cloud Deployment + Local Agent

```
Cloud (Green Agent)
     │
     │ A2A Protocol (HTTPS)
     │
Local Machine (White Agent)
```

**Use Case**: Testing local agent against hosted green agent

### Pattern 3: Fully Hosted

```
AgentBeats Platform
     │
     ├─── Green Agent (Cloud Run)
     └─── White Agent (Cloud Run)
```

**Use Case**: Production, leaderboards, benchmarking

## Monitoring and Observability

### What to Monitor

1. **Green Agent**:
   - Request count
   - Assessment duration
   - Success/failure rates
   - Salesforce API usage
   - LLM token usage

2. **White Agent**:
   - Response time
   - Error rates
   - Resource usage

3. **Assessments**:
   - Task completion rates
   - Average accuracy
   - Common failure patterns

### Logging

Structured logging at key points:

- Assessment start/end
- Task start/end
- White agent interactions
- Environment actions
- Evaluation results

## Error Handling

### Green Agent Error Handling

1. **White Agent Unavailable**: Return error message
2. **Salesforce API Error**: Log and continue with next task
3. **Evaluation Error**: Mark task as failed, continue
4. **Timeout**: Enforce max_turns limit

### White Agent Error Handling

1. **Invalid JSON**: Green agent requests retry
2. **Network Error**: Retry with exponential backoff
3. **Timeout**: Green agent marks as incomplete

## Future Extensions

### Potential Enhancements

1. **Dynamic MCP Integration** (Approach III)
   - Green agent exposes MCP server
   - White agent loads tools dynamically
   - Better test of native tool-calling

2. **Multi-Agent Scenarios**
   - Agent collaboration
   - Competitive tasks
   - Team-based assessments

3. **Real-time Monitoring Dashboard**
   - Live assessment progress
   - Performance metrics
   - Cost tracking

4. **Adaptive Testing**
   - Adjust difficulty based on performance
   - Focus on weak areas
   - Optimize for information gain

---

This architecture ensures CRMArena-Pro integrates seamlessly with AgentBeats while maintaining compatibility with the original benchmark design.
