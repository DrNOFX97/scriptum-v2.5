#!/bin/bash

# Deploy Scriptum API to Google Cloud Run
# Usage: ./deploy-gcp.sh

set -e

# Configuration
PROJECT_ID="scriptum-api"  # Change this to your GCP project ID
SERVICE_NAME="scriptum-api"
REGION="europe-west1"  # Frankfurt region (closest to Portugal)
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Scriptum API to Google Cloud Run..."
echo "📦 Project: ${PROJECT_ID}"
echo "🌍 Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Set GCP project
echo "📋 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push Docker image
echo "🔨 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "DEBUG=False" \
    --set-env-vars "TMDB_API_KEY=${TMDB_API_KEY}" \
    --set-env-vars "OPENSUBTITLES_API_KEY=${OPENSUBTITLES_API_KEY}" \
    --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Next steps:"
echo "   1. Update frontend API_BASE to: ${SERVICE_URL}"
echo "   2. Test the API: curl ${SERVICE_URL}/health"
echo ""
