from .jgo import resolve_dependencies, _jgo_main as main
from .util import (
    main_from_endpoint,
    maven_scijava_repository,
    add_jvm_args_as_necessary,
)

__all__ = (
    "add_jvm_args_as_necessary",
    "main_from_endpoint",
    "main",
    "maven_scijava_repository",
    "resolve_dependencies",
)
