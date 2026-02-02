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

from ..parse.coordinate import Coordinate
from .core import Dependency, DependencyNode, create_pom
from .model import Model, ProfileConstraints
from .pom import write_temp_pom

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager
    from typing import List, TypeVar

    from .core import Artifact, Component

    T = TypeVar("T")

    # Type for progress callback:
    # Receives (filename, total_size) and returns a context manager
    # that yields an update function that accepts bytes_count
    ProgressCallback = Callable[
        [str, int], AbstractContextManager[Callable[[int], None]]
    ]


_log = logging.getLogger(__name__)


def _listify(items: List[T] | T) -> List[T]:
    """Convert single item to list for uniform handling."""
    return items if isinstance(items, list) else [items]


def _resolve_boms(
    components: list[Component], managed: bool, boms: list[Component] | None
) -> list[Component] | None:
    """
    Determine which components to use as BOMs.

    When managed=True and boms is not explicitly provided, uses components
    with concrete versions as BOMs. MANAGED-versioned components are excluded
    since they consume dependency management rather than provide it.
    """
    if boms is None and managed:
        # Exclude MANAGED components - they can't provide dependency management
        return [c for c in components if c.version != "MANAGED"]
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

        Args:
            artifact: The artifact for which a local path should be resolved.

        Returns:
            Local path to the saved artifact, or None if the artifact cannot be resolved.
        """
        ...

    @abstractmethod
    def resolve(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        transitive: bool = True,
    ) -> tuple[list[Dependency], list[Dependency]]:
        """
        Resolve dependencies for the given Maven component.

        Args:
            components: The component(s) for which to determine the dependencies.
            managed: If True, use dependency management (import components as BOMs).
            boms: List of components to import as BOMs in dependencyManagement.
                If None and managed=True, uses [component].
            transitive: Whether to include transitive dependencies.

        Returns:
            Tuple of (resolved_components, resolved_deps) where:
            - resolved_components: Components with MANAGED versions resolved
            - resolved_deps: Transitive dependencies (excludes the components themselves)
        """
        ...

    def _build_dependency_list(
        self, components: list[Component], deps: list[Dependency]
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Common logic for building dependency list structure.

        Args:
            components: List of Maven components
            deps: List of resolved dependencies

        Returns:
            Tuple of (root_node, dependency_nodes)
        """
        root = _create_root(components)

        # Add components as children of root
        for comp in components:
            comp_artifact = comp.artifact()
            comp_dep = Dependency(comp_artifact)
            root.children.append(DependencyNode(comp_dep))

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        # Convert to DependencyNode list
        dep_nodes = [DependencyNode(dep) for dep in deps]

        return root, dep_nodes

    def _prepare_dependency_resolution(
        self,
        components: list[Component] | Component,
        managed: bool,
        boms: list[Component] | None,
    ) -> tuple[list[Component], list[Component] | None]:
        """
        Prepare components and BOMs for dependency resolution.

        Args:
            components: Component(s) to resolve
            managed: Whether to use managed dependencies
            boms: Optional list of components to use as BOMs

        Returns:
            Tuple of (components_list, boms_list)

        Raises:
            ValueError: If no components provided
        """
        components = _listify(components)

        if not components:
            raise ValueError("At least one component is required")

        boms = _resolve_boms(components, managed, boms)

        return components, boms

    @abstractmethod
    def get_dependency_list(
        self,
        component: Component,
        transitive: bool = True,
        optional_depth: int = 0,
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        This returns the dependency data in a common format that can be used by
        the dependency printing logic to ensure consistent output across resolvers.

        Args:
            component: The component for which to get dependencies.
            transitive: If False, return only direct dependencies.
            optional_depth: Maximum depth at which to include optional dependencies.

        Returns:
            Tuple of (root_node, dependencies_list) where root_node is the
            component itself and dependencies_list is the sorted list of all
            resolved transitive dependencies.
        """
        ...

    @abstractmethod
    def get_dependency_tree(
        self, component: Component, optional_depth: int = 0
    ) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        This returns the dependency data in a common format that can be used by
        the dependency printing logic to ensure consistent output across resolvers.

        Args:
            component: The component for which to get the dependency tree.
            optional_depth: Maximum depth at which to include optional dependencies.
                Defaults to 0, matching Maven's behavior.

        Returns:
            DependencyNode representing the root component with children populated
            recursively to form the complete dependency tree.
        """
        ...


class PythonResolver(Resolver):
    """
    A resolver that works by pure Python code.
    Low overhead, but less feature complete than mvn.
    """

    def __init__(
        self,
        profile_constraints: ProfileConstraints | None = None,
        progress_callback: ProgressCallback | None = None,
    ):
        """
        Initialize Python resolver.

        Args:
            profile_constraints: Profile constraints for Maven model building
            progress_callback: Optional callback for download progress reporting.
                Receives (filename, total_size) and returns a context manager
                that yields an update function accepting bytes_count.
        """
        self.profile_constraints = profile_constraints
        self.progress_callback = progress_callback

    def download(self, artifact: Artifact) -> Path | None:
        # For SNAPSHOT versions, ensure we have the metadata first
        is_snapshot = artifact.version.endswith("-SNAPSHOT")
        if is_snapshot:
            # Check if we already have metadata cached
            if not artifact.component.snapshot_metadata:
                # Try to fetch metadata from remote repos
                artifact.component.update_snapshot_metadata()

            # If still no metadata, we might be dealing with a remote repo
            # that doesn't have the artifact yet
            if not artifact.component.snapshot_metadata:
                _log.warning(
                    f"No SNAPSHOT metadata found for {artifact.component}. "
                    "Attempting download with SNAPSHOT version..."
                )

        for remote_repo in artifact.context.remote_repos.values():
            # Convert Path to forward-slash string for URL
            path_str = str(artifact.component.path_prefix).replace("\\", "/")
            url = f"{remote_repo}/{path_str}/{artifact.filename}"
            _log.debug(f"Trying {url}")

            # Use streaming to enable progress bar
            response: requests.Response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Artifact downloaded successfully.
                # TODO: Also get MD5 and SHA1 files if available.
                # And for each, if it *is* available and successfully gotten,
                # check the actual hash of the downloaded file contents against the expected one.
                cached_file = artifact.cached_path
                assert not cached_file.exists()
                cached_file.parent.mkdir(parents=True, exist_ok=True)

                # Get total size from Content-Length header
                total_size = int(response.headers.get("content-length", 0))

                # Use progress callback if provided and size is known
                if self.progress_callback and total_size > 0:
                    with self.progress_callback(
                        artifact.filename, total_size
                    ) as update_progress:
                        with open(cached_file, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                                update_progress(len(chunk))
                else:
                    # No progress callback - download without progress display
                    with open(cached_file, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                if is_snapshot:
                    _log.info(f"Downloaded SNAPSHOT {artifact} to {cached_file}")
                else:
                    _log.debug(f"Downloaded {artifact} to {cached_file}")
                return cached_file

        raise RuntimeError(
            f"Artifact {artifact} not found in remote repositories "
            f"{artifact.context.remote_repos}"
        )

    def resolve(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        transitive: bool = True,
        optional_depth: int = 0,
    ) -> tuple[list[Dependency], list[Dependency]]:
        """
        Get all dependencies for the given components.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            transitive: Whether to include transitive dependencies
            optional_depth: Maximum depth at which to include optional dependencies

        Returns:
            Tuple of (resolved_components, resolved_deps) where:
            - resolved_components: Components with MANAGED versions resolved
            - resolved_deps: Transitive dependencies (excludes the components themselves)
        """
        components = _listify(components)

        if not components:
            raise ValueError("At least one component is required")

        boms = _resolve_boms(components, managed, boms)

        pom = create_pom(components, boms)
        model = Model(
            pom, components[0].context, profile_constraints=self.profile_constraints
        )
        # When transitive=False, set max_depth=1 to get one level of dependencies
        # from the synthetic wrapper (i.e., the direct dependencies of the components)
        max_depth = 1 if not transitive else None
        deps, _ = model.dependencies(max_depth=max_depth, optional_depth=optional_depth)

        # Build resolved component dependencies
        # For MANAGED components, find their resolved versions in deps
        resolved_components = []
        component_coords = set()
        for comp in components:
            if comp.version == "MANAGED":
                # Find the resolved version in deps
                for dep in deps:
                    if (
                        dep.groupId == comp.groupId
                        and dep.artifactId == comp.artifactId
                    ):
                        resolved_components.append(dep)
                        component_coords.add((dep.groupId, dep.artifactId, dep.version))
                        break
            else:
                resolved_components.append(Dependency(comp.artifact()))
                component_coords.add(
                    (comp.groupId, comp.artifactId, comp.resolved_version)
                )

        # Filter out components from transitive deps list
        resolved_deps = [
            dep
            for dep in deps
            if (dep.groupId, dep.artifactId, dep.version) not in component_coords
        ]

        # Filter out test scope dependencies (they're not needed for running the application)
        resolved_deps = [dep for dep in resolved_deps if dep.scope not in ("test",)]

        return resolved_components, resolved_deps

    def get_dependency_list(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        transitive: bool = True,
        optional_depth: int = 0,
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            transitive: If False, return only direct dependencies
            optional_depth: Maximum depth at which to include optional dependencies

        Returns:
            Tuple of (root_node, flat_list_of_dependencies)
        """
        components = _listify(components)

        if not components:
            raise ValueError("At least one component is required")

        boms = _resolve_boms(components, managed, boms)

        pom = create_pom(components, boms)
        model = Model(
            pom, components[0].context, profile_constraints=self.profile_constraints
        )

        # Create resolved components list using model.deps for MANAGED versions
        resolved_components = []
        for comp in components:
            if comp.version == "MANAGED":
                # Find resolved version in model.deps
                resolved_version = None
                for dep in model.deps.values():
                    if (
                        dep.groupId == comp.groupId
                        and dep.artifactId == comp.artifactId
                    ):
                        resolved_version = dep.version
                        break
                if resolved_version:
                    resolved_components.append(
                        comp.project.at_version(resolved_version)
                    )
                else:
                    resolved_components.append(comp)  # fallback
            else:
                resolved_components.append(comp)

        max_depth = 1 if not transitive else None
        deps, _ = model.dependencies(max_depth=max_depth, optional_depth=optional_depth)
        deps = _filter_component_deps(deps, resolved_components)
        deps = [dep for dep in deps if dep.scope not in ("test",)]

        return self._build_dependency_list(resolved_components, deps)

    def get_dependency_tree(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        optional_depth: int = 0,
    ) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        This implementation uses the tree built during dependency resolution,
        ensuring perfect consistency with the dependency mediation algorithm.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            optional_depth: Maximum depth at which to include optional dependencies

        Returns:
            Root DependencyNode with full tree structure
        """
        components = _listify(components)
        boms = _resolve_boms(components, managed, boms)

        # Build model and get dependency tree
        pom = create_pom(components, boms)
        model = Model(
            pom, components[0].context, profile_constraints=self.profile_constraints
        )
        _, root = model.dependencies(optional_depth=optional_depth)

        return root


class MvnResolver(Resolver):
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

    def _create_temp_pom(
        self, components: list[Component], boms: list[Component] | None
    ) -> Path:
        """Create temporary POM file for Maven commands."""
        pom = create_pom(components, boms or [])
        temp_pom = write_temp_pom(pom)
        _log.debug(
            f"Created wrapper POM at {temp_pom} with {len(components)} "
            f"component(s) and {len(boms or [])} BOM(s)"
        )
        return temp_pom

    def _filter_dep_scopes(
        self, deps: list[Dependency], scopes: str | list[str]
    ) -> list[Dependency]:
        """
        Filter dependencies to include only specified scopes.

        This method filters Maven dependency results to match the desired scope(s),
        compensating for Maven's quirky -Dscope behavior (which includes test-scoped
        direct dependencies even when -Dscope=runtime is specified:
        apache/maven#10874, apache/maven-dependency-tree#54).

        Args:
            deps: List of dependencies to filter
            scopes: Scope name or list of scope names to include.
                Special scope values:
                - "runtime": includes compile, runtime, provided (default for jgo)
                - "compile": includes compile, provided
                - "test": includes compile, runtime, provided, test
                Or pass an explicit list like ["compile", "runtime"]

        Returns:
            Filtered list including only dependencies with specified scopes
        """
        # Expand scope shortcuts to full scope lists
        if isinstance(scopes, str):
            if scopes == "runtime":
                scope_list = ["compile", "runtime", "provided"]
            elif scopes == "compile":
                scope_list = ["compile", "provided"]
            elif scopes == "test":
                scope_list = ["compile", "runtime", "provided", "test"]
            else:
                # Single scope name
                scope_list = [scopes]
        else:
            scope_list = scopes

        return [dep for dep in deps if dep.scope in scope_list]

    def _filter_maven_output(self, output: str, log_debug: bool = True) -> list[str]:
        """Filter Maven output to extract [INFO] lines."""
        lines = []
        for line in output.splitlines():
            line = line.strip()
            if log_debug and line.startswith(("[DEBUG]", "[WARNING]", "[ERROR]")):
                _log.debug(line)
            if not line.startswith("[INFO]"):
                continue
            # Skip download/progress messages
            if (
                "Downloading from" in line
                or "Downloaded from" in line
                or "Progress" in line
            ):
                continue
            lines.append(line)
        return lines

    def _parse_maven_coordinate(
        self, content: str, context, require_scope: bool = False
    ) -> Dependency | None:
        """Parse Maven output coordinate string into Dependency object."""
        # Strip module information added by Java 9+
        if " -- module " in content:
            content = content.split(" -- module ")[0].strip()

        try:
            coord = Coordinate.parse(content)

            # For dependency:list output, we need to validate the scope
            if require_scope:
                if not coord.scope or coord.scope not in (
                    "compile",
                    "runtime",
                    "provided",
                    "test",
                    "system",
                    "import",
                ):
                    return None

            return context.create_dependency(coord)
        except ValueError:
            return None

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

    def resolve(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        transitive: bool = True,
        optional_depth: int = 0,
    ) -> tuple[list[Dependency], list[Dependency]]:
        """
        Get all dependencies for the given components.

        Args:
            components: Single component or list of components to resolve dependencies for
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            transitive: Whether to include transitive dependencies
            optional_depth: Maximum depth at which to include optional dependencies.
                NOTE: MvnResolver does not support custom optional_depth - Maven always
                excludes optional transitive dependencies (equivalent to optional_depth=0).

        Returns:
            Tuple of (resolved_components, resolved_deps) where:
            - resolved_components: Components with MANAGED versions resolved
            - resolved_deps: Transitive dependencies (excludes the components themselves)
        """
        if optional_depth > 0:
            _log.warning(
                f"MvnResolver does not support optional_depth={optional_depth}. "
                "Maven always excludes optional transitive dependencies. "
                "Use PythonResolver (--resolver=python) for custom optional_depth."
            )

        components = _listify(components)

        if not transitive:
            # Use get_dependency_tree and extract only direct children (depth 1)
            root = self.get_dependency_tree(components, managed=managed, boms=boms)
            dependencies = []

            # Extract direct children of the root's children (which are the components)
            for component_node in root.children:
                # component_node represents one of the input components
                # Its direct children are the direct dependencies we want
                dependencies.extend(component_node.children)

            # Convert DependencyNodes back to Dependency objects
            resolved_deps = [node.dep for node in dependencies]

            # Build resolved components - for non-transitive, components are just themselves
            # (MANAGED versions would have been resolved during tree building)
            resolved_components = [node.dep for node in root.children]

            return resolved_components, resolved_deps

        # For transitive=True, use dependency:list

        if not components:
            raise ValueError("At least one component is required")

        # Get context and repo cache from first component
        context = components[0].context
        assert context.repo_cache

        boms = _resolve_boms(components, managed, boms) or []

        # Log what we're resolving
        _log.info(f"Resolving dependencies for {len(components)} component(s)")
        for comp in components:
            _log.debug(f"  Component: {comp.groupId}:{comp.artifactId}:{comp.version}")

        # Create temporary POM
        temp_pom = self._create_temp_pom(components, boms)

        output = self._mvn(
            "dependency:list",
            "-f",
            str(temp_pom),
            f"-Dmaven.repo.local={context.repo_cache}",
            "-Dscope=runtime",
        )

        # Parse Maven's dependency:list output format:
        # Java 8:  [INFO]    groupId:artifactId:packaging:version:scope
        # Java 9+: [INFO]    groupId:artifactId:packaging:version:scope -- module module.name
        dependencies = []

        info_lines = self._filter_maven_output(output)

        for line in info_lines:
            # Remove [INFO] prefix and whitespace
            content = line[6:].strip()

            # Skip non-dependency lines
            if ":" not in content:
                continue

            # Parse G:A:P[:C]:V:S format using Coordinate
            dep = self._parse_maven_coordinate(content, context, require_scope=True)
            if not dep:
                # Not a valid coordinate format
                continue

            # Create dependency object from coordinate
            dependencies.append(dep)

        # Build resolved component dependencies
        # For MANAGED components, find their resolved versions in dependencies
        resolved_components = []
        component_coords = set()
        for comp in components:
            if comp.version == "MANAGED":
                # Find the resolved version in dependencies
                for dep in dependencies:
                    if (
                        dep.groupId == comp.groupId
                        and dep.artifactId == comp.artifactId
                    ):
                        resolved_components.append(dep)
                        component_coords.add((dep.groupId, dep.artifactId, dep.version))
                        break
            else:
                resolved_components.append(Dependency(comp.artifact()))
                component_coords.add(
                    (comp.groupId, comp.artifactId, comp.resolved_version)
                )

        # Filter out components from transitive deps list
        resolved_deps = [
            dep
            for dep in dependencies
            if (dep.groupId, dep.artifactId, dep.version) not in component_coords
        ]

        # Filter to runtime scopes only (compensate for Maven's -Dscope quirk)
        resolved_deps = self._filter_dep_scopes(resolved_deps, "runtime")

        return resolved_components, resolved_deps

    def get_dependency_list(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        transitive: bool = True,
        optional_depth: int = 0,
    ) -> tuple[DependencyNode, list[DependencyNode]]:
        """
        Get the flat list of resolved dependencies as data structures.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            transitive: If False, return only direct dependencies
            optional_depth: Maximum depth at which to include optional dependencies
                NOTE: Not supported by MvnResolver - use PythonResolver instead

        Returns:
            Tuple of (root_node, flat_list_of_dependencies)
        """
        components = _listify(components)
        resolved_components, resolved_deps = self.resolve(
            components,
            managed=managed,
            boms=boms,
            transitive=transitive,
            optional_depth=optional_depth,
        )
        return self._build_dependency_list(components, resolved_deps)

    def get_dependency_tree(
        self,
        components: list[Component] | Component,
        managed: bool = False,
        boms: list[Component] | None = None,
        optional_depth: int = 0,
    ) -> DependencyNode:
        """
        Get the full dependency tree as a data structure.

        Args:
            components: Single component or list of components
            managed: If True and boms is None, use components as BOMs
            boms: Optional list of components to import in dependencyManagement
            optional_depth: Maximum depth at which to include optional dependencies
                NOTE: Not supported by MvnResolver - use PythonResolver instead

        Returns:
            Root DependencyNode with full tree structure
        """
        if optional_depth > 0:
            _log.warning(
                f"MvnResolver does not support optional_depth={optional_depth}. "
                "Maven always excludes optional transitive dependencies. "
                "Use PythonResolver (--resolver=python) for custom optional_depth."
            )

        components = _listify(components)

        if not components:
            raise ValueError("At least one component is required")

        context = components[0].context
        assert context.repo_cache

        boms = _resolve_boms(components, managed, boms) or []

        # Create temporary POM
        temp_pom = self._create_temp_pom(components, boms)

        output = self._mvn(
            "dependency:tree",
            "-f",
            str(temp_pom),
            f"-Dmaven.repo.local={context.repo_cache}",
            "-Dscope=runtime",
        )

        # Parse the tree output
        # Format: [INFO] org.apposed.jgo:INTERNAL-WRAPPER:jar:0-SNAPSHOT
        #         [INFO] \- org.example:my-component:pom:1.2.3:compile
        #         [INFO]    +- dep1:jar:1.0:scope
        #         [INFO]    |  \- dep2:jar:2.0:scope
        #         [INFO]    \- dep3:jar:3.0:scope

        info_lines = self._filter_maven_output(output, log_debug=False)
        root = None
        stack = []  # Stack of (indent_level, node)

        for line in info_lines:
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

            # Parse G:A:P[:C]:V[:S] format using Coordinate
            dep = self._parse_maven_coordinate(clean_content, context)
            if not dep:
                continue

            # Filter out test-scoped dependencies to match PythonResolver behavior
            # (compensates for Maven's -Dscope quirk)
            if dep.scope == "test":
                continue

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
        return MvnResolver._run(self.mvn_command, *self.mvn_flags, *args)

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
