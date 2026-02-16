"""
Dependency injection container for Scriptum API.
Centralizes service instantiation and management.
"""

from dataclasses import dataclass
from typing import Optional

from .config import Config
from .services.video_service import VideoService
from .services.movie_service import MovieService
from .services.subtitle_service import SubtitleService
from .services.translation_service import TranslationService
from .services.sync_service import SyncService
from .services.legendasdivx_service import LegendasDivxService
from .services.job_storage_service import JobStorageService
from .utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ServiceContainer:
    """
    Dependency injection container for all services.

    Benefits:
    - Centralized service instantiation
    - Easy to mock in tests
    - Clear dependency graph
    - No global state
    """
    video_service: VideoService
    movie_service: MovieService
    subtitle_service: SubtitleService
    translation_service: TranslationService
    sync_service: SyncService
    legendasdivx_service: LegendasDivxService
    job_storage_service: JobStorageService

    @classmethod
    def create(cls, config: Config) -> 'ServiceContainer':
        """
        Factory method to create service container with all dependencies.

        Args:
            config: Application configuration

        Returns:
            Fully initialized ServiceContainer
        """
        logger.info("Initializing service container")

        # Validate configuration
        warnings = config.validate()
        for warning in warnings:
            logger.warning(warning)

        # Initialize services with their dependencies
        try:
            video_service = VideoService()
            logger.debug("VideoService initialized")

            movie_service = MovieService(config.TMDB_API_KEY)
            logger.debug("MovieService initialized")

            subtitle_service = SubtitleService(config.OPENSUBTITLES_API_KEY)
            logger.debug("SubtitleService initialized")

            translation_service = TranslationService(config.GEMINI_API_KEY)
            logger.debug("TranslationService initialized")

            sync_service = SyncService()
            logger.debug("SyncService initialized")

            legendasdivx_service = LegendasDivxService(api_base_url=config.LEGENDASDIVX_API_URL)
            logger.debug(f"LegendasDivxService initialized with URL: {config.LEGENDASDIVX_API_URL}")

            job_storage_service = JobStorageService()
            logger.debug("JobStorageService initialized")

            logger.info("All services initialized successfully")

            return cls(
                video_service=video_service,
                movie_service=movie_service,
                subtitle_service=subtitle_service,
                translation_service=translation_service,
                sync_service=sync_service,
                legendasdivx_service=legendasdivx_service,
                job_storage_service=job_storage_service
            )

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise


def create_services(config: Optional[Config] = None) -> ServiceContainer:
    """
    Convenience function to create service container.

    Args:
        config: Optional configuration (uses default if None)

    Returns:
        ServiceContainer instance
    """
    if config is None:
        config = Config()

    return ServiceContainer.create(config)
