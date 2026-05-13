"""
HTTP utility functions.

Thin wrappers around ``requests`` that retry with backoff when the remote
server returns 429 (Too Many Requests), honoring the ``Retry-After`` header.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

_log = logging.getLogger(__name__)

_MAX_RETRIES = 3
_DEFAULT_RETRY_AFTER = 60


def request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """
    Issue an HTTP request, retrying on 429 responses.
    """
    response: requests.Response | None = None
    for attempt in range(_MAX_RETRIES + 1):
        response = requests.request(method, url, **kwargs)
        if response.status_code != 429 or attempt >= _MAX_RETRIES:
            return response
        wait = int(response.headers.get("Retry-After", _DEFAULT_RETRY_AFTER))
        _log.debug(f"Rate-limited by {url}; retrying in {wait}s")
        time.sleep(wait)
    assert response is not None
    return response


def get(url: str, **kwargs: Any) -> requests.Response:
    """GET with 429 retry/backoff. See :func:`request`."""
    return request("GET", url, **kwargs)


def head(url: str, **kwargs: Any) -> requests.Response:
    """HEAD with 429 retry/backoff. See :func:`request`."""
    return request("HEAD", url, **kwargs)
