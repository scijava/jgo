"""
Dependency printing utilities.

Provides formatting logic for dependency lists and trees,
used by both PythonResolver and MvnResolver to ensure consistent output.
"""

from __future__ import annotations

from rich.tree import Tree

from ..util.rich_utils import NoWrapTree
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


def format_dependency_list_rich(
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

    def format_coord(dep_node: DependencyNode) -> str:
        """Format a coordinate with Rich color markup."""
        coord = (
            f"[bold cyan]{dep_node.dep.groupId}[/]:"
            f"[bold]{dep_node.dep.artifactId}[/]:"
            f"[green]{dep_node.dep.version}[/]"
        )
        if dep_node.dep.optional:
            coord += " [dim](optional)[/]"
        return coord

    # Skip INTERNAL-WRAPPER root and print its children instead
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Print direct dependencies (the actual components)
        for child in root.children:
            lines.append(format_coord(child))
    else:
        # Print root component if it's not INTERNAL-WRAPPER
        lines.append(format_coord(root))

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

            # Format with colors
            colored = (
                f"   [bold cyan]{group_id}[/]:"
                f"[bold]{artifact_id}[/]:"
                f"{packaging}:"
                f"[green]{version}[/]"
            )
            if scope:
                colored += f":[dim]{scope}[/]"

            lines.append(colored)
        else:
            # Fallback for unexpected format
            lines.append(f"   {dep}")

    return lines


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


def format_dependency_tree_rich(root: DependencyNode, no_wrap: bool = False) -> Tree:
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

    def add_children_rich(tree: Tree, nodes: list[DependencyNode]):
        """Recursively add child nodes to Rich tree."""
        for node in nodes:
            # Format coordinate with colors
            coord = (
                f"[bold cyan]{node.dep.groupId}[/]:"
                f"[bold]{node.dep.artifactId}[/]:"
                f"[green]{node.dep.version}[/]"
            )

            # Add optional marker
            if node.dep.optional:
                coord += " [dim](optional)[/]"

            # Add branch and recurse
            branch = tree.add(coord)
            if node.children:
                add_children_rich(branch, node.children)

    # Skip INTERNAL-WRAPPER root and treat children as top-level
    if (
        root.dep.groupId == "org.apposed.jgo"
        and root.dep.artifactId == "INTERNAL-WRAPPER"
    ):
        # Create invisible root for multiple top-level items
        tree = TreeClass("")
        for child in root.children:
            coord = (
                f"[bold cyan]{child.dep.groupId}[/]:"
                f"[bold]{child.dep.artifactId}[/]:"
                f"[green]{child.dep.version}[/]"
            )
            branch = tree.add(coord)
            if child.children:
                add_children_rich(branch, child.children)
    else:
        # Create tree with root as label
        coord = (
            f"[bold cyan]{root.dep.groupId}[/]:"
            f"[bold]{root.dep.artifactId}[/]:"
            f"[green]{root.dep.version}[/]"
        )
        tree = TreeClass(coord)
        if root.children:
            add_children_rich(tree, root.children)

    return tree
