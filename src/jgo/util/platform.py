"""
Platform-specific utilities for jgo.

Provides platform-aware functions that can be easily mocked in tests.
"""

from pathlib import Path


def get_user_home() -> Path:
    """
    Get the user's home directory in a platform-aware manner.

    This function is designed to be easily mockable in tests, unlike Path.home()
    which directly accesses platform-specific environment variables that differ
    between Unix (HOME) and Windows (USERPROFILE).

    On Windows, Path.home() uses USERPROFILE (or HOMEDRIVE/HOMEPATH), not HOME.
    On Unix, Path.home() uses HOME environment variable.

    By centralizing home directory access through this function, tests can
    monkeypatch a single location regardless of platform.

    Returns:
        Path to the user's home directory
    """
    return Path.home()
