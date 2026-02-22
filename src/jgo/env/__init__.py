"""
Environment layer for jgo.

This module provides the environment materialization functionality,
including Environment class, EnvironmentBuilder, and spec file handling.
"""

from ._builder import EnvironmentBuilder
from ._bytecode import analyze_jar_bytecode, bytecode_to_java_version, round_to_lts
from ._environment import Environment
from ._jar import find_main_classes, parse_manifest, read_raw_manifest
from ._linking import LinkStrategy
from ._lockfile import LockedDependency, LockFile, compute_spec_hash
from ._spec import EnvironmentSpec

__all__ = [
    # builder
    "EnvironmentBuilder",
    # bytecode
    "analyze_jar_bytecode",
    "bytecode_to_java_version",
    "round_to_lts",
    # environment
    "Environment",
    # jar
    "find_main_classes",
    "parse_manifest",
    "read_raw_manifest",
    # linking
    "LinkStrategy",
    # lockfile
    "LockedDependency",
    "LockFile",
    "compute_spec_hash",
    # spec
    "EnvironmentSpec",
]
