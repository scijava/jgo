"""jgo sync - Resolve dependencies and build environment"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import click

from ...util import is_info_enabled, setup_logging

if TYPE_CHECKING:
    from ...env.lockfile import LockFile
    from ..parser import ParsedArgs

_log = logging.getLogger("jgo")


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
    # Set up logging based on verbosity level
    setup_logging(args.verbose, args.quiet)

    from ...env import EnvironmentBuilder
    from ...env.linking import LinkStrategy
    from ...env.lockfile import LockFile
    from ...maven import MavenContext
    from ..helpers import (
        handle_dry_run,
        load_spec_file,
        print_exception_if_verbose,
    )

    # Get the spec file path
    spec, exit_code = load_spec_file(args)
    if exit_code != 0:
        return exit_code

    spec_file = args.get_spec_file()

    _log.debug(f"Syncing environment from {spec_file}")
    if spec.name:
        _log.debug(f"  Name: {spec.name}")
    if spec.description:
        _log.debug(f"  Description: {spec.description}")
    _log.debug(f"  Dependencies: {len(spec.coordinates)}")

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

        # Load old lock file if updating (for version change reporting)
        update = args.update or getattr(args, "force", False)
        old_lockfile = None
        if update and is_info_enabled():
            # Determine lock file path based on project mode
            if builder.is_project_mode():
                lock_path = args.cache_dir / "jgo.lock.toml"
            else:
                # For ad-hoc mode, we'd need to compute the cache key
                # Skip old lockfile loading for now in ad-hoc mode
                lock_path = None

            if lock_path and lock_path.exists():
                try:
                    old_lockfile = LockFile.load(lock_path)
                except Exception:
                    pass  # Ignore errors loading old lockfile

        # Build environment from spec
        env = builder.from_spec(spec, update=update)

        _log.debug(f"Environment built at: {env.path}")
        _log.debug(f"Classpath entries: {len(env.classpath)}")

        # Show version changes if updating and verbose
        if update and is_info_enabled() and old_lockfile:
            _show_version_changes(old_lockfile, env.path / "jgo.lock.toml", args)

        return 0

    except Exception as e:
        _log.error(f"Failed to build environment: {e}")
        print_exception_if_verbose(args)
        return 1


def _show_version_changes(
    old_lock_path: LockFile | Path, new_lock_path: Path, args: ParsedArgs
) -> None:
    """
    Show what dependencies changed between old and new lock files.

    Args:
        old_lock_path: Old lock file or path to it
        new_lock_path: Path to new lock file
        args: Parsed arguments for verbose level
    """
    import logging

    from ...env.lockfile import LockFile

    _log = logging.getLogger("jgo")

    try:
        # Load lock files
        if isinstance(old_lock_path, LockFile):
            old_lock = old_lock_path
        else:
            old_lock = LockFile.load(old_lock_path)

        if not new_lock_path.exists():
            return

        new_lock = LockFile.load(new_lock_path)

        # Build maps of groupId:artifactId -> version
        old_versions = {
            f"{dep.groupId}:{dep.artifactId}": dep.version
            for dep in old_lock.dependencies
        }
        new_versions = {
            f"{dep.groupId}:{dep.artifactId}": dep.version
            for dep in new_lock.dependencies
        }

        # Find changes
        added = []
        removed = []
        updated = []

        for coord, new_version in new_versions.items():
            if coord not in old_versions:
                added.append((coord, new_version))
            elif old_versions[coord] != new_version:
                updated.append((coord, old_versions[coord], new_version))

        for coord, old_version in old_versions.items():
            if coord not in new_versions:
                removed.append((coord, old_version))

        # Log changes
        if updated or added or removed:
            _log.info("")
            _log.info("Dependency changes:")

        if updated:
            _log.info("  Updated:")
            for coord, old_ver, new_ver in sorted(updated):
                _log.info(f"    {coord}: {old_ver} -> {new_ver}")

        if added:
            _log.info("  Added:")
            for coord, version in sorted(added):
                _log.info(f"    {coord}:{version}")

        if removed:
            _log.info("  Removed:")
            for coord, version in sorted(removed):
                _log.info(f"    {coord}:{version}")

        if not (updated or added or removed):
            _log.info("")
            _log.info("No dependency changes detected.")

    except Exception:
        # Silently ignore errors in version change reporting
        pass
