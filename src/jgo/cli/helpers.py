"""
Common helper functions for CLI subcommands.

This module consolidates repeated patterns across subcommand implementations
to reduce duplication and improve consistency.
"""

from __future__ import annotations

import configparser
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..env import EnvironmentSpec
    from ..parse.coordinate import Coordinate
    from .parser import ParsedArgs


def verbose_print(args: ParsedArgs, message: str, level: int = 0):
    """
    Print message if verbose level is high enough.

    Args:
        args: Parsed arguments containing verbose level
        message: Message to print
        level: Minimum verbose level required (default: 0)
    """
    if args.verbose > level:
        print(message)


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
        print(message)
        return True
    return False


def load_spec_file(args: ParsedArgs) -> tuple[EnvironmentSpec | None, int]:
    """
    Load environment spec file with error handling.

    Args:
        args: Parsed arguments containing spec file path

    Returns:
        Tuple of (spec, exit_code). If successful, exit_code is 0.
        If failed, spec is None and exit_code is 1.
    """
    from ..env import EnvironmentSpec

    spec_file = args.get_spec_file()
    if not spec_file.exists():
        print(f"Error: {spec_file} does not exist", file=sys.stderr)
        print("Run 'jgo init' to create a new environment file first.", file=sys.stderr)
        return None, 1

    try:
        spec = EnvironmentSpec.load(spec_file)
        return spec, 0
    except Exception as e:
        print(f"Error: Failed to load {spec_file}: {e}", file=sys.stderr)
        return None, 1


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


def validate_config_section(
    parser: configparser.ConfigParser, section: str
) -> int | None:
    """
    Validate that section exists in config parser.

    Args:
        parser: ConfigParser to validate
        section: Section name to check

    Returns:
        1 if error (section not found), None if valid
    """
    if not parser.has_section(section):
        print(f"Error: Section [{section}] not found", file=sys.stderr)
        return 1
    return None


def validate_config_key(
    parser: configparser.ConfigParser, section: str, key: str
) -> int | None:
    """
    Validate that key exists in section.

    Args:
        parser: ConfigParser to validate
        section: Section name
        key: Key name to check

    Returns:
        1 if error, None if valid
    """
    if error := validate_config_section(parser, section):
        return error
    if not parser.has_option(section, key):
        print(f"Error: Key '{key}' not found in section [{section}]", file=sys.stderr)
        return 1
    return None


def load_config_parser(config_file: Path) -> configparser.ConfigParser:
    """
    Load config file into ConfigParser.

    Args:
        config_file: Path to config file

    Returns:
        ConfigParser with loaded config (empty if file doesn't exist)
    """
    parser = configparser.ConfigParser()
    if config_file.exists():
        parser.read(config_file)
    return parser


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


def parse_coordinate_safe(
    endpoint: str, error_msg: str = "Invalid endpoint format"
) -> tuple[Coordinate | None, int]:
    """
    Parse coordinate with error handling.

    Args:
        endpoint: Coordinate string to parse
        error_msg: Custom error message prefix

    Returns:
        Tuple of (coordinate, exit_code). If successful, exit_code is 0.
        If failed, coordinate is None and exit_code is 1.
    """
    try:
        from ..parse.coordinate import Coordinate

        coord = Coordinate.parse(endpoint)
        return coord, 0
    except ValueError:
        print(f"Error: {error_msg}: {endpoint}", file=sys.stderr)
        print("Expected: groupId:artifactId[:version]", file=sys.stderr)
        return None, 1


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
