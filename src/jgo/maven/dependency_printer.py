"""
Dependency printing utilities.

Provides common data structures and formatting logic for dependency lists and trees,
used by both SimpleResolver and MavenResolver to ensure consistent output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import Dependency


@dataclass
class DependencyNode:
    """
    Represents a dependency in a dependency tree or list.

    This is a common data structure returned by both SimpleResolver and MavenResolver,
    allowing for consistent formatting regardless of the resolution mechanism.
    """

    dep: Dependency
    children: list["DependencyNode"] = field(default_factory=list)

    def __str__(self):
        return str(self.dep)
        # return self.coordinate_string()

    def coordinate_string(self, include_scope: bool = True) -> str:
        # FIXME: Reconcile with Dependency __str__
        """
        Format this node as a Maven coordinate string.

        Args:
            include_scope: Whether to include the scope suffix (e.g., ":runtime")

        Returns:
            Formatted coordinate string like "groupId:artifactId:packaging[:classifier]:version[:scope]"
        """
        parts = [self.dep.groupId, self.dep.artifactId, self.dep.artifact.packaging]

        # Add classifier if present
        if self.dep.classifier:
            parts.append(self.dep.classifier)

        # Add version
        parts.append(self.dep.version)

        coord = ":".join(parts)

        # Add scope suffix if requested and scope is not compile (default)
        if include_scope and self.dep.scope and self.dep.scope != "compile":
            coord += f":{self.dep.scope}"

        # Add optional marker if applicable
        if self.dep.optional:
            coord += " (optional)"

        return coord


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
        coord = dep.coordinate_string(include_scope=True)
        lines.append(f"   {coord}")

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
            coord = node.coordinate_string(include_scope=False)

            # Add scope if not compile
            if node.dep.scope and node.dep.scope != "compile":
                coord += f":{node.dep.scope}"

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
            is_last = i == len(root.children) - 1
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
