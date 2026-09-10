"""
HTTP helpers with retry/backoff for provider calls.
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Optional

import requests

from veni.logger import logger

RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class APIError(Exception):
    """Custom exception for API errors with retry information."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, retries: int = 0
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retries = retries


def request_with_retries(
    method: str,
    url: str,
    *,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    retry_status_codes: Iterable[int] = RETRY_STATUS_CODES,
    timeout: float = 30.0,
    **kwargs,
) -> requests.Response:
    """
    Execute a request with jittered exponential backoff retries.
    Retries on network errors and selected HTTP status codes.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        max_retries: Maximum number of retry attempts
        backoff_seconds: Initial backoff time in seconds
        retry_status_codes: HTTP status codes that trigger retries
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests.request()

    Returns:
        requests.Response object

    Raises:
        APIError: If all retries fail
        requests.RequestException: For network errors
    """
    last_exc: Optional[Exception] = None
    last_status: Optional[int] = None

    # Set default timeout if not provided
    if "timeout" not in kwargs:
        kwargs["timeout"] = timeout

    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            last_status = response.status_code

            if last_status in retry_status_codes and attempt < max_retries - 1:
                delay = backoff_seconds * (2**attempt)
                jitter = random.uniform(0, backoff_seconds * 0.5)
                sleep_time = delay + jitter
                logger.warning(
                    "Request %s %s returned %s, retrying (attempt %d/%d) after %.1fs",
                    method,
                    url,
                    last_status,
                    attempt + 1,
                    max_retries,
                    sleep_time,
                )
                time.sleep(sleep_time)
                continue

            logger.debug("Request %s %s completed with %s", method, url, last_status)
            return response

        except requests.exceptions.Timeout as exc:
            last_exc = exc
            if attempt >= max_retries - 1:
                logger.error(
                    "Request %s %s timed out after %d attempts",
                    method,
                    url,
                    max_retries,
                )
                raise APIError(
                    f"Request timed out after {max_retries} attempts",
                    retries=max_retries,
                ) from exc
            delay = backoff_seconds * (2**attempt)
            jitter = random.uniform(0, backoff_seconds * 0.5)
            sleep_time = delay + jitter
            logger.warning(
                "Request %s %s timed out, retrying (attempt %d/%d) after %.1fs",
                method,
                url,
                attempt + 1,
                max_retries,
                sleep_time,
            )
            time.sleep(sleep_time)

        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            if attempt >= max_retries - 1:
                logger.error(
                    "Request %s %s connection failed after %d attempts",
                    method,
                    url,
                    max_retries,
                )
                raise APIError(
                    f"Connection failed after {max_retries} attempts. Check your internet connection.",
                    retries=max_retries,
                ) from exc
            delay = backoff_seconds * (2**attempt)
            jitter = random.uniform(0, backoff_seconds * 0.5)
            sleep_time = delay + jitter
            logger.warning(
                "Request %s %s connection error, retrying (attempt %d/%d) after %.1fs",
                method,
                url,
                attempt + 1,
                max_retries,
                sleep_time,
            )
            time.sleep(sleep_time)

        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= max_retries - 1:
                logger.error(
                    "Request %s %s failed after %d attempts: %s",
                    method,
                    url,
                    max_retries,
                    exc,
                )
                raise APIError(
                    f"Request failed: {str(exc)}",
                    status_code=last_status,
                    retries=max_retries,
                ) from exc
            delay = backoff_seconds * (2**attempt)
            jitter = random.uniform(0, backoff_seconds * 0.5)
            sleep_time = delay + jitter
            logger.warning(
                "Request %s %s failed, retrying (attempt %d/%d) after %.1fs: %s",
                method,
                url,
                attempt + 1,
                max_retries,
                sleep_time,
                exc,
            )
            time.sleep(sleep_time)

    if last_exc:
        raise APIError(
            f"Request failed after {max_retries} attempts: {str(last_exc)}",
            status_code=last_status,
            retries=max_retries,
        ) from last_exc
    raise APIError("Request failed without exception", retries=max_retries)


def ping_provider(
    base_url: str, api_key: str | None = None, provider_name: str = ""
) -> str:
    """
    Quick health-check ping to an AI provider endpoint.
    Returns a human-readable status string.
    """
    url = base_url
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if provider_name == "ollama":
        url = f"{base_url.rstrip('/')}/api/tags"
    try:
        resp = request_with_retries("GET", url, headers=headers, timeout=5)
        return f"ok ({resp.status_code})"
    except requests.RequestException as e:
        return f"fail ({type(e).__name__})"
