"""jgo update - Update dependencies to latest versions"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    pass


@click.command(help="Update dependencies to latest versions")
@click.option(
    "--force",
    is_flag=True,
    help="Force rebuild even if cached",
)
@click.pass_context
def update(ctx, force):
    """
    Update dependencies to latest versions within constraints.

    This is a convenience alias for 'jgo sync --update'.
    It resolves dependencies and updates them to their latest available versions
    while respecting version constraints in jgo.toml.

    EXAMPLES:
      jgo update
      jgo update --force
    """
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args
    from . import sync as sync_cmd

    opts = ctx.obj
    config = JgoConfig.load_from_opts(opts)

    # Force update flag to be set
    opts["update"] = True

    args = _build_parsed_args(opts, command="update")
    args.force = force

    exit_code = sync_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)
