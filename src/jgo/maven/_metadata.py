"""
Maven metadata handling (maven-metadata.xml files).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from itertools import combinations
from re import match
from typing import TYPE_CHECKING, Iterable

from ._pom import XML

if TYPE_CHECKING:
    from pathlib import Path


class Metadata(ABC):
    """Abstract base class for Maven metadata."""

    @property
    @abstractmethod
    def groupId(self) -> str | None: ...

    @property
    @abstractmethod
    def artifactId(self) -> str | None: ...

    @property
    @abstractmethod
    def lastUpdated(self) -> datetime | None: ...

    @property
    @abstractmethod
    def latest(self) -> str | None: ...

    @property
    @abstractmethod
    def versions(self) -> list[str]: ...

    @property
    @abstractmethod
    def lastVersion(self) -> str | None: ...

    @property
    @abstractmethod
    def release(self) -> str | None: ...


class MetadataXML(XML, Metadata):
    """
    Convenience wrapper around a maven-metadata.xml document.
    """

    def __init__(self, source: Path | str):
        super().__init__(source)

    @property
    def groupId(self) -> str | None:
        return self.value("groupId")

    @property
    def artifactId(self) -> str | None:
        return self.value("artifactId")

    @property
    def lastUpdated(self) -> datetime | None:
        value = self.value("versioning/lastUpdated")
        return ts2dt(value) if value else None

    @property
    def latest(self) -> str | None:
        """
        The latest version from this metadata file's <latest> tag.

        NOTE: This faithfully returns the XML tag value, which may be absent
        or unreliable. The tag often reflects the newest version in this
        repository at the time the metadata was generated.

        WARNING: This only reflects the latest version in THIS repository.
        When multiple repositories are configured, use Project.latest instead
        for smart resolution across all repositories.

        See docs/version-resolution.md for details on version resolution behavior.
        """
        return self.value("versioning/latest")

    @property
    def versions(self) -> list[str]:
        return [
            v for v in self.values("versioning/versions/version") if v is not None
        ] or []

    @property
    def lastVersion(self) -> str | None:
        return vs[-1] if (vs := self.versions) else None

    @property
    def release(self) -> str | None:
        """
        The release version from this metadata file's <release> tag.

        WARNING: This only reflects the newest release in THIS repository.
        When multiple repositories are configured, use Project.release instead
        for smart resolution across all repositories.

        See docs/version-resolution.md for details on version resolution behavior.
        """
        return self.value("versioning/release")


class SnapshotMetadataXML(MetadataXML):
    """
    Convenience wrapper around a SNAPSHOT version's maven-metadata.xml document.

    This metadata file is located at the version level:
    e.g., groupId/artifactId/1.0-SNAPSHOT/maven-metadata.xml

    It contains timestamped build information for SNAPSHOT artifacts.
    """

    @property
    def snapshot_timestamp(self) -> str | None:
        """Get the snapshot timestamp (e.g., '20230706.150124')."""
        return self.value("versioning/snapshot/timestamp")

    @property
    def snapshot_build_number(self) -> int | None:
        """Get the snapshot build number (e.g., 1)."""
        value = self.value("versioning/snapshot/buildNumber")
        return int(value) if value else None

    def get_timestamped_version(
        self, packaging: str = "jar", classifier: str = ""
    ) -> str | None:
        """
        Get the timestamped version for a specific artifact type.

        Args:
            packaging: The artifact packaging/extension (e.g., 'jar', 'pom')
            classifier: Optional classifier (e.g., 'sources', 'javadoc')

        Returns:
            Timestamped version string (e.g., '2.94.3-20230706.150124-1'),
            or None if not found.
        """
        # First try to find exact match in snapshotVersions
        for el in self.elements("versioning/snapshotVersions/snapshotVersion"):
            ext = el.findtext("extension") or ""
            clf = el.findtext("classifier") or ""
            if ext == packaging and clf == classifier:
                return el.findtext("value")

        # Fallback: construct from snapshot timestamp and buildNumber
        timestamp = self.snapshot_timestamp
        build_num = self.snapshot_build_number
        version = self.value("version")

        if timestamp and build_num is not None and version:
            if version.endswith("-SNAPSHOT"):
                base = version[:-9]  # Remove "-SNAPSHOT"
                return f"{base}-{timestamp}-{build_num}"

        return None


class Metadatas(Metadata):
    """
    A unified Maven metadata combined over a collection of individual Maven metadata.
    The typical use case for this class is to aggregate multiple maven-metadata.xml files
    describing the same project, across multiple local repository cache and storage directories.

    NOTE: The `release` and `latest` properties use Maven-compatible resolution which has
    limitations when dealing with multiple repositories. For smart resolution, use the
    Project class instead. See docs/version-resolution.md for details.
    """

    def __init__(self, metadatas: Iterable[Metadata]):
        self.metadatas: list[Metadata] = sorted(
            metadatas, key=lambda m: m.lastUpdated or datetime.min
        )
        for a, b in combinations(self.metadatas, 2):
            assert a.groupId == b.groupId and a.artifactId == b.artifactId

    @property
    def groupId(self) -> str | None:
        return self.metadatas[0].groupId if self.metadatas else None

    @property
    def artifactId(self) -> str | None:
        return self.metadatas[0].artifactId if self.metadatas else None

    @property
    def lastUpdated(self) -> datetime | None:
        return self.metadatas[-1].lastUpdated if self.metadatas else None

    @property
    def latest(self) -> str | None:
        """
        The latest version using Maven-compatible resolution.

        Returns the latest version from the most recently updated repository
        (based on <lastUpdated> timestamp). This matches Maven's behavior but
        has limitations when artifacts are split across multiple repositories.

        WARNING: This may not return the truly most recent version. For smart
        resolution, use Project.latest instead.

        See docs/version-resolution.md for details on version resolution behavior.
        """
        return next((m.latest for m in reversed(self.metadatas) if m.latest), None)

    @property
    def versions(self) -> list[str]:
        return [v for m in self.metadatas for v in m.versions]

    @property
    def lastVersion(self) -> str | None:
        return versions[-1] if (versions := self.versions) else None

    @property
    def release(self) -> str | None:
        """
        The release version using Maven-compatible resolution.

        Returns the release version from the most recently updated repository
        (based on <lastUpdated> timestamp). This matches Maven's behavior but
        has a critical bug when newer releases exist in other repositories.

        WARNING: This may not return the truly newest release. For correct
        version comparison across all repositories, use Project.release instead.

        See docs/version-resolution.md for details on version resolution behavior.
        """
        return next((m.release for m in reversed(self.metadatas) if m.release), None)


def ts2dt(ts: str) -> datetime:
    """
    Convert a Maven-style timestamp string into a Python datetime object.

    Valid forms:
    * 20210702144918 (seen in <lastUpdated> in maven-metadata.xml)
    * 20210702.144917 (seen in deployed SNAPSHOT filenames and <snapshotVersion><value>)
    """
    m = match(r"(\d{4})(\d\d)(\d\d)\.?(\d\d)(\d\d)(\d\d)", ts)
    if not m:
        raise ValueError(f"Invalid timestamp: {ts}")
    return datetime(*map(int, m.groups()))  # type: ignore[arg-type]
