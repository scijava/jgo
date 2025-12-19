"""jgo config shortcut - Manage global endpoint shortcuts"""

from __future__ import annotations

import configparser
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(name="shortcut", help="Manage global endpoint shortcuts")
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

    Shortcuts are stored in ~/.config/jgo/config (or ~/.jgorc for legacy).
    They provide quick aliases for Maven endpoint strings.

    Without arguments: list all shortcuts
    With NAME only: show what NAME expands to
    With NAME and ENDPOINT: add/update shortcut

    Shortcuts support composition with '+':
      jgo run repl+groovy → expands both shortcuts

    EXAMPLES:
      jgo config shortcut                                      # List all
      jgo config shortcut repl                                 # Show expansion
      jgo config shortcut repl org.scijava:scijava-common@ScriptREPL  # Add/update
      jgo config shortcut groovy org.scijava:scripting-groovy@GroovySh
      jgo config shortcut --remove repl                        # Remove
    """
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    jgorc = JgoConfig.load_from_opts(opts)
    args = _build_parsed_args(opts, command="config")

    exit_code = execute(
        args,
        jgorc.to_dict(),
        name=name,
        endpoint=endpoint,
        remove_name=remove_name,
        list_all=list_all,
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
) -> int:
    """
    Execute the config shortcut command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc
        name: Shortcut name
        endpoint: Endpoint to map to
        remove_name: Shortcut name to remove
        list_all: Whether to list all shortcuts
        config_file: Config file path (for testing)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Determine config file location (always global for shortcuts)
    if config_file is None:
        from ...config.jgorc import config_file_path

        config_file = config_file_path()

    # Handle remove
    if remove_name:
        return _remove_shortcut(config_file, remove_name, args)

    # Handle list
    if list_all or (name is None and endpoint is None):
        return _list_shortcuts(config_file, config, args)

    # Handle show (name only)
    if name and endpoint is None:
        return _show_shortcut(config_file, config, name, args)

    # Handle add/update (name and endpoint)
    if name and endpoint:
        return _add_shortcut(config_file, name, endpoint, args)

    # Should not reach here
    print("Error: Invalid arguments", file=sys.stderr)
    return 1


def _list_shortcuts(config_file: Path, config: dict, args: ParsedArgs) -> int:
    """List all shortcuts."""
    shortcuts = config.get("shortcuts", {})

    if not shortcuts:
        print("No shortcuts configured.")
        print()
        print("Add shortcuts with:")
        print("  jgo config shortcut NAME ENDPOINT")
        print()
        print("Example:")
        print("  jgo config shortcut repl org.scijava:scijava-common@ScriptREPL")
        return 0

    print(f"Shortcuts from {config_file}:")
    print()

    # Find the longest shortcut name for alignment
    max_name_len = max(len(name) for name in shortcuts.keys())

    for name in sorted(shortcuts.keys()):
        endpoint = shortcuts[name]
        print(f"  {name:<{max_name_len}}  →  {endpoint}")

    print()
    print(f"Total: {len(shortcuts)} shortcut(s)")
    return 0


def _show_shortcut(config_file: Path, config: dict, name: str, args: ParsedArgs) -> int:
    """Show what a shortcut expands to."""
    shortcuts = config.get("shortcuts", {})

    if name not in shortcuts:
        print(f"Error: Shortcut '{name}' not found", file=sys.stderr)
        print("Use 'jgo config shortcut' to list all shortcuts", file=sys.stderr)
        return 1

    endpoint = shortcuts[name]
    print(f"{name} → {endpoint}")
    return 0


def _add_shortcut(config_file: Path, name: str, endpoint: str, args: ParsedArgs) -> int:
    """Add or update a shortcut."""
    # Validate shortcut name
    if not name or not name[0].isalnum():
        print(f"Error: Invalid shortcut name '{name}'", file=sys.stderr)
        print("Shortcut names must start with a letter or number", file=sys.stderr)
        return 1

    # Check if shortcut already exists
    parser = configparser.ConfigParser()
    if config_file.exists():
        parser.read(config_file)

    is_update = parser.has_section("shortcuts") and parser.has_option("shortcuts", name)

    # Dry run
    if args.dry_run:
        action = "update" if is_update else "add"
        print(f"Would {action} shortcut: {name} → {endpoint}")
        print(f"In file: {config_file}")
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
    print(f"{action} shortcut: {name} → {endpoint}")

    if args.verbose > 0:
        print(f"Saved to: {config_file}")

    return 0


def _remove_shortcut(config_file: Path, name: str, args: ParsedArgs) -> int:
    """Remove a shortcut."""
    if not config_file.exists():
        print(f"Error: No configuration file found at {config_file}", file=sys.stderr)
        return 1

    parser = configparser.ConfigParser()
    parser.read(config_file)

    if not parser.has_section("shortcuts"):
        print("Error: No shortcuts configured", file=sys.stderr)
        return 1

    if not parser.has_option("shortcuts", name):
        print(f"Error: Shortcut '{name}' not found", file=sys.stderr)
        return 1

    # Dry run
    if args.dry_run:
        endpoint = parser.get("shortcuts", name)
        print(f"Would remove shortcut: {name} → {endpoint}")
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

    print(f"Removed shortcut: {name} → {endpoint}")

    if args.verbose > 0:
        print(f"Updated: {config_file}")

    return 0
