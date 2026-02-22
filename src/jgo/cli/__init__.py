"""
CLI module for jgo.

Provides argument parsing and command execution for the jgo command-line interface.
"""

from ._args import ParsedArgs
from ._context import (
    create_environment_builder,
    create_java_runner,
    create_maven_context,
)

__all__ = [
    "ParsedArgs",
    "create_environment_builder",
    "create_java_runner",
    "create_maven_context",
]
