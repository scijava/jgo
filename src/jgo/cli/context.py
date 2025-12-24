"""
Factory functions for creating Maven contexts, environment builders, and Java runners.

These functions encapsulate the logic for creating the core objects needed
by CLI commands, extracting common configuration from ParsedArgs and config dicts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import DEFAULT_MAVEN_REPO, MAVEN_CENTRAL_URL
from ..env import EnvironmentBuilder, LinkStrategy
from ..exec import JavaRunner, JavaSource, JVMConfig
from ..maven import MavenContext, MvnResolver, PythonResolver
from ..util import is_debug_enabled, is_info_enabled

if TYPE_CHECKING:
    from .parser import ParsedArgs


def create_maven_context(args: ParsedArgs, config: dict) -> MavenContext:
    """
    Create Maven context from parsed arguments and configuration.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Configured MavenContext instance
    """
    # Determine resolver
    if args.resolver == "python":
        resolver = PythonResolver()
    elif args.resolver == "mvn":
        from jgo.util import ensure_maven_available

        mvn_command = ensure_maven_available()
        resolver = MvnResolver(
            mvn_command, update=args.update, debug=is_debug_enabled()
        )
    else:  # auto
        resolver = PythonResolver()  # Default to pure Python

    # Get repo cache path
    repo_cache = args.repo_cache
    if repo_cache is None:
        # Check config, then default
        repo_cache = config.get("repo_cache", DEFAULT_MAVEN_REPO)
    repo_cache = Path(repo_cache).expanduser()

    # Get remote repositories
    remote_repos = {}

    # Start with Maven Central
    remote_repos["central"] = MAVEN_CENTRAL_URL

    # Add from config
    if "repositories" in config:
        remote_repos.update(config["repositories"])

    # Add from command line (overrides config)
    if args.repositories:
        remote_repos.update(args.repositories)

    # Create context
    return MavenContext(
        repo_cache=repo_cache,
        remote_repos=remote_repos,
        resolver=resolver,
    )


def create_environment_builder(
    args: ParsedArgs, config: dict, context: MavenContext
) -> EnvironmentBuilder:
    """
    Create environment builder from parsed arguments and configuration.

    Args:
        args: Parsed command line arguments
        config: Global settings
        context: Maven context to use

    Returns:
        Configured EnvironmentBuilder instance
    """
    # Determine link strategy
    link_strategy_map = {
        "hard": LinkStrategy.HARD,
        "soft": LinkStrategy.SOFT,
        "copy": LinkStrategy.COPY,
        "auto": LinkStrategy.AUTO,
    }
    link_strategy = link_strategy_map[args.link]

    # Get cache directory
    cache_dir = args.cache_dir
    if cache_dir is None:
        # Check config
        cache_dir = config.get("cache_dir")
    # If still None, EnvironmentBuilder will auto-detect

    return EnvironmentBuilder(
        context=context,
        cache_dir=cache_dir,
        link_strategy=link_strategy,
    )


def create_java_runner(args: ParsedArgs, config: dict) -> JavaRunner:
    """
    Create Java runner from parsed arguments and configuration.

    Args:
        args: Parsed command line arguments
        config: Global settings (currently unused, reserved for future)

    Returns:
        Configured JavaRunner instance
    """
    java_source = JavaSource.SYSTEM if args.use_system_java else JavaSource.AUTO

    # Create JVM config
    jvm_config = JVMConfig()

    # TODO: Load JVM options from settings file

    verbose = is_info_enabled() and not args.quiet

    return JavaRunner(
        jvm_config=jvm_config,
        java_source=java_source,
        java_version=args.java_version,
        java_vendor=args.java_vendor,
        verbose=verbose,
    )
