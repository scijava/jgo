"""
Utility modules for jgo 2.0.
"""

from .logging import setup_logging, get_logger
from .compat import (
    add_jvm_args_as_necessary,
    maven_scijava_repository,
    main_from_endpoint,
)
from .cjdk import ensure_maven_available, fetch_maven

__all__ = [
    "setup_logging",
    "get_logger",
    "add_jvm_args_as_necessary",
    "maven_scijava_repository",
    "main_from_endpoint",
    "ensure_maven_available",
    "fetch_maven",
]
