#!/bin/bash
# Automated deployment script for Scriptum API
# Usage: ./deploy.sh [environment]
# environment: production (default) | staging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_ID="ligafaro-8000"
SERVICE_NAME="scriptum-v2-5"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Scriptum API Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Find gcloud
GCLOUD_PATH=$(which gcloud 2>/dev/null || echo "/usr/local/share/google-cloud-sdk/bin/gcloud")
if [ ! -f "$GCLOUD_PATH" ]; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Using gcloud: ${GCLOUD_PATH}${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Will use Cloud Build.${NC}"
    USE_CLOUD_BUILD=true
else
    USE_CLOUD_BUILD=false
fi

# Step 2: Set active project
echo -e "${YELLOW}🔧 Setting active project...${NC}"
${GCLOUD_PATH} config set project ${PROJECT_ID}

# Step 3: Build Docker image
echo ""
echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
echo "This may take a few minutes..."
echo ""

${GCLOUD_PATH} builds submit --tag ${IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful!${NC}"

# Step 4: Deploy to Cloud Run
echo ""
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
echo ""

${GCLOUD_PATH} run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --update-env-vars "PRODUCTION_CORS=true,ENVIRONMENT=${ENVIRONMENT},LEGENDASDIVX_API_URL=https://legendasdivx-api-315653817267.europe-west1.run.app"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get service URL
SERVICE_URL=$(${GCLOUD_PATH} run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')
echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"
echo ""

# Step 5: Test deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
HEALTH_CHECK=$(curl -s ${SERVICE_URL}/health | jq -r '.data.status' 2>/dev/null || echo "error")

if [ "$HEALTH_CHECK" = "ok" ]; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed. Please verify manually.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the API: ${SERVICE_URL}/health"
echo "2. View logs: ${GCLOUD_PATH} run services logs read ${SERVICE_NAME} --region=${REGION}"
echo "3. Monitor: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}"
echo ""
