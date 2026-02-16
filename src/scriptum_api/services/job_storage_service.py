"""
Job storage service using Cloud Firestore.
Handles persistent storage of translation jobs across Cloud Run instances.
"""

from typing import Dict, Any, Optional
from google.cloud import firestore
from datetime import datetime, timedelta
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class JobStorageService:
    """
    Service for storing and retrieving translation jobs using Firestore.

    Solves the problem of in-memory storage not working across Cloud Run instances.
    Each job is stored as a document in the 'translation_jobs' collection.
    """

    def __init__(self):
        """Initialize Firestore client."""
        try:
            self.db = firestore.Client()
            self.collection = self.db.collection('translation_jobs')
            logger.info("JobStorageService initialized with Firestore")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}", exc_info=True)
            raise

    def create_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Create a new translation job.

        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary

        Returns:
            True if successful
        """
        try:
            # Add metadata
            job_data['created_at'] = firestore.SERVER_TIMESTAMP
            job_data['updated_at'] = firestore.SERVER_TIMESTAMP

            self.collection.document(job_id).set(job_data)
            logger.info(f"Created job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create job {job_id}: {e}", exc_info=True)
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a translation job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data dictionary or None if not found
        """
        try:
            doc = self.collection.document(job_id).get()

            if not doc.exists:
                logger.warning(f"Job {job_id} not found")
                return None

            job_data = doc.to_dict()
            logger.debug(f"Retrieved job {job_id}")
            return job_data

        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}", exc_info=True)
            return None

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a translation job.

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        try:
            # Add update timestamp
            updates['updated_at'] = firestore.SERVER_TIMESTAMP

            self.collection.document(job_id).update(updates)
            logger.debug(f"Updated job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}", exc_info=True)
            return False

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a translation job.

        Args:
            job_id: Job identifier

        Returns:
            True if successful
        """
        try:
            self.collection.document(job_id).delete()
            logger.info(f"Deleted job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}", exc_info=True)
            return False

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        Clean up jobs older than specified days.

        Args:
            days: Delete jobs older than this many days

        Returns:
            Number of jobs deleted
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Query old jobs
            old_jobs = self.collection.where('created_at', '<', cutoff).stream()

            deleted_count = 0
            for job in old_jobs:
                job.reference.delete()
                deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} jobs older than {days} days")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}", exc_info=True)
            return 0
