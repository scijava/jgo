"""
Dependency formatting utilities.

Provides plain-text formatting logic for dependency lists and trees,
used by both PythonResolver and MvnResolver to ensure consistent output.

For Rich-formatted output (with colors and visual structure), see
jgo.cli.rich.formatters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import DependencyNode


def format_dependency_list(
    root: DependencyNode, dependencies: list[DependencyNode]
) -> str:
    """
    Format a flat list of resolved dependencies (like mvn dependency:list).

    This shows what will actually be used when building the environment,
    after dependency mediation has been applied.

    Args:
        root: The root component
        dependencies: List of resolved dependencies

    Returns:
        Formatted dependency list as a string
    """

    lines = []

    # Skip INTERNAL-WRAPPER root and print its children instead
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Print direct dependencies (the actual components)
        for child in root.children:
            lines.append(
                f"{child.dep.groupId}:{child.dep.artifactId}:{child.dep.version}"
            )
    else:
        # Print root component if it's not INTERNAL-WRAPPER
        lines.append(f"{root.dep.groupId}:{root.dep.artifactId}:{root.dep.version}")

    # Print dependencies with indentation
    for dep in dependencies:
        lines.append(f"   {dep}")

    return "\n".join(lines)


def format_dependency_tree(root: DependencyNode) -> str:
    """
    Format a dependency tree (like mvn dependency:tree).

    Uses Unicode box-drawing characters for a clean tree visualization.

    Args:
        root: The root node of the dependency tree

    Returns:
        Formatted dependency tree as a string
    """

    lines = []

    def add_children(nodes: list[DependencyNode], prefix: str = ""):
        """Recursively add child nodes to the tree."""
        for i, node in enumerate(nodes):
            is_last_child = i == len(nodes) - 1

            # Determine connectors
            connector = "└── " if is_last_child else "├── "
            extension = "    " if is_last_child else "│   "

            # Format node
            coord = str(node)

            # Add optional marker
            if node.dep.optional:
                coord += " (optional)"

            line = f"{prefix}{connector}{coord}"
            lines.append(line)

            # Recursively add children
            if node.children:
                add_children(node.children, prefix + extension)

    # Skip INTERNAL-WRAPPER root and print its children as top-level instead
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Treat children as roots (no prefix, no connector)
        for i, child in enumerate(root.children):
            lines.append(
                f"{child.dep.groupId}:{child.dep.artifactId}:{child.dep.version}"
            )
            if child.children:
                add_children(child.children)
    else:
        # Print root if it's not INTERNAL-WRAPPER
        lines.append(f"{root.dep.groupId}:{root.dep.artifactId}:{root.dep.version}")
        if root.children:
            add_children(root.children)

    return "\n".join(lines)
