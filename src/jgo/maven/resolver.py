"""
Maven artifact resolvers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import run
from typing import TYPE_CHECKING

import requests

from .core import Dependency, create_pom
from .dependency_printer import (
    DependencyNode,
    format_dependency_list,
    format_dependency_tree,
)
from .model import Model
from .pom import write_temp_pom

if TYPE_CHECKING:
    from .core import Artifact, Component

_log = logging.getLogger(__name__)


def _ensure_component_list(components: list[Component] | Component) -> list[Component]:
    """Convert single component to list for uniform handling."""
    return components if isinstance(components, list) else [components]


def _resolve_boms(
    components: list[Component], managed: bool, boms: list[Component] | None
) -> list[Component] | None:
    """Determine which components to use as BOMs."""
    if boms is None and managed:
        return components
    return boms


def _filter_component_deps(
    deps: list[Dependency], components: list[Component]
) -> list[Dependency]:
    """Remove components themselves from dependency list."""
    component_coords = {
        (comp.groupId, comp.artifactId, comp.resolved_version) for comp in components
    }
    return [
        dep
        for dep in deps
        if (dep.groupId, dep.artifactId, dep.version) not in component_coords
    ]


def _create_root(components: list[Component]) -> DependencyNode:
    """Create a synthetic root node for multi-component resolution."""
    return DependencyNode(
        Dependency(
            components[0]
            .context.project("org.apposed.jgo", "INTERNAL-WRAPPER")
            .at_version("0-SNAPSHOT")
            .artifact(packaging="pom")
        )
    )


class Resolver(ABC):
    """
    Logic for doing non-trivial Maven-related things, including:
    * downloading and caching an artifact from a remote repository; and
    * determining the dependencies of a particular Maven component.
    """

    @abstractmethod
    def download(self, artifact: Artifact) -> Path | None:
        """
        Download an artifact file from a remote repository.
        :param artifact: The artifact for which a local path should be resolved.
        :return: Local path to the saved artifact, or None if the artifact cannot be resolved.
        """
        ...

    @abstractmethod
    def dependencies(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> list[Dependency]:
        """
        Determine dependencies for the given Maven component.
        :param components: The component(s) for which to determine the dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param boms: List of components to import as BOMs in dependencyManagement.
                                   If None and managed=True, uses [component].
        :return: The list of dependencies.
        """
        ...

    @abstractmethod
    def get_dependency_list(
        self, component: Component
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        This returns the dependency data in a common format that can be used by
        the dependency printing logic to ensure consistent output across resolvers.

        :param component: The component for which to get dependencies.
        :return: Tuple of (root_node, dependencies_list) where root_node is the
                 component itself and dependencies_list is the sorted list of all
                 resolved transitive dependencies.
        """
        ...

    @abstractmethod
    def get_dependency_tree(self, component: Component) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        This returns the dependency data in a common format that can be used by
        the dependency printing logic to ensure consistent output across resolvers.

        :param component: The component for which to get the dependency tree.
        :return: DependencyNode representing the root component with children populated
                 recursively to form the complete dependency tree.
        """
        ...

    def print_dependency_list(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> str:
        """
        Print a flat list of resolved dependencies (like mvn dependency:list).
        This shows what will actually be used when building the environment.
        :param components: The component(s) for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param boms: List of components to import as BOMs. Defaults to [component].
        :return: The dependency list as a string.
        """
        root, deps = self.get_dependency_list(components, managed=managed, boms=boms)
        return format_dependency_list(root, deps)

    def print_dependency_tree(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> str:
        """
        Print the full dependency tree for the given component (like mvn dependency:tree).
        Uses proper dependency mediation - only one version per artifact.
        :param components: The component(s) for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param boms: List of components to import as BOMs. Defaults to [component].
        :return: The dependency tree as a string.
        """
        root = self.get_dependency_tree(components, managed=managed, boms=boms)
        return format_dependency_tree(root)


class SimpleResolver(Resolver):
    """
    A resolver that works by pure Python code.
    Low overhead, but less feature complete than mvn.
    """

    def download(self, artifact: Artifact) -> Path | None:
        if artifact.version.endswith("-SNAPSHOT"):
            raise RuntimeError("Downloading of snapshots is not yet implemented.")

        for remote_repo in artifact.context.remote_repos.values():
            url = f"{remote_repo}/{artifact.component.path_prefix}/{artifact.filename}"
            response: requests.Response = requests.get(url)
            if response.status_code == 200:
                # Artifact downloaded successfully.
                # TODO: Also get MD5 and SHA1 files if available.
                # And for each, if it *is* available and successfully gotten,
                # check the actual hash of the downloaded file contents against the expected one.
                cached_file = artifact.cached_path
                assert not cached_file.exists()
                cached_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cached_file, "wb") as f:
                    f.write(response.content)
                _log.debug(f"Downloaded {url} to {cached_file}")
                return cached_file

        raise RuntimeError(
            f"Artifact {artifact} not found in remote repositories "
            f"{artifact.context.remote_repos}"
        )

    def dependencies(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> list[Dependency]:
        """
        Get all dependencies for the given components.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Flat list of all transitive dependencies
        """
        components = _ensure_component_list(components)

        if not components:
            raise ValueError("At least one component is required")

        boms = _resolve_boms(components, managed, boms)

        pom = create_pom(components, boms)
        model = Model(pom, components[0].context)
        deps = model.dependencies()

        deps = _filter_component_deps(deps, components)

        # Filter out test scope dependencies (they're not needed for running the application)
        return [dep for dep in deps if dep.scope not in ("test",)]

    def get_dependency_list(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Tuple of (root_node, flat_list_of_dependencies)
        """
        components = _ensure_component_list(components)
        root = _create_root(components)

        # Add components as children of root for proper display
        for comp in components:
            comp_artifact = comp.artifact()
            comp_dep = Dependency(comp_artifact)
            root.children.append(DependencyNode(comp_dep))

        boms = _resolve_boms(components, managed, boms)

        # Synthesize a wrapper POM
        pom = create_pom(components, boms)

        # Build the model and get mediated dependencies
        model = Model(pom, components[0].context)
        deps = model.dependencies()

        deps = _filter_component_deps(deps, components)

        # Filter out test scope dependencies
        deps = [dep for dep in deps if dep.scope not in ("test",)]

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        # Convert to DependencyNode list
        dep_nodes = [DependencyNode(dep) for dep in deps]

        return root, dep_nodes

    def get_dependency_tree(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Root DependencyNode with full tree structure
        """
        components = _ensure_component_list(components)
        root = _create_root(components)
        boms = _resolve_boms(components, managed, boms)

        # Track which G:A:C:T we've already processed (version not included for mediation)
        processed = set()

        def build_tree(deps: list[Dependency]) -> list[DependencyNode]:
            """Recursively build dependency tree."""
            nodes = []
            for dep in deps:
                # Use G:A:C:T (without version) for deduplication, like Maven does
                dep_key = (dep.groupId, dep.artifactId, dep.classifier, dep.type)

                # Create node
                node = DependencyNode(dep)

                # Recursively process children if not already seen
                if dep_key not in processed:
                    processed.add(dep_key)
                    try:
                        dep_model = Model(
                            dep.artifact.component.pom(), dep.artifact.component.context
                        )
                        # Only show compile/runtime dependencies transitively
                        transitive_deps = [
                            d
                            for d in dep_model.deps.values()
                            if d.scope in ("compile", "runtime") and not d.optional
                        ]
                        if transitive_deps:
                            node.children = build_tree(transitive_deps)
                    except Exception as e:
                        _log.debug(f"Could not resolve dependencies for {dep}: {e}")

                nodes.append(node)

            return nodes

        # Add components as direct children of root
        for comp in components:
            comp_artifact = comp.artifact()
            comp_dep = Dependency(comp_artifact)
            comp_node = DependencyNode(comp_dep)

            # Build tree from component's dependencies (exclude test scope)
            comp_model = Model(comp.pom(), comp.context)
            direct_deps = [
                dep for dep in comp_model.deps.values() if dep.scope not in ("test",)
            ]
            comp_node.children = build_tree(direct_deps)

            root.children.append(comp_node)

        return root


class MavenResolver(Resolver):
    """
    A resolver that works by shelling out to mvn.
    Requires Maven to be installed.
    """

    def __init__(self, mvn_command: Path, update: bool = False, debug: bool = False):
        self.mvn_command = mvn_command
        self.mvn_flags = ["-B", "-T8"]
        if update:
            self.mvn_flags.append("-U")
        if debug:
            self.mvn_flags.append("-X")

    def download(self, artifact: Artifact) -> Path | None:
        _log.info(f"Downloading artifact: {artifact}")
        assert artifact.context.repo_cache
        assert artifact.groupId
        assert artifact.artifactId
        assert artifact.version
        assert artifact.packaging
        args = [
            f"-Dmaven.repo.local={artifact.context.repo_cache}",
            f"-DgroupId={artifact.groupId}",
            f"-DartifactId={artifact.artifactId}",
            f"-Dversion={artifact.version}",
            f"-Dpackaging={artifact.packaging}",
        ]
        if artifact.classifier:
            args.append(f"-Dclassifier={artifact.classifier}")
        if artifact.context.remote_repos:
            remote_repos = ",".join(
                f"{name}::::{url}"
                for name, url in artifact.context.remote_repos.items()
            )
            args.append(f"-DremoteRepositories={remote_repos}")

        self._mvn("dependency:get", *args)

        # The file should now exist in the local repo cache.
        assert artifact.cached_path and artifact.cached_path.exists()
        return artifact.cached_path

    def dependencies(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> list[Dependency]:
        """
        Get all dependencies for the given components.

        Args:
            components: Single component or list of components to resolve dependencies for
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Flat list of all transitive dependencies
        """
        components = _ensure_component_list(components)

        if not components:
            raise ValueError("At least one component is required")

        # Get context and repo cache from first component
        context = components[0].context
        assert context.repo_cache

        boms = _resolve_boms(components, managed, boms) or []

        # Write to temporary file (MavenResolver needs a file for mvn command)
        pom = create_pom(components, boms)
        temp_pom = write_temp_pom(pom)
        _log.debug(
            f"Created wrapper POM at {temp_pom} with {len(components)} component(s) and {len(boms)} BOM(s)"
        )

        output = self._mvn(
            "dependency:list",
            "-f",
            str(temp_pom),
            f"-Dmaven.repo.local={context.repo_cache}",
        )

        # Parse Maven's dependency:list output format:
        # Java 8:  [INFO]    groupId:artifactId:packaging:version:scope
        # Java 9+: [INFO]    groupId:artifactId:packaging:version:scope -- module module.name
        dependencies = []

        for line in output.splitlines():
            line = line.strip()
            if (
                line.startswith("[DEBUG]")
                or line.startswith("[WARNING]")
                or line.startswith("[ERROR]")
            ):
                _log.debug(line)
            if not line.startswith("[INFO]"):
                continue

            # Remove [INFO] prefix and whitespace
            content = line[6:].strip()

            # Skip non-dependency lines
            if ":" not in content:
                continue

            # Strip module information added by Java 9+ (e.g., " -- module org.junit.jupiter.api")
            if " -- module " in content:
                content = content.split(" -- module ")[0].strip()

            # Parse G:A:P[:C]:V:S format using Coordinate
            try:
                from ..parse.coordinate import Coordinate

                coord = Coordinate.parse(content)
            except ValueError:
                # Not a valid coordinate format
                continue

            # Check if this looks like a dependency (has scope)
            if not coord.scope or coord.scope not in (
                "compile",
                "runtime",
                "provided",
                "test",
                "system",
                "import",
            ):
                continue

            # Create dependency object from coordinate
            dep = context.create_dependency(coord)
            dependencies.append(dep)

        return _filter_component_deps(dependencies, components)

    def get_dependency_list(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Tuple of (root_node, flat_list_of_dependencies)
        """
        components = _ensure_component_list(components)
        root = _create_root(components)

        # Add components as children of root for proper display
        for comp in components:
            comp_artifact = comp.artifact()
            comp_dep = Dependency(comp_artifact)
            root.children.append(DependencyNode(comp_dep))

        # Get dependencies using existing method
        deps = self.dependencies(components, managed=managed, boms=boms)

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        # Convert to DependencyNode list
        dep_nodes = [DependencyNode(dep) for dep in deps]

        return root, dep_nodes

    def get_dependency_tree(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
    ) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement

        Returns:
            Root DependencyNode with full tree structure
        """
        components = _ensure_component_list(components)

        if not components:
            raise ValueError("At least one component is required")

        context = components[0].context
        assert context.repo_cache

        boms = _resolve_boms(components, managed, boms) or []

        # Write to temporary file (MavenResolver needs a file for mvn command)
        pom = create_pom(components, boms)
        temp_pom = write_temp_pom(pom)
        _log.debug(
            f"Created wrapper POM at {temp_pom} with {len(components)} component(s) and {len(boms)} BOM(s)"
        )

        output = self._mvn(
            "dependency:tree",
            "-f",
            str(temp_pom),
            f"-Dmaven.repo.local={context.repo_cache}",
        )

        # Parse the tree output
        # Format: [INFO] org.apposed.jgo:INTERNAL-WRAPPER:jar:0-SNAPSHOT
        #         [INFO] \- org.example:my-component:pom:1.2.3:compile
        #         [INFO]    +- dep1:jar:1.0:scope
        #         [INFO]    |  \- dep2:jar:2.0:scope
        #         [INFO]    \- dep3:jar:3.0:scope

        lines = output.splitlines()
        root = None
        stack = []  # Stack of (indent_level, node)

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped.startswith("[INFO]"):
                continue

            # Remove [INFO] prefix
            content = line[6:]  # Skip "[INFO] "

            # Skip lines that don't look like dependencies
            # (e.g., "Building ...", "Finished at:", etc.)
            if ":" not in content:
                continue

            # Skip lines that contain common Maven status messages
            skip_patterns = [
                "Finished at:",
                "Total time:",
                "Building ",
                "from ",
                "---",
                "Scanning",
            ]
            if any(pattern in content for pattern in skip_patterns):
                continue

            # Determine indentation level by counting tree characters
            indent = 0
            for char in content:
                if char in " |+\\-":
                    indent += 1
                else:
                    break

            # Clean up tree characters to get just the coordinate
            clean_content = content.lstrip(" |+\\-")

            if not clean_content or ":" not in clean_content:
                continue

            # Strip module information added by Java 9+ (e.g., " -- module org.junit.jupiter.api")
            if " -- module " in clean_content:
                clean_content = clean_content.split(" -- module ")[0].strip()

            # Parse G:A:P[:C]:V[:S] format using Coordinate
            try:
                from ..parse.coordinate import Coordinate

                coord = Coordinate.parse(clean_content)
            except ValueError:
                # Not a valid coordinate format
                continue

            # Create dependency and node
            dep = context.create_dependency(coord)
            node = DependencyNode(dep)

            # Handle root node (no indent)
            if indent == 0 or root is None:
                root = node
                stack = [(0, root)]
            else:
                # Find parent by popping stack until we find correct indent level
                while stack and stack[-1][0] >= indent:
                    stack.pop()

                if stack:
                    parent_indent, parent_node = stack[-1]
                    parent_node.children.append(node)

                stack.append((indent, node))

        return root if root else DependencyNode(Dependency(components[0].artifact()))

    def _mvn(self, *args) -> str:
        return MavenResolver._run(self.mvn_command, *self.mvn_flags, *args)

    @staticmethod
    def _run(command, *args) -> str:
        command_and_args = (command,) + args
        _log.debug(f"Executing: {command_and_args}")
        result = run(command_and_args, capture_output=True)
        if result.returncode == 0:
            return result.stdout.decode()

        error_message = (
            f"Command failed with exit code {result.returncode}:\n{command_and_args}"
        )
        if result.stdout:
            error_message += f"\n\n[stdout]\n{result.stdout.decode()}"
        if result.stderr:
            error_message += f"\n\n[stderr]\n{result.stderr.decode()}"
        raise RuntimeError(error_message)
