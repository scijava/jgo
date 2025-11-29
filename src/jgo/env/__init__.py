"""
Environment layer for jgo 2.0.

This module provides the environment materialization functionality,
including Environment class, EnvironmentBuilder, and spec file handling.
"""

from .environment import Environment
from .builder import EnvironmentBuilder
from .linking import LinkStrategy
from .spec import EnvironmentSpec
from .lockfile import LockFile, LockedDependency

__all__ = [
    "Environment",
    "EnvironmentBuilder",
    "LinkStrategy",
    "EnvironmentSpec",
    "LockFile",
    "LockedDependency",
]
