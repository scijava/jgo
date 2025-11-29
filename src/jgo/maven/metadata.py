"""
Maven metadata handling (maven-metadata.xml files).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Iterable, List, Optional

from .core import XML, MavenContext
from .util import ts2dt


class Metadata(ABC):
    """Abstract base class for Maven metadata."""

    @property
    @abstractmethod
    def groupId(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def artifactId(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def lastUpdated(self) -> Optional[datetime]:
        ...

    @property
    @abstractmethod
    def latest(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def versions(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def lastVersion(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def release(self) -> Optional[str]:
        ...


class MetadataXML(XML, Metadata):
    """
    Convenience wrapper around a maven-metadata.xml document.
    """

    def __init__(self, source: Path | str, maven_context: Optional[MavenContext] = None):
        super().__init__(source, maven_context)

    @property
    def groupId(self) -> Optional[str]:
        return self.value("groupId")

    @property
    def artifactId(self) -> Optional[str]:
        return self.value("artifactId")

    @property
    def lastUpdated(self) -> Optional[datetime]:
        value = self.value("versioning/lastUpdated")
        return ts2dt(value) if value else None

    @property
    def latest(self) -> Optional[str]:
        # WARNING: The <latest> value is often wrong, for reasons I don't know.
        # However, the last <version> under <versions> has the correct value.
        # Consider using lastVersion instead of latest.
        return self.value("versioning/latest")

    @property
    def versions(self) -> List[str]:
        return self.values("versioning/versions/version")

    @property
    def lastVersion(self) -> Optional[str]:
        return vs[-1] if (vs := self.versions) else None

    @property
    def release(self) -> Optional[str]:
        return self.value("versioning/release")


class Metadatas(Metadata):
    """
    A unified Maven metadata combined over a collection of individual Maven metadata.
    The typical use case for this class is to aggregate multiple maven-metadata.xml files
    describing the same project, across multiple local repository cache and storage directories.
    """

    def __init__(self, metadatas: Iterable[Metadata]):
        self.metadatas: List[Metadata] = sorted(
            metadatas, key=lambda m: m.lastUpdated or datetime.min
        )
        for a, b in combinations(self.metadatas, 2):
            assert a.groupId == b.groupId and a.artifactId == b.artifactId

    @property
    def groupId(self) -> Optional[str]:
        return self.metadatas[0].groupId if self.metadatas else None

    @property
    def artifactId(self) -> Optional[str]:
        return self.metadatas[0].artifactId if self.metadatas else None

    @property
    def lastUpdated(self) -> Optional[datetime]:
        return self.metadatas[-1].lastUpdated if self.metadatas else None

    @property
    def latest(self) -> Optional[str]:
        return next((m.latest for m in reversed(self.metadatas) if m.latest), None)

    @property
    def versions(self) -> List[str]:
        return [v for m in self.metadatas for v in m.versions]

    @property
    def lastVersion(self) -> Optional[str]:
        return versions[-1] if (versions := self.versions) else None

    @property
    def release(self) -> Optional[str]:
        return next((m.release for m in reversed(self.metadatas) if m.release), None)
