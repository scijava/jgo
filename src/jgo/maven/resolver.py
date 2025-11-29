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
        return list(model.deps.values())


class MavenResolver(Resolver):
    """
    A resolver that works by shelling out to mvn.
    Requires Maven to be installed.
    """

    def __init__(self, mvn_command: Path):
        self.mvn_command = mvn_command
        self.mvn_flags = ["-B", "-T8"]

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
        from .pom import POM

        # Invoke the dependency:list goal, direct dependencies only.
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.maven_context.repo_cache
        output = self._mvn(
            "dependency:list",
            "-f", pom_artifact.resolve(),
            "-DexcludeTransitive=true",
            f"-Dmaven.repo.local={pom_artifact.maven_context.repo_cache}"
        )

        # FIXME: Fix the following logic to parse dependency:list output.

        # Filter to include only the actual lines of XML.
        lines = output.splitlines()
        snip = snap = None
        for i, line in enumerate(lines):
            if snip is None and line.startswith("<?xml"):
                snip = i
            elif line == "</project>":
                snap = i
                break
        assert snip is not None and snap is not None
        pom = POM("\n".join(lines[snip:snap + 1]), pom_artifact.maven_context)

        # Extract the flattened dependencies.
        return pom.dependencies()

    def _mvn(self, *args) -> str:
        # TODO: Windows.
        return MavenResolver._run(self.mvn_command, *self.mvn_flags, *args)

    @staticmethod
    def _run(command, *args) -> str:
        command_and_args = (command,) + args
        _log.debug(f"Executing: {command_and_args}")
        result = run(command_and_args, capture_output=True)
        if result.returncode == 0:
            return result.stdout.decode()

        error_message = (
            f"Command failed with exit code {result.returncode}:\n"
            f"{command_and_args}"
        )
        if result.stdout:
            error_message += f"\n\n[stdout]\n{result.stdout.decode()}"
        if result.stderr:
            error_message += f"\n\n[stderr]\n{result.stderr.decode()}"
        raise RuntimeError(error_message)
