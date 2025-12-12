"""
Utility modules for jgo.
"""

from .cjdk import ensure_maven_available, fetch_maven
from .compat import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)
from .logging import get_logger, setup_logging

__all__ = [
    "setup_logging",
    "get_logger",
    "add_jvm_args_as_necessary",
    "maven_scijava_repository",
    "main_from_endpoint",
    "ensure_maven_available",
    "fetch_maven",
]
