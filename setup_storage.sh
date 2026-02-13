#!/bin/bash

# Script to setup Cloud Storage for large file uploads

PROJECT_ID="scriptum-v2-50"
BUCKET_NAME="scriptum-uploads"
REGION="europe-west1"

echo "🪣 Creating Cloud Storage bucket..."

# Create bucket
gcloud storage buckets create gs://${BUCKET_NAME} \
    --project=${PROJECT_ID} \
    --location=${REGION} \
    --uniform-bucket-level-access

# Set CORS configuration
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["https://scriptum-v2-50.web.app", "https://scriptum-v2-50.firebaseapp.com", "http://localhost:5173"],
    "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
    "maxAgeSeconds": 3600
  }
]
EOF

gcloud storage buckets update gs://${BUCKET_NAME} --cors-file=/tmp/cors.json

# Set lifecycle (delete files older than 7 days)
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF

gcloud storage buckets update gs://${BUCKET_NAME} --lifecycle-file=/tmp/lifecycle.json

echo "✅ Bucket created: gs://${BUCKET_NAME}"
echo "🌍 Region: ${REGION}"
echo "🔄 CORS enabled for Firebase + localhost"
echo "🗑️  Auto-delete files after 7 days"
