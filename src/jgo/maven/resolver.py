"""
Maven artifact resolvers.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import run
from typing import TYPE_CHECKING, List, Optional

import requests

if TYPE_CHECKING:
    from .core import Artifact, Component, Dependency

_log = logging.getLogger(__name__)


class Resolver(ABC):
    """
    Logic for doing non-trivial Maven-related things, including:
    * downloading and caching an artifact from a remote repository; and
    * determining the dependencies of a particular Maven component.
    """

    @abstractmethod
    def download(self, artifact: "Artifact") -> Optional[Path]:
        """
        Download an artifact file from a remote repository.
        :param artifact: The artifact for which a local path should be resolved.
        :return: Local path to the saved artifact, or None if the artifact cannot be resolved.
        """
        ...

    @abstractmethod
    def dependencies(self, component: "Component") -> List["Dependency"]:
        """
        Determine dependencies for the given Maven component.
        :param component: The component for which to determine the dependencies.
        :return: The list of dependencies.
        """
        ...


class SimpleResolver(Resolver):
    """
    A resolver that works by pure Python code.
    Low overhead, but less feature complete than mvn.
    """

    def download(self, artifact: "Artifact") -> Optional[Path]:
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

    def dependencies(self, component: "Component") -> List["Dependency"]:
        from .model import Model

        model = Model(component.pom())
        return model.dependencies()

    def print_dependency_list(self, component: "Component") -> str:
        """
        Print a flat list of resolved dependencies (like mvn dependency:list).
        This shows what will actually be used when building the environment.
        :param component: The component for which to print dependencies.
        :return: The dependency list as a string.
        """
        from .model import Model

        lines = []
        lines.append(f"{component.groupId}:{component.artifactId}:{component.version}")

        # Build the model and get mediated dependencies
        model = Model(component.pom())
        deps = model.dependencies()

        # Sort for consistent output
        deps.sort(key=lambda d: (d.groupId, d.artifactId, d.version))

        for dep in deps:
            scope_suffix = f":{dep.scope}" if dep.scope != "compile" else ""
            line = f"   {dep.groupId}:{dep.artifactId}:{dep.type}:{dep.version}{scope_suffix}"
            lines.append(line)

        return "\n".join(lines)

    def print_dependency_tree(self, component: "Component") -> str:
        """
        Print the full dependency tree for the given component (like mvn dependency:tree).
        Uses proper dependency mediation - only one version per artifact.
        :param component: The component for which to print dependencies.
        :return: The dependency tree as a string.
        """
        from .model import Model

        lines = []
        lines.append(f"{component.groupId}:{component.artifactId}:{component.version}")

        # Build the model to get dependencies
        model = Model(component.pom())

        # Track which G:A:C:T we've already processed (version not included for mediation)
        processed = set()

        def add_deps(deps, prefix="", is_last=True):
            """Recursively add dependencies to the tree."""
            for i, dep in enumerate(deps):
                is_last_item = i == len(deps) - 1
                connector = "└── " if is_last_item else "├── "
                extension = "    " if is_last_item else "│   "

                # Use G:A:C:T (without version) for deduplication, like Maven does
                dep_key = (dep.groupId, dep.artifactId, dep.classifier, dep.type)
                scope_suffix = f":{dep.scope}" if dep.scope != "compile" else ""
                optional_suffix = " (optional)" if dep.optional else ""

                line = f"{prefix}{connector}{dep.groupId}:{dep.artifactId}:{dep.type}:{dep.version}{scope_suffix}{optional_suffix}"
                lines.append(line)

                # Recursively show transitive dependencies, but use proper mediation
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
                            add_deps(
                                transitive_deps,
                                prefix + extension,
                                is_last=is_last_item,
                            )
                    except Exception as e:
                        _log.debug(f"Could not resolve dependencies for {dep}: {e}")

        # Add direct dependencies
        direct_deps = list(model.deps.values())
        add_deps(direct_deps)

        return "\n".join(lines)


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

    def download(self, artifact: "Artifact") -> Optional[Path]:
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

    def dependencies(self, component: "Component") -> List["Dependency"]:
        # Invoke the dependency:list goal, including all transitive dependencies.
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache
        output = self._mvn(
            "dependency:list",
            "-f",
            pom_artifact.resolve(),
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}",
        )

        # Parse Maven's dependency:list output format:
        # [INFO]    groupId:artifactId:packaging:version:scope
        # [INFO]    groupId:artifactId:packaging:classifier:version:scope
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

            # Parse G:A:P[:C]:V:S format
            parts = content.split(":")
            if len(parts) < 5:
                continue

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

            # Handle optional dependencies (marked with " (optional)")
            optional = False
            if scope.endswith(" (optional)"):
                scope = scope[:-11]  # Remove " (optional)"
                optional = True

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

    def print_dependency_list(self, component: "Component") -> str:
        """
        Print a flat list of resolved dependencies (like mvn dependency:list).
        This shows what will actually be used when building the environment.
        :param component: The component for which to print dependencies.
        :return: The dependency list as a string.
        """
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache

        # First ensure the POM is resolved
        pom_artifact.resolve()

        output = self._mvn(
            "dependency:list",
            "-f",
            pom_artifact.cached_path,
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}",
        )

        return output

    def print_dependency_tree(self, component: "Component") -> str:
        """
        Print the full dependency tree for the given component.
        :param component: The component for which to print dependencies.
        :return: The dependency tree as a string.
        """
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache

        # First ensure the POM is resolved
        pom_artifact.resolve()

        output = self._mvn(
            "dependency:tree",
            "-f",
            pom_artifact.cached_path,
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}",
        )

        return output

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
