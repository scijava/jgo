"""
CLI argument parser for jgo 2.0 using Click.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click


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
        # Dependency management
        managed: bool = True,
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
        dry_run: bool = False,
        # Spec file
        file: Path | None = None,
        entrypoint: str | None = None,
        init: str | None = None,
        list_entrypoints: bool = False,
        # Java
        java_version: int | None = None,
        java_vendor: str | None = None,
        java_source: str = "cjdk",
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
        # Dependency management
        self.managed = managed
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
        self.dry_run = dry_run
        # Spec file
        self.file = file
        self.entrypoint = entrypoint
        self.init = init
        self.list_entrypoints = list_entrypoints
        # Java
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.java_source = java_source
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

                if sys.version_info < (3, 11):
                    import tomli
                else:
                    import tomllib

                pyproject = (
                    Path(__file__).parent.parent.parent.parent / "pyproject.toml"
                )
                if pyproject.exists():
                    with open(pyproject, "rb") as f:
                        if sys.version_info < (3, 11):
                            data = tomli.load(f)
                        else:
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
        type=click.Choice(["auto", "pure", "maven"]),
        default="auto",
        help="Dependency resolver: auto (default), pure, or maven",
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
        "--managed/--no-managed",
        default=True,
        help="Use dependency management (import scope) - DEFAULT",
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
        "--java-source",
        type=click.Choice(["cjdk", "system"]),
        default="cjdk",
        help="Java source: cjdk (default) or system",
    )(f)

    # Advanced options
    f = click.option(
        "--link",
        type=click.Choice(["hard", "soft", "copy", "auto"]),
        default="auto",
        help="How to link JARs: hard, soft, copy, or auto (default)",
    )(f)
    f = click.option(
        "--main-class", metavar="CLASS", help="Specify main class explicitly"
    )(f)
    f = click.option(
        "--add-classpath",
        multiple=True,
        metavar="PATH",
        help="Append to classpath (JARs, directories, etc.)",
    )(f)
    f = click.option(
        "--entrypoint", metavar="NAME", help="Run specific entry point from jgo.toml"
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

    return f


@click.group(
    cls=JgoGroup,
    invoke_without_command=True,
    help="Launch Java applications from Maven coordinates without manual installation.",
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


@cli.command(help="Run a Java application from Maven coordinates or jgo.toml")
@click.option(
    "--main-class",
    metavar="CLASS",
    help="Main class to run (supports auto-completion for simple names)",
)
@click.argument("endpoint", required=False)
@click.argument("remaining", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def run(ctx, main_class, endpoint, remaining):
    """
    Run a Java application from Maven coordinates or jgo.toml.

    ENDPOINT FORMAT:
      groupId:artifactId[:version][:classifier][@mainClass]

    Multiple coordinates can be combined with '+':
      org.scijava:scijava-common+org.scijava:parsington

    Main class can be specified in two ways:
      1. Using @ syntax: org.scijava:scijava-common@ScriptREPL
      2. Using --main-class: --main-class ScriptREPL

    Simple class names are auto-completed. For example:
      ScriptREPL → org.scijava.script.ScriptREPL

    If no endpoint is provided, runs the default entrypoint from jgo.toml.

    EXAMPLES:
      jgo run org.python:jython-standalone
      jgo run org.scijava:scijava-common@ScriptREPL
      jgo run --main-class ScriptREPL org.scijava:scijava-common
      jgo run org.python:jython-standalone:2.7.3 -- -Xmx2G -- script.py
    """
    from ..cli.commands import JgoCommands
    from ..config.jgorc import JgoConfig

    # Get global options from context
    opts = ctx.obj

    # Add run-specific main-class option
    if main_class:
        opts["main_class"] = main_class

    # Parse remaining args for JVM/app args
    jvm_args, app_args = _parse_remaining(remaining)

    # Load config
    if opts.get("ignore_jgorc"):
        config = JgoConfig()
    else:
        config = JgoConfig.load()

    # Build ParsedArgs for backwards compat with existing code
    args = _build_parsed_args(
        opts, endpoint=endpoint, jvm_args=jvm_args, app_args=app_args, command="run"
    )

    # Execute
    commands = JgoCommands(args, config.to_dict())
    if args.is_spec_mode():
        exit_code = commands._cmd_run_spec()
    else:
        exit_code = commands._cmd_run_endpoint()

    ctx.exit(exit_code)


@cli.command(help="Create a new jgo.toml environment file")
@click.argument("endpoint", required=False)
@click.pass_context
def init(ctx, endpoint):
    """Create a new jgo.toml file."""
    from ..cli.subcommands import init as init_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="init")

    exit_code = init_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


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


@info.command(help="Show classpath")
@click.argument("endpoint", required=False)
@click.pass_context
def classpath(ctx, endpoint):
    """Show the classpath for the given endpoint."""
    from ..cli.subcommands import info as info_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    opts["print_classpath"] = True
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = info_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@info.command(help="Show dependency tree")
@click.argument("endpoint", required=False)
@click.pass_context
def deptree(ctx, endpoint):
    """Show the dependency tree for the given endpoint."""
    from ..cli.subcommands import info as info_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = True
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = info_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@info.command(help="Show flat list of dependencies")
@click.argument("endpoint", required=False)
@click.pass_context
def deplist(ctx, endpoint):
    """Show a flat list of all dependencies for the given endpoint."""
    from ..cli.subcommands import info as info_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = True
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = info_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@info.command(help="Show Java version requirements")
@click.argument("endpoint", required=False)
@click.pass_context
def javainfo(ctx, endpoint):
    """Show Java version requirements for the given endpoint."""
    from ..cli.subcommands import info as info_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = True
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = info_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@info.command(help="Show entrypoints from jgo.toml")
@click.pass_context
def entrypoints(ctx):
    """Show available entrypoints defined in jgo.toml."""
    from ..cli.subcommands import info as info_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = True

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=None, command="info")

    exit_code = info_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@info.command(help="List available versions of an artifact")
@click.argument("coordinate", required=True)
@click.pass_context
def versions(ctx, coordinate):
    """List available versions of a Maven artifact."""
    from ..cli.subcommands import versions as versions_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=coordinate, command="versions")

    exit_code = versions_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(name="list", help="List resolved dependencies (flat list)")
@click.argument("endpoint", required=False)
@click.pass_context
def list_cmd(ctx, endpoint):
    """List resolved dependencies as a flat list."""
    from ..cli.subcommands import list as list_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="list")

    exit_code = list_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(help="Show dependency tree")
@click.argument("endpoint", required=False)
@click.pass_context
def tree(ctx, endpoint):
    """Show the dependency tree for an endpoint or jgo.toml."""
    from ..cli.subcommands import tree as tree_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="tree")

    exit_code = tree_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(help="Display jgo's version")
def version():
    """Display jgo's version."""
    parser = JgoArgumentParser()
    click.echo(f"jgo {parser._get_version()}")


@cli.command(help="Add dependencies to jgo.toml")
@click.argument("coordinates", nargs=-1, required=True)
@click.option(
    "--no-sync",
    is_flag=True,
    help="Don't automatically sync after adding dependencies",
)
@click.pass_context
def add(ctx, coordinates, no_sync):
    """
    Add one or more dependencies to jgo.toml.

    Automatically runs 'jgo sync' unless --no-sync is specified.

    EXAMPLES:
      jgo add org.python:jython-standalone:2.7.3
      jgo add org.scijava:scijava-common org.scijava:parsington
      jgo add --no-sync net.imagej:imagej:2.15.0
    """
    from ..cli.subcommands import add as add_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, command="add")
    args.coordinates = list(coordinates)
    args.no_sync = no_sync

    exit_code = add_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(help="Remove dependencies from jgo.toml")
@click.argument("coordinates", nargs=-1, required=True)
@click.option(
    "--no-sync",
    is_flag=True,
    help="Don't automatically sync after removing dependencies",
)
@click.pass_context
def remove(ctx, coordinates, no_sync):
    """
    Remove one or more dependencies from jgo.toml.

    Coordinates can be specified as groupId:artifactId (version ignored).
    Automatically runs 'jgo sync' unless --no-sync is specified.

    EXAMPLES:
      jgo remove org.python:jython-standalone
      jgo remove org.scijava:scijava-common org.scijava:parsington
      jgo remove --no-sync net.imagej:imagej
    """
    from ..cli.subcommands import remove as remove_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, command="remove")
    args.coordinates = list(coordinates)
    args.no_sync = no_sync

    exit_code = remove_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(help="Resolve dependencies and build environment")
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
    from ..cli.subcommands import sync as sync_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, command="sync")
    args.force = force

    exit_code = sync_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


@cli.command(help="Update jgo.lock.toml without building environment")
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
    from ..cli.subcommands import lock as lock_cmd
    from ..config.jgorc import JgoConfig

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, command="lock")
    args.check = check

    exit_code = lock_cmd.execute(args, config.to_dict())
    ctx.exit(exit_code)


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
        # Dependency management
        managed=opts.get("managed", True),
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
        dry_run=opts.get("dry_run", False),
        # Spec file
        file=opts.get("file"),
        entrypoint=opts.get("entrypoint"),
        init=opts.get("init"),
        list_entrypoints=opts.get("list_entrypoints", False),
        # Java
        java_version=opts.get("java_version"),
        java_vendor=opts.get("java_vendor"),
        java_source=opts.get("java_source", "cjdk"),
        # Endpoint and args
        endpoint=endpoint,
        jvm_args=jvm_args or [],
        app_args=app_args or [],
        # Command
        command=command,
    )


if __name__ == "__main__":
    cli()
