"""
CLI argument parser for jgo.
"""

from __future__ import annotations

from pathlib import Path

import rich_click as click

from ..util import setup_logging
from .commands.add import add
from .commands.config import config
from .commands.info import (
    classpath,
    deplist,
    deptree,
    entrypoints,
    javainfo,
    manifest,
    pom,
)
from .commands.init import init
from .commands.list import list_cmd
from .commands.lock import lock
from .commands.remove import remove
from .commands.run import run
from .commands.search import search
from .commands.sync import sync
from .commands.tree import tree
from .commands.update import update
from .commands.versions import versions


def detect_os_properties() -> tuple[str, str, str]:
    """
    Detect current platform as (os_name, os_family, os_arch).

    Returns values that match Maven's OS property conventions for use in
    profile activation.
    """
    import platform

    system = platform.system()
    machine = platform.machine()

    # Map system -> (os_name, os_family)
    # Match Maven's OS family conventions from plexus-utils
    if system == "Linux":
        os_name, os_family = "Linux", "unix"
    elif system == "Darwin":
        os_name, os_family = "Mac OS X", "mac"
    elif system == "Windows":
        os_name, os_family = "Windows", "windows"
    elif system == "FreeBSD":
        os_name, os_family = "FreeBSD", "unix"
    elif system == "OpenBSD":
        os_name, os_family = "OpenBSD", "unix"
    elif system == "NetBSD":
        os_name, os_family = "NetBSD", "unix"
    elif system in ("SunOS", "Solaris"):
        os_name, os_family = "SunOS", "unix"
    elif system == "AIX":
        os_name, os_family = "AIX", "unix"
    else:
        # Unknown system - use the raw value
        os_name, os_family = system or "Unknown", "unknown"

    # Map machine -> os_arch (Python -> Java conventions)
    # Java uses different arch names than Python in some cases
    arch_map = {
        "x86_64": "amd64",  # Linux 64-bit
        "AMD64": "amd64",  # Windows 64-bit
        "arm64": "aarch64",  # macOS ARM (M1/M2/M3)
        "aarch64": "aarch64",  # Linux ARM
        "i386": "i386",  # Linux 32-bit
        "i486": "i386",
        "i586": "i386",
        "i686": "i386",
        "x86": "x86",  # Windows 32-bit
    }
    os_arch = arch_map.get(machine, machine)

    return os_name, os_family, os_arch


# Platform mappings: platform -> (os_name, os_family, os_arch)
PLATFORMS: dict[str, tuple[str, str, str]] = {
    # Linux
    "linux": ("Linux", "unix", "auto"),
    "linux-arm64": ("Linux", "unix", "aarch64"),
    "linux-x32": ("Linux", "unix", "i386"),
    "linux-x64": ("Linux", "unix", "amd64"),
    # macOS
    "macos": ("Mac OS X", "mac", "auto"),
    "macos-arm64": ("Mac OS X", "mac", "aarch64"),
    "macos-x32": ("Mac OS X", "mac", "x86"),
    "macos-x64": ("Mac OS X", "mac", "x86_64"),
    # Windows
    "windows": ("Windows", "windows", "auto"),
    "windows-arm64": ("Windows", "windows", "aarch64"),
    "windows-x32": ("Windows", "windows", "x86"),
    "windows-x64": ("Windows", "windows", "amd64"),
    # BSD variants
    "freebsd": ("FreeBSD", "unix", "auto"),
    "freebsd-x64": ("FreeBSD", "unix", "amd64"),
    "openbsd": ("OpenBSD", "unix", "auto"),
    "openbsd-x64": ("OpenBSD", "unix", "amd64"),
    "netbsd": ("NetBSD", "unix", "auto"),
    "netbsd-x64": ("NetBSD", "unix", "amd64"),
    # Solaris/SunOS
    "solaris": ("SunOS", "unix", "auto"),
    "solaris-x64": ("SunOS", "unix", "amd64"),
    # AIX
    "aix": ("AIX", "unix", "auto"),
    "aix-ppc64": ("AIX", "unix", "ppc64"),
}

# Convenience aliases
PLATFORM_ALIASES: dict[str, str] = {
    "linux32": "linux-x32",
    "linux64": "linux-x64",
    "macos32": "macos-x32",
    "macos64": "macos-x64",
    "win32": "windows-x32",
    "win64": "windows-x64",
}

# Windows os.arch values:
#
# | os.arch value | OpenJDK versions |
# |---------------|------------------|
# | aarch64       | 16 - 25+         |
# | amd64         | 6 - 25+          |
# | ia64          | 6 - 9            |
# | x86           | 6 - 23           |
# | unknown       | 6 - 25+          |
#
# As specified in the Windows java_props_md.c:
# - https://github.com/openjdk/jdk6/blob/jdk6-b49/jdk/src/windows/native/java/lang/java_props_md.c#L858-L866
# - https://github.com/openjdk/jdk/blob/jdk7-b147/jdk/src/windows/native/java/lang/java_props_md.c#L467-L474
# - https://github.com/openjdk/jdk/blob/jdk8-b120/jdk/src/windows/native/java/lang/java_props_md.c#L468-L476
# - https://github.com/openjdk/jdk/blob/jdk-9%2B181/jdk/src/java.base/windows/native/libjava/java_props_md.c#L562-L570
# - https://github.com/openjdk/jdk/blob/jdk-10%2B46/src/java.base/windows/native/libjava/java_props_md.c#L562-L568
# - https://github.com/openjdk/jdk/blob/jdk-11-ga/src/java.base/windows/native/libjava/java_props_md.c#L562-L568
# - https://github.com/openjdk/jdk/blob/jdk-12-ga/src/java.base/windows/native/libjava/java_props_md.c#L573-L579
# - https://github.com/openjdk/jdk/blob/jdk-13-ga/src/java.base/windows/native/libjava/java_props_md.c#L567-L573
# - https://github.com/openjdk/jdk/blob/jdk-14-ga/src/java.base/windows/native/libjava/java_props_md.c#L567-L573
# - https://github.com/openjdk/jdk/blob/jdk-15-ga/src/java.base/windows/native/libjava/java_props_md.c#L568-L574
# - https://github.com/openjdk/jdk/blob/jdk-16-ga/src/java.base/windows/native/libjava/java_props_md.c#L568-L576
# - https://github.com/openjdk/jdk/blob/jdk-17-ga/src/java.base/windows/native/libjava/java_props_md.c#L571-L579
# - https://github.com/openjdk/jdk/blob/jdk-18-ga/src/java.base/windows/native/libjava/java_props_md.c#L585-L593
# - https://github.com/openjdk/jdk/blob/jdk-19-ga/src/java.base/windows/native/libjava/java_props_md.c#L580-L588
# - https://github.com/openjdk/jdk/blob/jdk-20-ga/src/java.base/windows/native/libjava/java_props_md.c#L580-L588
# - https://github.com/openjdk/jdk/blob/jdk-21-ga/src/java.base/windows/native/libjava/java_props_md.c#L581-L589
# - https://github.com/openjdk/jdk/blob/jdk-22-ga/src/java.base/windows/native/libjava/java_props_md.c#L551-L559
# - https://github.com/openjdk/jdk/blob/jdk-23-ga/src/java.base/windows/native/libjava/java_props_md.c#L551-L559
# - https://github.com/openjdk/jdk/blob/jdk-24-ga/src/java.base/windows/native/libjava/java_props_md.c#L553-L559
# - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/windows/native/libjava/java_props_md.c#L557-L563


def expand_platform(platform: str | None) -> tuple[str | None, str | None, str | None]:
    """
    Expand a platform shorthand to (os_name, os_family, os_arch).

    Args:
        platform: Platform name like 'linux-x64' or alias like 'win64'

    Returns:
        Tuple of (os_name, os_family, os_arch), or (None, None, None) if not found
    """
    if platform is None:
        return None, None, None

    # Resolve alias first
    platform = PLATFORM_ALIASES.get(platform, platform)

    # Look up in platforms
    return PLATFORMS.get(platform) or (None, None, None)


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
        ignore_config: bool = False,
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
        # Profile constraints
        os_name: str | None = None,
        os_family: str | None = None,
        os_arch: str | None = None,
        os_version: str | None = None,
        properties: dict[str, str] | None = None,
        # Lenient mode
        lenient: bool = False,
        # Module mode
        class_path_only: bool = False,
        module_path_only: bool = False,
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
        self.ignore_config = ignore_config
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
        # Profile constraints
        self.os_name = os_name
        self.os_family = os_family
        self.os_arch = os_arch
        self.os_version = os_version
        self.properties = properties or {}
        # Lenient mode
        self.lenient = lenient
        # Module mode
        self.class_path_only = class_path_only
        self.module_path_only = module_path_only
        # Endpoint and args
        self.endpoint = endpoint
        self.jvm_args = jvm_args or []
        self.app_args = app_args or []
        # Command (for new command-based interface)
        self.command = command

    @property
    def module_mode(self) -> str:
        """Derive module mode from flags."""
        if self.class_path_only:
            return "class-path-only"
        elif self.module_path_only:
            return "module-path-only"
        return "auto"

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


# Custom Click group that handles shorthand endpoint syntax and shortcuts
class JgoGroup(click.RichGroup):
    """Custom group that auto-detects shorthand endpoint syntax and shortcuts."""

    def invoke(self, ctx):
        """
        Override to handle shorthand endpoint detection and bare shortcuts.

        Resolution policy:
        1. Built-in commands take precedence
        2. If first arg contains ':', treat as endpoint and inject 'run'
        3. If first arg is a configured shortcut (and not a command), inject 'run'
        4. Otherwise, fall through to normal Click behavior
        """
        if not ctx.protected_args:
            return super().invoke(ctx)

        first_arg = ctx.protected_args[0]

        # Check if it's a built-in command (takes precedence)
        if first_arg in self.commands:
            return super().invoke(ctx)

        # Check if it's an endpoint (contains ':')
        if ":" in first_arg:
            ctx.protected_args.insert(0, "run")
            return super().invoke(ctx)

        # Check if it's a configured shortcut
        try:
            from ..config.settings import GlobalSettings

            settings = GlobalSettings.load()
            if first_arg in settings.shortcuts:
                # It's a shortcut - inject 'run' command
                ctx.protected_args.insert(0, "run")
                return super().invoke(ctx)
        except Exception:
            # If we can't load settings, just fall through
            pass

        return super().invoke(ctx)


# Global options (available to all commands)
def global_options(f):
    """Decorator to add global options to commands."""
    # General options
    f = click.option(
        "-v",
        "--verbose",
        count=True,
        help="Verbose output (can be repeated: -vv, -vvv).",
    )(f)
    f = click.option("-q", "--quiet", is_flag=True, help="Suppress all output.")(f)
    f = click.option(
        "--color",
        type=click.Choice(["auto", "always", "never"]),
        default="auto",
        help="Control colored output: auto (default, color if TTY), always (force color), never (disable color).",
        envvar="COLOR",
        show_envvar=True,
    )(f)
    f = click.option(
        "-f",
        "--file",
        type=click.Path(path_type=Path),
        metavar="FILE",
        help="Use specific environment file (default: [cyan]jgo.toml[/]).",
    )(f)
    f = click.option(
        "--dry-run",
        is_flag=True,
        help="Show what would be done without doing it. Note: while this mode prevents the primary action (e.g. running Java, creating files), jgo may still download dependencies and build cached environments as needed to report accurate information.",
    )(f)

    # Cache options
    f = click.option(
        "-u",
        "--update",
        is_flag=True,
        help="Update cached environment.",
        envvar="JGO_UPDATE",
        show_envvar=True,
    )(f)
    f = click.option(
        "--offline",
        is_flag=True,
        help="Work offline, don't download.",
        envvar="JGO_OFFLINE",
        show_envvar=True,
    )(f)
    f = click.option(
        "--no-cache",
        is_flag=True,
        help="Skip cache entirely, always rebuild.",
        envvar="JGO_NO_CACHE",
        show_envvar=True,
    )(f)
    f = click.option(
        "--cache-dir",
        type=click.Path(path_type=Path),
        metavar="PATH",
        help="Override cache directory.",
        envvar="JGO_CACHE_DIR",
        show_envvar=True,
    )(f)
    f = click.option(
        "--repo-cache",
        type=click.Path(path_type=Path),
        metavar="PATH",
        help="Override Maven repo cache.",
        envvar="M2_REPO",
        show_envvar=True,
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
        help="Add remote Maven repository.",
    )(f)
    f = click.option(
        "-m",
        "--managed",
        "managed",
        flag_value=False,
        default=False,
        hidden=True,
        help="[DEPRECATED] Enable dependency management (this is now the default and has no effect).",
    )(f)

    # Java options
    f = click.option(
        "--java-version",
        type=int,
        metavar="VERSION",
        help="Force specific Java version (e.g., 17).",
        envvar="JAVA_VERSION",
        show_envvar=True,
    )(f)
    f = click.option(
        "--java-vendor",
        metavar="VENDOR",
        help="Prefer specific Java vendor (e.g., 'adoptium', 'zulu').",
    )(f)
    f = click.option(
        "--system-java",
        "use_system_java",
        is_flag=True,
        help="Use system Java instead of downloading Java on demand.",
    )(f)

    # Profile constraints
    all_platforms = list(PLATFORMS.keys()) + list(PLATFORM_ALIASES.keys())
    f = click.option(
        "--platform",
        type=click.Choice(all_platforms),
        metavar="PLATFORM",
        help="Target platform for profile activation. "
        "Sets os-name, os-family, and os-arch together. "
        f"Choices: {', '.join(PLATFORMS.keys())}. "
        f"Aliases: {', '.join(f'{k}={v}' for k, v in PLATFORM_ALIASES.items())}.",
    )(f)
    f = click.option(
        "--os-name",
        metavar="NAME",
        help="Set OS name for profile activation (e.g., 'Linux', 'Windows'). Use 'auto' to auto-detect. Overrides --platform.",
    )(f)
    f = click.option(
        "--os-family",
        metavar="FAMILY",
        help="Set OS family for profile activation (e.g., 'unix', 'windows'). Use 'auto' to auto-detect. Overrides --platform.",
    )(f)
    f = click.option(
        "--os-arch",
        metavar="ARCH",
        help="Set OS architecture for profile activation (e.g., 'amd64', 'aarch64'). Use 'auto' to auto-detect. Overrides --platform.",
    )(f)
    f = click.option(
        "--os-version",
        metavar="VERSION",
        help="Set OS version for profile activation (e.g., '5.1.2600').",
    )(f)
    f = click.option(
        "--property",
        "-D",
        "properties",
        multiple=True,
        metavar="KEY=VALUE",
        help="Set property for profile activation.",
    )(f)

    # Advanced options
    f = click.option(
        "--link",
        type=click.Choice(["hard", "soft", "copy", "auto"]),
        default="auto",
        help="How to link JARs: hard, soft, copy, or auto (default)",
    )(f)
    f = click.option(
        "--lenient",
        is_flag=True,
        help="Warn instead of failing on unresolved dependencies.",
        envvar="JGO_LENIENT",
        show_envvar=True,
    )(f)

    # Module path options
    f = click.option(
        "--class-path-only",
        is_flag=True,
        help="Force all JARs to classpath (disable module detection).",
    )(f)
    f = click.option(
        "--module-path-only",
        is_flag=True,
        help="Force all JARs to module-path (treat as modular).",
    )(f)

    f = click.option(
        "--ignore-config", is_flag=True, help="Ignore ~/.jgorc configuration file."
    )(f)
    # Hidden alias for backward compatibility
    f = click.option("--ignore-jgorc", "ignore_config", is_flag=True, hidden=True)(f)

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
        help="Show jgo version and exit.",
    )(f)

    return f


@click.group(
    cls=JgoGroup,
    invoke_without_command=True,
    context_settings=dict(ignore_unknown_options=True, allow_interspersed_args=False),
    help="""[bold]Environment manager and launcher for Java programs.[/]

Launch Java applications directly from [bold magenta]Maven coordinates[/],
build reproducible environments, manage Java versions,
and resolve dependencies -- [bold]without manual installation[/].""",
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
    # Configure Rich console color settings based on flags
    from rich.console import Console

    from . import output

    color = kwargs.get("color", "auto")

    if color == "never":
        output._console = Console(no_color=True)
        output._err_console = Console(stderr=True, no_color=True)
    elif color == "always":
        output._console = Console(force_terminal=True)
        output._err_console = Console(stderr=True, force_terminal=True)
    # else: "auto" - use defaults (Rich handles TTY detection automatically)

    # Setup logging based on verbose/quiet/color flags
    verbose = kwargs.get("verbose", 0)
    quiet = kwargs.get("quiet", False)
    setup_logging(verbose, quiet, color=color)

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


@cli.group(
    help="Show information about environment or artifact.",
    epilog="[dim]TIP: To see the launch command, use: [yellow]jgo --dry-run run <endpoint>[/]",
)
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

    Related:
      To see the launch command: jgo --dry-run run <endpoint>
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


@cli.command(help="Display jgo's version.")
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
            # Invoke the command with --help to trigger rich-click's help rendering
            cmd.main(["--help"], standalone_mode=False, parent=current_ctx)
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
    """Build a ParsedArgs object from Click options."""
    # Parse repositories from NAME=URL format
    repositories = {}
    if opts.get("repository"):
        for repo in opts["repository"]:
            if "=" in repo:
                name, url = repo.split("=", 1)
                repositories[name] = url

    # Parse properties from KEY=VALUE format
    properties = {}
    if opts.get("properties"):
        for prop in opts["properties"]:
            if "=" in prop:
                key, value = prop.split("=", 1)
                properties[key] = value

    # Expand platform to os_name, os_family, os_arch.
    # Explicit --os-name/--os-family/--os-arch override --platform values.
    plat_name, plat_family, plat_arch = expand_platform(opts.get("platform"))
    os_name = opts.get("os_name") or plat_name
    os_family = opts.get("os_family") or plat_family
    os_arch = opts.get("os_arch") or plat_arch

    # Populate remaining None and "auto" values from the current system.
    # This ensures we always have concrete values for profile activation,
    # matching Maven's behavior where OS properties are always populated.
    detected_name, detected_family, detected_arch = detect_os_properties()
    if os_name is None or os_name == "auto":
        os_name = detected_name
    if os_family is None or os_family == "auto":
        os_family = detected_family
    if os_arch is None or os_arch == "auto":
        os_arch = detected_arch

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
        ignore_config=opts.get("ignore_config", False),
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
        # Profile constraints
        os_name=os_name,
        os_family=os_family,
        os_arch=os_arch,
        os_version=opts.get("os_version"),
        properties=properties,
        # Lenient mode
        lenient=opts.get("lenient", False),
        # Module mode
        class_path_only=opts.get("class_path_only", False),
        module_path_only=opts.get("module_path_only", False),
        # Endpoint and args
        endpoint=endpoint,
        jvm_args=jvm_args or [],
        app_args=app_args or [],
        # Command
        command=command,
    )


if __name__ == "__main__":
    cli()
