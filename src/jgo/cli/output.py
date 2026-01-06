"""
Output formatting functions for CLI commands.

These functions handle printing classpath, dependencies, Java info,
and user-facing messages in various formats with consistent styling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..env import Environment
    from ..maven import MavenContext
    from ..maven.core import Component
    from .parser import ParsedArgs

# Import shared console instances (configured at startup)
from .console import get_console, get_err_console, get_wrap_mode

_console = get_console()
_err_console = get_err_console()


# === Message Output Functions ===


def print_dry_run(message: str) -> None:
    """
    Print a dry-run message.

    Args:
        message: Dry-run message (e.g., "Would add 5 dependencies")
    """
    _console.print(r"[cyan bold]\[DRY-RUN] " + message, highlight=False)


def handle_dry_run(args: ParsedArgs, message: str) -> bool:
    """
    Check if in dry run mode and print message if so.

    Args:
        args: Parsed arguments containing dry_run flag
        message: Message to print in dry run mode

    Returns:
        True if dry run (caller should return 0), False otherwise
    """
    if args.dry_run:
        print_dry_run(message)
        return True
    return False


# === Data Output Functions ===


def print_classpath(environment: Environment) -> None:
    """
    Print environment classpath.

    Args:
        environment: The resolved environment
    """
    # Get classpath JARs only (class-path, not module-path)
    class_path_jars = environment.class_path_jars
    if not class_path_jars:
        _err_console.print("[red]No JARs on classpath[/]")
        _err_console.print(
            "[dim]TIP: Use 'jgo info module-path' to see module-path JARs[/]"
        )
        return

    # Print one classpath element per line (raw output, no Rich formatting)
    for jar_path in class_path_jars:
        print(jar_path)


def print_modulepath(environment: Environment) -> None:
    """
    Print environment module-path.

    Args:
        environment: The resolved environment
    """
    # Get module-path JARs only (module-path, not classpath)
    module_jars = environment.module_path_jars
    if not module_jars:
        _err_console.print("[red]No JARs on module-path[/]")
        _err_console.print(
            "[dim]TIP: Use 'jgo info classpath' to see classpath JARs[/]"
        )
        return

    # Print one module-path element per line (raw output, no Rich formatting)
    for jar_path in module_jars:
        print(jar_path)


def print_jars(environment: Environment) -> None:
    """
    Print all JAR paths (both classpath and module-path) with section headers.

    Args:
        environment: The resolved environment
    """
    cp_jars = environment.class_path_jars
    mp_jars = environment.module_path_jars

    if not cp_jars and not mp_jars:
        _err_console.print("[red]No JARs in environment[/]")
        return

    # Print classpath JARs
    if cp_jars:
        _console.print("[bold cyan]Classpath:[/]")
        for jar_path in cp_jars:
            print(jar_path)
    else:
        _console.print("[yellow]No classpath JARs[/]")

    # Print module-path JARs
    if mp_jars:
        if cp_jars:
            _console.print("\n[bold cyan]Module-path:[/]")
        else:
            _console.print("[bold cyan]Module-path:[/]")
        for jar_path in mp_jars:
            print(jar_path)
    else:
        _console.print("[yellow]No module-path JARs[/]")


def print_main_classes(environment: Environment) -> None:
    """
    Print all classes with public static void main(String[]) methods.

    Args:
        environment: The resolved environment
    """
    from ..env.jar import find_main_classes

    all_jars = environment.all_jars
    if not all_jars:
        _err_console.print("[red]No JARs in environment[/]")
        return

    # Scan all JARs for main classes
    main_classes_by_jar = {}
    for jar_path in all_jars:
        main_classes = find_main_classes(jar_path)
        if main_classes:
            main_classes_by_jar[jar_path.name] = main_classes

    if not main_classes_by_jar:
        _err_console.print("[yellow]No classes with main methods found[/]")
        return

    # Print results grouped by JAR
    _console.print(
        f"\n[bold]Found {sum(len(v) for v in main_classes_by_jar.values())} classes with main methods:[/]\n"
    )

    for jar_name, main_classes in sorted(main_classes_by_jar.items()):
        _console.print(f"[cyan]{jar_name}[/]:")
        for cls in main_classes:
            _console.print(f"  {cls}")
        _console.print()


def print_dependencies(
    components: list[Component],
    context: MavenContext,
    boms: list[Component] | None = None,
    list_mode: bool = False,
    direct_only: bool = False,
    optional_depth: int = 0,
) -> None:
    """
    Print dependencies for the given components.

    Args:
        components: List of components to print dependencies for
        context: Maven context containing the resolver
        boms: List of components to use as managed BOMs (None = none managed)
        list_mode: If True, print flat list (like mvn dependency:list).
                  If False, print tree (like mvn dependency:tree).
        direct_only: If True and list_mode is True, show only direct dependencies
        optional_depth: Maximum depth at which to include optional dependencies (default: 0)
    """

    # In "raw" mode, use NoWrapTree/Table variants and disable column truncation
    no_wrap = get_wrap_mode() == "raw"

    if list_mode:
        # Flat list mode - use Rich for colored output
        from .rich.formatters import format_dependency_list_rich

        # Get the dependency list
        root, deps = context.resolver.get_dependency_list(
            components,
            managed=bool(boms),
            boms=boms,
            transitive=not direct_only,
            optional_depth=optional_depth,
        )

        # Format and print using Rich
        # Pass soft_wrap for raw mode to enable natural terminal wrapping
        lines = format_dependency_list_rich(root, deps)
        for line in lines:
            _console.print(line, highlight=False, soft_wrap=no_wrap)
    else:
        # Tree mode - use Rich Tree for beautiful colored output
        from .rich.formatters import format_dependency_tree_rich

        # Get the dependency tree
        tree = context.resolver.get_dependency_tree(
            components,
            managed=bool(boms),
            boms=boms,
            optional_depth=optional_depth,
        )

        # Format and print using Rich
        # Use NoWrapTree when wrap mode is "raw" and pass soft_wrap for natural wrapping
        rich_tree = format_dependency_tree_rich(tree, no_wrap=no_wrap)
        _console.print(rich_tree, soft_wrap=no_wrap)


def print_java_info(environment: Environment) -> None:
    """
    Print detailed Java version requirements for the environment.

    Args:
        environment: The resolved environment
    """
    from rich.panel import Panel

    from jgo.env.bytecode import (
        analyze_jar_bytecode,
        bytecode_to_java_version,
        round_to_lts,
    )

    from .rich.widgets import create_table

    # In "raw" mode, use NoWrapTable variant and disable column truncation
    no_wrap = get_wrap_mode() == "raw"

    # Get all JARs from both jars/ and modules/ directories
    jar_files = environment.all_jars
    if not jar_files:
        _err_console.print("[red]No JARs in environment[/]")
        return

    # Print environment info
    _console.print(f"\n[bold]Environment:[/] {environment.path}")
    if environment.has_classpath:
        _console.print(f"[bold]Class-path JARs:[/] {len(environment.class_path_jars)}")
    if environment.has_modules:
        _console.print(
            f"[bold]Module-path JARs:[/] {len(environment.module_path_jars)}"
        )
    _console.print(f"[bold]Total JARs:[/] {len(jar_files)}\n")

    # Analyze each JAR
    jar_analyses = []
    overall_max_java = None

    for jar_path in jar_files:
        analysis = analyze_jar_bytecode(jar_path)
        if analysis and analysis.get("java_version"):
            jar_analyses.append((jar_path.name, analysis))
            java_ver = analysis["java_version"]
            if overall_max_java is None or java_ver > overall_max_java:
                overall_max_java = java_ver

    # Sort by Java version (highest first)
    jar_analyses.sort(key=lambda x: x[1]["java_version"], reverse=True)

    # Print summary in a panel
    lts_version = round_to_lts(overall_max_java) if overall_max_java else None
    summary_text = f"[bold cyan]Minimum Java version:[/] {overall_max_java}\n"
    if lts_version != overall_max_java:
        summary_text += f"[bold cyan]Rounded to LTS:[/] {lts_version}"
    else:
        summary_text += "[dim](already an LTS version)[/]"

    summary_panel = Panel(
        summary_text,
        title="[bold]Java Version Requirements[/]",
        border_style="cyan",
    )
    _console.print(summary_panel)

    # Print per-JAR analysis in a table
    # Use NoWrapTable when wrap mode is "raw" to show full JAR names
    table = create_table(
        no_wrap=no_wrap,
        title="Per-JAR Analysis",
        show_header=True,
        header_style="bold cyan",
    )
    # When wrap mode is "raw", disable column truncation
    table.add_column("JAR", style="bold", no_wrap=no_wrap)
    table.add_column("Java Version", justify="right", style="green")
    table.add_column("Max Bytecode", justify="right")
    table.add_column("Class Count", justify="right")

    for jar_name, analysis in jar_analyses:
        java_ver = analysis["java_version"]
        max_bytecode = analysis["max_version"]
        version_counts = analysis["version_counts"]
        total_classes = sum(version_counts.values())

        table.add_row(
            jar_name,
            str(java_ver),
            str(max_bytecode),
            str(total_classes),
        )

    _console.print(table, soft_wrap=no_wrap)

    # Print detailed breakdown for JARs with mixed bytecode versions
    _console.print("\n[bold]Bytecode Version Details:[/]")
    for jar_name, analysis in jar_analyses[:10]:  # Show first 10 for brevity
        java_ver = analysis["java_version"]
        version_counts = analysis["version_counts"]

        # Only show details if there are multiple bytecode versions
        if len(version_counts) > 1:
            _console.print(f"\n[cyan]{jar_name}[/]")

            # Show distribution
            for bytecode_ver in sorted(version_counts.keys(), reverse=True):
                count = version_counts[bytecode_ver]
                java_v = bytecode_to_java_version(bytecode_ver)
                _console.print(
                    f"  Java {java_v:2d} (bytecode {bytecode_ver}): {count:5d} classes"
                )

            # Show high-version classes if applicable
            high_classes = analysis["high_version_classes"]
            max_ver = high_classes[0][1] if high_classes else None
            high_ver_only = [
                (name, ver) for name, ver in high_classes if ver == max_ver
            ]
            if high_ver_only and len(high_ver_only) <= 5:
                _console.print(f"  [dim]Classes requiring Java {java_ver}:[/]")
                for class_name, _ in high_ver_only:
                    _console.print(f"    - {class_name}")

    if len(jar_analyses) > 10:
        _console.print(
            f"\n[dim]... and {len(jar_analyses) - 10} more JARs (showing first 10)[/]"
        )
