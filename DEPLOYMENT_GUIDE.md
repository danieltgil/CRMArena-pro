# AgentBeats Deployment Guide for CRMArena-Pro

This guide walks you through deploying the CRMArena-Pro green agent to get a public controller URL for AgentBeats.

## Prerequisites

- Google Cloud account (free tier available) OR any VPS provider
- Salesforce credentials (you already have these from .env)
- OpenAI API key
- `gcloud` CLI installed (for Google Cloud)

## Option A: Google Cloud Run (Recommended)

### Why Cloud Run?
- ✅ Free tier (2 million requests/month)
- ✅ Automatic HTTPS
- ✅ Auto-scaling
- ✅ No server management
- ✅ Pay only when used

### Steps

#### 1. Install Google Cloud SDK

```bash
# macOS
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 2. Create Dockerfile

We'll use Docker instead of buildpacks for better control:

```bash
# Create Dockerfile in project root
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-agentbeats.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements-agentbeats.txt

# Copy application code
COPY . .

# Make run.sh executable
RUN chmod +x run.sh

# Expose port (Cloud Run will set PORT env var)
ENV PORT=8080
ENV AGENT_PORT=8080

# Run the controller
CMD ["agentbeats", "run_ctrl"]
EOF
```

#### 3. Create .dockerignore

```bash
cat > .dockerignore << 'EOF'
.env
.env.example
*.pyc
__pycache__
*.egg-info
.git
.gitignore
logs/
results/
*.md
examples/
docs/
EOF
```

#### 4. Set Up Environment Variables in Cloud

You can't commit your .env file, so we'll use Secret Manager:

```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create secrets (replace with your actual values)
echo -n "your_salesforce_username" | gcloud secrets create SALESFORCE_USERNAME --data-file=-
echo -n "your_salesforce_password" | gcloud secrets create SALESFORCE_PASSWORD --data-file=-
echo -n "your_salesforce_token" | gcloud secrets create SALESFORCE_SECURITY_TOKEN --data-file=-

# B2B credentials
echo -n "your_b2b_username" | gcloud secrets create SALESFORCE_USERNAME_B2B --data-file=-
echo -n "your_b2b_password" | gcloud secrets create SALESFORCE_PASSWORD_B2B --data-file=-
echo -n "your_b2b_token" | gcloud secrets create SALESFORCE_SECURITY_TOKEN_B2B --data-file=-

# B2C credentials
echo -n "your_b2c_username" | gcloud secrets create SALESFORCE_USERNAME_B2C --data-file=-
echo -n "your_b2c_password" | gcloud secrets create SALESFORCE_PASSWORD_B2C --data-file=-
echo -n "your_b2c_token" | gcloud secrets create SALESFORCE_SECURITY_TOKEN_B2C --data-file=-

# OpenAI API key
echo -n "your_openai_key" | gcloud secrets create OPENAI_API_KEY --data-file=-
```

#### 5. Build and Deploy

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export SERVICE_NAME=crmarena-green-agent
export REGION=us-central1

# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run with secrets
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-secrets "SALESFORCE_USERNAME=SALESFORCE_USERNAME:latest,SALESFORCE_PASSWORD=SALESFORCE_PASSWORD:latest,SALESFORCE_SECURITY_TOKEN=SALESFORCE_SECURITY_TOKEN:latest,SALESFORCE_USERNAME_B2B=SALESFORCE_USERNAME_B2B:latest,SALESFORCE_PASSWORD_B2B=SALESFORCE_PASSWORD_B2B:latest,SALESFORCE_SECURITY_TOKEN_B2B=SALESFORCE_SECURITY_TOKEN_B2B:latest,SALESFORCE_USERNAME_B2C=SALESFORCE_USERNAME_B2C:latest,SALESFORCE_PASSWORD_B2C=SALESFORCE_PASSWORD_B2C:latest,SALESFORCE_SECURITY_TOKEN_B2C=SALESFORCE_SECURITY_TOKEN_B2C:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

#### 6. Get Your Controller URL

After deployment completes, you'll see output like:

```
Service [crmarena-green-agent] revision [crmarena-green-agent-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://crmarena-green-agent-xyz123-uc.a.run.app
```

**This is your controller URL!** 🎉

Test it:

```bash
# Check if agent card is accessible
curl https://crmarena-green-agent-xyz123-uc.a.run.app/.well-known/agent-card.json
```

---

## Option B: Railway.app (Alternative - Very Easy)

Railway offers a simpler deployment with free tier.

### Steps

#### 1. Sign up at railway.app

Visit https://railway.app and sign up (free tier available)

#### 2. Create New Project

- Click "New Project"
- Select "Deploy from GitHub repo"
- Connect your GitHub account and select the CRMArena-pro repo

#### 3. Add Environment Variables

In Railway dashboard, go to Variables tab and add:

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

#### 4. Configure Build

Railway will auto-detect the Procfile. No additional configuration needed!

#### 5. Deploy

Click "Deploy" - Railway will build and deploy automatically.

Your controller URL will be: `https://your-project-name.up.railway.app`

---

## Option C: Any VPS (DigitalOcean, AWS EC2, etc.)

### Steps

#### 1. Provision a Server

- Ubuntu 22.04 or similar
- At least 2GB RAM
- Public IP address

#### 2. Set Up Domain (Optional but Recommended)

Point a domain/subdomain to your server's IP:

```
crmarena.yourdomain.com -> 123.45.67.89
```

#### 3. SSH into Server and Install

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Nginx
sudo apt install nginx -y

# Clone your repo
git clone https://github.com/yourusername/CRMArena-pro.git
cd CRMArena-pro

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-agentbeats.txt
```

#### 4. Set Up Environment Variables

```bash
# Create .env file
nano .env

# Add your credentials (paste from local .env)
# Save with Ctrl+X, Y, Enter
```

#### 5. Create systemd Service

```bash
sudo nano /etc/systemd/system/crmarena-green-agent.service
```

Paste:

```ini
[Unit]
Description=CRMArena Green Agent
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/CRMArena-pro
Environment="PATH=/home/YOUR_USERNAME/CRMArena-pro/venv/bin"
EnvironmentFile=/home/YOUR_USERNAME/CRMArena-pro/.env
ExecStart=/home/YOUR_USERNAME/CRMArena-pro/venv/bin/agentbeats run_ctrl
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username.

```bash
# Enable and start service
sudo systemctl enable crmarena-green-agent
sudo systemctl start crmarena-green-agent

# Check status
sudo systemctl status crmarena-green-agent
```

#### 6. Configure Nginx with SSL

```bash
# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y

# Configure Nginx
sudo nano /etc/nginx/sites-available/crmarena
```

Paste:

```nginx
server {
    listen 80;
    server_name crmarena.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/crmarena /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d crmarena.yourdomain.com
```

Your controller URL: `https://crmarena.yourdomain.com`

---

## Step 3: Verify Your Deployment

Test your controller URL:

```bash
# Replace with your actual URL
export CONTROLLER_URL="https://your-url-here.com"

# Check agent card
curl $CONTROLLER_URL/.well-known/agent-card.json

# Should return JSON with agent info
```

Expected response:

```json
{
  "name": "CRMArena-Pro Green Agent",
  "description": "Assessment agent for evaluating CRM task performance...",
  "capabilities": {
    "streaming": false,
    "task_types": ["assessment", "evaluation"]
  }
}
```

---

## Step 4: Register on AgentBeats Platform

Once you have your controller URL:

1. **Visit AgentBeats Platform**: Go to https://agentbeats.org (or the actual platform URL)

2. **Register Your Agent**: Fill out the registration form:

```
Agent Type: Green Agent (Assessor)
Controller URL: https://your-controller-url.com
Agent Name: CRMArena-Pro Green Agent
Description: Assessment agent for CRM tasks using Salesforce
Tags: crm, salesforce, evaluation, tool-use
```

3. **Configure Assessments**: The platform will read your `.agentbeats.json` and set up predefined assessments:
   - CRMArena-Pro B2B
   - CRMArena-Pro B2C
   - CRMArena-Pro Interactive
   - CRMArena-Pro Privacy

4. **Test Integration**: Run a test assessment from the platform to verify everything works.

---

## Cost Estimates

### Google Cloud Run (Recommended)
- **Free Tier**: 2M requests/month, 360,000 GB-seconds/month
- **Typical Usage**: ~$0-5/month for light usage
- **Pay-as-you-go**: Only charged when assessments run

### Railway.app
- **Free Tier**: $5 credit/month (usually enough for testing)
- **Pro**: $20/month for more resources

### VPS (DigitalOcean/AWS)
- **Basic Droplet**: $6-12/month (always running)
- **No usage-based pricing**: Same cost whether used or not

**Recommendation**: Start with Google Cloud Run for cost-effectiveness.

---

## Troubleshooting

### "Service Unavailable" Error

Check logs:

```bash
# Google Cloud Run
gcloud run services logs read crmarena-green-agent --region us-central1

# VPS
sudo journalctl -u crmarena-green-agent -f
```

### "Agent Card Not Found"

Make sure the controller is running:

```bash
# Check if port 8000/8080 is accessible
curl http://localhost:8000/.well-known/agent-card.json
```

### "Salesforce Login Failed"

Verify environment variables are set:

```bash
# Google Cloud Run
gcloud run services describe crmarena-green-agent --region us-central1

# VPS
sudo systemctl status crmarena-green-agent
```

### "Out of Memory"

Increase memory allocation:

```bash
# Google Cloud Run
gcloud run services update crmarena-green-agent \
  --region us-central1 \
  --memory 4Gi
```

---

## Security Best Practices

1. **Never Commit Credentials**: Use secret managers or environment variables
2. **Enable Authentication**: For production, add authentication to your controller
3. **Monitor Usage**: Set up billing alerts and usage monitoring
4. **Regular Updates**: Keep dependencies updated
5. **Backup Secrets**: Keep a secure backup of your credentials

---

## Next Steps After Deployment

1. ✅ Test your controller URL
2. ✅ Register on AgentBeats platform
3. ✅ Run first hosted assessment
4. ✅ Check leaderboards
5. ✅ Share your green agent with the community!

---

## Quick Reference Commands

```bash
# Google Cloud Run - Deploy
gcloud run deploy crmarena-green-agent \
  --image gcr.io/$PROJECT_ID/crmarena-green-agent \
  --region us-central1

# Google Cloud Run - View Logs
gcloud run services logs read crmarena-green-agent --region us-central1

# Google Cloud Run - Update Environment
gcloud run services update crmarena-green-agent \
  --update-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --region us-central1

# VPS - Restart Service
sudo systemctl restart crmarena-green-agent

# VPS - View Logs
sudo journalctl -u crmarena-green-agent -f

# Test Controller
curl https://your-url.com/.well-known/agent-card.json
```

---

You're all set! 🚀
