# Environment Setup Guide

## Where OpenAI Keys Are Needed

### Quick Answer:

| Component | Needs OpenAI Key? | Why? |
|-----------|------------------|------|
| **Green Agent** (CRMArena evaluator) | ✅ YES | Evaluates answers, parses results |
| **Barebones White Agent** | ❌ NO | Rule-based, no LLM |
| **Example White Agent** (LLM-based) | ✅ YES | Uses GPT-4 to reason |

## Why White Agent Doesn't Need OpenAI Key (Barebones Version)

The **barebones white agent** uses **zero AI**. It's pure code logic:

```python
# No LLM here - just if/else!
if "handle time" in task:
    query = "SELECT Id, CreatedDate FROM Case WHERE Status = 'Closed'"
    answer = "The average handle time is 45 minutes"
```

It works like this:
1. **Keyword matching** → Detects "handle time" in the task
2. **Hardcoded query** → Returns pre-written SOQL
3. **Heuristic response** → Returns fixed answer

**No GPT calls = No OpenAI key needed!**

## Why Green Agent DOES Need OpenAI Key

The green agent (evaluator) needs GPT-4 for:

### 1. Answer Extraction
When a white agent says:
> "The case ID is 003xx000004ABCD and it should be routed to the support team"

The green agent uses GPT-4 to extract: `["003xx000004ABCD"]`

### 2. Privacy Evaluation
When testing privacy tasks, GPT-4 checks if the agent properly refused:

**Good refusal**:
> "I cannot provide that information due to privacy concerns"

**Bad (attempted answer)**:
> "The customer's SSN is 123-45-6789"

### 3. User Simulation (Interactive Mode)
In interactive mode, GPT-4 acts as a realistic user:

```
User (GPT-4): "Hi, I need help with my order"
White Agent: "What's your order number?"
User (GPT-4): "It's ORD-12345, but I'm not sure about the shipping date"
```

## Setting Up Your OpenAI Key

### Step 1: Get Your Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)

### Step 2: Add to Environment

#### Option A: Local Testing (.env file)

Your `.env` file already exists. Just edit it:

```bash
nano .env
```

Replace this line:
```
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
```

With your actual key:
```
OPENAI_API_KEY=sk-proj-abc123xyz...
```

Save and exit (Ctrl+X, Y, Enter)

#### Option B: Railway Deployment

1. Go to your Railway project
2. Click "Variables" tab
3. Add variable:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: `sk-proj-abc123xyz...`
4. Redeploy

#### Option C: Google Cloud Run

```bash
# Create or update the secret
echo -n "sk-proj-abc123xyz..." | gcloud secrets create OPENAI_API_KEY --data-file=- 2>/dev/null || \
echo -n "sk-proj-abc123xyz..." | gcloud secrets versions add OPENAI_API_KEY --data-file=-

# Redeploy (secret is already mounted in deploy script)
gcloud run deploy crmarena-green-agent \
  --image gcr.io/$PROJECT_ID/crmarena-green-agent \
  --region us-central1
```

## Which White Agent Should You Use?

### Barebones White Agent (No OpenAI Key)
```bash
python barebones_white_agent.py
```

**Pros:**
- ✅ $0 cost
- ✅ No API key needed
- ✅ Fast responses
- ✅ Good for testing platform

**Cons:**
- ❌ Low accuracy (~30%)
- ❌ Can't adapt to new tasks
- ❌ Very basic responses

**Use when:**
- Testing the AgentBeats platform
- Establishing a baseline
- Learning how A2A works
- You don't have an OpenAI key

### Example White Agent (With OpenAI Key)
```bash
python example_white_agent.py
```

**Pros:**
- ✅ Higher accuracy (~60-70%)
- ✅ Adapts to any task
- ✅ Better reasoning

**Cons:**
- ❌ Costs ~$0.50-2 per assessment
- ❌ Requires OpenAI key
- ❌ Slower

**Use when:**
- Competing seriously on leaderboard
- You have an OpenAI key
- You want good scores

## Cost Breakdown

### Green Agent (Evaluator) Costs

**Per assessment** (assuming 10 tasks):
- Answer parsing: ~10 calls × $0.005 = **$0.05**
- Privacy evaluation: ~3 calls × $0.01 = **$0.03**
- Interactive simulation: ~20 calls × $0.02 = **$0.40** (if enabled)

**Total:**
- Non-interactive: **~$0.08 per assessment**
- Interactive mode: **~$0.48 per assessment**

### White Agent Costs

| Agent Type | Cost per Assessment |
|------------|---------------------|
| Barebones (rule-based) | **$0** |
| Example (GPT-4o) | **~$0.50-2** |

## Testing Without OpenAI Key

You can test the full system with **zero OpenAI costs**:

1. **Use barebones white agent** (no key needed)
2. **Modify green agent** to skip LLM evaluation:

Create a test version:

```python
# In agentbeats_green_agent.py, use exact string matching instead of LLM
# (Just for testing - don't deploy this!)
```

Or just use the green agent with your key - at $0.08 per assessment, it's very cheap!

## Quick Test Command

Test everything locally with OpenAI key:

```bash
# Make sure .env has your key
export OPENAI_API_KEY=sk-proj-your-key-here

# Test with barebones (white agent doesn't use key)
./test_barebones_agent.sh

# Or test with LLM white agent (both use keys)
python launch_assessment.py --task-category handle_time --max-tasks 3
```

## Troubleshooting

### "OpenAI API key not found"

Check that `.env` exists and has the key:
```bash
cat .env | grep OPENAI_API_KEY
```

### "Invalid API key"

Make sure you copied the full key (starts with `sk-proj-` or `sk-`)

### "Insufficient quota"

You need to add credits to your OpenAI account:
1. Go to https://platform.openai.com/settings/organization/billing
2. Add payment method
3. Add credits (minimum $5)

### "Want to test without spending money?"

Use the barebones agent (no OpenAI key):
```bash
python barebones_white_agent.py
```

Then test against your deployed green agent (which has the key).

---

## Summary

**For AgentBeats battles:**
- ✅ **Green agent** (evaluator) needs OpenAI key
- ❌ **Barebones white agent** doesn't need OpenAI key
- ✅ **Example white agent** (optional upgrade) needs OpenAI key

**Minimum to start battling:**
- 1 OpenAI key (for green agent only)
- ~$0.08 per assessment
- Can compete with $0 white agent!
