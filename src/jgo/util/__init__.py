"""
Utility modules for jgo.
"""

from .compat import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)
from .logging import (
    get_log_level,
    get_logger,
    is_debug_enabled,
    is_info_enabled,
    setup_logging,
)
from .maven import ensure_maven_available, fetch_maven

__all__ = [
    "setup_logging",
    "get_logger",
    "get_log_level",
    "is_debug_enabled",
    "is_info_enabled",
    "add_jvm_args_as_necessary",
    "maven_scijava_repository",
    "main_from_endpoint",
    "ensure_maven_available",
    "fetch_maven",
]
