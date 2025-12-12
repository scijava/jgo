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
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, command="sync")
    args.force = force

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the sync command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env import EnvironmentBuilder, EnvironmentSpec
    from ...env.linking import LinkStrategy
    from ...maven import MavenContext

    # Get the spec file path
    spec_file = args.get_spec_file()

    if not spec_file.exists():
        print(f"Error: {spec_file} does not exist", file=sys.stderr)
        print("Run 'jgo init' to create a new environment file first.", file=sys.stderr)
        return 1

    # Load spec
    try:
        spec = EnvironmentSpec.load(spec_file)
    except Exception as e:
        print(f"Error: Failed to load {spec_file}: {e}", file=sys.stderr)
        return 1

    if args.verbose > 0:
        print(f"Syncing environment from {spec_file}")
        if spec.name:
            print(f"  Name: {spec.name}")
        if spec.description:
            print(f"  Description: {spec.description}")
        print(f"  Dependencies: {len(spec.coordinates)}")

    # Dry run mode
    if args.dry_run:
        print(f"Would sync environment from {spec_file}")
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
            managed=args.managed,
        )

        # Build environment from spec
        update = args.update or getattr(args, "force", False)
        env = builder.from_spec(spec, update=update)

        if args.verbose > 0:
            print(f"Environment built at: {env.path}")
            print(f"Classpath entries: {len(env.classpath)}")

        return 0

    except Exception as e:
        print(f"Error: Failed to build environment: {e}", file=sys.stderr)
        if args.verbose > 1:
            import traceback

            traceback.print_exc()
        return 1
