"""
TOML library compatibility layer.

Provides a single import point for TOML parsing that works across Python versions.
Python 3.11+ has built-in tomllib, older versions need tomli.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

__all__ = ["tomllib", "load_toml_file"]


def load_toml_file(path: Path) -> dict | None:
    """
    Load TOML file.

    Args:
        path: Path to TOML file

    Returns:
        Parsed TOML data as dict, or None if file doesn't exist

    Examples:
        >>> config = load_toml_file(Path("jgo.toml"))
        >>> if config:
        ...     print(config["dependencies"])
    """
    if not path.exists():
        return None

    with open(path, "rb") as f:
        return tomllib.load(f)
