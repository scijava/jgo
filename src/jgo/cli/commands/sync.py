"""jgo sync - Resolve dependencies and build environment"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Resolve dependencies and build environment")
@click.option(
    "--force",
    is_flag=True,
    help="Force rebuild even if cached",
)
@click.pass_context
def sync(ctx, force):
    """
    Resolve dependencies and build environment in .jgo/ directory.

    Reads jgo.toml, resolves all dependencies using Maven, and creates
    the local environment directory with all JARs linked.

    EXAMPLES:
      jgo sync
      jgo sync --force
      jgo sync --offline
      jgo sync -u  # Update to latest versions
    """
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="sync")
    args.force = force

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the sync command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env import EnvironmentBuilder
    from ...env.linking import LinkStrategy
    from ...maven import MavenContext
    from ..helpers import (
        handle_dry_run,
        load_spec_file,
        print_exception_if_verbose,
        verbose_multiline,
        verbose_print,
    )

    # Get the spec file path
    spec, exit_code = load_spec_file(args)
    if exit_code != 0:
        return exit_code

    spec_file = args.get_spec_file()

    verbose_messages = [
        f"Syncing environment from {spec_file}",
    ]
    if spec.name:
        verbose_messages.append(f"  Name: {spec.name}")
    if spec.description:
        verbose_messages.append(f"  Description: {spec.description}")
    verbose_messages.append(f"  Dependencies: {len(spec.coordinates)}")
    verbose_multiline(args, verbose_messages)

    # Dry run mode
    if handle_dry_run(args, f"Would sync environment from {spec_file}"):
        return 0

    # Build environment
    try:
        # Create Maven context
        context = MavenContext(
            repo_cache=args.repo_cache,
            remote_repos=args.repositories or {},
        )

        # Determine link strategy
        link_str = args.link or "auto"
        link_strategy = LinkStrategy[link_str.upper()]

        # Create builder
        builder = EnvironmentBuilder(
            context=context,
            cache_dir=args.cache_dir,
            link_strategy=link_strategy,
        )

        # Build environment from spec
        update = args.update or getattr(args, "force", False)
        env = builder.from_spec(spec, update=update)

        verbose_print(args, f"Environment built at: {env.path}")
        verbose_print(args, f"Classpath entries: {len(env.classpath)}")

        return 0

    except Exception as e:
        print(f"Error: Failed to build environment: {e}", file=sys.stderr)
        print_exception_if_verbose(args)
        return 1
