"""
Execution layer for jgo 2.0.

This module provides the Java execution functionality, including JVM configuration,
Java locator (with cjdk integration), and the JavaRunner.
"""

from .config import JVMConfig
from .java_source import JavaLocator, JavaSource
from .runner import JavaRunner

__all__ = [
    "JVMConfig",
    "JavaSource",
    "JavaLocator",
    "JavaRunner",
]
