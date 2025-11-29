"""
Environment layer for jgo 2.0.

This module provides the environment materialization functionality,
including Environment class and EnvironmentBuilder.
"""

from .environment import Environment
from .builder import EnvironmentBuilder
from .linking import LinkStrategy

__all__ = [
    "Environment",
    "EnvironmentBuilder",
    "LinkStrategy",
]
