"""
Create Cloud Storage bucket using service account credentials
"""
import os
from google.cloud import storage

def create_bucket():
    """Create the scriptum-uploads bucket"""
    try:
        client = storage.Client()
        bucket_name = 'scriptum-uploads'
        
        # Check if bucket exists
        try:
            bucket = client.get_bucket(bucket_name)
            print(f"✅ Bucket already exists: gs://{bucket_name}")
            return bucket
        except Exception:
            pass
        
        # Create bucket
        bucket = client.create_bucket(
            bucket_name,
            location='europe-west1'
        )
        
        # Set CORS
        bucket.cors = [
            {
                "origin": ["https://scriptum-v2-50.web.app", "http://localhost:5173"],
                "method": ["GET", "PUT", "POST"],
                "responseHeader": ["Content-Type"],
                "maxAgeSeconds": 3600
            }
        ]
        bucket.patch()
        
        # Set lifecycle (auto-delete after 7 days)
        bucket.add_lifecycle_delete_rule(age=7)
        bucket.patch()
        
        print(f"✅ Bucket created: gs://{bucket_name}")
        print(f"📍 Region: europe-west1")
        print(f"🔄 CORS enabled")
        print(f"🗑️  Auto-delete: 7 days")
        
        return bucket
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible solutions:")
        print("1. Grant yourself 'Storage Admin' role in IAM")
        print("2. Use gcloud: gcloud projects add-iam-policy-binding scriptum-v2-5 \\")
        print("   --member='user:YOUR_EMAIL' --role='roles/storage.admin'")
        return None

if __name__ == '__main__':
    create_bucket()
