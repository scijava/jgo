"""
Maven metadata handling (maven-metadata.xml files).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from itertools import combinations
from pathlib import Path
from re import match
from typing import TYPE_CHECKING, Iterable

from .pom import XML

if TYPE_CHECKING:
    pass


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
        # WARNING: The <latest> value is often wrong, for reasons I don't know.
        # However, the last <version> under <versions> has the correct value.
        # Consider using lastVersion instead of latest.
        return self.value("versioning/latest")

    @property
    def versions(self) -> list[str]:
        return self.values("versioning/versions/version")

    @property
    def lastVersion(self) -> str | None:
        return vs[-1] if (vs := self.versions) else None

    @property
    def release(self) -> str | None:
        return self.value("versioning/release")


class Metadatas(Metadata):
    """
    A unified Maven metadata combined over a collection of individual Maven metadata.
    The typical use case for this class is to aggregate multiple maven-metadata.xml files
    describing the same project, across multiple local repository cache and storage directories.
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
        return next((m.latest for m in reversed(self.metadatas) if m.latest), None)

    @property
    def versions(self) -> list[str]:
        return [v for m in self.metadatas for v in m.versions]

    @property
    def lastVersion(self) -> str | None:
        return versions[-1] if (versions := self.versions) else None

    @property
    def release(self) -> str | None:
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
    return datetime(*map(int, m.groups()))  # noqa
