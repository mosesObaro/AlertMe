"""Polite HTTP requester with rate limiting, retries, and backoff."""

import time
import requests
from typing import Optional, Dict, Any
from src.utils.logger import logger

DEFAULT_HEADERS = {
    "User-Agent": "EdgePhDResearchIntelligence/1.0 (Academic Research Assistant; mailto:obaro.moses.phd@example.com)",
    "Accept": "application/json, application/xml, text/xml, text/html, */*",
}


class PoliteRequester:
    """Wrapper around requests with delay pacing, exponential backoff, and polite headers."""

    def __init__(self, delay_seconds: float = 0.5, timeout: int = 8, max_retries: int = 2):
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_request_time: Dict[str, float] = {}
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _pace(self, host: str):
        """Enforces minimum delay between consecutive calls to the same host."""
        last_time = self._last_request_time.get(host, 0.0)
        elapsed = time.time() - last_time
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_time[host] = time.time()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[requests.Response]:
        """Performs a GET request with retry backoff and rate limiting."""
        from urllib.parse import urlparse
        host = urlparse(url).netloc

        req_timeout = timeout or self.timeout
        merged_headers = dict(DEFAULT_HEADERS)
        if headers:
            merged_headers.update(headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                self._pace(host)
                response = self.session.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=req_timeout
                )
                
                # Check rate limit status codes
                if response.status_code in [429, 503, 504]:
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    logger.warning(
                        f"HTTP {response.status_code} for {url}. Backing off {retry_after}s (Attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request failed for {url}: {e} (Attempt {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Exhausted retries for {url}: {e}")
                    return None

        return None
