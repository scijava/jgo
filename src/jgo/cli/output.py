"""
Output formatting functions for CLI commands.

These functions handle printing classpath, dependencies, Java info,
and user-facing messages in various formats with consistent styling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from ..env.bytecode import (
    analyze_jar_bytecode,
    bytecode_to_java_version,
    round_to_lts,
)
from ..env.jar import find_main_classes
from .console import console_print, get_wrap_mode
from .rich.formatters import format_dependency_list, format_dependency_tree
from .rich.widgets import create_table

if TYPE_CHECKING:
    from ..env import Environment
    from ..maven import MavenContext
    from ..maven.core import Component
    from .args import ParsedArgs


# === Message Output Functions ===


def print_dry_run(message: str) -> None:
    """
    Print a dry-run message.

    Args:
        message: Dry-run message (e.g., "Would add 5 dependencies")
    """
    console_print(r"[cyan bold]\[DRY-RUN] " + message, highlight=False)


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
        console_print("[red]No JARs on classpath[/]", stderr=True)
        console_print(
            "[dim]TIP: Use 'jgo info module-path' to see module-path JARs[/]",
            stderr=True,
        )
        return

    # Print one classpath element per line
    for jar_path in class_path_jars:
        console_print(jar_path)


def print_modulepath(environment: Environment) -> None:
    """
    Print environment module-path.

    Args:
        environment: The resolved environment
    """
    # Get module-path JARs only (module-path, not classpath)
    module_jars = environment.module_path_jars
    if not module_jars:
        console_print("[red]No JARs on module-path[/]", stderr=True)
        console_print(
            "[dim]TIP: Use 'jgo info classpath' to see classpath JARs[/]", stderr=True
        )
        return

    # Print one module-path element per line
    for jar_path in module_jars:
        console_print(jar_path)


def print_jars(environment: Environment) -> None:
    """
    Print all JAR paths (both classpath and module-path) with section headers.

    Args:
        environment: The resolved environment
    """
    cp_jars = environment.class_path_jars
    mp_jars = environment.module_path_jars

    if not cp_jars and not mp_jars:
        console_print("[red]No JARs in environment[/]", stderr=True)
        return

    # Print classpath JARs
    if cp_jars:
        console_print("[bold cyan]Classpath:[/]")
        for jar_path in cp_jars:
            console_print(jar_path)
    else:
        console_print("[yellow]No classpath JARs[/]")

    # Print module-path JARs
    if mp_jars:
        if cp_jars:
            console_print("\n[bold cyan]Module-path:[/]")
        else:
            console_print("[bold cyan]Module-path:[/]")
        for jar_path in mp_jars:
            console_print(jar_path)
    else:
        console_print("[yellow]No module-path JARs[/]")


def print_main_classes(environment: Environment) -> None:
    """
    Print all classes with public static void main(String[]) methods.

    Args:
        environment: The resolved environment
    """

    all_jars = environment.all_jars
    if not all_jars:
        console_print("[red]No JARs in environment[/]", stderr=True)
        return

    # Scan all JARs for main classes
    main_classes_by_jar = {}
    for jar_path in all_jars:
        main_classes = find_main_classes(jar_path)
        if main_classes:
            main_classes_by_jar[jar_path.name] = main_classes

    if not main_classes_by_jar:
        console_print("[yellow]No classes with main methods found[/]", stderr=True)
        return

    # Print results grouped by JAR
    console_print(
        f"\n[bold]Found {sum(len(v) for v in main_classes_by_jar.values())} classes with main methods:[/]\n"
    )

    for jar_name, main_classes in sorted(main_classes_by_jar.items()):
        console_print(f"[cyan]{jar_name}[/]:")
        for cls in main_classes:
            console_print(f"  {cls}")
        console_print()


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

        # Get the dependency list
        root, deps = context.resolver.get_dependency_list(
            components,
            managed=bool(boms),
            boms=boms,
            transitive=not direct_only,
            optional_depth=optional_depth,
        )

        # Format and print using Rich
        # console_print auto-handles soft_wrap based on wrap mode
        lines = format_dependency_list(root, deps)
        for line in lines:
            console_print(line, highlight=False)
    else:
        # Tree mode - use Rich Tree for beautiful colored output

        # Get the dependency tree
        tree = context.resolver.get_dependency_tree(
            components,
            managed=bool(boms),
            boms=boms,
            optional_depth=optional_depth,
        )

        # Format and print using Rich
        # Use NoWrapTree when wrap mode is "raw"
        rich_tree = format_dependency_tree(tree, no_wrap=no_wrap)
        console_print(rich_tree)


def print_java_info(environment: Environment) -> None:
    """
    Print detailed Java version requirements for the environment.

    Args:
        environment: The resolved environment
    """

    # In "raw" mode, use NoWrapTable variant and disable column truncation
    no_wrap = get_wrap_mode() == "raw"

    # Get all JARs from both jars/ and modules/ directories
    jar_files = environment.all_jars
    if not jar_files:
        console_print("[red]No JARs in environment[/]", stderr=True)
        return

    # Print environment info
    console_print(f"\n[bold]Environment:[/] {environment.path}")
    if environment.has_classpath:
        console_print(f"[bold]Class-path JARs:[/] {len(environment.class_path_jars)}")
    if environment.has_modules:
        console_print(f"[bold]Module-path JARs:[/] {len(environment.module_path_jars)}")
    console_print(f"[bold]Total JARs:[/] {len(jar_files)}\n")

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
    console_print(summary_panel)

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

    console_print(table)

    # Print detailed breakdown for JARs with mixed bytecode versions
    console_print("\n[bold]Bytecode Version Details:[/]")
    for jar_name, analysis in jar_analyses[:10]:  # Show first 10 for brevity
        java_ver = analysis["java_version"]
        version_counts = analysis["version_counts"]

        # Only show details if there are multiple bytecode versions
        if len(version_counts) > 1:
            console_print(f"\n[cyan]{jar_name}[/]")

            # Show distribution
            for bytecode_ver in sorted(version_counts.keys(), reverse=True):
                count = version_counts[bytecode_ver]
                java_v = bytecode_to_java_version(bytecode_ver)
                console_print(
                    f"  Java {java_v:2d} (bytecode {bytecode_ver}): {count:5d} classes"
                )

            # Show high-version classes if applicable
            high_classes = analysis["high_version_classes"]
            max_ver = high_classes[0][1] if high_classes else None
            high_ver_only = [
                (name, ver) for name, ver in high_classes if ver == max_ver
            ]
            if high_ver_only and len(high_ver_only) <= 5:
                console_print(f"  [dim]Classes requiring Java {java_ver}:[/]")
                for class_name, _ in high_ver_only:
                    console_print(f"    - {class_name}")

    if len(jar_analyses) > 10:
        console_print(
            f"\n[dim]... and {len(jar_analyses) - 10} more JARs (showing first 10)[/]"
        )
