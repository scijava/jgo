from .jgo import _jgo_main as main
from .jgo import resolve_dependencies
from .util import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)

__all__ = (
    "add_jvm_args_as_necessary",
    "main_from_endpoint",
    "main",
    "maven_scijava_repository",
    "resolve_dependencies",
)
