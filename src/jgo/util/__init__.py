"""
Utility modules for jgo.
"""

from .compat import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)
from .java import (
    JavaLocator,
    JavaSource,
    JavaVersion,
    parse_java_version,
    parse_jdk_activation_range,
    version_matches_jdk_range,
)
from .logging import (
    get_log,
    get_log_level,
    is_debug_enabled,
    is_info_enabled,
    setup_logging,
)
from .maven import ensure_maven_available, fetch_maven

__all__ = [
    # compat
    "add_jvm_args_as_necessary",
    "main_from_endpoint",
    "maven_scijava_repository",
    # java
    "JavaLocator",
    "JavaSource",
    "JavaVersion",
    "parse_java_version",
    "parse_jdk_activation_range",
    "version_matches_jdk_range",
    # logging
    "get_log",
    "get_log_level",
    "is_debug_enabled",
    "is_info_enabled",
    "setup_logging",
    # maven
    "ensure_maven_available",
    "fetch_maven",
]
