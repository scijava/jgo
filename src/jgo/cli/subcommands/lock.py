"""jgo lock - Update jgo.lock.toml without building environment"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Update jgo.lock.toml without building environment")
@click.option(
    "--check",
    is_flag=True,
    help="Check if lock file is up to date",
)
@click.pass_context
def lock(ctx, check):
    """
    Update jgo.lock.toml without building the environment.

    Useful for updating the lock file when RELEASE versions are involved,
    or to verify the lock file is up to date.

    EXAMPLES:
      jgo lock
      jgo lock --check
      jgo lock --update
    """
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig.load_from_opts(opts)
    args = _build_parsed_args(opts, command="lock")
    args.check = check

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the lock command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env import EnvironmentSpec

    # Get the spec file path
    spec_file = args.get_spec_file()

    if not spec_file.exists():
        print(f"Error: {spec_file} does not exist", file=sys.stderr)
        print("Run 'jgo init' to create a new environment file first.", file=sys.stderr)
        return 1

    # Load spec
    try:
        _spec = EnvironmentSpec.load(spec_file)
    except Exception as e:
        print(f"Error: Failed to load {spec_file}: {e}", file=sys.stderr)
        return 1

    # Check if --check mode
    if getattr(args, "check", False):
        lock_file = spec_file.parent / "jgo.lock.toml"
        if not lock_file.exists():
            print("Lock file does not exist", file=sys.stderr)
            return 1

        # TODO: Implement lock file validation
        # For now, just check if it exists
        print(f"Lock file exists: {lock_file}")
        return 0

    if args.verbose > 0:
        print(f"Updating lock file for {spec_file}")

    # TODO: Implement lock file generation
    # This would resolve dependencies using Maven and create a lock file
    # with pinned versions without actually building the environment

    print("Lock file generation not yet implemented", file=sys.stderr)
    print(
        "Use 'jgo sync' to resolve dependencies and build environment", file=sys.stderr
    )
    return 1
