"""jgo config - Manage jgo configuration"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click
from rich.markup import escape

from ...config import GlobalSettings, get_settings_path, parse_config_key
from ...styles import JGO_CONF_GLOBAL, JGO_TOML, error, filepath
from ...util.toml import load_toml_file
from .._args import build_parsed_args
from .._console import console_print
from .._output import handle_dry_run

if TYPE_CHECKING:
    from pathlib import Path

    from .._args import ParsedArgs

_log = logging.getLogger(__name__)


@click.group(help="Manage jgo configuration.", invoke_without_command=True)
@click.pass_context
def config(ctx):
    """
    Manage jgo configuration.

    Use subcommands to manage configuration:
      list      - List all configuration values
      get       - Get a specific configuration value
      set       - Set a configuration value
      unset     - Remove a configuration value
      shortcut  - Manage endpoint shortcuts

    EXAMPLES:
      jgo config list                         # Show all config
      jgo config get cache_dir                # Show cache_dir value
      jgo config get settings.cache_dir       # Show cache_dir from settings section
      jgo config set cache_dir ~/.jgo         # Set cache_dir
      jgo config set repositories.central URL # Set repository URL
      jgo config unset cache_dir              # Remove cache_dir setting
      jgo config --global set cache_dir ~/.jgo # Set in global config
      jgo config --local set cache_dir .jgo   # Set in local config
      jgo config shortcut list                # List all shortcuts
    """
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


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
        config: Global settings
        key: Configuration key to get/set
        value: Value to set (only used with key)
        unset: Key to unset
        list_all: Whether to list all configuration
        global_config: Whether to use global settings
        local_config: Whether to use local config (jgo.toml)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Determine which settings/config file to use
    if local_config and global_config:
        _log.error("Cannot use both --global and --local")
        return 1

    if local_config:
        config_file = args.get_spec_file()
        config_type = "local"
    else:
        # Default to global settings
        config_file = get_settings_path()
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
    _log.error("Invalid arguments")
    return 1


def _list_config(config_file: Path, config_type: str, args: ParsedArgs) -> int:
    """List all configuration values."""
    if not config_file.exists():
        console_print(f"No {config_type} configuration file found at {config_file}")
        return 0

    if config_type == "global":
        return _list_jgorc(config_file, args)
    else:
        return _list_toml(config_file, args)


def _list_jgorc(config_file: Path, args: ParsedArgs) -> int:
    """List all configuration from global settings file."""

    settings = GlobalSettings.load(config_file)

    console_print(f"Configuration from {config_file}:")
    console_print()

    # Print [settings] section
    # Use escape() to prevent Rich from interpreting [...] as markup
    console_print(escape("[settings]"))
    console_print(f"  cache_dir = {settings.cache_dir}")
    console_print(f"  repo_cache = {settings.repo_cache}")
    console_print(f"  links = {settings.links}")
    console_print()

    # Print [repositories] section if any
    if settings.repositories:
        console_print(escape("[repositories]"))
        for name, url in settings.repositories.items():
            console_print(f"  {name} = {url}")
        console_print()

    # Print [shortcuts] section if any
    if settings.shortcuts:
        console_print(escape("[shortcuts]"))
        for name, replacement in settings.shortcuts.items():
            console_print(f"  {name} = {replacement}")
        console_print()

    return 0


def _list_toml(config_file: Path, args: ParsedArgs) -> int:
    """List all configuration from jgo.toml file."""

    data = load_toml_file(config_file)
    if data is None:
        return 1

    console_print(f"Configuration from {config_file}:")
    console_print()

    # Show settings section
    # Use escape() to prevent Rich from interpreting [...] as markup
    if "settings" in data:
        console_print(escape("[settings]"))
        for key, value in data["settings"].items():
            console_print(f"  {key} = {value}")
        console_print()

    # Show repositories
    if "repositories" in data:
        console_print(escape("[repositories]"))
        for key, value in data["repositories"].items():
            console_print(f"  {key} = {value}")
        console_print()

    return 0


def _get_config(config_file: Path, config_type: str, key: str, args: ParsedArgs) -> int:
    """Get a specific configuration value."""

    if not config_file.exists():
        console_print(
            error(f"No {config_type} configuration file found at {config_file}"),
            stderr=True,
        )
        return 1

    # Parse key as section.key or just key
    section, key_name = parse_config_key(key)

    if config_type == "global":
        return _get_jgorc(config_file, section, key_name, args)
    else:
        return _get_toml(config_file, section, key_name, args)


def _get_jgorc(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Get value from global settings file."""

    settings = GlobalSettings.load(config_file)

    # Get value based on section
    if section == "settings":
        if key == "cache_dir":
            console_print(settings.cache_dir)
        elif key == "repo_cache":
            console_print(settings.repo_cache)
        elif key == "links":
            console_print(settings.links)
        else:
            _log.error(f"Unknown setting: {key}")
            return 1
    elif section == "repositories":
        if key in settings.repositories:
            console_print(settings.repositories[key])
        else:
            _log.error(f"Repository '{key}' not found")
            return 1
    elif section == "shortcuts":
        if key in settings.shortcuts:
            console_print(settings.shortcuts[key])
        else:
            _log.error(f"Shortcut '{key}' not found")
            return 1
    else:
        _log.error(f"Unknown section: [{section}]")
        return 1

    return 0


def _get_toml(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Get value from jgo.toml file."""

    data = load_toml_file(config_file)
    if data is None:
        return 1

    if section not in data:
        _log.error(f"Section [{section}] not found")
        return 1

    if key not in data[section]:
        _log.error(f"Key '{key}' not found in section [{section}]")
        return 1

    value = data[section][key]
    console_print(value)
    return 0


def _set_config(
    config_file: Path, config_type: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set a configuration value."""

    # Parse key as section.key or just key
    section, key_name = parse_config_key(key)

    if config_type == "global":
        return _set_jgorc(config_file, section, key_name, value, args)
    else:
        return _set_toml(config_file, section, key_name, value, args)


def _set_jgorc(
    config_file: Path, section: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set value in global settings file."""
    import configparser

    # Validate section and key
    valid_settings = ("cache_dir", "repo_cache", "links")
    if section == "settings" and key not in valid_settings:
        _log.error(f"Unknown setting: {key}")
        return 1
    elif section not in ("settings", "repositories", "shortcuts"):
        _log.error(f"Unknown section: [{section}]")
        return 1

    # Load existing config
    parser = configparser.ConfigParser()
    if config_file.exists():
        parser.read(config_file)

    # Create section if it doesn't exist
    if not parser.has_section(section):
        parser.add_section(section)

    # Set value
    parser.set(section, key, value)

    # Dry run
    if handle_dry_run(args, f"Would set [{section}] {key} = {value} in {config_file}"):
        return 0

    # Write to file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        parser.write(f)

    _log.debug(f"Set [{section}] {key} = {value} in {config_file}")

    return 0


def _set_toml(
    config_file: Path, section: str, key: str, value: str, args: ParsedArgs
) -> int:
    """Set value in jgo.toml file."""
    import tomli_w

    # Read existing file
    data = load_toml_file(config_file)
    if data is None:
        console_print(
            error(f"No local configuration file found at {config_file}"),
            stderr=True,
        )
        console_print(
            "Run 'jgo init' to create a new environment file first.", stderr=True
        )
        return 1

    # Create section if it doesn't exist
    if section not in data:
        data[section] = {}

    # Set value (try to parse as number/bool if possible)
    parsed_value = _parse_value(value)
    data[section][key] = parsed_value

    # Dry run
    if handle_dry_run(
        args, f"Would set [{section}] {key} = {parsed_value} in {config_file}"
    ):
        return 0

    # Write to file
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    _log.debug(f"Set [{section}] {key} = {parsed_value} in {config_file}")

    return 0


def _unset_config(
    config_file: Path, config_type: str, key: str, args: ParsedArgs
) -> int:
    """Unset a configuration value."""

    if not config_file.exists():
        console_print(
            error(f"No {config_type} configuration file found at {config_file}"),
            stderr=True,
        )
        return 1

    # Parse key as section.key or just key
    section, key_name = parse_config_key(key)

    if config_type == "global":
        return _unset_jgorc(config_file, section, key_name, args)
    else:
        return _unset_toml(config_file, section, key_name, args)


def _unset_jgorc(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Unset value in global settings file."""
    import configparser

    if not config_file.exists():
        console_print(
            error(f"No configuration file found at {config_file}"),
            stderr=True,
        )
        return 1

    # Load existing config
    parser = configparser.ConfigParser()
    parser.read(config_file)

    # Validate that section and key exist
    if not parser.has_section(section):
        _log.error(f"Section [{section}] not found")
        return 1

    if not parser.has_option(section, key):
        _log.error(f"Key '{key}' not found in section [{section}]")
        return 1

    # Dry run
    if handle_dry_run(args, f"Would remove [{section}] {key} from {config_file}"):
        return 0

    # Remove option
    parser.remove_option(section, key)

    # Remove section if empty
    if not parser.options(section):
        parser.remove_section(section)

    # Write to file
    with open(config_file, "w") as f:
        parser.write(f)

    _log.debug(f"Removed [{section}] {key} from {config_file}")

    return 0


def _unset_toml(config_file: Path, section: str, key: str, args: ParsedArgs) -> int:
    """Unset value in jgo.toml file."""
    import tomli_w

    data = load_toml_file(config_file)
    if data is None:
        return 1

    if section not in data:
        _log.error(f"Section [{section}] not found")
        return 1

    if key not in data[section]:
        _log.error(f"Key '{key}' not found in section [{section}]")
        return 1

    # Dry run
    if handle_dry_run(args, f"Would remove [{section}] {key} from {config_file}"):
        return 0

    # Remove key
    del data[section][key]

    # Remove section if empty
    if not data[section]:
        del data[section]

    # Write to file
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    _log.debug(f"Removed [{section}] {key} from {config_file}")

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


# Subcommands


@config.command(name="list", help="List all configuration values.")
@click.option(
    "--global",
    "global_config",
    is_flag=True,
    help=f"Use global configuration ({JGO_CONF_GLOBAL}).",
)
@click.option(
    "--local",
    "local_config",
    is_flag=True,
    help=f"Use local configuration ({JGO_TOML}).",
)
@click.pass_context
def list_cmd(ctx, global_config, local_config):
    """List all configuration values."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        config.to_dict(),
        key=None,
        value=None,
        unset=None,
        list_all=True,
        global_config=global_config,
        local_config=local_config,
    )
    ctx.exit(exit_code)


@config.command(name="get", help="Get a configuration value.")
@click.argument(
    "key",
    cls=click.RichArgument,
    help=f"Configuration key in dot notation (e.g., {filepath('repositories.scijava')})",
)
@click.option(
    "--global",
    "global_config",
    is_flag=True,
    help=f"Use global configuration ({JGO_CONF_GLOBAL})",
)
@click.option(
    "--local",
    "local_config",
    is_flag=True,
    help=f"Use local configuration ({JGO_TOML})",
)
@click.pass_context
def get_cmd(ctx, key, global_config, local_config):
    """Get a configuration value."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        config.to_dict(),
        key=key,
        value=None,
        unset=None,
        list_all=False,
        global_config=global_config,
        local_config=local_config,
    )
    ctx.exit(exit_code)


@config.command(name="set", help="Set a configuration value.")
@click.argument(
    "key",
    cls=click.RichArgument,
    help=f"Configuration key in dot notation (e.g., {filepath('repositories.scijava')})",
)
@click.argument("value", cls=click.RichArgument, help="Configuration value to set")
@click.option(
    "--global",
    "global_config",
    is_flag=True,
    help=f"Use global configuration ({JGO_CONF_GLOBAL})",
)
@click.option(
    "--local",
    "local_config",
    is_flag=True,
    help=f"Use local configuration ({JGO_TOML})",
)
@click.pass_context
def set_cmd(ctx, key, value, global_config, local_config):
    """Set a configuration value."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        config.to_dict(),
        key=key,
        value=value,
        unset=None,
        list_all=False,
        global_config=global_config,
        local_config=local_config,
    )
    ctx.exit(exit_code)


@config.command(name="unset", help="Remove a configuration value.")
@click.argument(
    "key",
    cls=click.RichArgument,
    help=f"Configuration key in dot notation (e.g., {filepath('repositories.scijava')})",
)
@click.option(
    "--global",
    "global_config",
    is_flag=True,
    help=f"Use global configuration ({JGO_CONF_GLOBAL}).",
)
@click.option(
    "--local",
    "local_config",
    is_flag=True,
    help=f"Use local configuration ({JGO_TOML}).",
)
@click.pass_context
def unset_cmd(ctx, key, global_config, local_config):
    """Remove a configuration value."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        config.to_dict(),
        key=None,
        value=None,
        unset=key,
        list_all=False,
        global_config=global_config,
        local_config=local_config,
    )
    ctx.exit(exit_code)


# Import and register shortcut subcommand
from .config_shortcut import shortcut  # noqa: E402

config.add_command(shortcut)
