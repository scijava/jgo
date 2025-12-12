"""jgo info - Show information about environment or artifact"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Show classpath")
@click.argument("endpoint", required=False)
@click.pass_context
def classpath(ctx, endpoint):
    """Show the classpath for the given endpoint."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    opts["print_classpath"] = True
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


@click.command(help="Show dependency tree")
@click.argument("endpoint", required=False)
@click.pass_context
def deptree(ctx, endpoint):
    """Show the dependency tree for the given endpoint."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = True
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


@click.command(help="Show flat list of dependencies")
@click.argument("endpoint", required=False)
@click.pass_context
def deplist(ctx, endpoint):
    """Show a flat list of all dependencies for the given endpoint."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = True
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


@click.command(help="Show Java version requirements")
@click.argument("endpoint", required=False)
@click.pass_context
def javainfo(ctx, endpoint):
    """Show Java version requirements for the given endpoint."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = True
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = False

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


@click.command(help="Show entrypoints from jgo.toml")
@click.pass_context
def entrypoints(ctx):
    """Show available entrypoints defined in jgo.toml."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    opts["print_classpath"] = False
    opts["print_java_info"] = False
    opts["print_dependency_tree"] = False
    opts["print_dependency_list"] = False
    opts["list_entrypoints"] = True

    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=None, command="info")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the info command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    import sys
    from pathlib import Path

    from ...env import EnvironmentSpec
    from ..commands import JgoCommands

    # Check which info was requested
    if args.list_entrypoints:
        # List entrypoints from jgo.toml
        spec_file = args.file or Path("jgo.toml")

        if not spec_file.exists():
            print(f"Error: {spec_file} not found", file=sys.stderr)
            return 1

        spec = EnvironmentSpec.load(spec_file)

        if not spec.entrypoints:
            print("No entrypoints defined")
            return 0

        print("Available entrypoints:")
        for name, main_class in spec.entrypoints.items():
            marker = " (default)" if name == spec.default_entrypoint else ""
            print(f"  {name}: {main_class}{marker}")

        return 0

    # For other info types, delegate to commands but ensure proper flags are set
    # so they print info instead of running
    commands = JgoCommands(args, config)

    # If no specific info flag set, show a helpful message
    if not (
        args.print_classpath
        or args.print_java_info
        or args.print_dependency_tree
        or args.print_dependency_list
    ):
        print("Use 'jgo info' with a subcommand:", file=sys.stderr)
        print("  jgo info classpath <endpoint>     Show classpath", file=sys.stderr)
        print(
            "  jgo info deptree <endpoint>       Show dependency tree", file=sys.stderr
        )
        print(
            "  jgo info deplist <endpoint>       Show flat dependency list",
            file=sys.stderr,
        )
        print(
            "  jgo info javainfo <endpoint>      Show Java version requirements",
            file=sys.stderr,
        )
        print(
            "  jgo info entrypoints              Show entrypoints from jgo.toml",
            file=sys.stderr,
        )
        print(
            "  jgo info versions <coordinate>    List available versions",
            file=sys.stderr,
        )
        print("\nExamples:", file=sys.stderr)
        print("  jgo info classpath org.python:jython-standalone", file=sys.stderr)
        print("  jgo info javainfo org.scijava:scijava-common", file=sys.stderr)
        print("  jgo info versions org.python:jython-standalone", file=sys.stderr)
        return 1

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
