#!/bin/bash
# Quick deployment script for Google Cloud Run

set -e  # Exit on error

echo "🚀 CRMArena-Pro AgentBeats Deployment to Google Cloud Run"
echo "=========================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get or set project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "📝 No project configured. Please enter your Google Cloud Project ID:"
    read -r PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

echo "📦 Using project: $PROJECT_ID"

# Configuration
SERVICE_NAME="crmarena-green-agent"
REGION="us-central1"

# Check if .env exists for reference
if [ ! -f .env ]; then
    echo "⚠️  Warning: No .env file found. You'll need to set up secrets manually."
    echo "Would you like to create secrets now? (y/n)"
    read -r CREATE_SECRETS

    if [ "$CREATE_SECRETS" = "y" ]; then
        echo "📝 Creating secrets in Google Cloud Secret Manager..."

        # Prompt for each secret
        echo "Enter SALESFORCE_USERNAME:"
        read -r SF_USER
        echo -n "$SF_USER" | gcloud secrets create SALESFORCE_USERNAME --data-file=- 2>/dev/null || \
            echo -n "$SF_USER" | gcloud secrets versions add SALESFORCE_USERNAME --data-file=-

        echo "Enter SALESFORCE_PASSWORD:"
        read -rs SF_PASS
        echo
        echo -n "$SF_PASS" | gcloud secrets create SALESFORCE_PASSWORD --data-file=- 2>/dev/null || \
            echo -n "$SF_PASS" | gcloud secrets versions add SALESFORCE_PASSWORD --data-file=-

        echo "Enter SALESFORCE_SECURITY_TOKEN:"
        read -r SF_TOKEN
        echo -n "$SF_TOKEN" | gcloud secrets create SALESFORCE_SECURITY_TOKEN --data-file=- 2>/dev/null || \
            echo -n "$SF_TOKEN" | gcloud secrets versions add SALESFORCE_SECURITY_TOKEN --data-file=-

        # B2B
        echo "Enter SALESFORCE_USERNAME_B2B:"
        read -r SF_USER_B2B
        echo -n "$SF_USER_B2B" | gcloud secrets create SALESFORCE_USERNAME_B2B --data-file=- 2>/dev/null || \
            echo -n "$SF_USER_B2B" | gcloud secrets versions add SALESFORCE_USERNAME_B2B --data-file=-

        echo "Enter SALESFORCE_PASSWORD_B2B:"
        read -rs SF_PASS_B2B
        echo
        echo -n "$SF_PASS_B2B" | gcloud secrets create SALESFORCE_PASSWORD_B2B --data-file=- 2>/dev/null || \
            echo -n "$SF_PASS_B2B" | gcloud secrets versions add SALESFORCE_PASSWORD_B2B --data-file=-

        echo "Enter SALESFORCE_SECURITY_TOKEN_B2B:"
        read -r SF_TOKEN_B2B
        echo -n "$SF_TOKEN_B2B" | gcloud secrets create SALESFORCE_SECURITY_TOKEN_B2B --data-file=- 2>/dev/null || \
            echo -n "$SF_TOKEN_B2B" | gcloud secrets versions add SALESFORCE_SECURITY_TOKEN_B2B --data-file=-

        # B2C
        echo "Enter SALESFORCE_USERNAME_B2C:"
        read -r SF_USER_B2C
        echo -n "$SF_USER_B2C" | gcloud secrets create SALESFORCE_USERNAME_B2C --data-file=- 2>/dev/null || \
            echo -n "$SF_USER_B2C" | gcloud secrets versions add SALESFORCE_USERNAME_B2C --data-file=-

        echo "Enter SALESFORCE_PASSWORD_B2C:"
        read -rs SF_PASS_B2C
        echo
        echo -n "$SF_PASS_B2C" | gcloud secrets create SALESFORCE_PASSWORD_B2C --data-file=- 2>/dev/null || \
            echo -n "$SF_PASS_B2C" | gcloud secrets versions add SALESFORCE_PASSWORD_B2C --data-file=-

        echo "Enter SALESFORCE_SECURITY_TOKEN_B2C:"
        read -r SF_TOKEN_B2C
        echo -n "$SF_TOKEN_B2C" | gcloud secrets create SALESFORCE_SECURITY_TOKEN_B2C --data-file=- 2>/dev/null || \
            echo -n "$SF_TOKEN_B2C" | gcloud secrets versions add SALESFORCE_SECURITY_TOKEN_B2C --data-file=-

        # OpenAI
        echo "Enter OPENAI_API_KEY:"
        read -rs OPENAI_KEY
        echo
        echo -n "$OPENAI_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=- 2>/dev/null || \
            echo -n "$OPENAI_KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=-

        echo "✅ Secrets created!"
    fi
fi

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet

# Build container
echo "🏗️  Building container image..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-secrets "SALESFORCE_USERNAME=SALESFORCE_USERNAME:latest,SALESFORCE_PASSWORD=SALESFORCE_PASSWORD:latest,SALESFORCE_SECURITY_TOKEN=SALESFORCE_SECURITY_TOKEN:latest,SALESFORCE_USERNAME_B2B=SALESFORCE_USERNAME_B2B:latest,SALESFORCE_PASSWORD_B2B=SALESFORCE_PASSWORD_B2B:latest,SALESFORCE_SECURITY_TOKEN_B2B=SALESFORCE_SECURITY_TOKEN_B2B:latest,SALESFORCE_USERNAME_B2C=SALESFORCE_USERNAME_B2C:latest,SALESFORCE_PASSWORD_B2C=SALESFORCE_PASSWORD_B2C:latest,SALESFORCE_SECURITY_TOKEN_B2C=SALESFORCE_SECURITY_TOKEN_B2C:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)')

echo ""
echo "=========================================================="
echo "✅ Deployment Complete!"
echo "=========================================================="
echo ""
echo "🌐 Controller URL: $SERVICE_URL"
echo ""
echo "Test your deployment:"
echo "  curl $SERVICE_URL/.well-known/agent-card.json"
echo ""
echo "Next steps:"
echo "  1. Test the controller URL above"
echo "  2. Register on AgentBeats platform with this URL"
echo "  3. Run your first hosted assessment!"
echo ""
echo "=========================================================="
