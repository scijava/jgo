"""
Utility functions for fetching Maven using cjdk.

This module provides functions to automatically download and cache Maven
when it's not available on the system, similar to how scyjava handles it.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Union

_logger = logging.getLogger(__name__)


def ensure_maven_available() -> Path:
    """
    Ensure that Maven is available, downloading it with cjdk if necessary.

    Returns:
        Path to the mvn command

    Raises:
        RuntimeError: If Maven cannot be found or fetched
    """
    # First try to find mvn on the system PATH
    mvn_path = shutil.which("mvn")
    if mvn_path:
        _logger.debug(f"Found Maven on PATH: {mvn_path}")
        return Path(mvn_path)

    # Maven not found, try to fetch it with cjdk
    try:
        return fetch_maven()
    except ImportError:
        raise RuntimeError(
            "Maven not found on system PATH and cjdk is not installed. "
            "Either install Maven or install jgo with the 'cjdk' extra: "
            "pip install jgo[cjdk]"
        )


def fetch_maven(url: str = "", sha: str = "") -> Path:
    """
    Fetch Maven using cjdk and add it to the PATH.

    Args:
        url: URL to download Maven from (optional, uses default if not provided)
        sha: SHA hash to verify download (optional)

    Returns:
        Path to the mvn command

    Raises:
        ImportError: If cjdk is not installed
        RuntimeError: If Maven download or setup fails
    """
    try:
        import cjdk
    except ImportError:
        raise ImportError(
            "cjdk is required to automatically download Maven. "
            "Install it with: pip install jgo[cjdk]"
        )

    # Use default Maven URL if not provided
    # Maven 3.9.9 is a stable LTS version
    if not url:
        url = "https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz"
        sha = "e02cf0481a652a46ff4acbe52ad965e9d5659fa9e64d2fef2e8e8c78587848b558fe8a1ee5b8f0e9f7b04f61dc50e9b47c3b40f36e0e0f2f7ff14c849b8e2b89"

    # Fix URLs to have proper prefix for cjdk
    if url.startswith("http"):
        if url.endswith(".tar.gz"):
            url = url.replace("http", "tgz+http")
        elif url.endswith(".zip"):
            url = url.replace("http", "zip+http")

    # Determine SHA type based on length (cjdk requires specifying sha type)
    # Assuming hex-encoded SHA, length should be 40, 64, or 128
    kwargs = {}
    if sha_len := len(sha):  # empty sha is fine... we just don't pass it
        sha_lengths = {40: "sha1", 64: "sha256", 128: "sha512"}
        if sha_len not in sha_lengths:
            raise ValueError(
                "SHA must be a valid sha1, sha256, or sha512 hash. "
                f"Got invalid SHA length: {sha_len}."
            )
        kwargs = {sha_lengths[sha_len]: sha}

    _logger.info("Fetching Maven using cjdk...")
    maven_dir = cjdk.cache_package("Maven", url, **kwargs)
    _logger.debug(f"maven_dir -> {maven_dir}")

    # Find the mvn executable in the cached directory
    # Look for apache-maven-*/**/mvn pattern
    if maven_bin := next(maven_dir.rglob("apache-maven-*/bin/mvn"), None):
        _add_to_path(maven_bin.parent, front=True)
        _logger.info(f"Maven downloaded and cached at: {maven_bin}")
        return maven_bin
    else:
        raise RuntimeError(
            "Failed to find Maven executable in downloaded package. "
            f"Maven was cached to {maven_dir} but mvn binary not found."
        )


def _add_to_path(path: Union[Path, str], front: bool = False) -> None:
    """
    Add a path to the PATH environment variable.

    If front is True, the path is added to the front of the PATH.
    By default, the path is added to the end of the PATH.
    If the path is already in the PATH, it is not added again.
    """
    current_path = os.environ.get("PATH", "")
    if (path := str(path)) in current_path:
        return
    new_path = [path, current_path] if front else [current_path, path]
    os.environ["PATH"] = os.pathsep.join(new_path)
