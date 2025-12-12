"""
Maven POM (Project Object Model) parsing and handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .core import XML, Component

if TYPE_CHECKING:
    from .core import Artifact, Dependency, MavenContext


class POM(XML):
    """
    Convenience wrapper around a Maven POM XML document.
    """

    def __init__(self, source: Path | str, context: MavenContext | None = None):
        super().__init__(source, context)

    def artifact(self) -> Artifact:
        """
        Get an Artifact object representing this POM.
        """
        project = self.context.project(self.groupId, self.artifactId)
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
            parent_pom = POM(parent_path, self.context)
            if (
                g == parent_pom.groupId
                and a == parent_pom.artifactId
                and v == parent_pom.version
            ):
                return parent_pom

        pom_artifact = (
            self.context.project(g, a).at_version(v).artifact(packaging="pom")
        )
        return POM(pom_artifact.resolve(), self.context)

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
        return [self.context.dependency(el) for el in self.elements(xpath)]


def create_pom(components: list[Component], boms: list[Component] | None) -> POM:
    """
    Create a synthetic wrapper POM for multi-component resolution.

    Args:
        components: List of components to add as dependencies
        boms: Optional list of components to import in dependencyManagement

    Returns:
        POM object created from synthetic XML string
    """

    # Generate the POM XML content
    pom_xml = generate_pom_xml(components, boms)

    # Create POM object from XML string
    return POM(pom_xml, components[0].context)


def generate_pom_xml(
    components: list[Component], boms: list[Component] | None = None
) -> str:
    """
    Generate a wrapper POM XML string for multi-component resolution.

    This POM includes:
    - All components as direct dependencies
    - BOMs in dependencyManagement section (if provided)
    - Repository configuration from the first component's context

    Args:
        components: List of components to add as dependencies
        boms: Optional list of components to import in dependencyManagement

    Returns:
        Complete POM XML as a string
    """
    if not components:
        raise ValueError("At least one component is required")

    if boms is None:
        boms = []

    # Generate dependencyManagement section
    dep_mgmt_entries = []
    for bom in boms:
        dep_mgmt_entries.append(
            f"""        <dependency>
            <groupId>{bom.groupId}</groupId>
            <artifactId>{bom.artifactId}</artifactId>
            <version>{bom.resolved_version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>"""
        )

    dep_mgmt_section = "\n".join(dep_mgmt_entries) if dep_mgmt_entries else ""
    dep_mgmt_block = (
        f"""
    <dependencyManagement>
        <dependencies>
{dep_mgmt_section}
        </dependencies>
    </dependencyManagement>
"""
        if dep_mgmt_section
        else ""
    )

    # Generate dependencies section
    dep_entries = []
    for component in components:
        dep_entries.append(
            f"""        <dependency>
            <groupId>{component.groupId}</groupId>
            <artifactId>{component.artifactId}</artifactId>
            <version>{component.resolved_version}</version>
        </dependency>"""
        )

    deps_section = "\n".join(dep_entries)

    # Generate repositories section
    repos_entries = []
    for repo_id, repo_url in components[0].context.remote_repos.items():
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

    # Generate complete POM XML
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>org.apposed.jgo</groupId>
    <artifactId>INTERNAL-WRAPPER</artifactId>
    <version>0-SNAPSHOT</version>
{dep_mgmt_block}
    <dependencies>
{deps_section}
    </dependencies>
{repositories_block}</project>
"""


def write_pom(pom: POM, dest: Path | str) -> None:
    Path(dest).write_text(pom.source)


def write_temp_pom(pom: POM) -> Path:
    """
    Write a POM object to a temporary file.

    Args:
        pom: POM object to write

    Returns:
        Path to the generated temporary POM file
    """
    import tempfile

    temp_file = Path(tempfile.mktemp(suffix=".pom.xml", prefix="jgo-"))
    write_pom(pom, temp_file)

    return temp_file
