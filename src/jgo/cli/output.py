"""
Output formatting functions for CLI commands.

These functions handle printing classpath, dependencies, Java info,
and user-facing messages in various formats with consistent styling.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ..env import Environment
    from ..maven import MavenContext
    from ..maven.core import Component


# === Console Instances ===

# Create console instances that automatically handle color detection
# They respect NO_COLOR env var and TTY detection
_console = Console()  # For stdout
_err_console = Console(stderr=True)  # For stderr


# === Message Output Functions ===


def print_message(message: str, prefix: str = "", indent: int = 0, file=None) -> None:
    """
    Print a general message with optional prefix and indentation.

    Used for dry-run messages, informational output, etc.

    Args:
        message: Message to print
        prefix: Optional prefix (e.g., "DRY-RUN:")
        indent: Number of spaces to indent (default: 0)
        file: File to write to (default: stdout)
    """
    console = _err_console if file is sys.stderr else _console
    indentation = " " * indent

    if prefix:
        full_message = f"{indentation}{prefix} {message}"
    else:
        full_message = f"{indentation}{message}"

    console.print(full_message, highlight=False)


def print_success(message: str, indent: int = 0) -> None:
    """
    Print a success message (green if colors supported).

    Used for: "Added 5 dependencies", "Environment built successfully", etc.

    Args:
        message: Success message to print
        indent: Number of spaces to indent (default: 0)
    """
    indentation = " " * indent
    _console.print(f"{indentation}{message}", highlight=False)


def print_dry_run(message: str) -> None:
    """
    Print a dry-run message.

    Args:
        message: Dry-run message (e.g., "Would add 5 dependencies")
    """
    _console.print(r"[cyan bold]\[DRY-RUN] " + message, highlight=False)


# === Data Output Functions ===


def print_table_header(title: str, width: int = 70, char: str = "=") -> None:
    """
    Print a formatted table header.

    Args:
        title: Header title
        width: Width of the header line
        char: Character to use for the line (default: "=")
    """
    print(char * width)
    print(title)
    print(char * width)


def print_table_section(title: str, width: int = 70, char: str = "-") -> None:
    """
    Print a formatted table section separator.

    Args:
        title: Section title
        width: Width of the separator line
        char: Character to use for the line (default: "-")
    """
    print(f"\n{title}")
    print(char * width)


def print_key_value(key: str, value: str, indent: int = 2) -> None:
    """
    Print a key-value pair with consistent formatting.

    Args:
        key: Key name
        value: Value
        indent: Number of spaces to indent (default: 2)
    """
    indentation = " " * indent
    print(f"{indentation}{key}: {value}")


def print_list_item(item: str, indent: int = 2, marker: str = "-") -> None:
    """
    Print a list item with consistent formatting.

    Args:
        item: Item text
        indent: Number of spaces to indent (default: 2)
        marker: List marker character (default: "-")
    """
    indentation = " " * indent
    print(f"{indentation}{marker} {item}")


# === Existing Data Output Functions ===


def print_classpath(environment: Environment) -> None:
    """
    Print environment classpath.

    Args:
        environment: The resolved environment
    """
    classpath = environment.classpath
    if not classpath:
        print("No JARs in classpath", file=sys.stderr)
        return

    separator = ";" if sys.platform == "win32" else ":"
    classpath_str = separator.join(str(p) for p in classpath)
    print(classpath_str)


def print_dependencies(
    components: list[Component],
    context: MavenContext,
    boms: list[Component] | None = None,
    list_mode: bool = False,
    direct_only: bool = False,
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
    """
    if list_mode:
        # Flat list mode - use Rich for colored output
        from ..maven.dependency_printer import format_dependency_list_rich

        # Get the dependency list
        root, deps = context.resolver.get_dependency_list(
            components,
            managed=bool(boms),
            boms=boms,
            transitive=not direct_only,
        )

        # Format and print using Rich
        lines = format_dependency_list_rich(root, deps)
        for line in lines:
            _console.print(line, highlight=False)
    else:
        # Tree mode - use Rich Tree for beautiful colored output
        from ..maven.dependency_printer import format_dependency_tree_rich

        # Get the dependency tree
        tree = context.resolver.get_dependency_tree(
            components,
            managed=bool(boms),
            boms=boms,
        )

        # Format and print using Rich
        rich_tree = format_dependency_tree_rich(tree)
        _console.print(rich_tree)


def print_java_info(environment: Environment) -> None:
    """
    Print detailed Java version requirements for the environment.

    Args:
        environment: The resolved environment
    """
    from rich.panel import Panel
    from rich.table import Table

    from jgo.env.bytecode import (
        analyze_jar_bytecode,
        bytecode_to_java_version,
        round_to_lts,
    )

    jars_dir = environment.path / "jars"
    if not jars_dir.exists():
        _err_console.print("[red]No JARs directory found[/]")
        return

    jar_files = sorted(jars_dir.glob("*.jar"))
    if not jar_files:
        _err_console.print("[red]No JARs in environment[/]")
        return

    # Print environment info
    _console.print(f"\n[bold]Environment:[/] {environment.path}")
    _console.print(f"[bold]JARs directory:[/] {jars_dir}")
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
    table = Table(title="Per-JAR Analysis", show_header=True, header_style="bold cyan")
    table.add_column("JAR", style="bold", no_wrap=False, max_width=40)
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

    _console.print(table)

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
