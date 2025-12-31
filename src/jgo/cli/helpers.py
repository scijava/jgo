"""
Common helper functions for CLI subcommands.

This module consolidates repeated patterns across subcommand implementations
to reduce duplication and improve consistency.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..env import EnvironmentSpec
    from .parser import ParsedArgs

_log = logging.getLogger(__name__)


def verbose_print(args: ParsedArgs, message: str, level: int = 0):
    """
    Print message if verbose level is high enough.

    DEPRECATED: Use logger.debug() instead. Will be removed in jgo 3.0.

    Args:
        args: Parsed arguments containing verbose level
        message: Message to print
        level: Minimum verbose level required (default: 0)
    """
    import logging
    import warnings

    warnings.warn(
        "verbose_print is deprecated; use logger.debug() instead",
        DeprecationWarning,
        stacklevel=2,
    )

    logger = logging.getLogger(__name__)
    if args.verbose > level:
        logger.debug(message)


def verbose_multiline(args: ParsedArgs, messages: list[str], level: int = 0):
    """
    Print multiple messages if verbose level is high enough.

    Args:
        args: Parsed arguments containing verbose level
        messages: List of messages to print
        level: Minimum verbose level required (default: 0)
    """
    if args.verbose > level:
        for msg in messages:
            print(msg)


def handle_dry_run(args: ParsedArgs, message: str) -> bool:
    """
    Check if in dry run mode and print message if so.

    Args:
        args: Parsed arguments containing dry_run flag
        message: Message to print in dry run mode

    Returns:
        True if dry run (caller should return 0), False otherwise
    """
    if args.dry_run:
        from .output import print_dry_run

        print_dry_run(message)
        return True
    return False


def load_spec_file(args: ParsedArgs) -> EnvironmentSpec:
    """
    Load environment spec file.

    Args:
        args: Parsed arguments containing spec file path

    Returns:
        Loaded environment spec

    Raises:
        FileNotFoundError: If spec file does not exist
        ValueError: If spec file is invalid or cannot be parsed
    """
    from ..env import EnvironmentSpec

    spec_file = args.get_spec_file()
    if not spec_file.exists():
        _log.error(f"{spec_file} does not exist")
        _log.info("Run 'jgo init' to create a new environment file first.")
        raise FileNotFoundError(
            f"{spec_file} does not exist. Run 'jgo init' to create a new environment file first."
        )

    try:
        spec = EnvironmentSpec.load(spec_file)
        _log.debug(f"Loaded spec file from {spec_file}")
        return spec
    except Exception as e:
        _log.error(f"Failed to load {spec_file}: {e}")
        raise ValueError(f"Failed to load {spec_file}: {e}") from e


def parse_config_key(key: str, default_section: str = "settings") -> tuple[str, str]:
    """
    Parse a config key into section and key name.

    Args:
        key: Key in format "section.key" or just "key"
        default_section: Default section if not specified (default: "settings")

    Returns:
        Tuple of (section, key_name)
    """
    if "." in key:
        return tuple(key.split(".", 1))
    return default_section, key


def load_toml_file(config_file: Path) -> dict | None:
    """
    Load TOML file.

    Args:
        config_file: Path to TOML file

    Returns:
        Parsed TOML data as dict, or None if file doesn't exist
    """
    from ..util.toml import tomllib

    if not config_file.exists():
        return None

    with open(config_file, "rb") as f:
        return tomllib.load(f)


def print_exception_if_verbose(args: ParsedArgs, level: int = 1):
    """
    Print full traceback if verbose level is high enough.

    Args:
        args: Parsed arguments containing verbose level
        level: Minimum verbose level required (default: 1)
    """
    if args.verbose > level:
        import traceback

        traceback.print_exc()
