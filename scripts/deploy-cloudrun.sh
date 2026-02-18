#!/bin/bash
# Deploy to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e

# Configuration
PROJECT_ID=${1:-"your-gcp-project"}
REGION=${2:-"us-central1"}
SERVICE_NAME="constructio-mcp-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Required environment variables
REQUIRED_VARS=(
  "GCS_BUCKET"
  "FIRESTORE_COLLECTION"
  "GCP_PROJECT_ID"
)

echo "🚀 Deploying ${SERVICE_NAME} to Cloud Run..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Build container image
echo "📦 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCS_BUCKET=${GCS_BUCKET},FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION:-generators},GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "   Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Next steps:"
echo "   1. Test the service: curl ${SERVICE_URL}/v1/generators"
echo "   2. Set up API Gateway for authentication (see scripts/deploy-api-gateway.sh)"
