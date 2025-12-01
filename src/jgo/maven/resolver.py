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

if TYPE_CHECKING:
    from .core import Artifact, Component, Dependency
    from .dependency_printer import DependencyNode

_log = logging.getLogger(__name__)


class Resolver(ABC):
    """
    Logic for doing non-trivial Maven-related things, including:
    * downloading and caching an artifact from a remote repository; and
    * determining the dependencies of a particular Maven component.
    """

    @abstractmethod
    def download(self, artifact: "Artifact") -> Path | None:
        """
        Download an artifact file from a remote repository.
        :param artifact: The artifact for which a local path should be resolved.
        :return: Local path to the saved artifact, or None if the artifact cannot be resolved.
        """
        ...

    @abstractmethod
    def dependencies(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> list["Dependency"]:
        """
        Determine dependencies for the given Maven component.
        :param component: The component for which to determine the dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param managed_components: List of components to import as BOMs in dependencyManagement.
                                   If None and managed=True, uses [component].
        :return: The list of dependencies.
        """
        ...

    @abstractmethod
    def get_dependency_list(
        self, component: "Component"
    ) -> tuple["DependencyNode", list["DependencyNode"]]:
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
    def get_dependency_tree(self, component: "Component") -> "DependencyNode":
        """
        Get the full dependency tree as a data structure.

        This returns the dependency data in a common format that can be used by
        the dependency printing logic to ensure consistent output across resolvers.

        :param component: The component for which to get the dependency tree.
        :return: DependencyNode representing the root component with children populated
                 recursively to form the complete dependency tree.
        """
        ...


class SimpleResolver(Resolver):
    """
    A resolver that works by pure Python code.
    Low overhead, but less feature complete than mvn.
    """

    def download(self, artifact: "Artifact") -> Path | None:
        if artifact.version.endswith("-SNAPSHOT"):
            raise RuntimeError("Downloading of snapshots is not yet implemented.")

        for remote_repo in artifact.maven_context.remote_repos.values():
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
            f"{artifact.maven_context.remote_repos}"
        )

    def dependencies(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> list["Dependency"]:
        from .model import Model

        # Default to using the component itself if managed=True
        if managed and managed_components is None:
            managed_components = [component]

        model = Model(component.pom(), managed_components=managed_components)
        return model.dependencies()

    def get_dependency_list(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> tuple["DependencyNode", list["DependencyNode"]]:
        """
        Get the flat list of resolved dependencies as data structures.
        """
        from .dependency_printer import DependencyNode
        from .model import Model

        # Create root node
        root = DependencyNode(
            groupId=component.groupId,
            artifactId=component.artifactId,
            version=component.version,
            packaging="jar",
        )

        # Build the model and get mediated dependencies
        if managed and managed_components is None:
            managed_components = [component]
        model = Model(component.pom(), managed_components=managed_components)
        deps = model.dependencies()

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        # Convert to DependencyNode list
        dep_nodes = []
        for dep in deps:
            node = DependencyNode(
                groupId=dep.groupId,
                artifactId=dep.artifactId,
                version=dep.version,
                packaging=dep.type,
                classifier=dep.classifier if dep.classifier else None,
                scope=dep.scope,
                optional=dep.optional,
            )
            dep_nodes.append(node)

        return root, dep_nodes

    def get_dependency_tree(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> "DependencyNode":
        """
        Get the full dependency tree as a data structure.
        """
        from .dependency_printer import DependencyNode
        from .model import Model

        # Create root node
        root = DependencyNode(
            groupId=component.groupId,
            artifactId=component.artifactId,
            version=component.version,
            packaging="jar",
        )

        # Build the model to get dependencies
        if managed and managed_components is None:
            managed_components = [component]
        model = Model(component.pom(), managed_components=managed_components)

        # Track which G:A:C:T we've already processed (version not included for mediation)
        processed = set()

        def build_tree(deps: list["Dependency"]) -> list[DependencyNode]:
            """Recursively build dependency tree."""
            nodes = []
            for dep in deps:
                # Use G:A:C:T (without version) for deduplication, like Maven does
                dep_key = (dep.groupId, dep.artifactId, dep.classifier, dep.type)

                # Create node
                node = DependencyNode(
                    groupId=dep.groupId,
                    artifactId=dep.artifactId,
                    version=dep.version,
                    packaging=dep.type,
                    classifier=dep.classifier if dep.classifier else None,
                    scope=dep.scope,
                    optional=dep.optional,
                )

                # Recursively process children if not already seen
                if dep_key not in processed:
                    processed.add(dep_key)
                    try:
                        dep_model = Model(dep.artifact.component.pom())
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

        # Build tree from direct dependencies
        direct_deps = list(model.deps.values())
        root.children = build_tree(direct_deps)

        return root

    def print_dependency_list(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> str:
        """
        Print a flat list of resolved dependencies (like mvn dependency:list).
        This shows what will actually be used when building the environment.
        :param component: The component for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param managed_components: List of components to import as BOMs. Defaults to [component].
        :return: The dependency list as a string.
        """
        from .dependency_printer import format_dependency_list

        root, deps = self.get_dependency_list(
            component, managed=managed, managed_components=managed_components
        )
        return format_dependency_list(root, deps)

    def print_dependency_tree(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> str:
        """
        Print the full dependency tree for the given component (like mvn dependency:tree).
        Uses proper dependency mediation - only one version per artifact.
        :param component: The component for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param managed_components: List of components to import as BOMs. Defaults to [component].
        :return: The dependency tree as a string.
        """
        from .dependency_printer import format_dependency_tree

        root = self.get_dependency_tree(
            component, managed=managed, managed_components=managed_components
        )
        return format_dependency_tree(root)


class MavenResolver(Resolver):
    """
    A resolver that works by shelling out to mvn.
    Requires Maven to be installed.
    """

    def __init__(self, mvn_command: Path, update: bool = False):
        self.mvn_command = mvn_command
        self.mvn_flags = ["-B", "-T8"]
        if update:
            self.mvn_flags.append("-U")

    def download(self, artifact: "Artifact") -> Path | None:
        _log.info(f"Downloading artifact: {artifact}")
        assert artifact.maven_context.repo_cache
        assert artifact.groupId
        assert artifact.artifactId
        assert artifact.version
        assert artifact.packaging
        args = [
            f"-Dmaven.repo.local={artifact.maven_context.repo_cache}",
            f"-DgroupId={artifact.groupId}",
            f"-DartifactId={artifact.artifactId}",
            f"-Dversion={artifact.version}",
            f"-Dpackaging={artifact.packaging}",
        ]
        if artifact.classifier:
            args.append(f"-Dclassifier={artifact.classifier}")
        if artifact.maven_context.remote_repos:
            remote_repos = ",".join(
                f"{name}::::{url}"
                for name, url in artifact.maven_context.remote_repos.items()
            )
            args.append(f"-DremoteRepositories={remote_repos}")

        self._mvn("dependency:get", *args)

        # The file should now exist in the local repo cache.
        assert artifact.cached_path and artifact.cached_path.exists()
        return artifact.cached_path

    def dependencies(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> list["Dependency"]:
        # Invoke the dependency:list goal, including all transitive dependencies.
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache

        # If managed mode, create a synthetic POM that imports components as BOMs
        if managed:
            # Default to using the component itself if managed_components not provided
            if managed_components is None:
                managed_components = [component]
            pom_path = self._create_managed_pom(component, managed_components)
        else:
            pom_path = pom_artifact.resolve()

        output = self._mvn(
            "dependency:list",
            "-f",
            pom_path,
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}",
        )

        # Parse Maven's dependency:list output format:
        # Java 8:  [INFO]    groupId:artifactId:packaging:version:scope
        # Java 9+: [INFO]    groupId:artifactId:packaging:version:scope -- module module.name
        dependencies = []

        for line in output.splitlines():
            line = line.strip()
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

            # Parse G:A:P[:C]:V:S format
            parts = content.split(":")
            if len(parts) < 5:
                continue

            # Handle optional dependencies (marked with " (optional)") BEFORE scope validation
            optional = False
            if parts[-1].endswith(" (optional)"):
                parts[-1] = parts[-1][:-11]  # Remove " (optional)"
                optional = True

            # Check if this looks like a dependency (ends with scope like 'compile', 'runtime', etc.)
            if parts[-1] not in (
                "compile",
                "runtime",
                "provided",
                "test",
                "system",
                "import",
            ):
                continue

            # Handle both G:A:P:V:S and G:A:P:C:V:S formats
            if len(parts) == 5:
                # G:A:P:V:S
                groupId, artifactId, packaging, version, scope = parts
                classifier = None
            elif len(parts) == 6:
                # G:A:P:C:V:S
                groupId, artifactId, packaging, classifier, version, scope = parts
            else:
                # Unknown format, skip
                continue

            # Create dependency object
            from .core import Dependency

            dep_component = component.maven_context.project(
                groupId, artifactId
            ).at_version(version)
            dep_artifact = dep_component.artifact(
                packaging=packaging, classifier=classifier if classifier else None
            )
            dep = Dependency(
                artifact=dep_artifact,
                scope=scope,
                optional=optional,
            )
            dependencies.append(dep)

        return dependencies

    def get_dependency_list(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> tuple["DependencyNode", list["DependencyNode"]]:
        """
        Get the flat list of resolved dependencies as data structures.
        """
        from .dependency_printer import DependencyNode

        # Create root node
        root = DependencyNode(
            groupId=component.groupId,
            artifactId=component.artifactId,
            version=component.version,
            packaging="jar",
        )

        # Get dependencies using existing method
        deps = self.dependencies(
            component, managed=managed, managed_components=managed_components
        )

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        # Convert to DependencyNode list
        dep_nodes = []
        for dep in deps:
            node = DependencyNode(
                groupId=dep.groupId,
                artifactId=dep.artifactId,
                version=dep.version,
                packaging=dep.type,
                classifier=dep.classifier if dep.classifier else None,
                scope=dep.scope,
                optional=dep.optional,
            )
            dep_nodes.append(node)

        return root, dep_nodes

    def get_dependency_tree(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> "DependencyNode":
        """
        Get the full dependency tree as a data structure.

        Parses Maven's dependency:tree output and converts it to DependencyNode structure.
        """
        from .dependency_printer import DependencyNode

        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache

        # If managed mode, create a synthetic POM that imports components as BOMs
        if managed:
            # Default to using the component itself if managed_components not provided
            if managed_components is None:
                managed_components = [component]
            pom_path = self._create_managed_pom(component, managed_components)
        else:
            # First ensure the POM is resolved
            pom_artifact.resolve()
            pom_path = pom_artifact.cached_path

        output = self._mvn(
            "dependency:tree",
            "-f",
            pom_path,
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}",
        )

        # Parse the tree output
        # Format: [INFO] net.imagej:imagej:jar:2.17.0
        #         [INFO] +- dep1:jar:1.0:scope
        #         [INFO] |  \- dep2:jar:2.0:scope
        #         [INFO] \- dep3:jar:3.0:scope

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
            clean_content = content

            # Count indent based on tree structure characters
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

            # Additional validation: coordinates should have at least G:A:P:V format
            colon_count = clean_content.count(":")
            if colon_count < 3:
                continue

            # Parse G:A:P[:C]:V[:S] format
            # Can also have " (optional)" suffix
            parts = clean_content.split(":")
            if len(parts) < 4:
                continue

            optional = False
            if parts[-1].endswith(" (optional)"):
                parts[-1] = parts[-1][:-11]  # Remove " (optional)"
                optional = True

            # Parse based on number of parts
            if len(parts) == 4:
                # G:A:P:V
                groupId, artifactId, packaging, version_scope = parts
                classifier = None
                # Check if last part has scope
                if version_scope.count(":") == 0:
                    version = version_scope
                    scope = None
                else:
                    version, scope = version_scope.split(":", 1)
            elif len(parts) == 5:
                # Could be G:A:P:V:S or G:A:P:C:V
                groupId, artifactId, packaging, part4, part5 = parts
                # Check if part5 looks like a scope
                if part5 in (
                    "compile",
                    "runtime",
                    "provided",
                    "test",
                    "system",
                    "import",
                ):
                    # G:A:P:C:V:S
                    classifier = part4
                    version = part5
                    scope = None
                else:
                    # G:A:P:V:S
                    classifier = None
                    version = part4
                    scope = part5
            elif len(parts) == 6:
                # G:A:P:C:V:S
                groupId, artifactId, packaging, classifier, version, scope = parts
            else:
                continue

            # Create node
            node = DependencyNode(
                groupId=groupId,
                artifactId=artifactId,
                version=version,
                packaging=packaging,
                classifier=classifier if classifier else None,
                scope=scope if scope and scope != "compile" else None,
                optional=optional,
            )

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

        return (
            root
            if root
            else DependencyNode(
                groupId=component.groupId,
                artifactId=component.artifactId,
                version=component.version,
                packaging="jar",
            )
        )

    def print_dependency_list(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> str:
        """
        Print a flat list of resolved dependencies (like mvn dependency:list).
        This shows what will actually be used when building the environment.
        :param component: The component for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param managed_components: List of components to import as BOMs. Defaults to [component].
        :return: The dependency list as a string.
        """
        from .dependency_printer import format_dependency_list

        root, deps = self.get_dependency_list(
            component, managed=managed, managed_components=managed_components
        )
        return format_dependency_list(root, deps)

    def print_dependency_tree(
        self,
        component: "Component",
        managed: bool = False,
        managed_components: list["Component"] | None = None,
    ) -> str:
        """
        Print the full dependency tree for the given component.
        :param component: The component for which to print dependencies.
        :param managed: If True, use dependency management (import components as BOMs).
        :param managed_components: List of components to import as BOMs. Defaults to [component].
        :return: The dependency tree as a string.
        """
        from .dependency_printer import format_dependency_tree

        root = self.get_dependency_tree(
            component, managed=managed, managed_components=managed_components
        )
        return format_dependency_tree(root)

    def _mvn(self, *args) -> str:
        return MavenResolver._run(self.mvn_command, *self.mvn_flags, *args)

    def _create_managed_pom(
        self, component: "Component", managed_components: list["Component"]
    ) -> Path:
        """
        Create a synthetic POM that imports components as BOMs.

        This is used for managed dependency mode (-m flag), where the components'
        dependencyManagement sections are imported to ensure transitive deps use BOM versions.
        """
        import tempfile

        # Create temporary POM file
        temp_pom = Path(tempfile.mktemp(suffix=".pom.xml", prefix="jgo-managed-"))

        # Generate dependencyManagement section with all managed components
        dep_mgmt_entries = []
        for comp in managed_components:
            resolved_version = comp.resolved_version
            dep_mgmt_entries.append(
                f"""            <dependency>
                <groupId>{comp.groupId}</groupId>
                <artifactId>{comp.artifactId}</artifactId>
                <version>{resolved_version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>"""
            )

        dep_mgmt_section = "\n".join(dep_mgmt_entries)

        # Use the primary component's resolved version
        resolved_version = component.resolved_version

        # Generate repositories section if remote repos are configured
        repos_entries = []
        for repo_id, repo_url in component.maven_context.remote_repos.items():
            repos_entries.append(
                f"""        <repository>
            <id>{repo_id}</id>
            <url>{repo_url}</url>
        </repository>"""
            )

        repos_section = "\n".join(repos_entries) if repos_entries else ""
        repositories_block = (
            f"""
    <repositories>
{repos_section}
    </repositories>
"""
            if repos_section
            else ""
        )

        # Generate POM content
        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{component.groupId}-MANAGED</groupId>
    <artifactId>{component.artifactId}-MANAGED</artifactId>
    <version>1.0.0</version>

    <dependencyManagement>
        <dependencies>
{dep_mgmt_section}
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <dependency>
            <groupId>{component.groupId}</groupId>
            <artifactId>{component.artifactId}</artifactId>
            <version>{resolved_version}</version>
            <type>pom</type>
        </dependency>
    </dependencies>
{repositories_block}</project>
"""

        # Write POM to file
        temp_pom.write_text(pom_content)
        _log.debug(
            f"Created managed POM at {temp_pom} with {len(managed_components)} managed components"
        )

        return temp_pom

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
