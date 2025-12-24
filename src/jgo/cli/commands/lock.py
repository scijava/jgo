"""jgo lock - Update jgo.lock.toml without building environment"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_log = logging.getLogger("jgo")


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
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="lock")
    args.check = check

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the lock command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ..helpers import load_spec_file

    # Get the spec file path
    _spec, exit_code = load_spec_file(args)
    if exit_code != 0:
        return exit_code

    spec_file = args.get_spec_file()

    # Check if --check mode
    if getattr(args, "check", False):
        lock_file = spec_file.parent / "jgo.lock.toml"
        if not lock_file.exists():
            _log.error("Lock file does not exist")
            return 1

        # TODO: Implement lock file validation
        # For now, just check if it exists
        _log.info(f"Lock file exists: {lock_file}")
        return 0

    _log.debug(f"Updating lock file for {spec_file}")

    # TODO: Implement lock file generation
    # This would resolve dependencies using Maven and create a lock file
    # with pinned versions without actually building the environment

    _log.error("Lock file generation not yet implemented")
    _log.error("Use 'jgo sync' to resolve dependencies and build environment")
    return 1
