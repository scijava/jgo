"""jgo lock - Update jgo.lock.toml without building environment"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_log = logging.getLogger("jgo")


@click.command(help="Update [cyan]jgo.lock.toml[/] without building environment.")
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
    from ...env import EnvironmentBuilder
    from ...env.linking import LinkStrategy
    from ...env.lockfile import LockFile, compute_spec_hash
    from ...maven import MavenContext
    from ..helpers import load_spec_file, print_exception_if_verbose

    # Get the spec file path
    spec_file = args.get_spec_file()
    lock_file = spec_file.parent / "jgo.lock.toml"

    try:
        spec = load_spec_file(args)
    except (FileNotFoundError, ValueError) as e:
        _log.debug(f"Failed to load spec file: {e}")
        return 1

    # Check if --check mode
    if getattr(args, "check", False):
        if not lock_file.exists():
            _log.error("Lock file does not exist")
            _log.info("Run 'jgo lock' to generate it")
            return 1

        # Validate lock file
        try:
            lockfile = LockFile.load(lock_file)

            # Check if spec has changed since lockfile was generated
            if lockfile.spec_hash:
                current_hash = compute_spec_hash(spec_file)
                if current_hash != lockfile.spec_hash:
                    _log.error("Lock file is out of date (jgo.toml has changed)")
                    _log.info("Run 'jgo lock' to update it")
                    return 1

            _log.info("Lock file is up to date")
            return 0

        except Exception as e:
            _log.error(f"Failed to validate lock file: {e}")
            print_exception_if_verbose(args)
            return 1

    _log.debug(f"Updating lock file for {spec_file}")

    try:
        # Create Maven context
        context = MavenContext(
            repo_cache=args.repo_cache,
            remote_repos=args.repositories or {},
        )

        # Determine link strategy (not used for lock, but required for builder)
        link_str = args.link or "auto"
        link_strategy = LinkStrategy[link_str.upper()]

        # Create builder
        builder = EnvironmentBuilder(
            context=context,
            cache_dir=args.cache_dir,
            link_strategy=link_strategy,
        )

        # Resolve and generate lockfile without building environment
        _log.info(f"Resolving dependencies from {spec_file.name}...")
        lockfile = builder.resolve_lockfile(spec)

        # Save lockfile
        lockfile.save(lock_file)
        _log.info(f"Lock file saved to {lock_file}")
        _log.info(f"  {len(lockfile.dependencies)} dependencies resolved")
        if lockfile.entrypoints:
            _log.info(f"  {len(lockfile.entrypoints)} entrypoints found")

        return 0

    except Exception as e:
        _log.error(f"Failed to generate lock file: {e}")
        print_exception_if_verbose(args)
        return 1
