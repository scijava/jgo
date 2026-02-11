"""
Environment layer for jgo.

This module provides the environment materialization functionality,
including Environment class, EnvironmentBuilder, and spec file handling.
"""

from .builder import EnvironmentBuilder
from .bytecode import analyze_jar_bytecode, bytecode_to_java_version, round_to_lts
from .environment import Environment
from .jar import find_main_classes, parse_manifest, read_raw_manifest
from .linking import LinkStrategy
from .lockfile import LockedDependency, LockFile, compute_spec_hash
from .spec import EnvironmentSpec

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
