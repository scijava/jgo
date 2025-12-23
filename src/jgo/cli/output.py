"""
Output formatting functions for CLI commands.

These functions handle printing classpath, dependencies, and Java info
in various formats.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..env import Environment
    from ..maven import MavenContext
    from ..maven.core import Component


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
        output = context.resolver.print_dependency_list(
            components,
            managed=bool(boms),
            boms=boms,
            transitive=not direct_only,
        )
    else:
        output = context.resolver.print_dependency_tree(
            components,
            managed=bool(boms),
            boms=boms,
        )
    print(output)


def print_java_info(environment: Environment) -> None:
    """
    Print detailed Java version requirements for the environment.

    Args:
        environment: The resolved environment
    """
    from jgo.env.bytecode import (
        analyze_jar_bytecode,
        bytecode_to_java_version,
        round_to_lts,
    )

    jars_dir = environment.path / "jars"
    if not jars_dir.exists():
        print("No JARs directory found", file=sys.stderr)
        return

    jar_files = sorted(jars_dir.glob("*.jar"))
    if not jar_files:
        print("No JARs in environment", file=sys.stderr)
        return

    print(f"Environment: {environment.path}")
    print(f"JARs directory: {jars_dir}")
    print(f"Total JARs: {len(jar_files)}\n")

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

    # Print summary
    lts_version = round_to_lts(overall_max_java) if overall_max_java else None
    print("=" * 70)
    print("JAVA VERSION REQUIREMENTS")
    print("=" * 70)
    print(f"Detected minimum Java version: {overall_max_java}")
    if lts_version != overall_max_java:
        print(f"Rounded to LTS: {lts_version}")
    else:
        print("(already an LTS version)")
    print()

    # Print per-JAR analysis
    print("=" * 70)
    print("PER-JAR ANALYSIS")
    print("=" * 70)
    for jar_name, analysis in jar_analyses:
        java_ver = analysis["java_version"]
        max_bytecode = analysis["max_version"]
        version_counts = analysis["version_counts"]

        print(f"\n{jar_name}")
        print(f"  Required Java version: {java_ver} (bytecode {max_bytecode})")

        # Show distribution
        print("  Bytecode version distribution:")
        for bytecode_ver in sorted(version_counts.keys(), reverse=True):
            count = version_counts[bytecode_ver]
            java_v = bytecode_to_java_version(bytecode_ver)
            print(f"    Java {java_v:2d} (bytecode {bytecode_ver}): {count:5d} classes")

        # Show high-version classes if not all the same
        if len(version_counts) > 1:
            high_classes = analysis["high_version_classes"]
            max_ver = high_classes[0][1] if high_classes else None
            high_ver_only = [
                (name, ver) for name, ver in high_classes if ver == max_ver
            ]
            if high_ver_only and len(high_ver_only) <= 5:
                print(f"  Classes requiring Java {java_ver}:")
                for class_name, _ in high_ver_only:
                    print(f"    - {class_name}")

        # Show skipped files if any
        skipped = analysis.get("skipped", [])
        if skipped:
            print(f"  Skipped files (sample): {len(skipped)} files")
            for s in skipped[:3]:
                print(f"    - {s}")

    print("\n" + "=" * 70)
