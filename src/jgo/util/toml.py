"""
TOML library compatibility layer.

Provides a single import point for TOML parsing that works across Python versions.
Python 3.11+ has built-in tomllib, older versions need tomli.
"""

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

__all__ = ["tomllib"]
