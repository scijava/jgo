"""jgo config shortcut - Manage global endpoint shortcuts"""

from __future__ import annotations

import configparser
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click

from ...util import is_info_enabled
from ...util.console import get_console, get_err_console

if TYPE_CHECKING:
    from click import Context

    from ..parser import ParsedArgs

_log = logging.getLogger(__name__)
_console = get_console()
_err_console = get_err_console()


@click.command(name="shortcut", help="Manage global endpoint shortcuts.")
@click.option(
    "--remove",
    "-r",
    "remove_name",
    metavar="NAME",
    help="Remove a shortcut",
)
@click.option(
    "--list",
    "-l",
    "list_all",
    is_flag=True,
    help="List all shortcuts",
)
@click.argument("name", required=False)
@click.argument("endpoint", required=False)
@click.pass_context
def shortcut(ctx, remove_name, list_all, name, endpoint):
    """
    Manage global endpoint shortcuts.

    Shortcuts are stored in the settings file (~/.config/jgo.conf or ~/.jgorc).
    They provide quick aliases for Maven endpoint strings.

    Without arguments: show help (use -l/--list to list all shortcuts)
    With NAME only: show what NAME expands to
    With NAME and ENDPOINT: add/update shortcut

    Shortcuts support composition with '+':
      jgo run repl+groovy → expands both shortcuts

    EXAMPLES:
      jgo config shortcut                                      # Show help
      jgo config shortcut --list                               # List all
      jgo config shortcut repl                                 # Show expansion
      jgo config shortcut repl org.scijava:scijava-common@ScriptREPL  # Add/update
      jgo config shortcut groovy org.scijava:scripting-groovy@GroovySh
      jgo config shortcut --remove repl                        # Remove
    """
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        config.to_dict(),
        name=name,
        endpoint=endpoint,
        remove_name=remove_name,
        list_all=list_all,
        ctx=ctx,
    )
    ctx.exit(exit_code)


def execute(
    args: ParsedArgs,
    config: dict,
    name: str | None = None,
    endpoint: str | None = None,
    remove_name: str | None = None,
    list_all: bool = False,
    config_file: Path | None = None,
    ctx: Context | None = None,
) -> int:
    """
    Execute the config shortcut command.

    Args:
        args: Parsed command line arguments
        config: Global settings
        name: Shortcut name
        endpoint: Endpoint to map to
        remove_name: Shortcut name to remove
        list_all: Whether to list all shortcuts
        config_file: Config file path (for testing)
        ctx: Click context (for showing help)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Determine settings file location (always global for shortcuts)
    if config_file is None:
        from ...config.manager import get_settings_path

        config_file = get_settings_path()

    # Handle remove
    if remove_name:
        return _remove_shortcut(config_file, remove_name, args)

    # Handle list
    if list_all:
        return _list_shortcuts(config_file, config, args)

    # Show help if no arguments provided
    if name is None and endpoint is None:
        if ctx is not None:
            click.echo(ctx.get_help())
            return 0
        # Fallback for testing without context
        return _list_shortcuts(config_file, config, args)

    # Handle show (name only)
    if name and endpoint is None:
        return _show_shortcut(config_file, config, name, args)

    # Handle add/update (name and endpoint)
    if name and endpoint:
        return _add_shortcut(config_file, name, endpoint, args)

    # Should not reach here
    _log.error("Invalid arguments")
    return 1


def _list_shortcuts(config_file: Path, config: dict, args: ParsedArgs) -> int:
    """List all shortcuts."""
    shortcuts = config.get("shortcuts", {})

    if not shortcuts:
        _console.print("No shortcuts configured.")
        _console.print()
        _console.print("Add shortcuts with:")
        _console.print("  jgo config shortcut NAME ENDPOINT")
        _console.print()
        _console.print("Example:")
        _console.print("  jgo config shortcut repl org.scijava:scijava-common@ScriptREPL")
        return 0

    _console.print(f"Shortcuts from {config_file}:")
    _console.print()

    # Find the longest shortcut name for alignment
    max_name_len = max(len(name) for name in shortcuts.keys())

    for name in sorted(shortcuts.keys()):
        endpoint = shortcuts[name]
        _console.print(f"  {name:<{max_name_len}}  →  {endpoint}")

    _console.print()
    _console.print(f"Total: {len(shortcuts)} shortcut(s)")
    return 0


def _show_shortcut(config_file: Path, config: dict, name: str, args: ParsedArgs) -> int:
    """Show what a shortcut expands to."""
    shortcuts = config.get("shortcuts", {})

    if name not in shortcuts:
        _log.error(f"Shortcut '{name}' not found")
        _err_console.print("Use 'jgo config shortcut' to list all shortcuts")
        return 1

    endpoint = shortcuts[name]
    _console.print(f"{name} → {endpoint}")
    return 0


def _add_shortcut(config_file: Path, name: str, endpoint: str, args: ParsedArgs) -> int:
    """Add or update a shortcut."""
    from ..output import print_dry_run

    # Validate shortcut name
    if not name or not name[0].isalnum():
        _log.error(f"Invalid shortcut name '{name}'")
        _err_console.print("Shortcut names must start with a letter or number")
        return 1

    # Check if shortcut already exists
    parser = configparser.ConfigParser()
    if config_file.exists():
        parser.read(config_file)

    is_update = parser.has_section("shortcuts") and parser.has_option("shortcuts", name)

    # Dry run
    if args.dry_run:
        action = "update" if is_update else "add"
        print_dry_run(f"Would {action} shortcut: {name} → {endpoint}")
        _console.print(f"In file: {config_file}")
        return 0

    # Create shortcuts section if it doesn't exist
    if not parser.has_section("shortcuts"):
        parser.add_section("shortcuts")

    # Set shortcut
    parser.set("shortcuts", name, endpoint)

    # Write to file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        parser.write(f)

    action = "Updated" if is_update else "Added"
    _console.print(f"{action} shortcut: {name} → {endpoint}")

    if is_info_enabled():
        _log.info(f"Saved to: {config_file}")

    return 0


def _remove_shortcut(config_file: Path, name: str, args: ParsedArgs) -> int:
    """Remove a shortcut."""
    from ..output import print_dry_run

    if not config_file.exists():
        _log.error(f"No configuration file found at {config_file}")
        return 1

    parser = configparser.ConfigParser()
    parser.read(config_file)

    if not parser.has_section("shortcuts"):
        _log.error("No shortcuts configured")
        return 1

    if not parser.has_option("shortcuts", name):
        _log.error(f"Shortcut '{name}' not found")
        return 1

    # Dry run
    if args.dry_run:
        endpoint = parser.get("shortcuts", name)
        print_dry_run(f"Would remove shortcut: {name} → {endpoint}")
        return 0

    # Get endpoint for confirmation message
    endpoint = parser.get("shortcuts", name)

    # Remove shortcut
    parser.remove_option("shortcuts", name)

    # Remove section if empty
    if not parser.options("shortcuts"):
        parser.remove_section("shortcuts")

    # Write to file
    with open(config_file, "w") as f:
        parser.write(f)

    _console.print(f"Removed shortcut: {name} → {endpoint}")

    if is_info_enabled():
        _log.info(f"Updated: {config_file}")

    return 0
