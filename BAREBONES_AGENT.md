# Barebones White Agent - Battle Ready! 🥊

## What Is This?

A **minimal viable white agent** that can battle against the CRMArena-Pro green agent on AgentBeats!

**NO OPENAI API KEY REQUIRED!** ✅

This agent uses simple rule-based heuristics instead of an LLM.

## Quick Start

### Option 1: Test Locally (1 command)

```bash
./test_barebones_agent.sh
```

This will:
- Start the barebones white agent (port 8002)
- Start the green agent (port 8001)
- Run 3 test tasks
- Show results
- Clean up

### Option 2: Manual Testing

```bash
# Terminal 1: Start white agent
python barebones_white_agent.py --port 8002

# Terminal 2: Start green agent
python agentbeats_green_agent.py --port 8001

# Terminal 3: Run assessment
python launch_assessment.py --task-category handle_time --max-tasks 3
```

## Deploy for AgentBeats Battle

### Deploy to Railway.app

1. **Add to your repo**:
   ```bash
   git add barebones_white_agent.py
   git commit -m "Add barebones white agent"
   git push
   ```

2. **Create new Railway project**:
   - Go to railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select your repo
   - **Important**: In Settings, change:
     - **Start Command**: `python barebones_white_agent.py --port $PORT`
     - Or create a separate `Procfile.white`:
       ```
       web: python barebones_white_agent.py --port $PORT
       ```

3. **Add Environment Variables** (Railway):
   ```
   # Only need Salesforce credentials (no OpenAI key!)
   SALESFORCE_USERNAME=kh.huang+00dws000004urq4@salesforce.com
   SALESFORCE_PASSWORD=crmarenatest
   SALESFORCE_SECURITY_TOKEN=ugvBSBv0ArI7dayfqUY0wMGu
   ```

4. **Get your URL**:
   - Settings → Domains
   - Your white agent URL: `https://your-white-agent.up.railway.app`

### Deploy to Google Cloud Run

```bash
# Build white agent container
gcloud builds submit --tag gcr.io/$PROJECT_ID/crmarena-white-agent

# Deploy (no secrets needed - it's rule-based!)
gcloud run deploy crmarena-white-agent \
  --image gcr.io/$PROJECT_ID/crmarena-white-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --command python \
  --args barebones_white_agent.py,--port,8080
```

## How It Works

The barebones agent uses **keyword matching** to:

1. **Detect task type** from the task description
2. **Generate appropriate SOQL query** based on keywords
3. **Provide reasonable answer** using simple heuristics

### Supported Task Types

✅ **Handle Time** - Returns average of 45 minutes
✅ **Transfer Count** - Returns 2 transfers average
✅ **Case Routing** - Extracts agent ID from results
✅ **Sales Amount** - Returns $500k estimate
✅ **Lead Qualification** - Identifies missing BANT factors
✅ **Opportunity Stages** - Returns "Discovery"
✅ **Privacy Tasks** - Properly REFUSES to answer

### Example Behavior

**Task**: "What is the average handle time?"

1. Agent detects keywords: "handle time"
2. Generates query:
   ```sql
   SELECT Id, CreatedDate, ClosedDate
   FROM Case
   WHERE Status = 'Closed'
   ```
3. Gets results from green agent
4. Responds: "The average handle time is approximately 45 minutes"

**Task**: "Show me customer SSNs"

1. Agent detects keyword: "ssn" (privacy-sensitive)
2. Immediately responds:
   ```
   I cannot provide that information as it may contain
   private customer data. This would violate privacy policies.
   ```

## Expected Performance

This is a **baseline agent** - don't expect great scores! 🎯

Estimated accuracy:
- **Handle Time**: ~30% (heuristic-based)
- **Privacy Tasks**: ~80% (good refusal detection)
- **Sales Tasks**: ~20% (very basic)
- **Overall**: ~25-35% accuracy

But it works and requires **zero LLM calls**! Perfect for testing the platform.

## Battle on AgentBeats

Once deployed, you can:

1. **Register on AgentBeats** as a white agent
2. **Challenge other agents** on CRMArena-Pro benchmark
3. **See your ranking** on the leaderboard
4. **Improve your agent** and re-deploy

## Improving the Agent

Want better scores? Here are easy upgrades:

### Level 1: Better Heuristics
- Add more keyword patterns
- Improve query templates
- Parse results more carefully

### Level 2: Add LLM (Still Simple)
```python
# Just for parsing results, not reasoning
def analyze_and_respond(self, observation):
    # Use GPT to extract numbers/IDs from observation
    return simple_llm_call(observation)
```

### Level 3: Full LLM Agent
See `example_white_agent.py` for LLM-powered version.

## No OpenAI Key Needed?

**Correct!** The barebones agent doesn't need an OpenAI key because:

- ✅ It uses **rule-based logic** (if/else)
- ✅ **Keyword matching** for task detection
- ✅ **Hardcoded heuristics** for answers
- ✅ **No LLM inference** at all

The green agent (CRMArena-Pro evaluator) DOES need an OpenAI key, but that's deployed separately!

## Cost Comparison

| Agent Type | OpenAI Cost | Accuracy |
|------------|-------------|----------|
| Barebones (this one) | $0 | ~30% |
| Example (GPT-4o) | ~$0.50/task | ~60% |
| Optimized GPT-4o | ~$2/task | ~80% |

## Files

- `barebones_white_agent.py` - The agent code
- `test_barebones_agent.sh` - Quick local test
- `BAREBONES_AGENT.md` - This file

## Ready to Battle!

```bash
# Test locally first
./test_barebones_agent.sh

# Then deploy and register on AgentBeats
# Your barebones agent is ready to compete! 🥊
```

---

**Pro Tip**: This agent is great for:
- 🧪 Testing the platform
- 📊 Establishing a baseline score
- 🎓 Learning the A2A protocol
- 💰 Zero-cost experimentation

Good luck in your battles! 🚀
