#!/bin/bash

# Get Cloud Run service account
PROJECT_ID="scriptum-v2-5"
SERVICE_ACCOUNT="315653817267-compute@developer.gserviceaccount.com"

echo "🔑 Granting signBlob permission to Cloud Run service account..."

# Grant Service Account Token Creator role
gcloud iam service-accounts add-iam-policy-binding \
  ${SERVICE_ACCOUNT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=${PROJECT_ID}

echo "✅ Permission granted!"
echo "Now the service account can sign URLs for Cloud Storage"
