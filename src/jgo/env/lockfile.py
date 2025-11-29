"""
Lock file (jgo.lock.toml) generation and validation.

Lock files record exact resolved versions for reproducibility,
including SNAPSHOT timestamps and SHA256 checksums.
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Use tomllib (Python 3.11+) or tomli (backport for older versions)
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from jgo.maven import Dependency


class LockedDependency:
    """
    A dependency with locked version and checksum.
    """

    def __init__(
        self,
        groupId: str,
        artifactId: str,
        version: str,
        packaging: str = "jar",
        classifier: Optional[str] = None,
        sha256: Optional[str] = None,
    ):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.packaging = packaging
        self.classifier = classifier
        self.sha256 = sha256

    @classmethod
    def from_dependency(cls, dep: Dependency) -> "LockedDependency":
        """
        Create a LockedDependency from a resolved Dependency.

        This will:
        1. Lock SNAPSHOT versions to exact timestamps
        2. Compute SHA256 checksum of the artifact file
        """
        artifact = dep.artifact

        # Resolve to get the file path
        artifact_path = artifact.resolve()

        # Compute SHA256 checksum
        sha256 = compute_sha256(artifact_path) if artifact_path.exists() else None

        return cls(
            groupId=artifact.groupId,
            artifactId=artifact.artifactId,
            version=artifact.version,  # Will be timestamped for SNAPSHOTs
            packaging=artifact.packaging,
            classifier=artifact.classifier,
            sha256=sha256,
        )

    def to_dict(self) -> dict:
        """Convert to dict for TOML serialization."""
        data = {
            "groupId": self.groupId,
            "artifactId": self.artifactId,
            "version": self.version,
            "packaging": self.packaging,
        }
        if self.classifier:
            data["classifier"] = self.classifier
        if self.sha256:
            data["sha256"] = self.sha256
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LockedDependency":
        """Create from parsed TOML dict."""
        return cls(
            groupId=data["groupId"],
            artifactId=data["artifactId"],
            version=data["version"],
            packaging=data.get("packaging", "jar"),
            classifier=data.get("classifier"),
            sha256=data.get("sha256"),
        )

    def __repr__(self) -> str:
        return f"LockedDependency({self.groupId}:{self.artifactId}:{self.version})"


class LockFile:
    """
    Lock file for reproducible builds (jgo.lock.toml).

    Records:
    - Exact resolved versions (SNAPSHOT → timestamped)
    - SHA256 checksums for verification
    - Environment metadata (name, min_java_version)
    - Entrypoints
    """

    def __init__(
        self,
        dependencies: List[LockedDependency],
        environment_name: Optional[str] = None,
        min_java_version: Optional[int] = None,
        entrypoints: Optional[Dict[str, str]] = None,
        default_entrypoint: Optional[str] = None,
        jgo_version: str = "2.0.0",
    ):
        self.dependencies = dependencies
        self.environment_name = environment_name
        self.min_java_version = min_java_version
        self.entrypoints = entrypoints or {}
        self.default_entrypoint = default_entrypoint
        self.jgo_version = jgo_version
        self.generated = datetime.now(timezone.utc)

    @classmethod
    def from_resolved_dependencies(
        cls,
        dependencies: List[Dependency],
        environment_name: Optional[str] = None,
        min_java_version: Optional[int] = None,
        entrypoints: Optional[Dict[str, str]] = None,
        default_entrypoint: Optional[str] = None,
    ) -> "LockFile":
        """
        Create a lock file from resolved dependencies.

        This will lock SNAPSHOT versions and compute checksums.
        """
        locked_deps = [LockedDependency.from_dependency(dep) for dep in dependencies]

        return cls(
            dependencies=locked_deps,
            environment_name=environment_name,
            min_java_version=min_java_version,
            entrypoints=entrypoints,
            default_entrypoint=default_entrypoint,
        )

    @classmethod
    def load(cls, path: Path) -> "LockFile":
        """
        Load a lock file from jgo.lock.toml.

        Args:
            path: Path to jgo.lock.toml file

        Returns:
            LockFile instance

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Lock file not found: {path}")

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse {path}: {e}") from e

        # Parse metadata
        metadata = data.get("metadata", {})
        jgo_version = metadata.get("jgo_version", "unknown")

        # Parse environment section
        env_section = data.get("environment", {})
        environment_name = env_section.get("name")
        min_java_version = env_section.get("min_java_version")

        # Parse dependencies
        deps_list = data.get("dependencies", [])
        dependencies = [LockedDependency.from_dict(dep) for dep in deps_list]

        # Parse entrypoints
        entrypoints_section = data.get("entrypoints", {})
        default_entrypoint = entrypoints_section.pop("default", None)
        entrypoints = entrypoints_section

        lockfile = cls(
            dependencies=dependencies,
            environment_name=environment_name,
            min_java_version=min_java_version,
            entrypoints=entrypoints,
            default_entrypoint=default_entrypoint,
            jgo_version=jgo_version,
        )

        # Restore generated timestamp if available
        if "generated" in metadata:
            try:
                lockfile.generated = datetime.fromisoformat(metadata["generated"])
            except ValueError:
                pass  # Use current time if parsing fails

        return lockfile

    def save(self, path: Path):
        """
        Save this lock file to jgo.lock.toml.

        Args:
            path: Path to save jgo.lock.toml file
        """
        path = Path(path)
        data = self._to_dict()

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def _to_dict(self) -> dict:
        """Convert LockFile to dict for TOML serialization."""
        data = {}

        # [metadata] section
        metadata = {
            "generated": self.generated.isoformat(),
            "jgo_version": self.jgo_version,
        }
        data["metadata"] = metadata

        # [environment] section
        env_section = {}
        if self.environment_name:
            env_section["name"] = self.environment_name
        if self.min_java_version is not None:
            env_section["min_java_version"] = self.min_java_version
        if env_section:
            data["environment"] = env_section

        # [[dependencies]] array
        data["dependencies"] = [dep.to_dict() for dep in self.dependencies]

        # [entrypoints] section
        if self.entrypoints or self.default_entrypoint:
            entrypoints_section = dict(self.entrypoints)
            if self.default_entrypoint:
                entrypoints_section["default"] = self.default_entrypoint
            data["entrypoints"] = entrypoints_section

        return data

    def verify_checksums(self, maven_repo: Path) -> List[str]:
        """
        Verify that all locked dependencies still match their checksums.

        Args:
            maven_repo: Path to Maven repository (usually ~/.m2/repository)

        Returns:
            List of error messages (empty if all verified successfully)
        """
        errors = []
        maven_repo = Path(maven_repo)

        for dep in self.dependencies:
            if not dep.sha256:
                continue  # Skip if no checksum recorded

            # Construct path to artifact in Maven repo
            artifact_path = (
                maven_repo
                / dep.groupId.replace(".", "/")
                / dep.artifactId
                / dep.version
                / f"{dep.artifactId}-{dep.version}"
            )
            if dep.classifier:
                artifact_path = Path(str(artifact_path) + f"-{dep.classifier}")
            artifact_path = Path(str(artifact_path) + f".{dep.packaging}")

            if not artifact_path.exists():
                errors.append(
                    f"{dep.groupId}:{dep.artifactId}:{dep.version} "
                    f"not found at {artifact_path}"
                )
                continue

            # Compute actual checksum
            actual_sha256 = compute_sha256(artifact_path)
            if actual_sha256 != dep.sha256:
                errors.append(
                    f"{dep.groupId}:{dep.artifactId}:{dep.version} "
                    f"checksum mismatch: expected {dep.sha256}, got {actual_sha256}"
                )

        return errors

    def __repr__(self) -> str:
        return (
            f"LockFile({len(self.dependencies)} deps, "
            f"generated={self.generated.isoformat()})"
        )


def compute_sha256(path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        path: Path to file

    Returns:
        Hex-encoded SHA256 checksum
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
