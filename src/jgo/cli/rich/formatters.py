"""
Rich-specific dependency formatters for jgo CLI.

Provides Rich-formatted output for dependency lists and trees,
with colored markup and visual structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.tree import Tree

from ...parse.coordinate import coord2str
from ...styles import STYLES, format_tokens
from .widgets import NoWrapTree

if TYPE_CHECKING:
    from ...maven.core import DependencyNode
    from ...parse.coordinate import Coordinate


def format_coordinate(coord: Coordinate) -> str:
    """
    Format a Maven coordinate with Rich markup for semantic coloring.

    Uses Rich markup to colorize components based on their semantic meaning:
    - groupId: bold cyan
    - artifactId: bold
    - version: green
    - packaging: default color
    - classifier: default color
    - scope: dim
    - colons: dim

    The markup is automatically stripped by Rich when --color=plain is used.

    Args:
        coord: The Coordinate to format

    Returns:
        Formatted string with Rich markup

    Examples:
        >>> from jgo.parse.coordinate import Coordinate
        >>> coord = Coordinate("sc.fiji", "fiji", "2.17.0")
        >>> format_coordinate(coord)
        '[bold cyan]sc.fiji[/][dim]:[/][bold]fiji[/][dim]:[/][green]2.17.0[/]'
    """
    return coord2str(
        coord.groupId,
        coord.artifactId,
        coord.version,
        coord.classifier,
        coord.packaging,
        coord.scope,
        coord.optional,
        coord.raw,
        coord.placement,
        rich=True,
    )


def format_dependency_list(
    root: DependencyNode, dependencies: list[DependencyNode]
) -> list[str]:
    """
    Format a flat list of resolved dependencies with Rich markup for colored output.

    This shows what will actually be used when building the environment,
    after dependency mediation has been applied.

    Args:
        root: The root component
        dependencies: List of resolved dependencies

    Returns:
        List of formatted lines with Rich markup
    """

    lines = []

    def format_dep_node(dep_node: DependencyNode) -> str:
        """Format a DependencyNode coordinate with Rich color markup."""
        coord = format_tokens(
            [
                (dep_node.dep.groupId, "g"),
                (dep_node.dep.artifactId, "a"),
                (dep_node.dep.version, "v"),
            ]
        )
        if dep_node.dep.optional:
            coord += f" [{STYLES['optional']}](optional)[/]"
        return coord

    # Skip INTERNAL-WRAPPER root and print its children instead
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Print direct dependencies (the actual components)
        for child in root.children:
            lines.append(format_dep_node(child))
    else:
        # Print root component if it's not INTERNAL-WRAPPER
        lines.append(format_dep_node(root))

    # Print dependencies with indentation and coloring
    for dep in dependencies:
        # Parse the dependency string (format: groupId:artifactId:packaging:version:scope)
        parts = str(dep).split(":")
        if len(parts) >= 4:
            group_id = parts[0]
            artifact_id = parts[1]
            packaging = parts[2] if len(parts) > 2 else "jar"
            version = parts[3] if len(parts) > 3 else ""
            scope = parts[4] if len(parts) > 4 else ""

            # Format with colors using centralized styling
            colored = "   " + format_tokens(
                [
                    (group_id, "g"),
                    (artifact_id, "a"),
                    (packaging, "p"),
                    (version, "v"),
                    (scope, "s"),
                ]
            )

            lines.append(colored)
        else:
            # Fallback for unexpected format
            lines.append(f"   {dep}")

    return lines


def format_dependency_tree(root: DependencyNode, no_wrap: bool = False) -> Tree:
    """
    Format a dependency tree using Rich Tree for beautiful colored output.

    Args:
        root: The root node of the dependency tree
        no_wrap: If True, use NoWrapTree to prevent line wrapping

    Returns:
        Rich Tree object ready for printing
    """
    # Choose tree class based on no_wrap setting
    TreeClass = NoWrapTree if no_wrap else Tree

    def format_node(node: DependencyNode) -> str:
        """Format a DependencyNode for tree display."""
        coord = format_tokens(
            [
                (node.dep.groupId, "g"),
                (node.dep.artifactId, "a"),
                (node.dep.version, "v"),
            ]
        )
        if node.dep.optional:
            coord += f" [{STYLES['optional']}](optional)[/]"
        return coord

    def add_children(tree: Tree, nodes: list[DependencyNode]):
        """Recursively add child nodes to Rich tree."""
        for node in nodes:
            coord = format_node(node)
            branch = tree.add(coord)
            if node.children:
                add_children(branch, node.children)

    # Skip INTERNAL-WRAPPER root and treat children as top-level
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Create invisible root for multiple top-level items
        tree = TreeClass("")
        for child in root.children:
            branch = tree.add(format_node(child))
            if child.children:
                add_children(branch, child.children)
    else:
        # Create tree with root as label
        tree = TreeClass(format_node(root))
        if root.children:
            add_children(tree, root.children)

    return tree
