"""
Dependency printing utilities.

Provides common data structures and formatting logic for dependency lists and trees,
used by both SimpleResolver and MavenResolver to ensure consistent output.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyNode:
    """
    Represents a dependency in a dependency tree or list.

    This is a common data structure returned by both SimpleResolver and MavenResolver,
    allowing for consistent formatting regardless of the resolution mechanism.
    """

    groupId: str
    artifactId: str
    version: str
    packaging: str = "jar"
    classifier: str | None = None
    scope: str | None = None
    optional: bool = False
    children: list["DependencyNode"] = field(default_factory=list)

    def coordinate_string(self, include_scope: bool = True) -> str:
        """
        Format this node as a Maven coordinate string.

        Args:
            include_scope: Whether to include the scope suffix (e.g., ":runtime")

        Returns:
            Formatted coordinate string like "groupId:artifactId:packaging[:classifier]:version[:scope]"
        """
        parts = [self.groupId, self.artifactId, self.packaging]

        # Add classifier if present
        if self.classifier:
            parts.append(self.classifier)

        # Add version
        parts.append(self.version)

        coord = ":".join(parts)

        # Add scope suffix if requested and scope is not compile (default)
        if include_scope and self.scope and self.scope != "compile":
            coord += f":{self.scope}"

        # Add optional marker if applicable
        if self.optional:
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
        dependencies: List of resolved dependencies (should be sorted)

    Returns:
        Formatted dependency list as a string
    """
    lines = []

    # Print root component
    lines.append(f"{root.groupId}:{root.artifactId}:{root.version}")

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

    # Print root
    lines.append(f"{root.groupId}:{root.artifactId}:{root.version}")

    def add_children(
        nodes: list[DependencyNode], prefix: str = "", is_last: bool = True
    ):
        """Recursively add child nodes to the tree."""
        for i, node in enumerate(nodes):
            is_last_child = i == len(nodes) - 1

            # Determine connectors
            connector = "└── " if is_last_child else "├── "
            extension = "    " if is_last_child else "│   "

            # Format node
            coord = node.coordinate_string(include_scope=False)

            # Add scope if not compile
            if node.scope and node.scope != "compile":
                coord += f":{node.scope}"

            # Add optional marker
            if node.optional:
                coord += " (optional)"

            line = f"{prefix}{connector}{coord}"
            lines.append(line)

            # Recursively add children
            if node.children:
                add_children(node.children, prefix + extension, is_last_child)

    # Add children of root
    if root.children:
        add_children(root.children)

    return "\n".join(lines)
