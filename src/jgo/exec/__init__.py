"""
Execution layer for jgo.

This module provides the Java execution functionality, including JVM
configuration, Java locator (thanks to cjdk), and the JavaRunner.
"""

from ..util import JavaLocator, JavaSource
from ._config import JVMConfig
from ._gc_defaults import is_gc_flag, normalize_gc_flag
from ._runner import JavaRunner

__all__ = [
    "JVMConfig",
    "is_gc_flag",
    "JavaSource",
    "JavaLocator",
    "JavaRunner",
    "normalize_gc_flag",
]
