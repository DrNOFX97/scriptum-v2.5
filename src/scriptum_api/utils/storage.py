"""
Cloud Storage utilities for large file uploads
"""
import os
from datetime import timedelta, datetime
from google.cloud import storage
import google.auth
from google.auth.transport import requests as google_requests
from google.auth import iam
from google.auth import compute_engine

BUCKET_NAME = os.getenv('STORAGE_BUCKET', 'scriptum-uploads')

def get_storage_client():
    """Get Cloud Storage client"""
    return storage.Client()

def generate_upload_signed_url(filename: str, content_type: str = 'video/*') -> dict:
    """
    Generate signed URL for direct upload to Cloud Storage using IAM

    Args:
        filename: Original filename
        content_type: MIME type

    Returns:
        dict with signed_url and blob_name
    """
    import uuid

    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)

    # Generate unique blob name
    blob_name = f"uploads/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex}_{filename}"
    blob = bucket.blob(blob_name)

    # Get credentials and signing method
    credentials, project = google.auth.default()

    # For Cloud Run, we need to use IAM signBlob API
    if isinstance(credentials, compute_engine.Credentials):
        # Get service account email
        auth_request = google_requests.Request()
        credentials.refresh(auth_request)
        service_account_email = credentials.service_account_email

        # Create signing credentials using IAM
        signing_credentials = iam.Signer(
            auth_request,
            credentials,
            service_account_email
        )

        url = blob.generate_signed_url(
            version='v4',
            expiration=timedelta(hours=1),
            method='PUT',
            content_type=content_type,
            credentials=signing_credentials,
        )
    else:
        # Use default signing for local development
        url = blob.generate_signed_url(
            version='v4',
            expiration=timedelta(hours=1),
            method='PUT',
            content_type=content_type,
        )

    return {
        'signed_url': url,
        'blob_name': blob_name,
        'bucket': BUCKET_NAME
    }

def get_blob_download_url(blob_name: str) -> str:
    """Get temporary download URL for a blob"""
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)

    return blob.generate_signed_url(
        version='v4',
        expiration=timedelta(hours=24),
        method='GET'
    )

def download_blob_to_file(blob_name: str, destination_path: str):
    """Download blob to local file"""
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)

    blob.download_to_filename(destination_path)
    return destination_path

def delete_blob(blob_name: str):
    """Delete blob from storage"""
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.delete()
