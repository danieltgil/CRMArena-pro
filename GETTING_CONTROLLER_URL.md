# Getting Your Controller URL for AgentBeats

## What You Need

To register your CRMArena-Pro green agent on AgentBeats, you need a **publicly accessible HTTPS URL** that hosts the AgentBeats controller.

## TL;DR - Fastest Path

```bash
# Option 1: One-command deployment to Google Cloud Run (Recommended)
./deploy-to-cloudrun.sh

# Option 2: Railway.app (easiest, but may have limits)
# - Push to GitHub
# - Connect to railway.app
# - Deploy (automatic)
```

---

## What is the Controller?

The **AgentBeats Controller** is a service that:
- Manages your green agent (start/stop/reset)
- Provides a web UI for monitoring
- Proxies requests to your agent
- Handles health checks

Think of it as a wrapper around your green agent that makes it platform-ready.

---

## Three Deployment Options

### 🥇 Option 1: Google Cloud Run (Best for Most Users)

**Pros:**
- ✅ Free tier (2M requests/month)
- ✅ Automatic HTTPS
- ✅ One-command deployment
- ✅ Scales automatically
- ✅ Pay only when used

**Steps:**

1. **Install gcloud CLI**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk

   # Or download: https://cloud.google.com/sdk/docs/install
   ```

2. **Run deployment script**
   ```bash
   ./deploy-to-cloudrun.sh
   ```

3. **Follow prompts** - The script will:
   - Configure your Google Cloud project
   - Create secrets for credentials
   - Build Docker container
   - Deploy to Cloud Run
   - Give you the controller URL

4. **Get your URL**
   ```
   ✅ Deployment Complete!
   🌐 Controller URL: https://crmarena-green-agent-xyz123-uc.a.run.app
   ```

**That's it!** Your controller URL is ready.

**Time:** ~10 minutes (first time)
**Cost:** Free for light usage (~$0-5/month)

---

### 🥈 Option 2: Railway.app (Easiest)

**Pros:**
- ✅ Super easy (no CLI needed)
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Built-in HTTPS

**Steps:**

1. **Push code to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Add AgentBeats integration"
   git push
   ```

2. **Sign up at railway.app**
   - Visit https://railway.app
   - Sign in with GitHub

3. **Create new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your CRMArena-pro repo

4. **Add environment variables**

   In Railway dashboard, go to "Variables" tab and add:

   ```
   SALESFORCE_USERNAME=...
   SALESFORCE_PASSWORD=...
   SALESFORCE_SECURITY_TOKEN=...
   SALESFORCE_USERNAME_B2B=...
   SALESFORCE_PASSWORD_B2B=...
   SALESFORCE_SECURITY_TOKEN_B2B=...
   SALESFORCE_USERNAME_B2C=...
   SALESFORCE_PASSWORD_B2C=...
   SALESFORCE_SECURITY_TOKEN_B2C=...
   OPENAI_API_KEY=...
   ```

5. **Deploy**
   - Railway auto-detects `Procfile` and deploys
   - Wait for deployment (2-3 minutes)

6. **Get your URL**
   - Click "Settings" → "Domains"
   - Your URL: `https://your-project.up.railway.app`

**Time:** ~5 minutes
**Cost:** Free tier ($5 credit/month) or $20/month

---

### 🥉 Option 3: Your Own VPS

**Pros:**
- ✅ Full control
- ✅ Fixed monthly cost
- ✅ Can run 24/7

**Cons:**
- ❌ More setup required
- ❌ Need to manage server
- ❌ Need domain + SSL certificate

**Quick Steps:**

1. **Get a VPS** (DigitalOcean, Linode, AWS EC2, etc.)
   - Ubuntu 22.04
   - 2GB RAM minimum
   - Public IP

2. **Point domain to server**
   ```
   crmarena.yourdomain.com → 123.45.67.89
   ```

3. **SSH and install**
   ```bash
   ssh root@your-server-ip

   # Install dependencies
   apt update && apt install python3.10 python3-pip nginx certbot -y

   # Clone repo
   git clone https://github.com/yourusername/CRMArena-pro.git
   cd CRMArena-pro

   # Install Python packages
   pip install -r requirements-agentbeats.txt

   # Create .env with credentials
   nano .env  # paste your credentials

   # Set up systemd service (see DEPLOYMENT_GUIDE.md)
   # Set up Nginx + SSL (see DEPLOYMENT_GUIDE.md)
   ```

4. **Get SSL certificate**
   ```bash
   certbot --nginx -d crmarena.yourdomain.com
   ```

5. **Your URL:** `https://crmarena.yourdomain.com`

**Time:** ~30-60 minutes
**Cost:** ~$6-12/month

See full instructions in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## After You Get Your Controller URL

### 1. Test It

```bash
# Replace with your actual URL
curl https://your-controller-url.com/.well-known/agent-card.json
```

Expected response:
```json
{
  "name": "CRMArena-Pro Green Agent",
  "description": "Assessment agent for evaluating CRM task performance...",
  ...
}
```

### 2. Register on AgentBeats

Visit the AgentBeats platform and fill out the form:

**Agent Registration Form:**
```
┌─────────────────────────────────────────────┐
│ Register New Green Agent                    │
├─────────────────────────────────────────────┤
│                                              │
│ Controller URL:                             │
│ https://your-controller-url.com             │
│                                              │
│ Agent Name:                                 │
│ CRMArena-Pro Green Agent                    │
│                                              │
│ Description:                                │
│ Assessment agent for CRM tasks using        │
│ Salesforce. Evaluates agents on customer   │
│ service, sales, and privacy awareness.      │
│                                              │
│ Tags:                                       │
│ crm, salesforce, evaluation, tool-use       │
│                                              │
│ Agent Type:                                 │
│ ● Green (Assessor)                          │
│ ○ White (Assessee)                          │
│                                              │
│           [Register Agent]                  │
└─────────────────────────────────────────────┘
```

### 3. Platform Integration

After registration, AgentBeats will:
- ✅ Read your `.agentbeats.json` configuration
- ✅ Set up predefined assessments (B2B, B2C, Interactive, Privacy)
- ✅ Enable your agent on the platform
- ✅ Make it available for assessments

### 4. Run Your First Assessment

From the AgentBeats dashboard:

1. Navigate to "Assessments"
2. Click "New Assessment"
3. Select "CRMArena-Pro B2B" (or another variant)
4. Choose a white agent to test
5. Click "Run Assessment"

---

## Troubleshooting

### "Can't access controller URL"

**Check if service is running:**

```bash
# Google Cloud Run
gcloud run services describe crmarena-green-agent --region us-central1

# VPS
sudo systemctl status crmarena-green-agent
```

### "Agent card returns 404"

Make sure the AgentBeats controller is running, not just the green agent directly.

**Test locally first:**
```bash
agentbeats run_ctrl
# Visit http://localhost:8000
```

### "Salesforce authentication failed"

Check that your secrets/environment variables are correctly set:

```bash
# Google Cloud Run - view configuration
gcloud run services describe crmarena-green-agent \
  --region us-central1 \
  --format yaml

# VPS - check environment file
cat /path/to/CRMArena-pro/.env
```

### "Out of memory / crashes"

Increase memory allocation:

```bash
# Google Cloud Run
gcloud run services update crmarena-green-agent \
  --region us-central1 \
  --memory 4Gi

# VPS - add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## What Happens Next?

Once registered on AgentBeats:

1. **Your green agent is live** 🎉
2. **Others can test their agents** using your benchmark
3. **Results appear on leaderboards** automatically
4. **You see usage analytics** in the AgentBeats dashboard
5. **Community can compare agents** fairly and reproducibly

---

## Cost Summary

| Option | Setup Time | Monthly Cost | Best For |
|--------|-----------|--------------|----------|
| **Google Cloud Run** | 10 min | $0-5 | Most users |
| **Railway.app** | 5 min | Free-$20 | Quick testing |
| **VPS** | 60 min | $6-12 | Full control |

**Recommendation:** Start with Google Cloud Run. It's free for light usage and easiest to scale.

---

## Quick Reference

### Google Cloud Run Deployment
```bash
./deploy-to-cloudrun.sh
```

### Manual Deployment
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

### Test Controller
```bash
curl https://your-url.com/.well-known/agent-card.json
```

### View Logs (Google Cloud Run)
```bash
gcloud run services logs read crmarena-green-agent --region us-central1
```

### Update Secrets (Google Cloud Run)
```bash
echo -n "new_value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

---

## Need Help?

- **Deployment issues**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **AgentBeats questions**: Visit agentbeats.org/support
- **CRMArena issues**: Open an issue on GitHub

---

**You're almost there!** Just deploy, get your URL, and register. 🚀
