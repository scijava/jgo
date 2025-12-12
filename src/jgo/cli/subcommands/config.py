"""jgo config - Manage jgo configuration"""

from __future__ import annotations

import configparser
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def execute(
    args: ParsedArgs,
    config: dict,
    key: str | None = None,
    value: str | None = None,
    unset: str | None = None,
    list_all: bool = False,
    global_config: bool = False,
    local_config: bool = False,
) -> int:
    """
    Execute the config command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc
        key: Configuration key to get/set
        value: Value to set (only used with key)
        unset: Key to unset
        list_all: Whether to list all configuration
        global_config: Whether to use global config (~/.jgorc)
        local_config: Whether to use local config (jgo.toml)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Determine which config file to use
    if local_config and global_config:
        print("Error: Cannot use both --global and --local", file=sys.stderr)
        return 1

    if local_config:
        config_file = args.get_spec_file()
        config_type = "local"
    else:
        # Default to global
        config_file = Path.home() / ".jgorc"
        config_type = "global"

    # Handle different operations
    if unset:
        return _unset_config(config_file, config_type, unset, args)

    if list_all or (key is None and value is None):
        return _list_config(config_file, config_type, args)

    if key and value is None:
        return _get_config(config_file, config_type, key, args)

    if key and value:
        return _set_config(config_file, config_type, key, value, args)

    # Should not reach here
    print("Error: Invalid arguments", file=sys.stderr)
    return 1


def _list_config(config_file: Path, config_type: str, args: ParsedArgs) -> int:
    """List all configuration values."""
    if not config_file.exists():
        print(f"No {config_type} configuration file found at {config_file}")
        return 0

    if config_type == "global":
        return _list_jgorc(config_file, args)
    else:
        return _list_toml(config_file, args)


def _list_jgorc(config_file: Path, args: ParsedArgs) -> int:
    """List all configuration from .jgorc file."""
    parser = configparser.ConfigParser()
    parser.read(config_file)

    print(f"Configuration from {config_file}:")
    print()

    for section in parser.sections():
        print(f"[{section}]")
        for key, value in parser.items(section):
            print(f"  {key} = {value}")
        print()

    return 0


def _list_toml(config_file: Path, args: ParsedArgs) -> int:
    """List all configuration from jgo.toml file."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    print(f"Configuration from {config_file}:")
    print()

    # Show settings section
    if "settings" in data:
        print("[settings]")
        for key, value in data["settings"].items():
            print(f"  {key} = {value}")
        print()

    # Show repositories
    if "repositories" in data:
        print("[repositories]")
        for key, value in data["repositories"].items():
            print(f"  {key} = {value}")
        print()

    return 0


def _get_config(config_file: Path, config_type: str, key: str, args: ParsedArgs) -> int:
    """Get a specific configuration value."""
    if not config_file.exists():
        print(
            f"Error: No {config_type} configuration file found at {config_file}",
            file=sys.stderr,
        )
        return 1

    # Parse key as section.key or just key
    if "." in key:
        section, key_name = key.split(".", 1)
    else:
        # Default to settings section
        section = "settings"
        key_name = key

    if config_type == "global":
        return _get_jgorc(config_file, section, key_name, args)
    else:
        return _get_toml(config_file, section, key_name, args)


def _get_jgorc(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Get value from .jgorc file."""
    parser = configparser.ConfigParser()
    parser.read(config_file)

    if not parser.has_section(section):
        print(f"Error: Section [{section}] not found", file=sys.stderr)
        return 1

    if not parser.has_option(section, key):
        print(f"Error: Key '{key}' not found in section [{section}]", file=sys.stderr)
        return 1

    value = parser.get(section, key)
    print(value)
    return 0


def _get_toml(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Get value from jgo.toml file."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    if section not in data:
        print(f"Error: Section [{section}] not found", file=sys.stderr)
        return 1

    if key not in data[section]:
        print(f"Error: Key '{key}' not found in section [{section}]", file=sys.stderr)
        return 1

    value = data[section][key]
    print(value)
    return 0


def _set_config(
    config_file: Path, config_type: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set a configuration value."""
    # Parse key as section.key or just key
    if "." in key:
        section, key_name = key.split(".", 1)
    else:
        # Default to settings section
        section = "settings"
        key_name = key

    if config_type == "global":
        return _set_jgorc(config_file, section, key_name, value, args)
    else:
        return _set_toml(config_file, section, key_name, value, args)


def _set_jgorc(
    config_file: Path, section: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set value in .jgorc file."""
    parser = configparser.ConfigParser()

    # Read existing file if it exists
    if config_file.exists():
        parser.read(config_file)

    # Create section if it doesn't exist
    if not parser.has_section(section):
        parser.add_section(section)

    # Set value
    parser.set(section, key, value)

    # Dry run
    if args.dry_run:
        print(f"Would set [{section}] {key} = {value} in {config_file}")
        return 0

    # Write to file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        parser.write(f)

    if args.verbose > 0:
        print(f"Set [{section}] {key} = {value} in {config_file}")

    return 0


def _set_toml(
    config_file: Path, section: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set value in jgo.toml file."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    import tomli_w

    # Read existing file
    if not config_file.exists():
        print(
            f"Error: No local configuration file found at {config_file}",
            file=sys.stderr,
        )
        print("Run 'jgo init' to create a new environment file first.", file=sys.stderr)
        return 1

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    # Create section if it doesn't exist
    if section not in data:
        data[section] = {}

    # Set value (try to parse as number/bool if possible)
    parsed_value = _parse_value(value)
    data[section][key] = parsed_value

    # Dry run
    if args.dry_run:
        print(f"Would set [{section}] {key} = {parsed_value} in {config_file}")
        return 0

    # Write to file
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    if args.verbose > 0:
        print(f"Set [{section}] {key} = {parsed_value} in {config_file}")

    return 0


def _unset_config(
    config_file: Path, config_type: str, key: str, args: ParsedArgs
) -> int:
    """Unset a configuration value."""
    if not config_file.exists():
        print(
            f"Error: No {config_type} configuration file found at {config_file}",
            file=sys.stderr,
        )
        return 1

    # Parse key as section.key or just key
    if "." in key:
        section, key_name = key.split(".", 1)
    else:
        # Default to settings section
        section = "settings"
        key_name = key

    if config_type == "global":
        return _unset_jgorc(config_file, section, key_name, args)
    else:
        return _unset_toml(config_file, section, key_name, args)


def _unset_jgorc(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Unset value in .jgorc file."""
    parser = configparser.ConfigParser()
    parser.read(config_file)

    if not parser.has_section(section):
        print(f"Error: Section [{section}] not found", file=sys.stderr)
        return 1

    if not parser.has_option(section, key):
        print(f"Error: Key '{key}' not found in section [{section}]", file=sys.stderr)
        return 1

    # Dry run
    if args.dry_run:
        print(f"Would remove [{section}] {key} from {config_file}")
        return 0

    # Remove option
    parser.remove_option(section, key)

    # Remove section if empty
    if not parser.options(section):
        parser.remove_section(section)

    # Write to file
    with open(config_file, "w") as f:
        parser.write(f)

    if args.verbose > 0:
        print(f"Removed [{section}] {key} from {config_file}")

    return 0


def _unset_toml(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Unset value in jgo.toml file."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    import tomli_w

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    if section not in data:
        print(f"Error: Section [{section}] not found", file=sys.stderr)
        return 1

    if key not in data[section]:
        print(f"Error: Key '{key}' not found in section [{section}]", file=sys.stderr)
        return 1

    # Dry run
    if args.dry_run:
        print(f"Would remove [{section}] {key} from {config_file}")
        return 0

    # Remove key
    del data[section][key]

    # Remove section if empty
    if not data[section]:
        del data[section]

    # Write to file
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    if args.verbose > 0:
        print(f"Removed [{section}] {key} from {config_file}")

    return 0


def _parse_value(value: str) -> str | int | float | bool:
    """
    Parse a string value to its appropriate type.

    Args:
        value: String value to parse

    Returns:
        Parsed value (str, int, float, or bool)
    """
    # Try bool
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False

    # Try int
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value
