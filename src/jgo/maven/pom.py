"""
Maven POM (Project Object Model) parsing and handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import XML, Artifact, Dependency, MavenContext


class POM(XML):
    """
    Convenience wrapper around a Maven POM XML document.
    """

    def __init__(self, source: Path | str, maven_context: MavenContext | None = None):
        super().__init__(source, maven_context)

    def artifact(self) -> Artifact:
        """
        Get an Artifact object representing this POM.
        """
        project = self.maven_context.project(self.groupId, self.artifactId)
        return project.at_version(self.version).artifact(packaging="pom")

    def parent(self) -> "POM" | None:
        """
        Get POM data for this POM's parent POM, or None if no parent is declared.
        """
        if not self.element("parent"):
            return None

        g = self.value("parent/groupId")
        a = self.value("parent/artifactId")
        v = self.value("parent/version")
        assert g and a and v
        relativePath = self.value("parent/relativePath")

        if (
            isinstance(self.source, Path)
            and relativePath
            and (parent_path := self.source / relativePath).exists()
        ):
            # Use locally available parent POM file.
            parent_pom = POM(parent_path, self.maven_context)
            if (
                g == parent_pom.groupId
                and a == parent_pom.artifactId
                and v == parent_pom.version
            ):
                return parent_pom

        pom_artifact = (
            self.maven_context.project(g, a).at_version(v).artifact(packaging="pom")
        )
        return POM(pom_artifact.resolve(), self.maven_context)

    @property
    def groupId(self) -> str | None:
        """The POM's <groupId> (or <parent><groupId>) value."""
        return self.value("groupId") or self.value("parent/groupId")

    @property
    def artifactId(self) -> str | None:
        """The POM's <artifactId> value."""
        return self.value("artifactId")

    @property
    def version(self) -> str | None:
        """The POM's <version> (or <parent><version>) value."""
        return self.value("version") or self.value("parent/version")

    @property
    def name(self) -> str | None:
        """The POM's <name> value."""
        return self.value("name")

    @property
    def description(self) -> str | None:
        """The POM's <description> value."""
        return self.value("description")

    @property
    def scmURL(self) -> str | None:
        """The POM's <scm><url> value."""
        return self.value("scm/url")

    @property
    def issuesURL(self) -> str | None:
        """The POM's <issueManagement><url> value."""
        return self.value("issueManagement/url")

    @property
    def ciURL(self) -> str | None:
        """The POM's <ciManagement><url> value."""
        return self.value("ciManagement/url")

    @property
    def developers(self) -> list[dict[str, Any]]:
        """Dictionary of the POM's <developer> entries."""
        return self._people("developers/developer")

    @property
    def contributors(self) -> list[dict[str, Any]]:
        """Dictionary of the POM's <contributor> entries."""
        return self._people("contributors/contributor")

    def _people(self, path: str) -> list[dict[str, Any]]:
        people = []
        for el in self.elements(path):
            person: dict[str, Any] = {}
            for child in el:
                if len(child) == 0:
                    person[child.tag] = child.text
                else:
                    if child.tag == "properties":
                        for grand in child:
                            person[grand.tag] = grand.text
                    else:
                        person[child.tag] = [grand.text for grand in child]
            people.append(person)
        return people

    @property
    def properties(self) -> dict[str, str]:
        """Dictionary of key/value pairs from the POM's <properties>."""
        return {el.tag: el.text for el in self.elements("properties/*")}

    def dependencies(self, managed: bool = False) -> list[Dependency]:
        """
        Gets a list of the POM's <dependency> entries,
        represented as Dependency objects.

        :param managed:
            If True, dependency entries will correspond to the POM's
            <dependencyManagement> instead of <dependencies>.
        :return: The list of Dependency objects.
        """
        xpath = "dependencies/dependency"
        if managed:
            xpath = f"dependencyManagement/{xpath}"
        return [self.maven_context.dependency(el) for el in self.elements(xpath)]
