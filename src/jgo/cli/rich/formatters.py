"""
Rich-specific dependency formatters for jgo CLI.

Provides Rich-formatted output for dependency lists and trees,
with colored markup and visual structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.tree import Tree

from ...parse.coordinate import coord2str
from .widgets import NoWrapTree

if TYPE_CHECKING:
    from ...maven import DependencyNode
    from ...parse.coordinate import Coordinate


def _format_dependency(dep) -> str:
    """
    Format a Dependency object with Rich markup for colored output.

    Args:
        dep: A Dependency object with groupId, artifactId, type, classifier, version, scope, optional

    Returns:
        Formatted string with Rich markup (G:A:P:C:V:S format)
    """
    return coord2str(
        groupId=dep.groupId,
        artifactId=dep.artifactId,
        version=dep.version,
        classifier=dep.classifier,
        packaging=dep.type,
        scope=dep.scope,
        optional=dep.optional,
        display=True,
    )


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
        display=True,
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

    # Skip INTERNAL-WRAPPER root and print its children instead
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Print direct dependencies (the actual components)
        for child in root.children:
            lines.append(_format_dependency(child.dep))
    else:
        # Print root component if it's not INTERNAL-WRAPPER
        lines.append(_format_dependency(root.dep))

    # Print dependencies with indentation and coloring
    for dep in dependencies:
        # Access dependency attributes directly instead of parsing strings
        # Format: G:A:P:C:V:S (packaging, classifier, version, scope optional)
        dep_obj = dep.dep if hasattr(dep, "dep") else dep
        lines.append("   " + _format_dependency(dep_obj))

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

    def add_children(tree: Tree, nodes: list[DependencyNode]):
        """Recursively add child nodes to Rich tree."""
        for node in nodes:
            coord = _format_dependency(node.dep)
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
            branch = tree.add(_format_dependency(child.dep))
            if child.children:
                add_children(branch, child.children)
    else:
        # Create tree with root as label
        tree = TreeClass(_format_dependency(root.dep))
        if root.children:
            add_children(tree, root.children)

    return tree
