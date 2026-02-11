"""
Utility modules for jgo.
"""

from .compat import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)
from .java import JavaLocator, JavaSource
from .logging import (
    get_log,
    get_log_level,
    is_debug_enabled,
    is_info_enabled,
    setup_logging,
)
from .maven import ensure_maven_available, fetch_maven

__all__ = [
    # Logging utilities
    "get_log",
    "get_log_level",
    "is_debug_enabled",
    "is_info_enabled",
    "setup_logging",
    # Java detection and location
    "JavaLocator",
    "JavaSource",
    # Maven utilities
    "ensure_maven_available",
    "fetch_maven",
    # Compatibility/legacy utilities
    "add_jvm_args_as_necessary",
    "main_from_endpoint",
    "maven_scijava_repository",
]
