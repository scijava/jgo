"""
Core Maven data structures and configuration.

This module provides "smart" data structures and logic for Maven concepts.
Unlike the simple data structures in jgo.parse, these classes actively perform
Maven operations:
- Version resolution (RELEASE → newest release version, LATEST → latest snapshot)
- Metadata fetching and caching
- Artifact downloading from repositories
- POM parsing and interpolation
- Dependency management
- Repository configuration

The main classes form a hierarchy:
- MavenContext: Configuration (repositories, cache, resolver)
- Project [G:A]: A groupId:artifactId (G:A) pair with metadata access
- Component [G:A:V]: A Project at a specific version (V)
- Artifact [G:A:P:C:V]: One file of a Component, with classifier (C) and packaging (P)
- Dependency [G:A:P:C:V:S]: An Artifact with scope, optional flag, and exclusions

For simple/low-level data structures without Maven logic, see the jgo.parse subpackage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import md5, sha1
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from ..constants import DEFAULT_MAVEN_REPO, MAVEN_CENTRAL_URL
from ..parse.coordinate import Coordinate, coord2str
from ..util.io import binary, text

if TYPE_CHECKING:
    from .metadata import Metadata
    from .pom import POM
    from .resolver import Resolver

# -- Constants --

DEFAULT_LOCAL_REPOS = []
DEFAULT_REMOTE_REPOS = {"central": MAVEN_CENTRAL_URL}
DEFAULT_CLASSIFIER = ""
DEFAULT_PACKAGING = "jar"


class MavenContext:
    """
    Maven configuration and settings.
    * Local repo cache folder.
    * Local repository storage folders.
    * Remote repository name:URL pairs.
    * Artifact resolution mechanism.
    """

    def __init__(
        self,
        repo_cache: Path | None = None,
        local_repos: list[Path] | None = None,
        remote_repos: dict[str, str] | None = None,
        resolver: Resolver | None = None,
    ):
        """
        Create a Maven context.

        Args:
            repo_cache:
                Optional path to Maven local repository cache directory, i.e. destination
                of `mvn install`. Maven typically uses ~/.m2/repository by default.
                This directory is treated as *read-write* by this library, e.g.
                the download() function will store downloaded artifacts there.
                If no local repository cache path is given, Maven defaults will be used
                (M2_REPO environment variable, or ~/.m2/repository by default).
            local_repos:
                Optional list of Maven repository storage local paths to check for artifacts.
                These are real Maven repositories, such as those managed by a Sonatype Nexus v2 instance,
                i.e. ultimate destinations of `mvn deploy`, *not* local repository caches!
                These directories are treated as *read-only* by this library.
                If no local repository paths are given, none will be inferred.
            remote_repos:
                Optional dict of remote name:URL pairs, with each URL corresponding
                to a remote Maven repository accessible via HTTP/HTTPS.
                If no remote repository paths are given, only Maven Central will be used.
            resolver:
                Optional mechanism to use for resolving local paths to artifacts.
                By default, the PythonResolver will be used.
        """
        self.repo_cache: Path = repo_cache or Path(
            environ.get("M2_REPO", str(DEFAULT_MAVEN_REPO))
        )
        self.local_repos: list[Path] = (
            DEFAULT_LOCAL_REPOS if local_repos is None else local_repos
        ).copy()
        self.remote_repos: dict[str, str] = (
            DEFAULT_REMOTE_REPOS if remote_repos is None else remote_repos
        ).copy()
        # Import here to avoid circular dependency
        if resolver is None:
            from .resolver import PythonResolver

            resolver = PythonResolver()
        self.resolver: Resolver = resolver

    def project(self, groupId: str, artifactId: str) -> "Project":
        """
        Get a project (G:A) with the given groupId and artifactId.

        Args:
            groupId: The groupId of the project.
            artifactId: The artifactId of the project.

        Returns:
            The Project object.
        """
        return Project(self, groupId, artifactId)

    def parse_dependency_element(self, el) -> "Dependency":
        """
        Parse a <dependency> XML element into a Dependency object.

        This delegates to pom.py for XML parsing, then uses create_dependency
        to build the Dependency object.

        Args:
            el: The XML element from which to create the dependency.

        Returns:
            The Dependency object.
        """
        from .pom import parse_dependency_element_to_coordinate

        # Parse XML element to Coordinate (pom.py handles ElementTree)
        coord, exclusion_tuples = parse_dependency_element_to_coordinate(el)

        # Validate required fields
        assert coord.groupId and coord.artifactId, (
            f"Invalid dependency: groupId={coord.groupId}, artifactId={coord.artifactId}"
        )

        # Convert exclusion tuples to Project objects
        exclusions = [self.project(g, a) for g, a in exclusion_tuples if g and a]

        # Use create_dependency to build the Dependency
        return self.create_dependency(coord, exclusions)

    def create_dependency(
        self,
        coordinate: Coordinate | str,
        exclusions: Iterable[Project] | None = None,
    ) -> "Dependency":
        """
        Create a Dependency object from a Maven coordinate.

        Args:
            coordinate: The Maven coordinate to convert to a Dependency.
            exclusions: Optional list of Project exclusions.

        Returns:
            The Dependency object.
        """
        coord = Coordinate.parse(coordinate)
        groupId = coord.groupId
        artifactId = coord.artifactId
        version = coord.version
        classifier = coord.classifier or DEFAULT_CLASSIFIER
        packaging = coord.packaging or DEFAULT_PACKAGING
        scope = coord.scope
        optional = coord.optional or False

        project = self.project(groupId, artifactId)
        component = project.at_version(version) if version else project.at_version("")
        artifact = component.artifact(classifier, packaging)
        return Dependency(artifact, scope, optional, exclusions or [])

    def pom_to_artifact(self, pom: POM) -> "Artifact":
        """
        Create an Artifact object representing the given POM.

        Args:
            pom: The POM to convert to an Artifact.

        Returns:
            The Artifact object.
        """
        project = self.project(pom.groupId, pom.artifactId)
        return project.at_version(pom.version).artifact(packaging="pom")

    def pom_parent(self, pom: POM) -> "POM | None":
        """
        Resolve and return the parent POM, or None if no parent is declared.

        Args:
            pom: The POM whose parent to resolve.

        Returns:
            The parent POM object, or None if no parent.
        """
        from .pom import POM

        if not pom.element("parent"):
            return None

        g = pom.value("parent/groupId")
        a = pom.value("parent/artifactId")
        v = pom.value("parent/version")
        assert g and a and v
        relativePath = pom.value("parent/relativePath")

        if (
            isinstance(pom.source, Path)
            and relativePath
            and (parent_path := pom.source / relativePath).exists()
        ):
            # Use locally available parent POM file.
            parent_pom = POM(parent_path)
            if (
                g == parent_pom.groupId
                and a == parent_pom.artifactId
                and v == parent_pom.version
            ):
                return parent_pom

        pom_artifact = self.project(g, a).at_version(v).artifact(packaging="pom")
        return POM(pom_artifact.resolve())

    def pom_dependencies(self, pom: POM, managed: bool = False) -> list["Dependency"]:
        """
        Extract dependencies from POM as Dependency objects.

        Args:
            pom: The POM from which to extract dependencies.
            managed: If True, extract from dependencyManagement instead of dependencies.

        Returns:
            List of Dependency objects.
        """
        xpath = "dependencies/dependency"
        if managed:
            xpath = f"dependencyManagement/{xpath}"
        return [self.parse_dependency_element(el) for el in pom.elements(xpath)]


class Project:
    """
    This is a Maven project: i.e. a groupId+artifactId (G:A) pair.
    """

    def __init__(self, context: MavenContext, groupId: str, artifactId: str):
        self.context = context
        self.groupId = groupId
        self.artifactId = artifactId
        self._metadata: Metadata | None = None

    def __eq__(self, other):
        return (
            other is not None
            and self.groupId == other.groupId
            and self.artifactId == other.artifactId
        )

    def __hash__(self):
        return hash((self.groupId, self.artifactId))

    def __str__(self):
        return coord2str(self.groupId, self.artifactId)

    @property
    def path_prefix(self) -> Path:
        """
        Relative directory where artifacts of this project are organized.
        E.g. org.jruby:jruby-core -> org/jruby/jruby-core
        """
        return Path(*self.groupId.split("."), self.artifactId)

    def at_version(self, version: str) -> "Component":
        """
        Fix this project (G:A) at a particular version (G:A:V).

        Args:
            version: The version of the project.

        Returns:
            Component at the given version.
        """
        return Component(self, version)

    @property
    def metadata(self) -> Metadata:
        """Maven metadata about this project, encompassing all known sources."""
        if self._metadata is None:
            from .metadata import Metadatas, MetadataXML

            # Aggregate all locally available project maven-metadata.xml sources.
            repo_cache_dir = self.context.repo_cache / self.path_prefix
            paths = [p for p in repo_cache_dir.glob("maven-metadata*.xml")] + [
                r / self.path_prefix / "maven-metadata.xml"
                for r in self.context.local_repos
            ]
            self._metadata = Metadatas([MetadataXML(p) for p in paths if p.exists()])
        return self._metadata

    def update(self) -> None:
        """Update metadata from remote sources."""
        import requests

        repo_cache_dir = self.context.repo_cache / self.path_prefix
        repo_cache_dir.mkdir(parents=True, exist_ok=True)

        # Try to fetch maven-metadata.xml from each remote repository
        for repo_name, repo_url in self.context.remote_repos.items():
            metadata_url = f"{repo_url}/{self.path_prefix}/maven-metadata.xml"
            try:
                response = requests.get(metadata_url)
                if response.status_code == 200:
                    # Save to local cache with repo name suffix
                    metadata_file = repo_cache_dir / f"maven-metadata-{repo_name}.xml"
                    with open(metadata_file, "wb") as f:
                        f.write(response.content)
            except Exception:
                # Silently ignore failures - metadata might not be available
                pass

        # Force reload of metadata
        self._metadata = None

    @property
    def release(self) -> str:
        """
        The newest release version of this project.
        This is the equivalent of Maven's RELEASE version.
        """
        return self.metadata.release

    @property
    def latest(self) -> str:
        """
        The latest SNAPSHOT version of this project.
        This is the equivalent of Maven's LATEST version.
        """
        return self.metadata.latest

    def versions(
        self, releases: bool = True, snapshots: bool = False, locked: bool = False
    ) -> list["Component"]:
        """
        Get a list of all known versions of this project.

        Args:
            releases:
                If True, include release versions (those not ending in -SNAPSHOT) in the results.
            snapshots:
                If True, include snapshot versions (those ending in -SNAPSHOT) in the results.
            locked:
                If True, returned snapshot versions will include the timestamp or "lock" flavor
                of the version strings;
                For example: 2.94.3-20230706.150124-1 rather than 2.94.3-SNAPSHOT.
                As such, there may be more entries returned than when this flag is False.

        Returns:
            List of Component objects, each of which represents a known version.
        """
        # TODO: Think about whether multiple timestamped snapshots at the same snapshot
        # version should be one Component, or multiple Components.
        if locked:
            raise RuntimeError("Locked snapshot reporting is unimplemented")
        return [
            self.at_version(v)
            for v in self.metadata.versions
            if (
                (snapshots and v.endswith("-SNAPSHOT"))
                or (releases and not v.endswith("-SNAPSHOT"))
            )
        ]


class Component:
    """
    This is a Project at a particular version -- i.e. a G:A:V.
    One POM per component.
    """

    def __init__(self, project: Project, version: str):
        self.project = project
        self.version = version
        self._resolved_version = None

    def __eq__(self, other):
        return (
            other is not None
            and self.project == other.project
            and self.version == other.version
        )

    def __hash__(self):
        return hash((self.project, self.version))

    def __str__(self):
        return coord2str(self.groupId, self.artifactId, self.resolved_version)

    @property
    def context(self) -> MavenContext:
        """The component's Maven context."""
        return self.project.context

    @property
    def groupId(self) -> str:
        """The component's groupId."""
        return self.project.groupId

    @property
    def artifactId(self) -> str:
        """The component's artifactId."""
        return self.project.artifactId

    @property
    def resolved_version(self) -> str:
        """
        Get the resolved version, converting RELEASE/LATEST tokens to actual versions.
        """
        if self._resolved_version is not None:
            return self._resolved_version

        # Check if version needs resolution
        if self.version in ("RELEASE", "LATEST"):
            # Fetch metadata from remote if needed
            if not self.project.metadata or not self.project.metadata.versions:
                self.project.update()

            # Resolve to actual version
            if self.version == "RELEASE":
                resolved = self.project.release
            else:  # LATEST
                resolved = self.project.latest

            if not resolved:
                raise RuntimeError(
                    f"Could not resolve {self.version} version for "
                    f"{self.project.groupId}:{self.project.artifactId}"
                )

            self._resolved_version = resolved
            return resolved

        # Version is already concrete
        return self.version

    @property
    def path_prefix(self) -> Path:
        """
        Relative directory where artifacts of this component are organized.
        E.g. org.jruby:jruby-core:9.3.3.0 -> org/jruby/jruby-core/9.3.3.0
        """
        return self.project.path_prefix / self.resolved_version

    def artifact(
        self, classifier: str = DEFAULT_CLASSIFIER, packaging: str = DEFAULT_PACKAGING
    ) -> "Artifact":
        """
        Get an artifact (G:A:P:C:V) associated with this component.

        Args:
            classifier: Classifier of the artifact.
            packaging: Packaging/type of the artifact.

        Returns:
            The Artifact object representing this component
            with particular classifier and packaging.
        """
        return Artifact(self, classifier, packaging)

    def pom(self) -> POM:
        """
        Get a data structure with the contents of the POM.

        Returns:
            The POM content.
        """
        from .pom import POM

        pom_artifact = self.artifact(packaging="pom")
        return POM(pom_artifact.resolve())


class Artifact:
    """
    This is a Component plus classifier and packaging (G:A:P:C:V).
    One file per artifact.
    """

    def __init__(
        self,
        component: Component,
        classifier: str = DEFAULT_CLASSIFIER,
        packaging: str = DEFAULT_PACKAGING,
    ):
        self.component = component
        self.classifier = classifier
        self.packaging = packaging

    def __eq__(self, other):
        return (
            other is not None
            and self.component == other.component
            and self.classifier == other.classifier
            and self.packaging == other.packaging
        )

    def __hash__(self):
        return hash((self.component, self.classifier, self.packaging))

    def __str__(self):
        return coord2str(
            self.groupId, self.artifactId, self.version, self.classifier, self.packaging
        )

    @property
    def context(self) -> MavenContext:
        return self.component.context

    @property
    def groupId(self) -> str:
        """The artifact's groupId."""
        return self.component.groupId

    @property
    def artifactId(self) -> str:
        """The artifact's artifactId."""
        return self.component.artifactId

    @property
    def version(self) -> str:
        """The artifact's version (resolved if RELEASE/LATEST)."""
        return self.component.resolved_version

    @property
    def filename(self) -> str:
        """
        Filename portion of the artifact path. E.g.:
        - g=org.python a=jython v=2.7.0 -> jython-2.7.0.jar
        - g=org.lwjgl a=lwjgl v=3.3.1 c=natives-linux -> lwjgl-3.3.1-natives-linux.jar
        - g=org.scijava a=scijava-common v=2.94.2 p=pom -> scijava-common-2.94.2.pom
        """
        classifier_suffix = f"-{self.classifier}" if self.classifier else ""
        return f"{self.artifactId}-{self.component.resolved_version}{classifier_suffix}.{self.packaging}"

    @property
    def cached_path(self) -> Path | None:
        """
        Path to the artifact in the linked context's local repository cache.
        Might not actually exist! This just returns where it *would be* if present.
        """
        return (
            self.context.repo_cache / self.component.path_prefix / self.filename
            if self.context.repo_cache
            else None
        )

    def resolve(self) -> Path:
        """
        Resolve a local path to the artifact, downloading it as needed:

        1. If present in the linked local repository cache, use that path.
        2. Else if present in a linked locally available repository storage directory,
           use that path.
        3. Otherwise, invoke the context's resolver to download it.
        """

        # Check Maven local repository cache first if available.
        cached_file = self.cached_path
        if cached_file and cached_file.exists():
            return cached_file

        # Check any locally available Maven repository storage directories.
        for base in self.context.local_repos:
            # TODO: Be smarter than this when version is a SNAPSHOT,
            # because local repo storage has timestamped SNAPSHOT filenames.
            p = base / self.component.path_prefix / self.filename
            if p.exists():
                return p

        # Artifact was not found locally; need to download it.
        return self.context.resolver.download(self)

    def md5(self) -> str:
        """Compute the MD5 hash of the artifact."""
        return self._checksum("md5", md5)

    def sha1(self) -> str:
        """Compute the SHA1 hash of the artifact."""
        return self._checksum("sha1", sha1)

    def _checksum(self, suffix, func):
        p = self.resolve()
        checksum_path = p.parent / f"{p.name}.{suffix}"
        return text(checksum_path) or func(binary(p)).hexdigest()


class Dependency:
    """
    This is an Artifact with scope, optional flag, and exclusions list.
    """

    def __init__(
        self,
        artifact: Artifact,
        scope: str = None,
        optional: bool = False,
        exclusions: Iterable[Project] = None,
    ):
        # NB: scope can be None here - it will be set by dependency management injection
        # or default to "compile" later in the model building process
        self.artifact = artifact
        self.scope = scope
        self.optional = optional
        self.exclusions: tuple[Project] = (
            tuple() if exclusions is None else tuple(exclusions)
        )

    def __str__(self):
        return coord2str(
            self.groupId,
            self.artifactId,
            self.version,
            self.classifier,
            self.type,
            self.scope,
            self.optional,
        )

    @property
    def context(self) -> MavenContext:
        """The dependency's Maven context."""
        return self.artifact.context

    @property
    def groupId(self) -> str:
        """The dependency's groupId."""
        return self.artifact.groupId

    @property
    def artifactId(self) -> str:
        """The dependency's artifactId."""
        return self.artifact.artifactId

    @property
    def version(self) -> str:
        """The dependency's version."""
        return self.artifact.version

    @property
    def classifier(self) -> str:
        """The dependency's classifier."""
        return self.artifact.classifier

    @property
    def type(self) -> str:
        """The dependency's packaging/type."""
        return self.artifact.packaging

    def set_version(self, version: str) -> None:
        """
        Alter the dependency's version.

        Args:
            version: The new version to use.
        """
        assert isinstance(version, str)
        self.artifact.component.version = version
        self.artifact.component._resolved_version = None


@dataclass
class DependencyNode:
    """
    Represents a dependency in a dependency tree.

    This data structure is built during dependency resolution and captures
    the parent-child relationships discovered by the breadth-first traversal.
    It's also used for formatting dependency lists and trees.
    """

    dep: Dependency
    children: list["DependencyNode"] = field(default_factory=list)

    def __str__(self):
        return str(self.dep)


def create_pom(components: list[Component], boms: list[Component] | None) -> POM:
    """
    Create a synthetic wrapper POM for multi-component resolution.

    Args:
        components: List of components to add as dependencies
        boms: Optional list of components to import in dependencyManagement

    Returns:
        POM object created from synthetic XML string
    """
    from .pom import POM

    # Generate the POM XML content
    pom_xml = generate_pom_xml(components, boms)

    # Create POM object from XML string
    return POM(pom_xml)


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
