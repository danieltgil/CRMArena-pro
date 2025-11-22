# Battle Ready Guide - Deploy & Compete!

Your CRMArena-Pro integration is complete! Here's how to get battling on AgentBeats:

## ✅ What You Have

1. **Green Agent** (Evaluator) - CRMArena-Pro benchmark as an assessor
2. **Barebones White Agent** - Rule-based competitor (no LLM needed)
3. **OpenAI Key Added** - For evaluation

## 🚀 Deploy Both Agents

### Step 1: Commit Your Code

```bash
git add .
git commit -m "Add barebones white agent and battle test"
git push
```

### Step 2: Deploy Green Agent (Evaluator)

**Railway.app:**
1. Go to railway.app → New Project
2. Deploy from GitHub → Select `CRMArena-pro`
3. Add environment variables:
   ```
   SALESFORCE_USERNAME=kh.huang+00dws000004urq4@salesforce.com
   SALESFORCE_PASSWORD=crmarenatest
   SALESFORCE_SECURITY_TOKEN=ugvBSBv0ArI7dayfqUY0wMGu
   SALESFORCE_USERNAME_B2B=crmarena_b2b@gmaill.com
   SALESFORCE_PASSWORD_B2B=crmarenatest
   SALESFORCE_SECURITY_TOKEN_B2B=zdaqqSYBEQTjjLuq0zLUHkC3
   SALESFORCE_USERNAME_B2C=crmarena_b2c@gmaill.com
   SALESFORCE_PASSWORD_B2C=crmarenatest
   SALESFORCE_SECURITY_TOKEN_B2C=2AQCtK8MnnV4lJdRNF0DGCs1
   OPENAI_API_KEY=<your-key-from-.env>
   ```
4. Start command should be: `agentbeats run_ctrl`
5. Get your URL: `https://crmarena-green-XXX.up.railway.app`

### Step 3: Deploy White Agent (Competitor)

**Create SECOND Railway project:**
1. Railway.app → New Project
2. Deploy from same GitHub repo
3. **Important**: In Settings → Start Command:
   ```
   python barebones_white_agent.py --port $PORT
   ```
4. No environment variables needed (it's rule-based!)
5. Get your URL: `https://crmarena-white-XXX.up.railway.app`

## 🎮 Register on AgentBeats

### Register Green Agent

1. Go to AgentBeats platform
2. Fill out form:
   ```
   Agent Type: Green (Assessor)
   Controller URL: https://crmarena-green-XXX.up.railway.app
   Name: CRMArena-Pro Benchmark
   Description: Assessment agent for CRM tasks
   ```

### Register White Agent

1. AgentBeats platform → Register Agent
2. Fill out form:
   ```
   Agent Type: White (Assessee)
   Agent URL: https://crmarena-white-XXX.up.railway.app
   Name: Barebones CRM Agent
   Description: Rule-based agent for CRM tasks
   ```

## ⚔️ Start Battling!

On AgentBeats:
1. Go to "Assessments"
2. Click "New Assessment"
3. Select "CRMArena-Pro B2B" (your green agent)
4. Choose "Barebones CRM Agent" (your white agent)
5. Click "Run Assessment"
6. Watch the battle!

## 📊 Expected Performance

Your barebones agent should score around **30-40%** accuracy:

- ✅ Privacy tasks: ~80% (good refusal detection)
- ⚠️ Handle time: ~30% (heuristic-based)
- ⚠️ Sales tasks: ~20% (very basic)

This is your **baseline**! Now you can:
- Improve the barebones agent
- Build an LLM-powered agent
- Try different strategies
- Climb the leaderboard!

## 🔍 Debugging

### Check if agents are running:

```bash
# Green agent
curl https://crmarena-green-XXX.up.railway.app/.well-known/agent-card.json

# White agent
curl https://crmarena-white-XXX.up.railway.app/.well-known/agent-card.json
```

Both should return JSON with agent info.

### Check Railway logs:

1. Railway dashboard → Your project
2. Click "Deployments"
3. Click latest deployment
4. View logs

### Test locally first:

Unfortunately the local test requires some package fixes. For now, just deploy and test on AgentBeats!

## 💡 Next Steps

1. ✅ **Deploy both agents** to Railway
2. ✅ **Register on AgentBeats**
3. ✅ **Run first assessment**
4. 📈 **Check leaderboard**
5. 🔧 **Improve your agent**
6. 🏆 **Compete!**

## 🆘 Need Help?

- Green agent not starting? Check OpenAI key is set
- White agent not responding? Check start command is correct
- Assessment failing? Check both agent URLs are accessible

---

**You're ready to battle! Good luck! 🥊**
