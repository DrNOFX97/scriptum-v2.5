"""
Unified HTTP client for external API requests.
Consolidates duplicate request patterns with error handling, timeouts, and retries.
"""

import requests
from typing import Optional, Dict, Any
from .logger import setup_logger
from ..constants import (
    API_TIMEOUT_SHORT,
    API_TIMEOUT_MEDIUM,
    API_TIMEOUT_LONG,
    MAX_RETRIES,
    HTTP_OK,
    HTTP_NOT_FOUND
)

logger = setup_logger(__name__)


class HTTPClient:
    """
    Unified HTTP client with automatic retries and error handling.

    Features:
    - Automatic retry logic for failed requests
    - Configurable timeouts
    - Structured logging
    - Consistent error handling

    Example:
        >>> client = HTTPClient()
        >>> data = client.get("https://api.example.com/data")
        >>> result = client.post("https://api.example.com/action", {"key": "value"})
    """

    @staticmethod
    def get(
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = API_TIMEOUT_SHORT,
        max_retries: int = MAX_RETRIES
    ) -> Optional[Dict[str, Any]]:
        """
        Perform GET request with automatic retries and error handling.

        Args:
            url: Target URL
            headers: Optional HTTP headers
            params: Optional query parameters
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"GET {url} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout
                )

                if response.status_code == HTTP_OK:
                    logger.debug(f"GET {url} succeeded")
                    return response.json()

                elif response.status_code == HTTP_NOT_FOUND:
                    logger.warning(f"Resource not found: {url}")
                    return None

                else:
                    logger.warning(f"HTTP {response.status_code} from {url}")
                    if attempt < max_retries - 1:
                        continue
                    return None

            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries} for {url}")
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded for {url}")
                    return None

            except requests.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                if attempt == max_retries - 1:
                    return None

            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
                return None

        return None

    @staticmethod
    def post(
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = API_TIMEOUT_MEDIUM,
        max_retries: int = MAX_RETRIES
    ) -> Optional[Dict[str, Any]]:
        """
        Perform POST request with error handling.

        Args:
            url: Target URL
            data: Optional form data
            json_data: Optional JSON payload
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"POST {url} (attempt {attempt + 1}/{max_retries})")

                response = requests.post(
                    url,
                    data=data,
                    json=json_data,
                    headers=headers,
                    timeout=timeout
                )

                if response.status_code == HTTP_OK:
                    logger.debug(f"POST {url} succeeded")
                    return response.json()

                else:
                    logger.warning(f"POST failed with HTTP {response.status_code} for {url}")
                    if attempt < max_retries - 1:
                        continue
                    return None

            except requests.Timeout:
                logger.warning(f"POST timeout on attempt {attempt + 1}/{max_retries} for {url}")
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded for {url}")
                    return None

            except requests.RequestException as e:
                logger.error(f"POST request failed for {url}: {e}")
                if attempt == max_retries - 1:
                    return None

            except Exception as e:
                logger.error(f"Unexpected error in POST {url}: {e}", exc_info=True)
                return None

        return None

    @staticmethod
    def download_file(
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = API_TIMEOUT_LONG
    ) -> Optional[bytes]:
        """
        Download file as bytes.

        Args:
            url: File URL
            headers: Optional HTTP headers
            timeout: Request timeout in seconds

        Returns:
            File content as bytes or None on failure
        """
        try:
            logger.debug(f"Downloading file from {url}")

            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                stream=True
            )

            if response.status_code == HTTP_OK:
                content = response.content
                logger.info(f"Downloaded {len(content)} bytes from {url}")
                return content

            logger.error(f"Download failed with HTTP {response.status_code} from {url}")
            return None

        except requests.Timeout:
            logger.error(f"Download timeout for {url}")
            return None

        except Exception as e:
            logger.error(f"Download error for {url}: {e}", exc_info=True)
            return None
