"""
Environment layer for jgo.

This module provides the environment materialization functionality,
including Environment class, EnvironmentBuilder, and spec file handling.
"""

from .builder import EnvironmentBuilder
from .environment import Environment
from .linking import LinkStrategy
from .lockfile import LockedDependency, LockFile
from .spec import EnvironmentSpec

__all__ = [
    "Environment",
    "EnvironmentBuilder",
    "LinkStrategy",
    "EnvironmentSpec",
    "LockFile",
    "LockedDependency",
]
