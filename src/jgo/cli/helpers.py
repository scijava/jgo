"""
Common helper functions for CLI subcommands.

.. deprecated:: 2.0
    Most functions have been moved to more appropriate modules:
    - handle_dry_run → cli/output.py
    - load_spec_file → env/spec.py (as EnvironmentSpec.load_or_error)
    - parse_config_key → config/settings.py
    - load_toml_file → util/toml.py
    - print_exception_if_verbose → util/logging.py (as log_exception_if_verbose)

    This module will be removed in jgo 3.0.
"""

from __future__ import annotations

# Re-export moved functions for backward compatibility
from ..cli.output import handle_dry_run  # noqa: F401
from ..config.settings import parse_config_key  # noqa: F401
from ..util.logging import (
    log_exception_if_verbose as print_exception_if_verbose,  # noqa: F401
)
from ..util.toml import load_toml_file  # noqa: F401

__all__ = [
    "handle_dry_run",
    "parse_config_key",
    "load_toml_file",
    "print_exception_if_verbose",
]


def load_spec_file(args):
    """
    Load environment spec file.

    .. deprecated:: 2.0
        Use :meth:`~jgo.env.spec.EnvironmentSpec.load_or_error` instead.

    Args:
        args: Parsed arguments containing spec file path

    Returns:
        Loaded environment spec
    """
    import warnings

    from ..env.spec import EnvironmentSpec

    warnings.warn(
        "load_spec_file is deprecated; use EnvironmentSpec.load_or_error() instead",
        DeprecationWarning,
        stacklevel=2,
    )

    spec_file = args.get_spec_file()
    return EnvironmentSpec.load_or_error(spec_file)
