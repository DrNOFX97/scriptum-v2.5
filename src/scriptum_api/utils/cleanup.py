"""
Automatic file cleanup manager.
Removes old uploaded files to prevent disk space issues.
"""

from pathlib import Path
from datetime import datetime, timedelta
import threading
import time
from typing import Optional
from .logger import setup_logger

logger = setup_logger(__name__)


class FileCleanupManager:
    """
    Manages automatic cleanup of old uploaded files.

    Features:
    - Configurable file age threshold
    - Background cleanup thread
    - Safe file deletion with error handling
    - Comprehensive logging

    Example:
        >>> cleanup = FileCleanupManager(upload_folder, max_age_hours=24)
        >>> cleanup.start_background_cleanup(interval_hours=1)
    """

    def __init__(self, upload_folder: Path, max_age_hours: int = 24):
        """
        Initialize file cleanup manager.

        Args:
            upload_folder: Path to uploads directory
            max_age_hours: Maximum file age in hours before deletion
        """
        self.upload_folder = Path(upload_folder)
        self.max_age = timedelta(hours=max_age_hours)
        self.running = False
        self._thread: Optional[threading.Thread] = None

        logger.info(f"FileCleanupManager initialized for {upload_folder}")
        logger.info(f"Files older than {max_age_hours} hours will be deleted")

    def cleanup_old_files(self) -> dict:
        """
        Remove files older than max_age.

        Returns:
            Dictionary with cleanup statistics:
                - deleted: Number of files deleted
                - failed: Number of failed deletions
                - total_size: Total size freed in bytes
        """
        if not self.upload_folder.exists():
            logger.warning(f"Upload folder does not exist: {self.upload_folder}")
            return {'deleted': 0, 'failed': 0, 'total_size': 0}

        now = datetime.now()
        deleted_count = 0
        failed_count = 0
        total_size_freed = 0

        logger.debug(f"Starting cleanup scan of {self.upload_folder}")

        try:
            for file_path in self.upload_folder.glob('*'):
                if not file_path.is_file():
                    continue

                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    file_age = now - file_mtime

                    if file_age > self.max_age:
                        # Get file size before deletion
                        file_size = file_path.stat().st_size

                        # Delete file
                        file_path.unlink()

                        deleted_count += 1
                        total_size_freed += file_size

                        logger.info(
                            f"Deleted old file: {file_path.name} "
                            f"(age: {file_age.days}d {file_age.seconds//3600}h, "
                            f"size: {file_size / (1024*1024):.2f}MB)"
                        )

                except PermissionError:
                    logger.error(f"Permission denied deleting {file_path.name}")
                    failed_count += 1

                except Exception as e:
                    logger.error(f"Failed to delete {file_path.name}: {e}")
                    failed_count += 1

        except Exception as e:
            logger.error(f"Error during cleanup scan: {e}", exc_info=True)

        # Log summary
        if deleted_count > 0 or failed_count > 0:
            size_mb = total_size_freed / (1024 * 1024)
            logger.info(
                f"Cleanup completed: {deleted_count} files deleted "
                f"({size_mb:.2f}MB freed), {failed_count} failed"
            )
        else:
            logger.debug("Cleanup completed: no old files found")

        return {
            'deleted': deleted_count,
            'failed': failed_count,
            'total_size': total_size_freed
        }

    def cleanup_by_extension(self, extensions: list[str]) -> int:
        """
        Delete files with specific extensions regardless of age.

        Args:
            extensions: List of file extensions (without dots)

        Returns:
            Number of files deleted
        """
        deleted_count = 0

        for ext in extensions:
            pattern = f"*.{ext}"
            for file_path in self.upload_folder.glob(pattern):
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted {ext} file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path.name}: {e}")

        return deleted_count

    def get_folder_stats(self) -> dict:
        """
        Get statistics about the upload folder.

        Returns:
            Dictionary with folder statistics
        """
        if not self.upload_folder.exists():
            return {
                'exists': False,
                'total_files': 0,
                'total_size': 0,
                'old_files': 0
            }

        total_files = 0
        total_size = 0
        old_files = 0
        now = datetime.now()

        for file_path in self.upload_folder.glob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if (now - file_mtime) > self.max_age:
                    old_files += 1

        return {
            'exists': True,
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'old_files': old_files,
            'max_age_hours': self.max_age.total_seconds() / 3600
        }

    def start_background_cleanup(self, interval_hours: int = 1) -> None:
        """
        Start background cleanup task.

        Args:
            interval_hours: Cleanup interval in hours
        """
        if self.running:
            logger.warning("Cleanup thread already running")
            return

        self.running = True
        interval_seconds = interval_hours * 3600

        def cleanup_loop():
            logger.info(f"Background cleanup started (interval: {interval_hours}h)")

            while self.running:
                try:
                    self.cleanup_old_files()
                except Exception as e:
                    logger.error(f"Error in cleanup loop: {e}", exc_info=True)

                # Sleep in small increments to allow quick shutdown
                sleep_time = 0
                while sleep_time < interval_seconds and self.running:
                    time.sleep(60)  # Sleep 1 minute at a time
                    sleep_time += 60

            logger.info("Background cleanup stopped")

        self._thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._thread.start()

        logger.info("File cleanup service started successfully")

    def stop(self) -> None:
        """Stop background cleanup task."""
        if not self.running:
            return

        logger.info("Stopping file cleanup service...")
        self.running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info("File cleanup service stopped")
