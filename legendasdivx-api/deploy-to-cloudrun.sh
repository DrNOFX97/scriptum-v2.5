#!/bin/bash
set -e

# Configuration
PROJECT_ID="scriptum-v2-50"
SERVICE_NAME="legendasdivx-api"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying LegendasDivx API to Cloud Run${NC}"
echo ""

# Load environment variables from .env
if [ -f .env ]; then
    echo -e "${GREEN}✓ Loading credentials from .env${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found!"
    exit 1
fi

# Check if credentials are set
if [ -z "$LEGENDASDIVX_USER" ] || [ -z "$LEGENDASDIVX_PASS" ]; then
    echo "❌ LegendasDivx credentials not set in .env file!"
    exit 1
fi

# Build and push image
echo -e "${BLUE}📦 Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# Deploy to Cloud Run
echo -e "${BLUE}☁️  Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --allow-unauthenticated \
    --set-env-vars "LEGENDASDIVX_USER=${LEGENDASDIVX_USER},LEGENDASDIVX_PASS=${LEGENDASDIVX_PASS},API_HOST=0.0.0.0,API_PORT=8080,API_RELOAD=false,MAX_REQUESTS_PER_MINUTE=10,REQUEST_DELAY_SECONDS=3,CACHE_TTL_HOURS=24,DATABASE_PATH=/data/subtitles.db,LOG_LEVEL=INFO" \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo ""
echo -e "${BLUE}Testing health endpoint...${NC}"
curl -s "${SERVICE_URL}/health" | jq .

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Update backend config to use: ${SERVICE_URL}"
echo "2. Test subtitle search with the new endpoint"
