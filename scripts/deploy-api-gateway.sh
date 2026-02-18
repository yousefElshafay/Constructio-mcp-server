#!/bin/bash
# Deploy API Gateway configuration
# Usage: ./deploy-api-gateway.sh [PROJECT_ID] [REGION] [CLOUD_RUN_URL]

set -e

# Configuration
PROJECT_ID=${1:-"your-gcp-project"}
REGION=${2:-"us-central1"}
CLOUD_RUN_URL=${3}
API_ID="constructio-api"
API_GATEWAY_NAME="constructio-gateway"

echo "🔐 Deploying API Gateway with authentication..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get Cloud Run URL if not provided
if [ -z "$CLOUD_RUN_URL" ]; then
    echo "📡 Getting Cloud Run service URL..."
    CLOUD_RUN_URL=$(gcloud run services describe constructio-mcp-server --region ${REGION} --format 'value(status.url)')
    
    if [ -z "$CLOUD_RUN_URL" ]; then
        echo "❌ Could not find Cloud Run service. Deploy it first with scripts/deploy-cloudrun.sh"
        exit 1
    fi
    
    echo "   Found: ${CLOUD_RUN_URL}"
fi

# Update API Gateway config with Cloud Run URL
echo "📝 Updating API Gateway configuration..."
sed -i.bak "s|https://constructio-mcp-server-XXXXXX.a.run.app|${CLOUD_RUN_URL}|g" api-gateway-config.yaml
sed -i.bak "s|YOUR_PROJECT_ID|${PROJECT_ID}|g" api-gateway-config.yaml

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable apigateway.googleapis.com --project=${PROJECT_ID}
gcloud services enable servicemanagement.googleapis.com --project=${PROJECT_ID}
gcloud services enable servicecontrol.googleapis.com --project=${PROJECT_ID}

# Create API (if doesn't exist)
echo "🔧 Creating API Gateway API..."
if ! gcloud api-gateway apis describe ${API_ID} --project=${PROJECT_ID} 2>/dev/null; then
    gcloud api-gateway apis create ${API_ID} \
      --project=${PROJECT_ID}
fi

# Create API config
echo "📤 Uploading API configuration..."
CONFIG_NAME="${API_ID}-config-$(date +%s)"
gcloud api-gateway api-configs create ${CONFIG_NAME} \
  --api=${API_ID} \
  --openapi-spec=api-gateway-config.yaml \
  --project=${PROJECT_ID} \
  --backend-auth-service-account=$(gcloud run services describe constructio-mcp-server --region ${REGION} --format 'value(spec.template.spec.serviceAccountName)' || echo "default")

# Deploy gateway
echo "🚪 Deploying API Gateway..."
if ! gcloud api-gateway gateways describe ${API_GATEWAY_NAME} --location=${REGION} --project=${PROJECT_ID} 2>/dev/null; then
    # Create new gateway
    gcloud api-gateway gateways create ${API_GATEWAY_NAME} \
      --api=${API_ID} \
      --api-config=${CONFIG_NAME} \
      --location=${REGION} \
      --project=${PROJECT_ID}
else
    # Update existing gateway
    gcloud api-gateway gateways update ${API_GATEWAY_NAME} \
      --api=${API_ID} \
      --api-config=${CONFIG_NAME} \
      --location=${REGION} \
      --project=${PROJECT_ID}
fi

# Get gateway URL
GATEWAY_URL=$(gcloud api-gateway gateways describe ${API_GATEWAY_NAME} --location=${REGION} --project=${PROJECT_ID} --format='value(defaultHostname)')

echo ""
echo "✅ API Gateway deployed successfully!"
echo ""
echo "📋 Gateway Details:"
echo "   Gateway URL: https://${GATEWAY_URL}"
echo "   Cloud Run Backend: ${CLOUD_RUN_URL}"
echo ""
echo "🔐 Authentication:"
echo "   - All requests now require valid Firebase/Google auth tokens"
echo "   - Add 'Authorization: Bearer <token>' header to requests"
echo ""
echo "🧪 Test (requires valid token):"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' https://${GATEWAY_URL}/v1/generators"
