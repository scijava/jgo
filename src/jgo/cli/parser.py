"""
CLI argument parser for jgo.
"""

from __future__ import annotations

from pathlib import Path

import click

from .subcommands.add import add
from .subcommands.config import config
from .subcommands.info import (
    classpath,
    deplist,
    deptree,
    entrypoints,
    javainfo,
    manifest,
    pom,
)
from .subcommands.init import init
from .subcommands.list import list_cmd
from .subcommands.lock import lock
from .subcommands.remove import remove
from .subcommands.run import run
from .subcommands.search import search
from .subcommands.sync import sync
from .subcommands.tree import tree
from .subcommands.update import update
from .subcommands.versions import versions


class ParsedArgs:
    """
    Container for parsed CLI arguments.
    """

    def __init__(
        self,
        # General
        verbose: int = 0,
        quiet: bool = False,
        # Cache and update
        update: bool = False,
        offline: bool = False,
        no_cache: bool = False,
        # Resolver and linking
        resolver: str = "auto",
        link: str = "auto",
        # Paths
        cache_dir: Path | None = None,
        repo_cache: Path | None = None,
        repositories: dict | None = None,
        # Program to run
        main_class: str | None = None,
        # Classpath
        classpath_append: list[str] | None = None,
        # Backward compatibility
        ignore_jgorc: bool = False,
        additional_endpoints: list[str] | None = None,
        log_level: str | None = None,
        # Information commands
        list_versions: bool = False,
        print_classpath: bool = False,
        print_java_info: bool = False,
        print_dependency_tree: bool = False,
        print_dependency_list: bool = False,
        direct_only: bool = False,
        dry_run: bool = False,
        # Spec file
        file: Path | None = None,
        entrypoint: str | None = None,
        init: str | None = None,
        list_entrypoints: bool = False,
        # Java
        java_version: int | None = None,
        java_vendor: str | None = None,
        use_system_java: bool = False,
        # Endpoint and args
        endpoint: str | None = None,
        jvm_args: list[str] | None = None,
        app_args: list[str] | None = None,
        # Command (for new command-based interface)
        command: str | None = None,
    ):
        # General
        self.verbose = verbose
        self.quiet = quiet
        # Cache and update
        self.update = update
        self.offline = offline
        self.no_cache = no_cache
        # Resolver and linking
        self.resolver = resolver
        self.link = link
        # Paths
        self.cache_dir = cache_dir
        self.repo_cache = repo_cache
        self.repositories = repositories or {}
        # Program to run
        self.main_class = main_class
        # Classpath
        self.classpath_append = classpath_append or []
        # Backward compatibility
        self.ignore_jgorc = ignore_jgorc
        self.additional_endpoints = additional_endpoints
        self.log_level = log_level
        # Information commands
        self.list_versions = list_versions
        self.print_classpath = print_classpath
        self.print_java_info = print_java_info
        self.print_dependency_tree = print_dependency_tree
        self.print_dependency_list = print_dependency_list
        self.direct_only = direct_only
        self.dry_run = dry_run
        # Spec file
        self.file = file
        self.entrypoint = entrypoint
        self.init = init
        self.list_entrypoints = list_entrypoints
        # Java
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.use_system_java = use_system_java
        # Endpoint and args
        self.endpoint = endpoint
        self.jvm_args = jvm_args or []
        self.app_args = app_args or []
        # Command (for new command-based interface)
        self.command = command

    def is_spec_mode(self) -> bool:
        """Check if running in spec file mode (jgo.toml)."""
        return bool(
            self.file
            or self.entrypoint
            or self.init
            or self.list_entrypoints
            or (not self.endpoint and Path("jgo.toml").exists())
        )

    def get_spec_file(self) -> Path:
        """Get the spec file path (defaults to jgo.toml)."""
        return self.file or Path("jgo.toml")


class JgoArgumentParser:
    """Compatibility shim for version lookup."""

    def _get_version(self) -> str:
        """Get jgo version from package metadata."""
        try:
            # Try importlib.metadata (Python 3.8+)
            from importlib.metadata import version

            return version("jgo")
        except Exception:
            # Fallback: read from pyproject.toml
            try:
                from pathlib import Path

                from ..util.toml import tomllib

                pyproject = (
                    Path(__file__).parent.parent.parent.parent / "pyproject.toml"
                )
                if pyproject.exists():
                    with open(pyproject, "rb") as f:
                        data = tomllib.load(f)
                        return data.get("project", {}).get("version", "unknown")
            except Exception:
                pass
            return "unknown"


# Custom Click group that handles legacy endpoint syntax
class JgoGroup(click.Group):
    """Custom group that auto-detects legacy endpoint syntax."""

    def invoke(self, ctx):
        """Override to handle legacy endpoint detection."""
        # If we have args and first arg contains ':', inject 'run' command
        if ctx.protected_args and ":" in ctx.protected_args[0]:
            # Legacy endpoint syntax - inject 'run'
            ctx.protected_args.insert(0, "run")

        return super().invoke(ctx)


# Global options (available to all commands)
def global_options(f):
    """Decorator to add global options to commands."""
    # General options
    f = click.option(
        "-v",
        "--verbose",
        count=True,
        help="Verbose output (can be repeated: -vv, -vvv)",
    )(f)
    f = click.option("-q", "--quiet", is_flag=True, help="Suppress all output")(f)
    f = click.option(
        "-f",
        "--file",
        type=click.Path(path_type=Path),
        metavar="FILE",
        help="Use specific environment file (default: jgo.toml)",
    )(f)
    f = click.option(
        "--dry-run", is_flag=True, help="Show what would be done without doing it"
    )(f)

    # Cache options
    f = click.option(
        "-u",
        "--update",
        is_flag=True,
        help="Update cached environment [env: JGO_UPDATE]",
        envvar="JGO_UPDATE",
    )(f)
    f = click.option(
        "--offline",
        is_flag=True,
        help="Work offline, don't download [env: JGO_OFFLINE]",
        envvar="JGO_OFFLINE",
    )(f)
    f = click.option(
        "--no-cache",
        is_flag=True,
        help="Skip cache entirely, always rebuild [env: JGO_NO_CACHE]",
        envvar="JGO_NO_CACHE",
    )(f)
    f = click.option(
        "--cache-dir",
        type=click.Path(path_type=Path),
        metavar="PATH",
        help="Override cache directory [env: JGO_CACHE_DIR]",
        envvar="JGO_CACHE_DIR",
    )(f)
    f = click.option(
        "--repo-cache",
        type=click.Path(path_type=Path),
        metavar="PATH",
        help="Override Maven repo cache [env: M2_REPO]",
        envvar="M2_REPO",
    )(f)

    # Maven options
    f = click.option(
        "--resolver",
        type=click.Choice(["auto", "python", "mvn"]),
        default="auto",
        help="Dependency resolver: auto (default), python, or mvn",
    )(f)
    f = click.option(
        "-r",
        "--repository",
        multiple=True,
        metavar="NAME=URL",
        help="Add remote Maven repository",
    )(f)
    f = click.option(
        "-m",
        "--managed",
        "managed",
        flag_value=False,
        default=False,
        hidden=True,
        help="[DEPRECATED] Enable dependency management - this is now the default and has no effect",
    )(f)

    # Java options
    f = click.option(
        "--java-version",
        type=int,
        metavar="VERSION",
        help="Force specific Java version (e.g., 17) [env: JAVA_VERSION]",
        envvar="JAVA_VERSION",
    )(f)
    f = click.option(
        "--java-vendor",
        metavar="VENDOR",
        help="Prefer specific Java vendor (e.g., 'adoptium', 'zulu')",
    )(f)
    f = click.option(
        "--system-java",
        "use_system_java",
        is_flag=True,
        help="Use system Java instead of downloading Java on demand",
    )(f)

    # Advanced options
    f = click.option(
        "--link",
        type=click.Choice(["hard", "soft", "copy", "auto"]),
        default="auto",
        help="How to link JARs: hard, soft, copy, or auto (default)",
    )(f)
    f = click.option(
        "--ignore-jgorc", is_flag=True, help="Ignore ~/.jgorc configuration file"
    )(f)

    # Legacy flags (hidden)
    f = click.option("--init", metavar="ENDPOINT", hidden=True)(f)
    f = click.option("--list-versions", is_flag=True, hidden=True)(f)
    f = click.option("--print-classpath", is_flag=True, hidden=True)(f)
    f = click.option("--print-java-info", is_flag=True, hidden=True)(f)
    f = click.option("--print-dependency-tree", is_flag=True, hidden=True)(f)
    f = click.option("--print-dependency-list", is_flag=True, hidden=True)(f)
    f = click.option("--list-entrypoints", is_flag=True, hidden=True)(f)

    # Version flag
    def _print_version(ctx, param, value):
        if value:
            parser = JgoArgumentParser()
            click.echo(f"jgo {parser._get_version()}")
            ctx.exit(0)

    f = click.option(
        "--version",
        is_flag=True,
        callback=_print_version,
        expose_value=False,
        is_eager=True,
        help="Show jgo version and exit",
    )(f)

    return f


@click.group(
    cls=JgoGroup,
    invoke_without_command=True,
    context_settings=dict(ignore_unknown_options=True, allow_interspersed_args=False),
    help="""Environment manager for Java programs.

Launch Java applications directly from Maven coordinates,
build reproducible environments, manage Java versions,
and resolve dependencies -- without manual installation.""",
)
@global_options
@click.pass_context
def cli(ctx, **kwargs):
    """
    Main CLI entry point.

    Handles both:
    - Command mode: jgo <command> [options]
    - Legacy endpoint mode: jgo <endpoint> [options]
    """
    # Store global options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)

    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


# Register top-level commands
cli.add_command(add)
cli.add_command(config)
cli.add_command(init)
cli.add_command(list_cmd)
cli.add_command(lock)
cli.add_command(remove)
cli.add_command(run)
cli.add_command(search)
cli.add_command(sync)
cli.add_command(tree)
cli.add_command(update)


@cli.group(help="Show information about environment or artifact")
@click.pass_context
def info(ctx):
    """
    Show information about a jgo environment or Maven artifact.

    Use subcommands to specify what information to display:
      classpath    - Show classpath
      deptree      - Show dependency tree
      deplist      - Show flat list of dependencies
      javainfo     - Show Java version requirements
      entrypoints  - Show entrypoints from jgo.toml
      versions     - List available versions of an artifact

    Examples:
      jgo info classpath org.python:jython-standalone
      jgo info javainfo org.scijava:scijava-common
      jgo info deptree org.scijava:scijava-common
      jgo info versions org.python:jython-standalone
      jgo info entrypoints
    """
    pass


# Register info subcommands
info.add_command(classpath)
info.add_command(deplist)
info.add_command(deptree)
info.add_command(entrypoints)
info.add_command(javainfo)
info.add_command(manifest)
info.add_command(pom)
info.add_command(versions)


@cli.command(help="Display jgo's version")
def version():
    """Display jgo's version."""
    parser = JgoArgumentParser()
    click.echo(f"jgo {parser._get_version()}")


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_interspersed_args=False)
)
@click.argument("commands", nargs=-1, required=False)
@click.pass_context
def help(ctx, commands):
    """Show help for jgo or a specific command.

    Examples:
      jgo help              - Show main help
      jgo help version      - Show help for 'version' command
      jgo help run          - Show help for 'run' command
      jgo help config shortcut  - Show help for nested 'config shortcut' command
    """
    if not commands:
        # No command specified - show main help
        click.echo(ctx.parent.get_help())
        return

    # Navigate through nested commands
    current_group = ctx.parent.command
    current_ctx = ctx.parent

    for i, cmd_name in enumerate(commands):
        if not hasattr(current_group, "commands"):
            click.echo(f"Error: '{cmd_name}' is not a command group", err=True)
            ctx.exit(1)

        cmd = current_group.commands.get(cmd_name)
        if cmd is None:
            click.echo(f"Error: Unknown command '{cmd_name}'", err=True)
            ctx.exit(1)

        # If this is the last command, show its help
        if i == len(commands) - 1:
            # Get the help text without triggering Click's exit mechanism
            cmd_ctx = click.Context(cmd, info_name=cmd_name, parent=current_ctx)
            click.echo(cmd.get_help(cmd_ctx))
            return

        # Otherwise, navigate deeper if it's a group
        if isinstance(cmd, click.Group):
            # Create intermediate context
            current_ctx = click.Context(cmd, info_name=cmd_name, parent=current_ctx)
            current_group = cmd
        else:
            click.echo(f"Error: '{cmd_name}' is not a command group", err=True)
            ctx.exit(1)


def _parse_remaining(remaining):
    """
    Parse remaining args for JVM and app arguments.

    Format: [-- JVM_ARGS] [-- APP_ARGS]

    Returns:
        Tuple of (jvm_args, app_args)
    """
    if not remaining:
        return [], []

    # Convert to list
    remaining = list(remaining)

    # Find -- separators
    separators = [i for i, arg in enumerate(remaining) if arg == "--"]

    if not separators:
        # No separators - everything is app args
        return [], remaining

    if len(separators) == 1:
        # One separator
        sep_idx = separators[0]
        jvm_args = remaining[:sep_idx]
        app_args = remaining[sep_idx + 1 :]
        return jvm_args, app_args

    # Two or more separators
    first_sep = separators[0]
    second_sep = separators[1]
    jvm_args = remaining[:first_sep]
    app_args = remaining[second_sep + 1 :]
    return jvm_args, app_args


def _build_parsed_args(opts, endpoint=None, jvm_args=None, app_args=None, command=None):
    """Build a ParsedArgs object from Click options for backwards compatibility."""
    # Parse repositories from NAME=URL format
    repositories = {}
    if opts.get("repository"):
        for repo in opts["repository"]:
            if "=" in repo:
                name, url = repo.split("=", 1)
                repositories[name] = url

    return ParsedArgs(
        # General
        verbose=opts.get("verbose", 0),
        quiet=opts.get("quiet", False),
        # Cache and update
        update=opts.get("update", False),
        offline=opts.get("offline", False),
        no_cache=opts.get("no_cache", False),
        # Resolver and linking
        resolver=opts.get("resolver", "auto"),
        link=opts.get("link", "auto"),
        # Paths
        cache_dir=opts.get("cache_dir"),
        repo_cache=opts.get("repo_cache"),
        repositories=repositories,
        # Program to run
        main_class=opts.get("main_class"),
        # Classpath
        classpath_append=list(opts.get("add_classpath", [])),
        # Backward compatibility
        ignore_jgorc=opts.get("ignore_jgorc", False),
        additional_endpoints=None,
        log_level=None,
        # Information commands (legacy)
        list_versions=opts.get("list_versions", False),
        print_classpath=opts.get("print_classpath", False),
        print_java_info=opts.get("print_java_info", False),
        print_dependency_tree=opts.get("print_dependency_tree", False),
        print_dependency_list=opts.get("print_dependency_list", False),
        direct_only=opts.get("direct_only", False),
        dry_run=opts.get("dry_run", False),
        # Spec file
        file=opts.get("file"),
        entrypoint=opts.get("entrypoint"),
        init=opts.get("init"),
        list_entrypoints=opts.get("list_entrypoints", False),
        # Java
        java_version=opts.get("java_version"),
        java_vendor=opts.get("java_vendor"),
        use_system_java=opts.get("use_system_java", False),
        # Endpoint and args
        endpoint=endpoint,
        jvm_args=jvm_args or [],
        app_args=app_args or [],
        # Command
        command=command,
    )


if __name__ == "__main__":
    cli()
