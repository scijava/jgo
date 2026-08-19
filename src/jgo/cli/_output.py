"""
Output formatting functions for CLI commands.

These functions handle printing classpath, dependencies, Java info,
and user-facing messages in various formats with consistent styling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.panel import Panel

from ..env import (
    analyze_class_file,
    analyze_jar_bytecode,
    bytecode_to_java_version,
    find_main_classes,
    round_to_lts,
)
from ..styles import critical, filepath, header, secondary, tip, warning
from ._console import console_print, get_wrap_mode
from .rich._formatters import format_dependency_list, format_dependency_tree
from .rich._widgets import create_table

if TYPE_CHECKING:
    from pathlib import Path

    from ..env import Environment, JarCoordinate
    from ..maven import Dependency, MavenContext
    from ._args import ParsedArgs


# === Message Output Functions ===


def print_dry_run(message: str) -> None:
    """
    Print a dry-run message.

    Args:
        message: Dry-run message (e.g., "Would add 5 dependencies")
    """
    from ..styles import STYLES

    console_print(f"[{STYLES['header']}]\\[DRY-RUN] {message}", highlight=False)


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
        console_print(critical("No JARs on classpath"), stderr=True)
        console_print(
            tip("Use 'jgo info modulepath' to see module-path JARs"),
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
        console_print(critical("No JARs on module-path"), stderr=True)
        console_print(
            tip("Use 'jgo info classpath' to see classpath JARs"), stderr=True
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
        console_print(critical("No JARs in environment"), stderr=True)
        return

    # Print classpath JARs
    if cp_jars:
        console_print(header("Classpath:"))
        for jar_path in cp_jars:
            console_print(jar_path)
    else:
        console_print(warning("No classpath JARs"))

    # Print module-path JARs
    if mp_jars:
        if cp_jars:
            console_print(f"\n{header('Module-path:')}")
        else:
            console_print(header("Module-path:"))
        for jar_path in mp_jars:
            console_print(jar_path)
    else:
        console_print(warning("No module-path JARs"))


def print_main_classes(environment: Environment) -> None:
    """
    Print all classes with public static void main(String[]) methods.

    Args:
        environment: The resolved environment
    """

    all_jars = environment.all_jars
    if not all_jars:
        console_print(critical("No JARs in environment"), stderr=True)
        return

    # Scan all JARs for main classes
    main_classes_by_jar = {}
    for jar_path in all_jars:
        main_classes = find_main_classes(jar_path)
        if main_classes:
            main_classes_by_jar[jar_path.name] = main_classes

    if not main_classes_by_jar:
        console_print(warning("No classes with main methods found"), stderr=True)
        return

    # Print results grouped by JAR
    count = sum(len(v) for v in main_classes_by_jar.values())
    console_print(f"\n{header(f'Found {count} classes with main methods:')}\n")

    for jar_name, main_classes in sorted(main_classes_by_jar.items()):
        console_print(f"{filepath(jar_name)}:")
        for cls in main_classes:
            console_print(f"  {cls}")
        console_print()


def print_dependencies(
    dependencies: list[Dependency],
    context: MavenContext,
    list_mode: bool = False,
    direct_only: bool = False,
    optional_depth: int = 0,
) -> None:
    """
    Print dependencies for the given input dependencies.

    Args:
        dependencies: List of input dependencies to print
        context: Maven context containing the resolver
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
            dependencies,
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
            dependencies,
            optional_depth=optional_depth,
        )

        # Format and print using Rich
        # Use NoWrapTree when wrap mode is "raw"
        rich_tree = format_dependency_tree(tree, no_wrap=no_wrap)
        console_print(rich_tree)


def print_pom_dependencies(
    pom_path: Path,
    context: MavenContext,
    list_mode: bool = False,
    direct_only: bool = False,
    optional_depth: int = 0,
) -> None:
    """
    Print dependencies for a local project POM file.

    Unlike print_dependencies(), this resolves the real POM directly (no synthetic
    wrapper), so the project itself is the tree/list root and its own parent and
    dependencyManagement govern resolution.

    Args:
        pom_path: Path to the project's pom.xml.
        context: Maven context used to build the model.
        list_mode: If True, print a flat list; otherwise print a tree.
        direct_only: If True and list_mode is True, show only direct dependencies.
        optional_depth: Maximum depth at which to include optional dependencies.
    """
    from ..maven import POM

    pom = POM(pom_path)

    if list_mode:
        root, deps = context.pom_dependency_list(
            pom, transitive=not direct_only, optional_depth=optional_depth
        )
        lines = format_dependency_list(root, deps)
        for line in lines:
            console_print(line, highlight=False)
    else:
        no_wrap = get_wrap_mode() == "raw"
        tree = context.pom_dependency_tree(pom, optional_depth=optional_depth)
        rich_tree = format_dependency_tree(tree, no_wrap=no_wrap)
        console_print(rich_tree)


@dataclass
class SourceReport:
    """
    A single analyzed ``javainfo`` source (an endpoint, POM, JAR, or class file).

    Attributes:
        label: Human-readable name of the source (coordinate, file path, etc.).
        jars: List of ``(display_name, analysis)`` pairs for each analyzable
            artifact, where ``analysis`` has the shape returned by
            :func:`analyze_jar_bytecode` / :func:`analyze_class_file`. Only
            artifacts that contain class files are included.
        env_meta: Optional environment metadata (path and JAR counts) printed for
            coordinate/endpoint sources that resolve to a full environment.
        note: Optional message shown when the source has no analyzable classes.
    """

    label: str
    jars: list[tuple[str, dict]] = field(default_factory=list)
    env_meta: dict | None = None
    note: str | None = None


def analyses_from_paths(paths: list[Path]) -> list[tuple[str, dict]]:
    """
    Analyze a list of JAR and/or ``.class`` file paths.

    Returns ``(display_name, analysis)`` pairs for each path that contains
    analyzable class files, preserving input order.
    """
    analyses = []
    for path in paths:
        if path.suffix == ".class":
            analysis = analyze_class_file(path)
        else:
            analysis = analyze_jar_bytecode(path)
        if analysis and analysis.get("java_version"):
            analyses.append((path.name, analysis))
    return analyses


def environment_report(
    environment: Environment, label: str | None = None
) -> SourceReport:
    """Build a :class:`SourceReport` from a fully resolved environment."""
    jar_files = environment.all_jars
    env_meta = {
        "path": environment.path,
        "classpath": (
            len(environment.class_path_jars) if environment.has_classpath else 0
        ),
        "modules": (
            len(environment.module_path_jars) if environment.has_modules else 0
        ),
        "total": len(jar_files),
    }
    return SourceReport(
        label=label or str(environment.path),
        jars=analyses_from_paths(jar_files),
        env_meta=env_meta,
    )


def paths_report(label: str, paths: list[Path]) -> SourceReport:
    """Build a :class:`SourceReport` from a list of JAR and/or ``.class`` paths."""
    analyses = analyses_from_paths(paths)
    note = None if analyses else "No analyzable classes found"
    return SourceReport(label=label, jars=analyses, note=note)


def _java_summary_panel(max_java: int, title: str) -> Panel:
    """Build the min-Java-version summary panel for a set of analyses."""
    lts_version = round_to_lts(max_java)
    summary_text = f"{header('Minimum Java version:')} {max_java}\n"
    if lts_version != max_java:
        summary_text += f"{header('Rounded to LTS:')} {lts_version}"
    else:
        summary_text += secondary("(already an LTS version)")
    return Panel(summary_text, title=header(title), border_style="cyan")


def print_java_info(reports: list[SourceReport]) -> None:
    """
    Print detailed Java version requirements for one or more analysis sources.

    A single source renders standalone (summary panel + per-JAR table). Multiple
    sources are grouped under per-source headers with their own subtotal, followed
    by an overall summary panel spanning every source.

    Args:
        reports: The analyzed sources to display.
    """

    if not reports:
        console_print(critical("No JARs to analyze"), stderr=True)
        return

    # In "raw" mode, use NoWrapTable variant and disable column truncation
    no_wrap = get_wrap_mode() == "raw"
    multi = len(reports) > 1
    overall_max_java = None

    for report in reports:
        if multi:
            console_print(f"\n{header('Source:')} {report.label}")

        # Environment metadata block (coordinate/endpoint sources only)
        meta = report.env_meta
        if meta is not None:
            console_print(f"\n{header('Environment:')} {meta['path']}")
            if meta["classpath"]:
                console_print(f"{header('Class-path JARs:')} {meta['classpath']}")
            if meta["modules"]:
                console_print(f"{header('Module-path JARs:')} {meta['modules']}")
            console_print(f"{header('Total JARs:')} {meta['total']}\n")

        if not report.jars:
            console_print(report.note or "No analyzable classes found")
            continue

        source_max = _render_jar_analyses(report.jars, no_wrap=no_wrap)
        if source_max is not None:
            overall_max_java = (
                source_max
                if overall_max_java is None
                else max(overall_max_java, source_max)
            )
            if multi:
                lts = round_to_lts(source_max)
                extra = "" if lts == source_max else f" (rounds to LTS {lts})"
                console_print(
                    f"{header('Source minimum Java version:')} {source_max}{extra}"
                )

    if multi and overall_max_java is not None:
        console_print(
            _java_summary_panel(overall_max_java, "Overall Java Version Requirements")
        )


def print_jar_coordinates(
    results: list[tuple[Path, list[JarCoordinate]]], *, show_all: bool = False
) -> None:
    """
    Print the Maven coordinates inferred for each of a list of JAR files.

    Each JAR gets one row for the coordinate it appears to have been built from.
    Coordinates of bundled (shaded) dependencies are summarized by count, or
    listed individually when ``show_all`` is set.

    Args:
        results: ``(jar path, coordinates)`` pairs, as returned by ``jar_coordinates``
        show_all: List bundled coordinates instead of just counting them
    """

    if not results:
        console_print(critical("No JARs to inspect"), stderr=True)
        return

    no_wrap = get_wrap_mode() == "raw"
    table = create_table(
        no_wrap=no_wrap,
        title="Artifact Coordinates",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("JAR", style="bold", no_wrap=no_wrap)
    table.add_column("Coordinate")
    table.add_column("Source")

    hidden = 0
    for jar_path, coordinates in results:
        if not coordinates:
            table.add_row(jar_path.name, warning("unidentified"), "")
            continue

        primary = coordinates[0] if coordinates[0].primary else None
        bundled = coordinates[1:] if primary else coordinates

        if primary:
            table.add_row(jar_path.name, str(primary), _source_label(primary))
        else:
            table.add_row(jar_path.name, warning("no primary coordinate"), "")

        if show_all:
            for coordinate in bundled:
                table.add_row("", f"  {coordinate}", _source_label(coordinate))
        else:
            hidden += len(bundled)
            if bundled:
                table.add_row("", secondary(f"  +{len(bundled)} bundled"), "")

    console_print(table)

    if hidden:
        console_print(tip("Use --all to list bundled coordinates"))


def _source_label(coordinate: JarCoordinate) -> str:
    """Describe where a coordinate came from, flagging the unreliable source."""
    if coordinate.source == "manifest":
        return secondary("manifest (inferred)")
    return coordinate.source


def _render_jar_analyses(
    jar_analyses: list[tuple[str, dict]], *, no_wrap: bool
) -> int | None:
    """
    Render the summary panel, per-JAR table, and bytecode details for one source.

    Returns the maximum (non-LTS-rounded) Java version across the analyses, or
    None if the list is empty.
    """

    if not jar_analyses:
        return None

    # Sort by Java version (highest first)
    jar_analyses = sorted(
        jar_analyses, key=lambda x: x[1]["java_version"], reverse=True
    )
    overall_max_java = max(a["java_version"] for _, a in jar_analyses)

    # Print summary in a panel
    console_print(_java_summary_panel(overall_max_java, "Java Version Requirements"))

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
    interesting_analyses = [
        item for item in jar_analyses if len(item[1]["version_counts"]) > 1
    ]
    max_analyses = 10

    if interesting_analyses:
        console_print(f"\n{header('Bytecode Version Details:')}")
        for jar_name, analysis in interesting_analyses[
            :max_analyses
        ]:  # Show first few for brevity
            java_ver = analysis["java_version"]
            version_counts = analysis["version_counts"]

            console_print(f"\n{filepath(jar_name)}")

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
                console_print(f"  {secondary(f'Classes requiring Java {java_ver}:')}")
                for class_name, _ in high_ver_only:
                    console_print(f"    - {class_name}")

        if len(interesting_analyses) > max_analyses:
            console_print(
                f"\n{secondary(f'... and {len(interesting_analyses) - max_analyses} more JARs with mixed bytecode versions (showing first {max_analyses})')}"
            )

    return overall_max_java
